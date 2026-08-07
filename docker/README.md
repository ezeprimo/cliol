# Docker support for cliol

Build and run cliol using Docker — no local Python installation required.

## Build

```bash
docker build -t cliol -f docker/Dockerfile .
```

## Usage

```bash
# Show help
docker run --rm cliol --help

# Market quote (requires credentials mounted)
docker run --rm -v ~/.config/cliol:/home/cliol/.config/cliol cliol market quote GGAL
```

## Volume Mounts

Mount your config directory to use your IOL credentials:

```bash
# Linux
docker run --rm -v ~/.config/cliol:/home/cliol/.config/cliol cliol market quote GGAL --json

# Windows (PowerShell)
docker run --rm -v $env:APPDATA/cliol:/home/cliol/.config/cliol cliol portfolio show
```
