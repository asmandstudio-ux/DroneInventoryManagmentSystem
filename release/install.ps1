param(
  [switch]$NoPull,
  [switch]$Start,
  [switch]$NoShortcuts,
  [switch]$NoWait,
  [switch]$NoBrowser
)

$ErrorActionPreference = "Stop"

$ReleaseDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ComposeFile = Join-Path $ReleaseDir "docker-compose.release.yml"
$EnvExample = Join-Path $ReleaseDir ".env.release.example"
$EnvFile = Join-Path $ReleaseDir ".env"
$ImagesDir = Join-Path $ReleaseDir "images"
$LauncherCmd = Join-Path $ReleaseDir "DroneIMS.cmd"

function Ensure-Shortcut([string]$shortcutPath, [string]$targetPath, [string]$workingDir) {
  if (Test-Path -LiteralPath $shortcutPath) { return }
  $parent = Split-Path -Parent $shortcutPath
  if ($parent -and (-not (Test-Path -LiteralPath $parent))) {
    New-Item -ItemType Directory -Force -Path $parent | Out-Null
  }
  $shell = New-Object -ComObject WScript.Shell
  $s = $shell.CreateShortcut($shortcutPath)
  $s.TargetPath = $targetPath
  $s.WorkingDirectory = $workingDir
  $s.Save()
}

function Assert-Command($name) {
  if (-not (Get-Command $name -ErrorAction SilentlyContinue)) {
    throw "Missing required command: $name"
  }
}

Assert-Command "docker"

function Test-DockerReady() {
  try {
    docker version | Out-Null
    docker compose version | Out-Null
    return $true
  } catch {
    return $false
  }
}

function Start-DockerDesktopIfPossible() {
  $candidates = @(
    "$env:ProgramFiles\Docker\Docker\Docker Desktop.exe",
    "${env:ProgramFiles(x86)}\Docker\Docker\Docker Desktop.exe"
  ) | Where-Object { $_ -and (Test-Path $_) }

  if ($candidates.Count -gt 0) {
    Write-Host "[release] Starting Docker Desktop..."
    Start-Process -FilePath $candidates[0] | Out-Null
    return $true
  }
  return $false
}

Write-Host "[release] Checking Docker Desktop..."
if (-not (Test-DockerReady)) {
  $started = Start-DockerDesktopIfPossible
  Write-Host "[release] Waiting for Docker to become ready..."
  $deadline = (Get-Date).AddMinutes(3)
  while ((Get-Date) -lt $deadline) {
    if (Test-DockerReady) { break }
    Start-Sleep -Seconds 2
  }
  if (-not (Test-DockerReady)) {
    if ($started) {
      throw "Docker Desktop did not become ready in time. Please ensure Docker Desktop is running, then re-run."
    }
    throw "Docker is not ready. Please install and start Docker Desktop, then re-run."
  }
}

function New-RandomSecret([int]$bytes = 32) {
  $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
  $data = New-Object byte[] $bytes
  $rng.GetBytes($data)
  $rng.Dispose()
  $b64 = [Convert]::ToBase64String($data)
  return ($b64 -replace '\+', '-' -replace '/', '_' -replace '=', '')
}

function Update-EnvValue([string[]]$lines, [string]$key, [string]$newValue) {
  for ($i = 0; $i -lt $lines.Length; $i++) {
    if ($lines[$i] -match ("^\s*" + [Regex]::Escape($key) + "\s*=")) {
      $lines[$i] = "$key=$newValue"
      return $lines
    }
  }
  return $lines + @("$key=$newValue")
}

function Normalize-EnvFile([string]$path) {
  $lines = Get-Content -LiteralPath $path -ErrorAction Stop

  $kv = @{}
  foreach ($l in $lines) {
    if ($l -match '^\s*#') { continue }
    if ($l -match '^\s*$') { continue }
    $idx = $l.IndexOf('=')
    if ($idx -lt 1) { continue }
    $k = $l.Substring(0, $idx).Trim()
    $v = $l.Substring($idx + 1)
    $kv[$k] = $v
  }

  if (-not $kv.ContainsKey("JWT_SECRET_KEY") -or ($kv["JWT_SECRET_KEY"] -match "CHANGE-ME") -or [string]::IsNullOrWhiteSpace($kv["JWT_SECRET_KEY"])) {
    $lines = Update-EnvValue -lines $lines -key "JWT_SECRET_KEY" -newValue (New-RandomSecret 48)
  }

  if (-not $kv.ContainsKey("POSTGRES_PASSWORD") -or ($kv["POSTGRES_PASSWORD"] -match "CHANGE-ME") -or [string]::IsNullOrWhiteSpace($kv["POSTGRES_PASSWORD"])) {
    $lines = Update-EnvValue -lines $lines -key "POSTGRES_PASSWORD" -newValue (New-RandomSecret 24)
  }

  if (-not $kv.ContainsKey("MINIO_ROOT_USER") -or ($kv["MINIO_ROOT_USER"] -match "CHANGE-ME") -or [string]::IsNullOrWhiteSpace($kv["MINIO_ROOT_USER"])) {
    $lines = Update-EnvValue -lines $lines -key "MINIO_ROOT_USER" -newValue "minioadmin"
  }

  if (-not $kv.ContainsKey("MINIO_ROOT_PASSWORD") -or ($kv["MINIO_ROOT_PASSWORD"] -match "CHANGE-ME") -or [string]::IsNullOrWhiteSpace($kv["MINIO_ROOT_PASSWORD"])) {
    $lines = Update-EnvValue -lines $lines -key "MINIO_ROOT_PASSWORD" -newValue (New-RandomSecret 24)
  }

  Set-Content -LiteralPath $path -Value $lines -Encoding utf8
}

