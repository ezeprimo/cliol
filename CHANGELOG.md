# Changelog

All notable changes to cliol will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.2] - 2026-08-19

### Fixed
- `market mep-rate --json` was silently ignored for scalar responses and printed plain text; it now emits typed JSON (`{"simbolo", "precio"}`) (#8).
- `operations list` left `cantidad`/`precio`/`monto` null on executed operations; it now falls back to the executed (`*_operada`) fields (#8).
- Bumped `pyiol-client` to `>=0.1.3`, which maps the real MEP/CPD API payload keys: `mep estimate-buy/sell/parameters/validate` and `cpd commissions` now return fully mapped JSON (#8).

## [0.1.1] - 2026-08-18

### Fixed
- `--json` output now mirrors the table data (single typed shape) for `portfolio show` and `account status` (#5).

### Changed
- Updated `master` → `main` references in CONTRIBUTING and README (#4).

## [0.1.0] - 2026-08-07

### Added
- Initial release of cliol CLI
- Market data commands: quote, data, options, instruments, massive, panel, detail, mep-rate
- Portfolio commands: portfolio show, account status, operations list/show, profile
- FCI commands: list, detail, types, managers, types-by-manager, subscribe, redeem
- MEP commands: estimate-buy, estimate-sell, parameters, validate, buy
- CPD commands: can-operate, list, commissions, buy
- Trading commands: buy, sell, buy-usd, sell-usd, cancel
- Advisor commands: movements, test-questions, calculate-profile, save-profile, sell-usd
- Auth & config commands: auth test, config set/get/list, config trading enable/disable/status
- Security: spending password with bcrypt, per-operation confirmation
- Trading gate: consultation-only mode by default, explicit opt-in
- Output formats: table (Rich), JSON, CSV
- Cross-platform config paths (Linux + Windows) via platformdirs
- AI agent skill documentation at skills/cliol-skill/SKILL.md
- CI/CD pipeline: GitHub Actions for lint, test matrix, build verification, release

[0.1.2]: https://github.com/ezeprimo/cliol/releases/tag/v0.1.2
[0.1.1]: https://github.com/ezeprimo/cliol/releases/tag/v0.1.1
[0.1.0]: https://github.com/ezeprimo/cliol/releases/tag/v0.1.0
