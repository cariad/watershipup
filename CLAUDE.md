# CLAUDE.md

watershipup is a Python package and command that publishes a static website to a Bunny Storage zone.

## Commands

```bash
mise install                # Install the pinned tools
mise run lint               # Every linter, stopping at the first failure
mise run lint:editorconfig  # One linter
mise run test               # The unit tests, which must cover every line and branch
mise exec -- uv run --locked pytest --no-cov tests/unit/cli/test_main.py::test_help  # One test
mise exec -- rumdl fmt      # Fix Markdown
mise exec -- tombi format . # Fix TOML formatting
mise exec -- uv run --locked ruff check --fix  # Fix what ruff can
mise exec -- uv run --locked ruff format       # Format Python
```

## Keep in sync

- `.config/mise.toml`•`min_version` ↔ the mise-action `version` in every job that installs mise, in `.github/workflows/ci.yml`.
- After changing `.config/mise.toml`•`tools`, run `mise lock`, because CI sets `MISE_LOCKED=1`.
- Every `lint:*` task in `.config/mise.toml` ↔ a step of its own in `.github/workflows/ci.yml`'s `lint` job.
- `.config/mise.toml`•`tools`•`uv` ↔ `pyproject.toml`•`tool.uv`•`required-version`, which it must satisfy. The range's floor must never be above the uv that Dependabot's uv updater bundles (0.12.19 on 2026-10-18), or every one of Dependabot's uv updates fails. Until both move to 0.13, the test matrix's 3.15 jobs run 3.15.0rc3, because uv 0.12 knows 3.15 only up to its last release candidate.
- `pyproject.toml`•`project`•`requires-python` ↔ `pyproject.toml`•`tool.pyright`•`pythonVersion` ↔ the oldest Python in `.github/workflows/ci.yml`'s test matrix.

## Conventions

- The README is in the maintainer's own voice. Change only what a task needs, and ask before rewriting their wording.
- Use only `example.com`-style names and made-up hashes, and never name or describe a real site.
- Never run `mise trust`. If mise says a file isn't trusted, ask.
- British spelling.
- Within a Python module, functions are in alphabetical order, with private (underscored) names first.
- No `unittest.mock`, and no monkeypatching to reach a line. Setting an environment variable that the code reads is fine.
- Tests must cover every line and branch on Linux and on macOS, so a partial test run needs `--no-cov`.
- pyright is strict and flags a test that imports a private name, so anything a test needs must be public.
