# Changelog

All notable changes to cliol will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.6] - 2026-09-03

### Fixed
- Hide `--install-completion` and `--show-completion` from `cliol --help` (`add_completion=False` in `cliol/main.py`) so only `--version` and `--help` remain in Options; no regression in commands (#21).

## [0.1.5] - 2026-08-30

### Added
- TTY stderr banner with 24h cache and single unified message: `Update available: <current> -> <latest>` plus `curl -fsSL https://raw.githubusercontent.com/ezeprimo/cliol/main/install.sh | bash` or `pip install -U cliol`; preserves exit codes 0-5, never triggers on `--help`/`--version`, `CI`/`GITHUB_ACTIONS`/`TERM=dumb`, or when not TTY; cache at `platformdirs.user_cache_dir("cliol")/update_cache.json` (fallback `~/.config/cliol/.update_cache.json`) with 24h throttle, atomic write dir 0700/file 0600, corrupt cache silently ignored (#18).
- Trunk allowlist for banner: `setup`, `auth test`, `market quote`, `market data`, `portfolio show`, `account status`, `operations list`, `fci list`, `config list` only; suppressed with `--json`/`--csv` to keep output json-safe (#18).
- `cliol update check` command (from `cliol.commands.update`) with `--json` and `--force` flags: 2s network timeout, semver comparison via `packaging>=23`, JSON output `{"current","latest","update_available"}` and exit 2 on fetch failure; human-readable mode also supported (#18).
- Packaging dependency `packaging>=23` for semver comparison (#18).

### Changed
- Opt-out support: `CLIOL_NO_UPDATE_CHECK=1` (or `true`) and `cliol config set updates.check false` (alias `update_check.enabled=false`) suppress banner and background check; `ConfigManager.is_update_check_enabled()` added (#18).
- Uninstall cache cleanup (both paths) in `uninstall.sh --force` and `uninstall.ps1 -Force` best-effort (#18).
- Skill documentation for agent MAY check via `cliol update check` in `skills/cliol-skill/SKILL.md` (#18).

## [0.1.4] - 2026-08-29

### Added
- macOS binary support: release artifacts `cliol-macos-arm64` (Apple Silicon, `macos-15`) and `cliol-macos-amd64` (Intel, `macos-15-intel`) via PyInstaller; smoke tests on both runners (#15).

### Fixed
- CI: replace retired `macos-13` runner with `macos-15-intel` (#15).

## [0.1.3] - 2026-08-29

### Fixed
- Table output rendered twice in PyInstaller binary (`OutputFormatter.table()` printed to stdout via `Console` and again via the caller); routed `Console` to an in-memory buffer so only the returned string is printed (#1).

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

[0.1.6]: https://github.com/ezeprimo/cliol/releases/tag/v0.1.6
[0.1.5]: https://github.com/ezeprimo/cliol/releases/tag/v0.1.5
[0.1.4]: https://github.com/ezeprimo/cliol/releases/tag/v0.1.4
[0.1.3]: https://github.com/ezeprimo/cliol/releases/tag/v0.1.3
[0.1.2]: https://github.com/ezeprimo/cliol/releases/tag/v0.1.2
[0.1.1]: https://github.com/ezeprimo/cliol/releases/tag/v0.1.1
[0.1.0]: https://github.com/ezeprimo/cliol/releases/tag/v0.1.0
