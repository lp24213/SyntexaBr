$ErrorActionPreference = "SilentlyContinue"

function Get-DirSizeMB($path) {
    if (-not (Test-Path $path)) { return 0 }
    $sum = 0
    Get-ChildItem -Path $path -Recurse -Force -ErrorAction SilentlyContinue | ForEach-Object {
        if (-not $_.PSIsContainer) { $sum += $_.Length }
    }
    return [math]::Round($sum / 1MB, 2)
}

function Remove-OldItems($path, $days) {
    if (-not (Test-Path $path)) { return 0 }
    $removed = 0
    Get-ChildItem -Path $path -Recurse -Force -ErrorAction SilentlyContinue | ForEach-Object {
        if ((-not $_.PSIsContainer) -and ($_.LastWriteTime -lt (Get-Date).AddDays(-$days))) {
            $removed += $_.Length
            Remove-Item $_.FullName -Force -ErrorAction SilentlyContinue
        }
    }
    return [math]::Round($removed / 1MB, 2)
}

$totalBefore = 0
$totalAfter = 0

Write-Host "=== VERIFICANDO CACHES CURSOR E WINDSURF ===" -ForegroundColor Cyan

# Cursor
$cursorPaths = @{
    "workspaceStorage" = "$env:APPDATA\Cursor\User\workspaceStorage"
    "snapshots" = "$env:APPDATA\Cursor\snapshots"
    "logs" = "$env:APPDATA\Cursor\logs"
    "sentry" = "$env:APPDATA\Cursor\sentry"
    "process-monitor" = "$env:APPDATA\Cursor\process-monitor"
    "Cache" = "$env:APPDATA\Cursor\Cache"
    "CachedData" = "$env:APPDATA\Cursor\CachedData"
    "Code Cache" = "$env:APPDATA\Cursor\Code Cache"
    "GPUCache" = "$env:APPDATA\Cursor\GPUCache"
    "Crashpad" = "$env:APPDATA\Cursor\Crashpad"
    "blob_storage" = "$env:APPDATA\Cursor\blob_storage"
    "IndexedDB" = "$env:APPDATA\Cursor\IndexedDB"
    "Service Worker" = "$env:APPDATA\Cursor\Service Worker"
    "Network" = "$env:APPDATA\Cursor\Network"
}

foreach ($item in $cursorPaths.GetEnumerator()) {
    $size = Get-DirSizeMB $item.Value
    if ($size -gt 0) {
        Write-Host ("Cursor {0}: {1:N2} MB" -f $item.Key, $size) -ForegroundColor DarkGray
    }
}

# Windsurf
$windsurfPaths = @{
    "logs" = "$env:APPDATA\Windsurf\logs"
    "Cache" = "$env:APPDATA\Windsurf\Cache"
    "CachedData" = "$env:APPDATA\Windsurf\CachedData"
    "Code Cache" = "$env:APPDATA\Windsurf\Code Cache"
    "GPUCache" = "$env:APPDATA\Windsurf\GPUCache"
    "Crashpad" = "$env:APPDATA\Windsurf\Crashpad"
    "blob_storage" = "$env:APPDATA\Windsurf\blob_storage"
    "IndexedDB" = "$env:APPDATA\Windsurf\IndexedDB"
    "Service Worker" = "$env:APPDATA\Windsurf\Service Worker"
    "Network" = "$env:APPDATA\Windsurf\Network"
}

foreach ($item in $windsurfPaths.GetEnumerator()) {
    $size = Get-DirSizeMB $item.Value
    if ($size -gt 0) {
        Write-Host ("Windsurf {0}: {1:N2} MB" -f $item.Key, $size) -ForegroundColor DarkGray
    }
}

Write-Host "=== LIMPANDO CACHES (logs antigos, snapshots antigos, caches de GPU/Code) ===" -ForegroundColor Cyan

# Limpar logs antigos (>3 dias)
$removed = Remove-OldItems "$env:APPDATA\Cursor\logs" 3
if ($removed -gt 0) { Write-Host "Removido logs Cursor: $removed MB" -ForegroundColor Green }

$removed = Remove-OldItems "$env:APPDATA\Windsurf\logs" 3
if ($removed -gt 0) { Write-Host "Removido logs Windsurf: $removed MB" -ForegroundColor Green }

# Limpar caches de GPU/Code (sempre seguro recriar)
$safeCachesCursor = @("GPUCache", "Code Cache", "Cache", "CachedData", "Crashpad", "blob_storage")
foreach ($c in $safeCachesCursor) {
    $p = Join-Path "$env:APPDATA\Cursor" $c
    if (Test-Path $p) {
        $size = Get-DirSizeMB $p
        Remove-Item -Path "$p\*" -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "Limpo Cursor $c (~$size MB)" -ForegroundColor Green
    }
}

$safeCachesWindsurf = @("GPUCache", "Code Cache", "Cache", "CachedData", "Crashpad", "blob_storage")
foreach ($c in $safeCachesWindsurf) {
    $p = Join-Path "$env:APPDATA\Windsurf" $c
    if (Test-Path $p) {
        $size = Get-DirSizeMB $p
        Remove-Item -Path "$p\*" -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "Limpo Windsurf $c (~$size MB)" -ForegroundColor Green
    }
}

# Limpar snapshots antigos do Cursor (>3 dias)
$snapDir = "$env:APPDATA\Cursor\snapshots"
if (Test-Path $snapDir) {
    Get-ChildItem -Path $snapDir -Directory -Force -ErrorAction SilentlyContinue | ForEach-Object {
        if ($_.LastWriteTime -lt (Get-Date).AddDays(-3)) {
            $size = Get-DirSizeMB $_.FullName
            Remove-Item $_.FullName -Recurse -Force -ErrorAction SilentlyContinue
            Write-Host "Removido snapshot Cursor antigo: $($_.Name) (~$size MB)" -ForegroundColor Green
        }
    }
}

# Limpar workspaceStorage antigo do Cursor (>14 dias - pode ter dados de sessao)
$wsDir = "$env:APPDATA\Cursor\User\workspaceStorage"
if (Test-Path $wsDir) {
    Get-ChildItem -Path $wsDir -Directory -Force -ErrorAction SilentlyContinue | ForEach-Object {
        if ($_.LastWriteTime -lt (Get-Date).AddDays(-14)) {
            $size = Get-DirSizeMB $_.FullName
            Remove-Item $_.FullName -Recurse -Force -ErrorAction SilentlyContinue
            Write-Host "Removido workspaceStorage Cursor antigo: $($_.Name) (~$size MB)" -ForegroundColor Green
        }
    }
}

# Limpar sentry/process-monitor
$pDirs = @("$env:APPDATA\Cursor\sentry", "$env:APPDATA\Cursor\process-monitor")
foreach ($p in $pDirs) {
    if (Test-Path $p) {
        $size = Get-DirSizeMB $p
        Remove-Item -Path "$p\*" -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "Limpo $(Split-Path $p -Leaf) (~$size MB)" -ForegroundColor Green
    }
}

Write-Host "=== CONCLUIDO ===" -ForegroundColor Cyan
