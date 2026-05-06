<#
PowerShell wrapper: detect WSL and execute the Linux installer/deploy script inside WSL.
Usage: Run PowerShell as Administrator and execute this script.
#>
Set-StrictMode -Version Latest

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition

Write-Host "Verificando WSL..."
try {
    wsl -l >/dev/null 2>&1
} catch {
    Write-Host "WSL não encontrado. Instale o WSL ou execute o script equivalente em uma máquina Linux." -ForegroundColor Yellow
    exit 1
}

function Convert-WindowsPathToWsl($path) {
    $p = (Resolve-Path $path).ProviderPath
    $p = $p -replace "\\","/"
    if ($p -match '^([A-Za-z]):') {
        $drive = $matches[1].ToLower()
        $rest = $p.Substring(2)
        return "/mnt/$drive$rest"
    }
    return $p
}

$fullLinuxScript = Convert-WindowsPathToWsl((Join-Path $scriptPath "install_and_run_linux.sh"))

Write-Host "Executando script Linux no WSL: $fullLinuxScript"
wsl bash "$fullLinuxScript"
