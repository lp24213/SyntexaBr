# Analisador de uso de disco - mostra o que esta consumindo mais espaco
$ErrorActionPreference = "SilentlyContinue"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  ANALISE DE USO DE DISCO (C:)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Tamanho total do disco
$disk = Get-WmiObject -Class Win32_LogicalDisk -Filter "DeviceID='C:'"
$totalGB = [math]::Round($disk.Size / 1GB, 2)
$freeGB = [math]::Round($disk.FreeSpace / 1GB, 2)
$usedGB = [math]::Round(($disk.Size - $disk.FreeSpace) / 1GB, 2)
$percentUsed = [math]::Round($usedGB / $totalGB * 100, 1)

Write-Host "`nTAMANHO DO DISCO:" -ForegroundColor Yellow
Write-Host "  Total:    $totalGB GB"
Write-Host "  Usado:    $usedGB GB ($percentUsed%)"
Write-Host "  Livre:    $freeGB GB"

# Funcao para calcular tamanho de pasta
function Get-FolderSize($path) {
    $size = 0
    try {
        Get-ChildItem -Path $path -Recurse -Force -ErrorAction SilentlyContinue | ForEach-Object {
            if (-not $_.PSIsContainer) { $size += $_.Length }
        }
    } catch {}
    return $size
}

# Top pastas no C: raiz
Write-Host "`n--- TOP 20 PASTAS NO C: (raiz) ---" -ForegroundColor Yellow
$rootFolders = Get-ChildItem -Path "C:\" -Directory -Force -ErrorAction SilentlyContinue | ForEach-Object {
    $size = Get-FolderSize $_.FullName
    [PSCustomObject]@{
        Pasta = $_.Name
        "Tamanho (GB)" = [math]::Round($size / 1GB, 2)
    }
} | Sort-Object "Tamanho (GB)" -Descending | Select-Object -First 20

$rootFolders | Format-Table -AutoSize

# Top pastas no Users
Write-Host "`n--- TOP 15 PASTAS EM C:\Users\luisp ---" -ForegroundColor Yellow
$usersFolders = Get-ChildItem -Path "C:\Users\luisp" -Directory -Force -ErrorAction SilentlyContinue | ForEach-Object {
    $size = Get-FolderSize $_.FullName
    [PSCustomObject]@{
        Pasta = $_.Name
        "Tamanho (GB)" = [math]::Round($size / 1GB, 2)
    }
} | Sort-Object "Tamanho (GB)" -Descending | Select-Object -First 15

$usersFolders | Format-Table -AutoSize

# Top pastas no AppData\Local
Write-Host "`n--- TOP 20 PASTAS EM AppData\Local ---" -ForegroundColor Yellow
$localFolders = Get-ChildItem -Path "$env:LOCALAPPDATA" -Directory -ErrorAction SilentlyContinue | ForEach-Object {
    $size = Get-FolderSize $_.FullName
    [PSCustomObject]@{
        Pasta = $_.Name
        "Tamanho (GB)" = [math]::Round($size / 1GB, 2)
    }
} | Sort-Object "Tamanho (GB)" -Descending | Select-Object -First 20

$localFolders | Format-Table -AutoSize

# Top pastas no AppData\Roaming
Write-Host "`n--- TOP 15 PASTAS EM AppData\Roaming ---" -ForegroundColor Yellow
$roamFolders = Get-ChildItem -Path "$env:APPDATA" -Directory -ErrorAction SilentlyContinue | ForEach-Object {
    $size = Get-FolderSize $_.FullName
    [PSCustomObject]@{
        Pasta = $_.Name
        "Tamanho (GB)" = [math]::Round($size / 1GB, 2)
    }
} | Sort-Object "Tamanho (GB)" -Descending | Select-Object -First 15

$roamFolders | Format-Table -AutoSize

# Top pastas no Program Files / x86
Write-Host "`n--- TOP 10 PASTAS EM Program Files ---" -ForegroundColor Yellow
$pfFolders = Get-ChildItem -Path "C:\Program Files" -Directory -ErrorAction SilentlyContinue | ForEach-Object {
    $size = Get-FolderSize $_.FullName
    [PSCustomObject]@{
        Pasta = $_.Name
        "Tamanho (GB)" = [math]::Round($size / 1GB, 2)
    }
} | Sort-Object "Tamanho (GB)" -Descending | Select-Object -First 10

$pfFolders | Format-Table -AutoSize

Write-Host "`n--- TOP 10 PASTAS EM Program Files (x86) ---" -ForegroundColor Yellow
$pf86Folders = Get-ChildItem -Path "C:\Program Files (x86)" -Directory -ErrorAction SilentlyContinue | ForEach-Object {
    $size = Get-FolderSize $_.FullName
    [PSCustomObject]@{
        Pasta = $_.Name
        "Tamanho (GB)" = [math]::Round($size / 1GB, 2)
    }
} | Sort-Object "Tamanho (GB)" -Descending | Select-Object -First 10

$pf86Folders | Format-Table -AutoSize

# Procurar por arquivos grandes (>1GB)
Write-Host "`n--- ARQUIVOS MAIORES QUE 1GB EM C:\Users\luisp ---" -ForegroundColor Yellow
$largeFiles = Get-ChildItem -Path "C:\Users\luisp" -Recurse -Force -ErrorAction SilentlyContinue |
    Where-Object { (-not $_.PSIsContainer) -and ($_.Length -gt 1GB) } |
    Select-Object FullName, @{N="Tamanho (GB)";E={[math]::Round($_.Length / 1GB, 2)}} |
    Sort-Object "Tamanho (GB)" -Descending | Select-Object -First 20

$largeFiles | Format-Table -AutoSize

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "  ANALISE CONCLUIDA" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
