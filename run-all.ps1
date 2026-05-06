<#
Run-all: Provision Azure VM GPU and deploy ExLlamaV2 13B automatically.

Requirements (this script runs locally in PowerShell):
- `az` CLI already authenticated (`az login`).
- Windows with OpenSSH client available (for ssh/scp) or WSL.
- No interactive input is required; script is non-interactive.

#> 
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# non-interactive: allow running under restrictive ExecutionPolicy
try { Set-ExecutionPolicy Bypass -Scope Process -Force } catch {}

# Ensure Azure CLI 'az' is available in this pwsh session.
# If not found, try to prepend the common Azure CLI install folder to PATH.
try {
    $azProbe = Get-Command az -ErrorAction SilentlyContinue
    $azCmd = if ($azProbe) { $azProbe.Source } else { $null }
} catch {
    $azCmd = $null
}
if (-not $azCmd) {
    $defaultAzDir = 'C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin'
    if (Test-Path (Join-Path $defaultAzDir 'az.cmd')) {
        $env:PATH = "$defaultAzDir;$env:PATH"
        try {
            $azProbe = Get-Command az -ErrorAction SilentlyContinue
            $azCmd = if ($azProbe) { $azProbe.Source } else { $null }
        } catch {
            $azCmd = $null
        }
    }
}
if (-not $azCmd) {
    Write-Error "Azure CLI 'az' não encontrado. Instale o Azure CLI ou abra um terminal com 'az' no PATH." 
    exit 1
}

function Import-DotEnv([string]$path) {
    if (-Not (Test-Path $path)) { return }
    Get-Content $path | ForEach-Object {
        $line = $_.Trim()
        if ($line -eq '' -or $line.StartsWith('#')) { return }
        if ($line -match '^([^=]+)=(.*)$') {
            $k = $matches[1].Trim()
            $v = $matches[2].Trim('"')
                try {
                    Set-Item -Path "Env:\$k" -Value $v -ErrorAction Stop
                } catch {
                    [System.Environment]::SetEnvironmentVariable($k, $v, 'Process')
                }
        }
    }
}

function Invoke-Retry([ScriptBlock]$sb, [int]$attempts=3, [int]$delay=10) {
    for ($i=1; $i -le $attempts; $i++) {
        try {
            & $sb
            return $true
        } catch {
            Write-Warning "Attempt $i/$attempts failed: $($_.Exception.Message)"
            if ($i -eq $attempts) { throw $_ }
            Start-Sleep -Seconds $delay
        }
    }
}

function Exec([string]$cmd) {
    Write-Host "> $cmd"
    $process = Start-Process -FilePath pwsh -ArgumentList "-NoProfile","-Command",$cmd -NoNewWindow -PassThru -Wait -ErrorAction Stop
    if ($process.ExitCode -ne 0) { throw "Command failed ($($process.ExitCode)): $cmd" }
}

Write-Host "Loading environment variables from .env (if exists)"
Import-DotEnv "$PSScriptRoot\.env"

# Set variables (prefer .env values)
$subscriptionId = $env:AZURE_SUBSCRIPTION_ID
if (-not $subscriptionId) { $subscriptionId = $env:SUBSCRIPTION_ID }
$rg = $env:AZURE_RESOURCE_GROUP; if (-not $rg) { $rg = 'syntexa-rg' }
$location = $env:AZURE_LOCATION; if (-not $location) { $location = 'eastus' }
$vmName = $env:AZURE_VM_NAME; if (-not $vmName) { $vmName = 'exllama-vm' }
$vmSize = $env:AZURE_VM_SIZE; if (-not $vmSize) { $vmSize = 'Standard_NC6s_v3' }
$adminUser = $env:AZURE_ADMIN_USER; if (-not $adminUser) { $adminUser = 'azureuser' }
$sshPub = $env:SSH_PUB_PATH; if (-not $sshPub) { $sshPub = "$env:USERPROFILE\.ssh\id_rsa.pub" }
$sshKey = $env:SSH_PRIVATE_PATH; if (-not $sshKey) { $sshKey = "$env:USERPROFILE\.ssh\id_rsa" }

Write-Host "Using: ResourceGroup=$rg Location=$location VM=$vmName Size=$vmSize AdminUser=$adminUser"

# Verify az login
Write-Host "Verifying az authentication"
Invoke-Retry { az account show --output none }
if ($subscriptionId) { Invoke-Retry { az account set --subscription $subscriptionId | Out-Null } }

