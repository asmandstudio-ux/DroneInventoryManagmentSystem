param(
  [Parameter(Mandatory = $true)]
  [string]$Version
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$ReleaseDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$DistDir = Join-Path $RepoRoot "dist"
$Out = Join-Path $DistDir ("droneims-release_{0}.zip" -f $Version)

New-Item -ItemType Directory -Force -Path $DistDir | Out-Null

if (Test-Path $Out) {
  Remove-Item -Force $Out
}

$StagingDir = Join-Path $env:TEMP ("droneims_release_pack_{0}_{1}" -f $Version, [guid]::NewGuid().ToString("n"))
New-Item -ItemType Directory -Force -Path $StagingDir | Out-Null

Copy-Item -Path (Join-Path $ReleaseDir "*") -Destination $StagingDir -Recurse -Force -Exclude ".env"
Remove-Item -LiteralPath (Join-Path $StagingDir ".env") -Force -ErrorAction SilentlyContinue

Compress-Archive -Path (Join-Path $StagingDir "*") -DestinationPath $Out
Remove-Item -LiteralPath $StagingDir -Recurse -Force
Write-Host "[release] Created: $Out"
