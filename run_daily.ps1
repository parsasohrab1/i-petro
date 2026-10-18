# Local alternative to GitHub Actions: run once a day from Windows Task Scheduler.
Set-Location -Path $PSScriptRoot
$env:PYTHONIOENCODING = "utf-8"
python -m agent run *>> "data\run.log"
