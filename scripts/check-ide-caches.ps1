$folders = @(
    "$env:APPDATA\Cursor\User\workspaceStorage",
    "$env:APPDATA\Cursor\snapshots",
    "$env:APPDATA\Cursor\logs",
    "$env:APPDATA\Windsurf\logs",
    "$env:LOCALAPPDATA\cursor-updater",
    "$env:LOCALAPPDATA\Windsurf",
    "$env:APPDATA\Cursor\Backups",
    "$env:APPDATA\Windsurf\Backups"
)
foreach ($f in $folders) {
    if (Test-Path $f) {
        $size = (Get-ChildItem $f -Recurse -Force -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum / 1MB
        Write-Host ('{0:N2} MB - {1}' -f $size,$f)
    } else {
        Write-Host ('0,00 MB - {0}' -f $f)
    }
}