# Ensure SSH key exists, create if missing (robust generation via Start-Process)
if (-not (Test-Path $sshKey)) {
    Write-Host "SSH key not found at $sshKey - generating new key pair (ed25519)"
    $sshDir = Split-Path $sshKey -Parent
    if (-not (Test-Path $sshDir)) { New-Item -ItemType Directory -Path $sshDir -Force | Out-Null }
    $sshArgs = @('-t','ed25519','-N','', '-f', $sshKey)
    try {
            $proc = Start-Process -FilePath 'ssh-keygen' -ArgumentList $sshArgs -NoNewWindow -Wait -PassThru -ErrorAction Stop
        if ($proc.ExitCode -ne 0) { throw "ssh-keygen failed with exit code $($proc.ExitCode)" }
    } catch {
        Write-Error "Failed to generate SSH key: $_"
        throw $_
    }
}

if (-not (Test-Path $sshPub)) {
    # attempt to derive pub from private
    if (Test-Path $sshKey) {
        Write-Host "Generating public key from private key"
        ssh-keygen -y -f $sshKey > "$sshKey.pub"
        $sshPub = "$sshKey.pub"
    }
}

if (-not (Test-Path $sshPub)) { Write-Error "Public key not found at $sshPub after generation. Exiting."; exit 1 }

# fix permissions for private key on Windows
try { icacls $sshKey /inheritance:r | Out-Null; icacls $sshKey /grant:r "$env:USERNAME:F" | Out-Null } catch {}

Write-Host "Creating resource group $rg (idempotent)"
Invoke-Retry { az group create --name $rg --location $location --output none } 3 5

Write-Host "Creating VM $vmName (this can take several minutes)."
$pubKeyContent = Get-Content -Raw $sshPub
Invoke-Retry { az vm create --resource-group $rg --name $vmName --image Canonical:0001-com-ubuntu-server-jammy:22_04-lts-gen2 --size $vmSize --admin-username $adminUser --ssh-key-values $pubKeyContent --public-ip-sku Standard --output json | Out-Null } 3 15

Write-Host "Waiting for VM to be provisioned..."
Invoke-Retry { az vm wait --created --name $vmName --resource-group $rg } 6 10

Write-Host "Retrieving public IP..."
$ip = az vm list-ip-addresses --name $vmName --resource-group $rg --query "[0].virtualMachine.network.publicIpAddresses[0].ipAddress" -o tsv
if (-not $ip) { Write-Error "Failed to get public IP"; exit 1 }
Write-Host "VM public IP: $ip"

# Wait for SSH port
Write-Host "Waiting for SSH (port 22) to be reachable on $ip"
$sshOk = $false
for ($i=0; $i -lt 60; $i++) {
    try {
        $t = Test-NetConnection -ComputerName $ip -Port 22 -WarningAction SilentlyContinue
        if ($t.TcpTestSucceeded) { $sshOk = $true; break }
    } catch {}
    Start-Sleep -Seconds 5
}
if (-not $sshOk) { Write-Error "SSH port 22 not reachable on $ip"; exit 1 }

# Prepare HF token for remote script (if provided via env or .env)
$hfToken = $env:HF_TOKEN
$envFileBlock = ''
if ($hfToken) {
    # create a block that will write a secure env file on the VM
    $escaped = ($hfToken -replace '"','\"')
    $envFileBlock = @"
cat > /etc/exllama.env <<'EOF'
HF_TOKEN="$escaped"
HUGGINGFACE_HUB_TOKEN="$escaped"
EOF
chmod 600 /etc/exllama.env
"@
}

# Remote bootstrap script (runs on the VM via az run-command)
$remoteScript = @'
#!/bin/bash
set -e
LOG=/var/log/exllama_deploy.log
exec > >(tee -a $LOG) 2>&1
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y curl ca-certificates gnupg lsb-release unzip software-properties-common

# Install Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Try installing NVIDIA drivers/toolkit (best-effort)
DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends nvidia-driver-535 || true
distribution=$( . /etc/os-release; echo $ID$VERSION_ID )
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | apt-key add - || true
curl -s -L https://nvidia.github.io/nvidia-docker/ubuntu$(lsb_release -rs)/nvidia-docker.list | tee /etc/apt/sources.list.d/nvidia-docker.list || true
apt-get update || true
DEBIAN_FRONTEND=noninteractive apt-get install -y nvidia-container-toolkit || true
systemctl restart docker || true

