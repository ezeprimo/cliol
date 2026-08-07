param([switch]$Force, [switch]$DryRun)
$ErrorActionPreference = "Stop"
$Repo = if ($env:CLIOL_REPO) { $env:CLIOL_REPO } else { "ezeprimo/cliol" }
$InstallDir = if ($env:CLIOL_INSTALL_DIR) { $env:CLIOL_INSTALL_DIR } else { Join-Path $env:LOCALAPPDATA "cliol\bin" }
$TargetPath = Join-Path $InstallDir "cliol.exe"

if (-not $Force) { $answer = Read-Host "This will remove cliol and clean up shell configuration. Continue? [y/N]"; if ($answer -notmatch '^[Yy]') { Write-Host "Cancelled."; exit 0 } }
Write-Host "=== cliol uninstall ===" -ForegroundColor Cyan

if (Test-Path -LiteralPath $TargetPath) {
  if ($DryRun) { Write-Host "  [dry-run] would remove $TargetPath" -ForegroundColor Magenta }
  else { Remove-Item -LiteralPath $TargetPath -Force; Write-Host "  [removed] $TargetPath" -ForegroundColor Green }
} else { Write-Host "  [absent]  $TargetPath — nothing to clean" -ForegroundColor Gray }

# Clean user PATH
$current = [Environment]::GetEnvironmentVariable("Path", "User")
if ($current -and ($current.Split(';') -contains $InstallDir)) {
  if ($DryRun) { Write-Host "  [dry-run] would remove $InstallDir from user PATH" -ForegroundColor Magenta }
  else {
    $newPath = ($current.Split(';') | Where-Object { $_ -ne $InstallDir }) -join ';'
    [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
    Write-Host "  [removed] $InstallDir from user PATH" -ForegroundColor Green
  }
}

# Clean session PATH
$envPath = $env:Path.Split(';') | Where-Object { $_ -ne $InstallDir }
$env:Path = $envPath -join ';'
Write-Host "  Session PATH cleaned."

# Remove empty install directory
if ((Test-Path $InstallDir) -and (-not (Get-ChildItem $InstallDir))) {
  if ($DryRun) { Write-Host "  [dry-run] would remove empty $InstallDir" -ForegroundColor Magenta }
  else { Remove-Item $InstallDir -Force; Write-Host "  [removed] empty directory $InstallDir" -ForegroundColor Green }
}

Write-Host ""; Write-Host "To reinstall: irm https://raw.githubusercontent.com/$Repo/main/install.ps1 | iex"
