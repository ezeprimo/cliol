# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

**Please do NOT report security vulnerabilities through public GitHub issues.**

Instead, report them via email to **ezeprimo@gmail.com**.

You should receive a response within 48 hours. If the issue is confirmed,
we will release a patch as soon as possible depending on complexity.

## Security Model

cliol handles financial credentials and trading operations. Key security properties:

1. **Spending password**: All fund-movement operations require a bcrypt-hashed password, verified per-operation
2. **Consultation-only default**: Trading is disabled until explicitly enabled
3. **Credential storage**: IOL credentials stored in a config file with 0600 permissions
4. **No secrets in logs**: Passwords are masked in all output (config list, debug mode)
5. **No secrets in CLI args**: Passwords are never accepted as command-line arguments

If you discover a way to bypass the spending password, execute trades without the trading gate, or extract credentials, please report immediately.
