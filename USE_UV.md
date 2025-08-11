Using uv in this repository

This project uses uv for dependency management, environments, builds, tests and publishing.

Prerequisites
- Install uv: macOS/Linux: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Ensure `~/.local/bin` is on your PATH.

One-time setup
- Create venv and lock deps:
  - `uv venv`
  - `uv lock`
  - `uv sync`  (installs runtime + dev deps defined in `pyproject.toml`)

Common tasks
- Run tests: `uv run pytest -n auto tests`
- Lint: `uv run flake8 pykechain`
- Docstyle: `uv run pydocstyle pykechain`
- Build docs: `uv run sphinx-build -b html docs docs/_build/html`
- Build dist: `uv build` (creates `dist/*.whl` and `*.tar.gz`)
- Publish (local/manual):
  - Set `UV_PYPI_TOKEN` in your env
  - `uv publish`

Lockfile workflow
- Update dependencies in `pyproject.toml`
- Regenerate lock: `uv lock`
- Sync env: `uv sync`
- Commit `uv.lock`

CI summary
- GitHub Actions use uv to:
  - cache: `~/.cache/uv`
  - `uv sync` then `uv run pytest ...`
  - `uv build` and `uv publish` with `UV_PYPI_TOKEN`

Notes
- We no longer use tox or twine in CI.
- `requires-python` is `>=3.8`.
- If you hit resolver issues, try `uv clean` then `uv lock`.

