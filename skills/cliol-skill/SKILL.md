name: cliol-skill
description: >
  CLI for Invertir Online (IOL) trading platform. Query market data, portfolio,
  mutual funds, MEP dollar rates, and execute trades with safety gates.
  Trigger: IOL, invertir online, trading, stocks, portfolio, acciones,
  cotizaciones, FCI, MEP, CPD, BYMA, BCBA, Argentine market, broker.
---

# cliol — AI Agent Skill

You are an AI agent that can use `cliol` (the Invertir Online CLI) to help the user with their investments.

## Safety Rules (READ FIRST)

1. **cliol starts in consultation-only mode.** Trading operations are disabled by default.
2. **Trading operations require a spending password** — YOU must NEVER provide it. The user enters it at the prompt.
3. **Always use `--json`** for programmatic output parsing.
4. **Check exit codes** before parsing output: 0=success, 1=API error, 2=network, 3=auth, 4=wrong password, 5=trading disabled.
5. **Errors go to stderr, data to stdout.**

## Quick Health Check

```bash
# Is cliol configured?
cliol auth test

# Not configured? Guide user through setup
cliol setup
```

## Market Data Commands

```bash
# Stock quote (default market BCBA, default term T1)
cliol market quote GGAL --json

# With explicit market and term
cliol market quote PAMP --market nYSE --term t2 --json

# Instrument details
cliol market data GGAL --json

# Options chain
cliol market options GGAL --json

# All Argentine instruments
cliol market instruments --country argentina --json

# All Argentine stocks (bulk)
cliol market massive --instrument acciones --country argentina --json

# Merval panel
cliol market panel merval --instrument acciones --country argentina --json

# Detailed depth-of-book
cliol market detail GGAL --json

# MEP dollar rate
cliol market mep-rate --json
cliol market mep-rate --symbol GD30 --json
```

## Portfolio & Account Commands

```bash
# Current holdings
cliol portfolio show --json
cliol portfolio show --country estados_Unidos --json

# Account status (balances, P&L)
cliol account status --json

# Operations history
cliol operations list --json
cliol operations list --state pendientes --from 2026-01-01 --to 2026-06-30 --json

# Operation detail
cliol operations show 12345 --json

# User profile
cliol profile --json
```

## FCI (Mutual Funds) Commands

```bash
# List all funds
cliol fci list --json

# Fund detail
cliol fci detail AHORRO --json

# Fund types and managers
cliol fci types --json
cliol fci managers --json
cliol fci types-by-manager <admin> --json

# Fund types and managers
cliol fci types --json
cliol fci managers --json

# Subscribe (REQUIRES trading enabled + spending password)
cliol fci subscribe AHORRO 10000
# → prompts for spending password
# → use --validate for dry-run (no password needed)

# Redeem (REQUIRES trading enabled + spending password)
cliol fci redeem AHORRO --amount 5000
cliol fci redeem AHORRO --quantity 100
# → use --validate for dry-run
```

## MEP Dollar Commands

```bash
# Estimate purchase cost
cliol mep estimate-buy 100000 --json

# Estimate sale proceeds
cliol mep estimate-sell 500 --json

# Validate without executing
cliol mep validate 100000 --json

# Operation parameters
cliol mep parameters --json

# Buy MEP dollars (REQUIRES trading + password)
cliol mep buy 100000
# → prompts for password
```

## CPD (Deferred Checks) Commands

```bash
# Check eligibility
cliol cpd can-operate

# List available checks
cliol cpd list --state vigentes --json

# Calculate commissions
cliol cpd commissions 100000 30 45.5 --json

# Purchase (REQUIRES trading + password)
cliol cpd buy CH-12345 95000
```

## Advisor Commands

```bash
# List advisor movements (read-only)
cliol advisor movements --client-id 12345 --since 2026-01-01 --until 2026-06-30 --json

# Get investor test questions (read-only)
cliol advisor test-questions --json

# Calculate investor profile from answers (read-only, doesn't save)
cliol advisor calculate-profile --answers '[{"idPregunta":1,"idRespuesta":"A"}]' --json

# Save investor profile for a client (read-only, no trading gate)
cliol advisor save-profile --client-id 12345 --answers '[{"idPregunta":1,"idRespuesta":"A"}]'

# Sell USD bonds as advisor (REQUIRES trading + password — GATED)
cliol advisor sell-usd --client-id 12345 GD30 10 45
```

## Trading Commands (password required for orders, not for cancel)

```bash
# Buy stock (pesos)
cliol trading buy GGAL 10 500
cliol trading buy PAMP 5 3000 --market bCBA --term t0

# Sell stock (pesos)
cliol trading sell GGAL 5 520

# Buy/sell USD bonds
cliol trading buy-usd GD30 10 45
cliol trading sell-usd GD30 5 46

# Cancel pending order (trading mode required, NO password)
cliol trading cancel 12345
```

## Auth & Config Commands

```bash
# Test authentication
cliol auth test

# Config management
cliol config set iol.username mi_usuario
cliol config get iol.username
cliol config list

# Trading mode
cliol config trading status
cliol config trading enable    # requires spending password
cliol config trading disable   # clears password

# Spending password
cliol security set-password
cliol security change-password
cliol security clear-password
```

## Error Handling Pattern

When you run a command and it fails:

```bash
# Check exit code
cliol market quote INVALIDO --json
# exit code 1, stderr: "Error: El símbolo 'INVALIDO' no fue encontrado..."

# Trading disabled
cliol trading buy GGAL 10 500
# exit code 5, stderr: "Error: Operatoria deshabilitada..."

# Wrong password
cliol trading buy GGAL 10 500
# (user enters wrong password at prompt)
# exit code 4, stderr: "Error: Contraseña de gastos incorrecta."

# Network down
cliol market quote GGAL
# exit code 2, stderr: "Error: No se pudo conectar con IOL..."
```

## Enabling Trading Mode (Step by Step for Agent)

If the user asks to trade:
1. Check status: `cliol config trading status`
2. If disabled: tell user "Trading is disabled. To enable, run: `cliol security set-password` first, then `cliol config trading enable`"
3. After user sets password and enables, retry the trading command
4. The user WILL be prompted for their spending password — wait for them to type it

## Important Notes

- Markets: bCBA (BCBA), nYSE, nASDAQ, aMEX, bCS, rOFX
- Settlement terms: t0, t1 (default), t2, t3
- Countries: argentina (default), estados_Unidos
- Config path Linux: `~/.config/cliol/config.toml`
- Config path Windows: `%APPDATA%/cliol/config.toml`
