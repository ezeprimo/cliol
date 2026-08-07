# Contributing to cliol

## Quick Start

```bash
git clone https://github.com/ezeprimo/cliol.git
cd cliol
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -e ".[dev]"
```

## Rules

| Rule | Why |
|------|-----|
| Use the local `.venv` | Never install Python packages globally |
| Write tests first (TDD) | RED → GREEN → REFACTOR |
| Follow existing patterns | Match the codebase style |
| Keep commits focused | One logical change per commit |
| Run `ruff check` + `pytest` before pushing | CI must pass |

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/unit/test_security.py -v

# With coverage
pytest tests/ -v --cov=cliol --cov-report=term-missing

# Lint
ruff check cliol/ tests/
ruff format --check cliol/ tests/
```

## Pull Requests

- Create a feature branch from `master`
- Include tests for new functionality
- Ensure CI passes (lint + test matrix)
- Keep PRs focused and reviewable
