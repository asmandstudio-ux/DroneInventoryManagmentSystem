$ErrorActionPreference = "Stop"

$ReleaseDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Install = Join-Path $ReleaseDir "install.ps1"

if (-not (Test-Path $Install)) {
  Write-Error "Missing installer script: $Install"
  exit 1
}

& powershell -NoProfile -ExecutionPolicy Bypass -File $Install -Start -NoWait -NoBrowser
$code = 0
if ($LASTEXITCODE -is [int]) {
  $code = $LASTEXITCODE
}
exit $code
