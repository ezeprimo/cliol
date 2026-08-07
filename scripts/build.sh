#!/usr/bin/env bash
set -euo pipefail

CLEAN=0; VERSION=""; OUTPUT_DIR="dist"
while [[ $# -gt 0 ]]; do case "$1" in
  --clean|-c) CLEAN=1; shift;;
  --version|-v) VERSION="$2"; shift 2;;
  --output-dir|-o) OUTPUT_DIR="$2"; shift 2;;
  *) echo "Unknown option: $1"; exit 1;;
esac; done

if [[ -z "$VERSION" ]]; then echo "ERROR: --version is required (e.g. --version v0.1.0)"; exit 1; fi
PACKAGE_VERSION="${VERSION#v}"

# Use local venv if available
if [[ -d ".venv" ]]; then source .venv/bin/activate 2>/dev/null || true; fi

if [[ "$CLEAN" -eq 1 ]]; then
  rm -rf build dist *.spec
fi

pip install pyinstaller==6.11.0 --quiet
pip install -e . --quiet

python -m PyInstaller \
  --onefile \
  --name "cliol-linux-amd64" \
  --distpath "$OUTPUT_DIR" \
  --workpath build/pyinstaller \
  --add-data "cliol:cliol" \
  --hidden-import typer \
  --hidden-import rich \
  --hidden-import bcrypt \
  --hidden-import platformdirs \
  --hidden-import tomli \
  --hidden-import tomli_w \
  --collect-all typer \
  --collect-all rich \
  src/cliol/__main__.py

BINARY="$OUTPUT_DIR/cliol-linux-amd64"
if [[ -f "$BINARY" ]]; then
  chmod +x "$BINARY"
  echo "Built $BINARY ($(du -h "$BINARY" | cut -f1))"
  echo "Version check: $($BINARY --version 2>&1)"
else
  echo "ERROR: Build failed"; exit 1
fi
