# Contributing

## Development Setup

1. Clone and enter repo.
2. Install dependencies:
   - `pip install -e ".[dev]"`
3. Run tests:
   - `pytest -q`
4. Run lint:
   - `ruff check .`

## Pull Request Expectations

1. Keep changes scoped and explain purpose clearly.
2. Add or update tests for behavior changes.
3. Update docs if APIs, setup, or behavior changed.
4. Ensure CI is green before review.

## Commit Style

Use short imperative commit messages, for example:
- `Add API smoke tests for core endpoints`
- `Document Docker quickstart and compose workflow`

## Issue Reports

Include:
- expected behavior
- actual behavior
- minimal reproduction
- environment details (OS, Python version, backend config)
