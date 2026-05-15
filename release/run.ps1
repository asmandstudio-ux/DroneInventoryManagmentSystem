param(
  [Parameter(Mandatory = $true)]
  [ValidateSet("start", "stop", "restart", "down", "ps", "logs", "pull")]
  [string]$Action,

  # For "logs": pass service name (e.g., backend, dashboard, postgres, minio)
  [string]$Service = ""
)

$ErrorActionPreference = "Stop"

$ReleaseDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ComposeFile = Join-Path $ReleaseDir "docker-compose.release.yml"
$EnvFile = Join-Path $ReleaseDir ".env"

if (-not (Test-Path $EnvFile)) {
  throw "Missing env file: $EnvFile (run .\\release\\install.ps1 first)"
}

switch ($Action) {
  "start" {
    docker compose -f $ComposeFile --env-file $EnvFile up -d
  }
  "stop" {
    docker compose -f $ComposeFile --env-file $EnvFile stop
  }
  "restart" {
    docker compose -f $ComposeFile --env-file $EnvFile restart
  }
  "down" {
    docker compose -f $ComposeFile --env-file $EnvFile down
  }
  "ps" {
    docker compose -f $ComposeFile --env-file $EnvFile ps
  }
  "pull" {
    docker compose -f $ComposeFile --env-file $EnvFile pull
  }
  "logs" {
    if ($Service -eq "") {
      docker compose -f $ComposeFile --env-file $EnvFile logs -f --tail=200
    } else {
      docker compose -f $ComposeFile --env-file $EnvFile logs -f --tail=200 $Service
    }
  }
}