function Get-EnvMap([string]$path) {
  $m = @{}
  $lines = Get-Content -LiteralPath $path -ErrorAction Stop
  foreach ($l in $lines) {
    if ($l -match '^\s*#') { continue }
    if ($l -match '^\s*$') { continue }
    $idx = $l.IndexOf('=')
    if ($idx -lt 1) { continue }
    $k = $l.Substring(0, $idx).Trim()
    $v = $l.Substring($idx + 1)
    $m[$k] = $v
  }
  return $m
}

function Test-DockerImageExists([string]$imageRef) {
  if ([string]::IsNullOrWhiteSpace($imageRef)) { return $false }
  try {
    docker image inspect $imageRef | Out-Null
    return $true
  } catch {
    return $false
  }
}

if (-not (Test-Path $EnvFile)) {
  if (-not (Test-Path $EnvExample)) {
    throw "Missing env template: $EnvExample"
  }
  Copy-Item $EnvExample $EnvFile
  Normalize-EnvFile $EnvFile
  Write-Host "[release] Created env file with generated secrets: $EnvFile"
} else {
  Normalize-EnvFile $EnvFile
}

if (-not $NoShortcuts) {
  if (Test-Path -LiteralPath $LauncherCmd) {
    try {
      $desktop = [Environment]::GetFolderPath("DesktopDirectory")
      $programs = [Environment]::GetFolderPath("Programs")
      Ensure-Shortcut -shortcutPath (Join-Path $desktop "DroneIMS.lnk") -targetPath $LauncherCmd -workingDir $ReleaseDir
      Ensure-Shortcut -shortcutPath (Join-Path $programs "DroneIMS.lnk") -targetPath $LauncherCmd -workingDir $ReleaseDir
      Write-Host "[release] Created shortcuts (Desktop + Start Menu): DroneIMS"
    } catch {
      Write-Host "[release] Shortcut creation skipped: $($_.Exception.Message)"
    }
  }
}

$envMap = Get-EnvMap -path $EnvFile
$requiredImages = New-Object System.Collections.Generic.List[string]
if ($envMap.ContainsKey("BACKEND_IMAGE")) { $requiredImages.Add($envMap["BACKEND_IMAGE"]) }
if ($envMap.ContainsKey("DASHBOARD_IMAGE")) { $requiredImages.Add($envMap["DASHBOARD_IMAGE"]) }
if ($envMap.ContainsKey("WORKER_IMAGE") -and (-not [string]::IsNullOrWhiteSpace($envMap["WORKER_IMAGE"]))) { $requiredImages.Add($envMap["WORKER_IMAGE"]) }

$missingImages = @()
foreach ($img in $requiredImages) {
  if (-not (Test-DockerImageExists -imageRef $img)) { $missingImages += $img }
}

# Offline-first: if tarballs exist under release/images, load them and skip pulling.
$Tarballs = @()
if (Test-Path $ImagesDir) {
  $Tarballs = Get-ChildItem -Path $ImagesDir -Filter "*.tar" -File -ErrorAction SilentlyContinue
}