# Validate GPU
for i in {1..10}; do
  if command -v nvidia-smi >/dev/null 2>&1; then
    if nvidia-smi >/dev/null 2>&1; then
      echo "nvidia-smi OK"; break
    fi
  fi
  echo "Waiting for nvidia-smi... ($i)"; sleep 6
done

mkdir -p /opt/exllama/models
chown -R $USER /opt/exllama || true

# Pull and run ExLlama container
docker pull ghcr.io/turboderp/exllamav2:latest || true

# If HF token provided, write secure env file and pass to container
${envFileBlock}

# Run container with model env (container expected to handle model download)
docker rm -f exllama 2>/dev/null || true
if [ -f /etc/exllama.env ]; then
    docker run -d --gpus all --name exllama -p 8000:8000 -v /opt/exllama/models:/models --env-file /etc/exllama.env -e MODEL_REPO="TheBloke/Llama-2-13B-GPTQ" ghcr.io/turboderp/exllamav2:latest || true
else
    docker run -d --gpus all --name exllama -p 8000:8000 -v /opt/exllama/models:/models -e MODEL_REPO="TheBloke/Llama-2-13B-GPTQ" ghcr.io/turboderp/exllamav2:latest || true
fi

# Wait for API
for i in {1..20}; do
  if curl -sf http://127.0.0.1:8000/health >/dev/null 2>&1; then
    echo "ExLlama API healthy"; exit 0
  fi
  echo "Waiting for ExLlama API... ($i)"; sleep 6
done
echo "ExLlama did not start within timeout"; exit 2
'@

# Inject the envFileBlock placeholder content safely (here-string was literal)
$remoteScript = $remoteScript -replace '\$\{envFileBlock\}', $envFileBlock

Write-Host "Uploading and executing bootstrap script via az vm run-command"
# Write script to temp file
$tmp = [System.IO.Path]::GetTempFileName()
Set-Content -Path $tmp -Value $remoteScript -Encoding UTF8
# invoke remote script (contains token only if HF_TOKEN set in env/.env)
Invoke-Retry { az vm run-command invoke --command-id RunShellScript --name $vmName --resource-group $rg --scripts "$(Get-Content $tmp -Raw)" --output json | Out-Null } 3 15

Write-Host "Checking ExLlama service on VM..."
try {
    $max=20; $ok=$false
    for ($i=0; $i -lt $max; $i++) {
        try {
            $res = Invoke-WebRequest -UseBasicParsing -Uri "http://$ip:8000/health" -TimeoutSec 5 -ErrorAction Stop
            if ($res.StatusCode -eq 200) { Write-Host "ExLlama ready at http://$ip:8000"; $ok=$true; break }
        } catch {
            Write-Host "Waiting for service... ($($i+1)/$max)"; Start-Sleep -Seconds 6
        }
    }
    if (-not $ok) {
        Write-Warning "Service did not become healthy; fetching docker logs..."
        $logs = az vm run-command invoke --command-id RunShellScript --name $vmName --resource-group $rg --scripts "docker logs exllama --tail 200 || true" -o json
        Write-Host "---- container logs ----"
        Write-Host $logs
        throw "ExLlama container failed to start"
    }
} catch {
    throw $_
}

Write-Host "Updating ansible inventory (ansible/inventory.ini) with exllama IP"
$inventoryPath = Join-Path $PSScriptRoot 'ansible\inventory.ini'
if (Test-Path $inventoryPath) {
    $content = Get-Content $inventoryPath -Raw
    $newEx = "[exllama]`r`n$ip ansible_user=$adminUser ansible_ssh_private_key_file=$sshKey`r`n"
    $content = [System.Text.RegularExpressions.Regex]::Replace($content, '(?ms)(\[exllama\].*?)(?=\n\[|$)', $newEx)
    Set-Content -Path $inventoryPath -Value $content -Encoding UTF8
}

Write-Host "Running Ansible playbook to update Hetzner backend (.env)"
try {
    Exec "ansible-playbook -i `"$inventoryPath`" `"$PSScriptRoot\\ansible\\playbook.yml`""
} catch {
    Write-Warning "Ansible playbook failed (continuing). Error: $_"
}

Write-Host "Deployment finished. ExLlama should be available at http://$ip:8000"
