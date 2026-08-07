# Changelog

All notable changes to cliol will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

[0.1.0]: https://github.com/ezeprimo/cliol/releases/tag/v0.1.0
