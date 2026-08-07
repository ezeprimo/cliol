param([switch]$Clean, [string]$Version = "", [string]$OutputDir = "dist")
if (-not $Version) { Write-Error "--version is required (e.g. -Version v0.1.0)"; exit 1 }

if ($Clean) { Remove-Item -Recurse -Force build, dist, *.spec -ErrorAction SilentlyContinue }

pip install pyinstaller==6.11.0 --quiet
pip install -e . --quiet

python -m PyInstaller `
  --onefile `
  --name "cliol-windows-amd64" `
  --distpath "$OutputDir" `
  --workpath build/pyinstaller `
  --add-data "cliol;cliol" `
  --hidden-import typer `
  --hidden-import rich `
  --hidden-import bcrypt `
  --hidden-import platformdirs `
  --hidden-import tomli `
  --hidden-import tomli_w `
  --collect-all typer `
  --collect-all rich `
  src/cliol/__main__.py

$exe = Join-Path $OutputDir "cliol-windows-amd64.exe"
if (Test-Path $exe) {
  $size = (Get-Item $exe).Length / 1MB
  Write-Host "Built $exe ($([math]::Round($size, 1)) MB)"
  & $exe --version
} else { Write-Error "Build failed"; exit 1 }