if ($Tarballs.Count -gt 0) {
  Write-Host "[release] Found image tarballs in $ImagesDir (offline install mode)."

  $tarballFingerprint = ($Tarballs | ForEach-Object { "{0}|{1}|{2}" -f $_.Name, $_.Length, $_.LastWriteTimeUtc.Ticks }) -join "`n"
  $markerDir = Join-Path $env:LOCALAPPDATA "DroneIMS"
  try { New-Item -ItemType Directory -Force -Path $markerDir | Out-Null } catch {}
  $markerPath = Join-Path $markerDir "images_loaded.marker"
  $markerOk = $false

  if (Test-Path -LiteralPath $markerPath) {
    try {
      $existing = Get-Content -LiteralPath $markerPath -Raw -ErrorAction Stop
      if ($existing -eq $tarballFingerprint) { $markerOk = $true }
    } catch {}
  }

  $canSkipLoads = $markerOk -and ($missingImages.Count -eq 0)

  if ($canSkipLoads) {
    Write-Host "[release] Images already loaded. Skipping docker load."
  } else {
    if ($missingImages.Count -eq 0) {
      Write-Host "[release] Images appear to be present, but marker is missing or changed. Recreating marker."
    } else {
      Write-Host "[release] Missing images:"
      foreach ($mi in $missingImages) { Write-Host "  - $mi" }
    }

    $tarballsToLoad = $Tarballs
    if ($missingImages.Count -gt 0) {
      $mapped = New-Object System.Collections.Generic.List[System.IO.FileInfo]
      foreach ($mi in $missingImages) {
        $repo = $null
        $tag = $null
        $miParts = $mi.Split(":", 2)
        if ($miParts.Length -eq 2) { $repo = $miParts[0]; $tag = $miParts[1] }
        if (-not [string]::IsNullOrWhiteSpace($repo) -and -not [string]::IsNullOrWhiteSpace($tag)) {
          $expectedTar = "$repo" + "_" + "$tag" + ".tar"
          $match = $Tarballs | Where-Object { $_.Name -eq $expectedTar } | Select-Object -First 1
          if ($match) { $mapped.Add($match) }
        }
      }
      if ($mapped.Count -gt 0) { $tarballsToLoad = $mapped.ToArray() }
    }

    if ($tarballsToLoad.Count -gt 0 -and $missingImages.Count -gt 0) {
      Write-Host "[release] Loading missing images into Docker (first run can take several minutes)..."
      foreach ($t in $tarballsToLoad) {
        Write-Host "[release] docker load -i $($t.FullName)"
        docker load -i $t.FullName
        Write-Host "[release] Loaded: $($t.Name)"
      }

      $stillMissing = @()
      foreach ($img in $requiredImages) {
        if (-not (Test-DockerImageExists -imageRef $img)) { $stillMissing += $img }
      }
      if ($stillMissing.Count -gt 0) {
        Write-Host "[release] Warning: some required images are still missing after docker load:"
        foreach ($sm in $stillMissing) { Write-Host "  - $sm" }
      }
    }

    try {
      Set-Content -LiteralPath $markerPath -Value $tarballFingerprint -Encoding utf8
    } catch {
      Write-Host "[release] Warning: could not write marker file ($markerPath)."
    }
  }
} elseif (-not $NoPull) {
  Write-Host "[release] Pulling images (online install mode)..."
  docker compose -f $ComposeFile --env-file $EnvFile pull
} else {
  Write-Host "[release] Skipping image pull (NoPull=true)."
}

Write-Host "[release] Starting services..."
docker compose -f $ComposeFile --env-file $EnvFile up -d

Write-Host "[release] Status:"
docker compose -f $ComposeFile --env-file $EnvFile ps

function Wait-HttpOk([string]$url, [int]$timeoutSeconds = 60) {
  $sw = [Diagnostics.Stopwatch]::StartNew()
  while ($sw.Elapsed.TotalSeconds -lt $timeoutSeconds) {
    try {
      $code = & curl.exe -s -o NUL -w "%{http_code}" $url
      if ($code -match '^\d+$' -and [int]$code -ge 200 -and [int]$code -lt 400) {
        return $true
      }
    } catch {}
    Start-Sleep -Seconds 2
  }
  return $false
}

if (-not $NoWait) {
  Write-Host "[release] Waiting for API readiness..."
  $apiReady = Wait-HttpOk -url "http://localhost:8000/ready" -timeoutSeconds 90
  if (-not $apiReady) {
    Write-Host "[release] API did not report ready in time. Check logs with:"
    Write-Host "  docker compose -f $ComposeFile --env-file $EnvFile logs --tail=200 backend"
  }
} else {
  Write-Host "[release] Startup running in background."
}

Write-Host ""
Write-Host "[release] URLs (defaults):"
Write-Host "  - Dashboard: http://127.0.0.1:3000"
Write-Host "  - API:       http://127.0.0.1:8000/health"
Write-Host "  - MinIO:     http://localhost:9001"

if ($Start) {
  if (-not $NoBrowser) {
    Write-Host ""
    Write-Host "[release] Opening Dashboard..."
    Start-Process "http://localhost:3000/login" | Out-Null
  }
}
