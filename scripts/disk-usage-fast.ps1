$ErrorActionPreference = "SilentlyContinue"

function Fast-Size($path) {
    $sum = 0
    Get-ChildItem -Path $path -Recurse -Force -ErrorAction SilentlyContinue | ForEach-Object {
        if (-not $_.PSIsContainer) { $sum += $_.Length }
    }
    return [math]::Round($sum / 1GB, 2)
}

Write-Host "DISCO C:" -ForegroundColor Cyan
$disk = Get-WmiObject Win32_LogicalDisk -Filter "DeviceID='C:'"
$total = [math]::Round($disk.Size / 1GB, 2)
$free = [math]::Round($disk.FreeSpace / 1GB, 2)
$used = $total - $free
Write-Host "Total: $total GB | Usado: $used GB | Livre: $free GB" -ForegroundColor Yellow
Write-Host ""

$pastasRaiz = @(
    "C:\Windows",
    "C:\Users",
    "C:\Program Files",
    "C:\Program Files (x86)",
    "C:\ProgramData"
)

Write-Host "--- TAMANHO DAS PASTAS PRINCIPAIS ---" -ForegroundColor Green
foreach ($p in $pastasRaiz) {
    if (Test-Path $p) {
        $s = Fast-Size $p
        Write-Host ("{0,6:N2} GB  {1}" -f $s, $p)
    }
}

Write-Host ""
Write-Host "--- PASTAS GRANDES EM C:\Windows ---" -ForegroundColor Green
$pastasWindows = @("WinSxS","Installer","SysWOW64","System32","Logs","Temp","SoftwareDistribution")
foreach ($p in $pastasWindows) {
    $full = Join-Path "C:\Windows" $p
    if (Test-Path $full) {
        $s = Fast-Size $full
        if ($s -gt 0.5) { Write-Host ("{0,6:N2} GB  {1}" -f $s, $full) }
    }
}

Write-Host ""
Write-Host "--- PASTAS GRANDES EM C:\Users\luisp ---" -ForegroundColor Green
$pastasUser = @("AppData","Documents","Downloads","Desktop","Videos","Music","Pictures","OneDrive")
foreach ($p in $pastasUser) {
    $full = Join-Path "C:\Users\luisp" $p
    if (Test-Path $full) {
        $s = Fast-Size $full
        if ($s -gt 0.1) { Write-Host ("{0,6:N2} GB  {1}" -f $s, $full) }
    }
}

Write-Host ""
Write-Host "--- PASTAS GRANDES EM AppData\Local ---" -ForegroundColor Green
Get-ChildItem -Path "$env:LOCALAPPDATA" -Directory -ErrorAction SilentlyContinue | ForEach-Object {
    $s = Fast-Size $_.FullName
    if ($s -gt 0.5) { Write-Host ("{0,6:N2} GB  {1}" -f $s, $_.FullName) }
}

Write-Host ""
Write-Host "--- PASTAS GRANDES EM AppData\Roaming ---" -ForegroundColor Green
Get-ChildItem -Path "$env:APPDATA" -Directory -ErrorAction SilentlyContinue | ForEach-Object {
    $s = Fast-Size $_.FullName
    if ($s -gt 0.5) { Write-Host ("{0,6:N2} GB  {1}" -f $s, $_.FullName) }
}

Write-Host ""
Write-Host "--- ARQUIVOS DE SISTEMA GRANDES ---" -ForegroundColor Green
$arquivosSistema = @("C:\pagefile.sys","C:\hiberfil.sys","C:\swapfile.sys")
foreach ($a in $arquivosSistema) {
    if (Test-Path $a) {
        $f = Get-Item $a -Force
        $s = [math]::Round($f.Length / 1GB, 2)
        Write-Host ("{0,6:N2} GB  {1}" -f $s, $a)
    }
}

Write-Host ""
Write-Host "--- ARQUIVOS > 2GB EM C:\Users\luisp ---" -ForegroundColor Green
Get-ChildItem -Path "C:\Users\luisp" -Recurse -Force -ErrorAction SilentlyContinue |
    Where-Object { (-not $_.PSIsContainer) -and ($_.Length -gt 2GB) } |
    Select-Object -First 15 |
    ForEach-Object {
        $s = [math]::Round($_.Length / 1GB, 2)
        Write-Host ("{0,6:N2} GB  {1}" -f $s, $_.FullName)
    }

Write-Host ""
Write-Host "FIM DA ANALISE" -ForegroundColor Cyan
