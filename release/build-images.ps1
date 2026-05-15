param(
  [Parameter(Mandatory = $true)]
  [string]$Version
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$ReleaseDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ImagesDir = Join-Path $ReleaseDir "images"

New-Item -ItemType Directory -Force -Path $ImagesDir | Out-Null

$backend = "droneims-backend:$Version"
$worker = "droneims-worker:$Version"
$dashboard = "droneims-dashboard:$Version"

Write-Host "[release] Building backend (api) image: $backend"
docker build -f (Join-Path $RepoRoot "Dockerfile") --target api -t $backend $RepoRoot

Write-Host "[release] Building worker image: $worker"
docker build -f (Join-Path $RepoRoot "Dockerfile") --target worker -t $worker $RepoRoot

Write-Host "[release] Building dashboard image: $dashboard"
docker build -f (Join-Path $RepoRoot "web\\Dockerfile") --target prod -t $dashboard (Join-Path $RepoRoot "web")

Write-Host "[release] Exporting images to tarballs in: $ImagesDir"
docker save -o (Join-Path $ImagesDir "droneims-backend_$Version.tar") $backend
docker save -o (Join-Path $ImagesDir "droneims-worker_$Version.tar") $worker
docker save -o (Join-Path $ImagesDir "droneims-dashboard_$Version.tar") $dashboard

Write-Host "[release] Done. Next:"
Write-Host "  1) Copy release/.env.release.example to release/.env and set:"
Write-Host "       BACKEND_IMAGE=$backend"
Write-Host "       WORKER_IMAGE=$worker   (optional)"
Write-Host "       DASHBOARD_IMAGE=$dashboard"
Write-Host "  2) Zip the entire 'release' folder for distribution (includes tarballs + compose + scripts)."
