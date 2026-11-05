# Imports partner .eml drafts into the parsaint.group webmail Drafts folder.
# Nothing is sent: after this you open parsaint.group/webmail and press Send yourself.
#
# Usage:
#   .\import-drafts.ps1                       # newest partner-drafts-*.zip in Downloads
#   .\import-drafts.ps1 -Zip C:\path\file.zip # a specific zip, folder or single .eml
param(
    [string]$Zip
)

$repo = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $repo

if (-not $Zip) {
    $Zip = Get-ChildItem "$env:USERPROFILE\Downloads\partner-drafts-*.zip" -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending | Select-Object -First 1 -ExpandProperty FullName
}

if (-not $Zip) {
    Write-Host "No partner-drafts-*.zip in Downloads. In the partners tab press 'draft email for all partners (ZIP)' first." -ForegroundColor Yellow
    exit 1
}
if (-not (Test-Path -LiteralPath $Zip)) {
    Write-Host "File not found: $Zip" -ForegroundColor Red
    exit 1
}

python -c "import sys; from agent.config import env; sys.exit(0 if env('IMAP_PASSWORD') and env('IMAP_USER') else 1)"
if ($LASTEXITCODE -ne 0) {
    Write-Host "IMAP_USER / IMAP_PASSWORD are not set in .env - the drafts cannot be saved." -ForegroundColor Red
    exit 1
}

Write-Host "Importing: $Zip" -ForegroundColor Cyan
python -m agent save-drafts $Zip
if ($LASTEXITCODE -ne 0) {
    Write-Host "Import failed (see the error above)." -ForegroundColor Red
    exit $LASTEXITCODE
}
Write-Host "Open https://parsaint.group/webmail/ -> Drafts and press Send on each one." -ForegroundColor Green
