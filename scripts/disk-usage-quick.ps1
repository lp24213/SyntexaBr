$ErrorActionPreference = "SilentlyContinue"

function Measure-Dir($path) {
    if (-not (Test-Path $path)) { return 0 }
    $sum = 0L
    try {
        $files = [System.IO.Directory]::EnumerateFiles($path, "*", [System.IO.SearchOption]::AllDirectories)
        foreach ($f in $files) {
            try { $fi = [System.IO.FileInfo]::new($f); $sum += $fi.Length } catch {}
        }
    } catch {}
    return [math]::Round($sum / 1GB, 2)
}

Write-Host "DISCO C:  Total: 237 GB | Usado: ~228 GB | Livre: ~9.5 GB (96%)" -ForegroundColor Cyan
Write-Host ""

$map = @{
    "Windows"           = Measure-Dir "C:\Windows"
    "  -> WinSxS"       = Measure-Dir "C:\Windows\WinSxS"
    "  -> Installer"    = Measure-Dir "C:\Windows\Installer"
    "  -> System32"     = Measure-Dir "C:\Windows\System32"
    "  -> SysWOW64"     = Measure-Dir "C:\Windows\SysWOW64"
    "  -> Logs"         = Measure-Dir "C:\Windows\Logs"
    "Users\luisp"       = Measure-Dir "C:\Users\luisp"
    "  -> AppData\Local"= Measure-Dir "$env:LOCALAPPDATA"
    "  -> AppData\Roaming"= Measure-Dir "$env:APPDATA"
    "Program Files"     = Measure-Dir "C:\Program Files"
    "Program Files (x86)"= Measure-Dir "C:\Program Files (x86)"
    "ProgramData"       = Measure-Dir "C:\ProgramData"
}

Write-Host "--- PASTAS PRINCIPAIS ---" -ForegroundColor Yellow
$map.GetEnumerator() | Sort-Object Value -Descending | ForEach-Object {
    Write-Host ("{0,8:N2} GB  {1}" -f $_.Value, $_.Key)
}

Write-Host ""
Write-Host "--- PASTAS > 1GB EM AppData\Local ---" -ForegroundColor Yellow
Get-ChildItem "$env:LOCALAPPDATA" -Directory -ErrorAction SilentlyContinue | ForEach-Object {
    $s = Measure-Dir $_.FullName
    if ($s -gt 1) { Write-Host ("{0,8:N2} GB  {1}" -f $s, $_.Name) }
}

Write-Host ""
Write-Host "--- PASTAS > 1GB EM AppData\Roaming ---" -ForegroundColor Yellow
Get-ChildItem "$env:APPDATA" -Directory -ErrorAction SilentlyContinue | ForEach-Object {
    $s = Measure-Dir $_.FullName
    if ($s -gt 1) { Write-Host ("{0,8:N2} GB  {1}" -f $s, $_.Name) }
}

Write-Host ""
Write-Host "--- ARQUIVOS DE SISTEMA ---" -ForegroundColor Yellow
if (Test-Path "C:\pagefile.sys") {
    $s = (Get-Item "C:\pagefile.sys" -Force).Length / 1GB
    Write-Host ("{0,8:N2} GB  pagefile.sys" -f $s)
}
if (Test-Path "C:\hiberfil.sys") {
    $s = (Get-Item "C:\hiberfil.sys" -Force).Length / 1GB
    Write-Host ("{0,8:N2} GB  hiberfil.sys" -f $s)
}

Write-Host ""
Write-Host "FIM" -ForegroundColor Green
