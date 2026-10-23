# CLAUDE.md

watershipup is a Python package and command that publishes a static website to a Bunny Storage zone.

## Commands

```bash
mise install                # Install the pinned tools
mise run lint               # Every linter, stopping at the first failure
mise run lint:editorconfig  # One linter
```

## Keep in sync

- `.config/mise.toml`•`min_version` ↔ the mise-action `version` in every job that installs mise, in `.github/workflows/ci.yml`.
- After changing `.config/mise.toml`•`tools`, run `mise lock`, because CI sets `MISE_LOCKED=1`.
- Every `lint:*` task in `.config/mise.toml` ↔ a step of its own in `.github/workflows/ci.yml`'s `lint` job.

## Conventions

- The README is in the maintainer's own voice. Change only what a task needs, and ask before rewriting their wording.
- Use only `example.com`-style names and made-up hashes, and never name or describe a real site.
- Never run `mise trust`. If mise says a file isn't trusted, ask.
- British spelling.
