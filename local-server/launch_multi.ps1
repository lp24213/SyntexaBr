# Syntexa Sovereign AI — Multi-Environment Launcher (PowerShell)
# Launches multiple server instances for load distribution

param(
    [int]$GpuPort = 8000,
    [int]$CpuPort1 = 8001,
    [int]$CpuPort2 = 8002,
    [int]$CpuPort3 = 8003,
    [string]$ModelDir = "./models/syntexa-export/merged"
)

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $scriptPath

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "  Syntexa Sovereign AI — Multi-Launch" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

function Start-Server($Name, $Port, $ModelDir, $UseGpu) {
    $env = @{}
    if (-not $UseGpu) {
        $env["CUDA_VISIBLE_DEVICES"] = ""
    }
    
    $cmd = "python server.py --port $Port --model-dir '$ModelDir'"
    Write-Host "[$Name] Starting on port $Port (GPU: $UseGpu)..." -ForegroundColor Green
    
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $cmd -WorkingDirectory $scriptPath
}

# 1. GPU instance (main model)
Start-Server -Name "GPU-MAIN" -Port $GpuPort -ModelDir $ModelDir -UseGpu $true

Start-Sleep -Seconds 5

# 2. CPU instance 1 (fast/backup)
Start-Server -Name "CPU-FAST" -Port $CpuPort1 -ModelDir $ModelDir -UseGpu $false

Start-Sleep -Seconds 2

# 3. CPU instance 2 (medium)
Start-Server -Name "CPU-MED" -Port $CpuPort2 -ModelDir $ModelDir -UseGpu $false

Start-Sleep -Seconds 2

# 4. CPU instance 3 (backup)
Start-Server -Name "CPU-BACKUP" -Port $CpuPort3 -ModelDir $ModelDir -UseGpu $false

Write-Host ""
Write-Host "All instances launched!" -ForegroundColor Green
Write-Host ""
Write-Host "Endpoints:" -ForegroundColor Yellow
Write-Host "  GPU Main:   http://localhost:$GpuPort" -ForegroundColor White
Write-Host "  CPU Fast:   http://localhost:$CpuPort1" -ForegroundColor White
Write-Host "  CPU Med:    http://localhost:$CpuPort2" -ForegroundColor White
Write-Host "  CPU Backup: http://localhost:$CpuPort3" -ForegroundColor White
Write-Host ""
Write-Host "Press any key to stop all..." -ForegroundColor Red
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

# Kill all python processes started by this script
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
Write-Host "All servers stopped." -ForegroundColor Green
