# cliol — CLI for Invertir Online (IOL)

CLI tool for the IOL trading platform, built on `py_iol`. Designed for both human users and AI agents.

## Installation

### From GitHub Releases (recommended — single binary, no Python needed)

**Linux / WSL / macOS:**
```bash
curl -fsSL https://raw.githubusercontent.com/ezeprimo/cliol/main/install.sh | bash
```

**Windows (PowerShell):**
```powershell
irm https://raw.githubusercontent.com/ezeprimo/cliol/main/install.ps1 | iex
```

**Pin a specific version:**
```bash
# Linux
CLIOL_VERSION=v0.1.0 curl -fsSL https://raw.githubusercontent.com/ezeprimo/cliol/main/install.sh | bash

# Windows
$env:CLIOL_VERSION = 'v0.1.0'
irm https://raw.githubusercontent.com/ezeprimo/cliol/main/install.ps1 | iex
```

After install, open a new terminal or run `source ~/.profile` (Linux) / restart PowerShell (Windows).

### From PyPI (requires Python ≥3.10)

```bash
pip install cliol
# or
uv tool install cliol
```

### Update / Rollback

```bash
# Update to latest
unset CLIOL_VERSION
curl -fsSL https://raw.githubusercontent.com/ezeprimo/cliol/main/install.sh | bash

# Rollback to pinned version
CLIOL_VERSION=v0.1.0 curl -fsSL https://raw.githubusercontent.com/ezeprimo/cliol/main/install.sh | bash
```

### Uninstall

```bash
# Linux
curl -fsSL https://raw.githubusercontent.com/ezeprimo/cliol/main/uninstall.sh | bash

# Windows
irm https://raw.githubusercontent.com/ezeprimo/cliol/main/uninstall.ps1 | iex
```

## Quick Start

```bash
# First-time setup
cliol setup

# Test credentials
cliol auth test

# Get a stock quote
cliol market quote GGAL

# View your portfolio
cliol portfolio show
```

## Safety First

- **Consultation mode by default**: trading operations are disabled until you explicitly enable them
- **Spending password**: every fund-movement operation requires a separate password (unrelated to your IOL credentials)
- **Clear error messages**: attempted trades in consultation mode return clear instructions on how to enable

### Enable Trading

```bash
# Set a spending password first
cliol security set-password

# Enable trading mode
cliol config trading enable
```

## Command Reference

### Market Data (read-only)
```bash
cliol market quote <symbol>               # Real-time stock quote
cliol market data <symbol>                # Instrument details
cliol market options <symbol>             # Options chain
cliol market instruments [--country]      # List all instruments
cliol market massive [--instrument] [--country]  # Bulk quotes
cliol market panel <panel>                # Panel/index quotes
cliol market detail <symbol>              # Full depth-of-book quote
cliol market mep-rate [--symbol]          # MEP dollar exchange rate
```

### Portfolio & Account (read-only)
```bash
cliol portfolio show [--country]          # Current holdings
cliol account status                      # Account balances & statistics
cliol operations list [--state] [--from] [--to]  # Operations history
cliol operations show <id>                # Operation detail
cliol profile                             # IOL profile info
```

### Mutual Funds (FCI) — subscription/redeem require trading mode
```bash
cliol fci list                            # All available funds
cliol fci detail <symbol>                 # Fund details
cliol fci subscribe <symbol> <amount> [--validate]  # Subscribe (gated)
cliol fci redeem <symbol> [--amount] [--quantity] [--validate]  # Redeem (gated)
```

### MEP Dollar — buy requires trading mode
```bash
cliol mep estimate-buy <amount>           # Estimate MEP purchase cost
cliol mep estimate-sell <amount>          # Estimate MEP sale proceeds
cliol mep validate <amount>               # Validate without executing
cliol mep buy <amount>                    # Buy dollars via MEP (gated)
```

### CPD (Deferred Payment Checks) — buy requires trading mode
```bash
cliol cpd can-operate                     # Check CPD eligibility
cliol cpd list [--state] [--segment]      # Available checks
cliol cpd commissions <importe> <plazo> <tasa>  # Calculate costs
cliol cpd buy <check> <price> [--quantity]      # Purchase (gated)
```

### Trading — all operations require trading mode + spending password
```bash
cliol trading buy <symbol> <qty> <price> [--market] [--term]   # Buy (gated)
cliol trading sell <symbol> <qty> <price> [--market] [--term]  # Sell (gated)
cliol trading buy-usd <symbol> <qty> <price>                    # Buy USD bonds (gated)
cliol trading sell-usd <symbol> <qty> <price>                   # Sell USD bonds (gated)
cliol trading cancel <operation-id>                             # Cancel pending order (trading mode required, no password)
```

### Auth & Config
```bash
cliol auth test                           # Verify IOL credentials
cliol config set <key> <value>            # Set config value
cliol config get <key>                    # Get config value
cliol config list                         # List all config
cliol config trading enable|disable|status  # Trading mode management
cliol security set-password               # Set spending password
cliol security change-password            # Change spending password
cliol security clear-password             # Remove spending password
```

### Global Flags
| Flag | Effect |
|------|--------|
| `--json` | Output as JSON (recommended for AI agents) |
| `--csv` | Output as CSV |
| `--verbose` | Additional context to stderr |
| `--debug` | Full debug output to stderr |

### Exit Codes
| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | API or config error |
| 2 | Network error |
| 3 | Authentication error |
| 4 | Wrong spending password |
| 5 | Trading disabled |

## Configuration

Config stored at:
- Linux: `~/.config/cliol/config.toml`
- Windows: `%APPDATA%/cliol/config.toml`

## AI Agent Usage

When using cliol via an AI agent (OpenCode, Claude Code):
- Always use `--json` for programmatic output parsing
- Errors go to stderr, success to stdout — check exit codes before parsing
- The agent should NEVER provide the spending password — the user must enter it at the prompt
- In consultation mode, trading commands return exit code 5

## License

MIT — see [LICENCE](LICENCE).
