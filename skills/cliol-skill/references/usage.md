# cliol Command Reference for Agents

## Verify installation
```bash
cliol --version
cliol --help
```

## Quick health check
```bash
cliol auth test       # exit 0 if credentials work
cliol config trading status  # shows HABILITADO or DESHABILITADO
```

## Market data (read-only, always available)
```bash
cliol market quote GGAL --json
cliol market data GGAL --json
cliol market massive --json
cliol market mep-rate --json
```

## Portfolio (read-only)
```bash
cliol portfolio show --json
cliol account status --json
cliol operations list --json
```

## Trading (requires trading enabled + spending password)
```bash
# Enable if needed
cliol security set-password   # set spending password (masked)
cliol config trading enable   # activate trading mode

# Execute trades (password prompted per operation)
cliol trading buy GGAL 10 500
cliol fci subscribe AHORRO 10000
cliol mep buy 100000
```

## Exit codes
| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | API or config error |
| 2 | Network error |
| 3 | Invalid credentials |
| 4 | Wrong spending password |
| 5 | Trading disabled |

## Install from release
```bash
# Linux/WSL
curl -fsSL https://raw.githubusercontent.com/ezeprimo/cliol/main/install.sh | bash

# Windows PowerShell
irm https://raw.githubusercontent.com/ezeprimo/cliol/main/install.ps1 | iex

# Pin version
CLIOL_VERSION=v0.1.0 curl -fsSL https://raw.githubusercontent.com/ezeprimo/cliol/main/install.sh | bash
```

## Uninstall
```bash
# Linux
curl -fsSL https://raw.githubusercontent.com/ezeprimo/cliol/main/uninstall.sh | bash

# Windows
irm https://raw.githubusercontent.com/ezeprimo/cliol/main/uninstall.ps1 | iex
```
