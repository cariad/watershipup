# Contributing

## Requirements

- [mise](https://mise.jdx.dev/)

## Setup

1. Clone the repository.

   ```bash
   git clone git@github.com:cariad/watershipup.git
   ```

1. Change into the repository's directory.

   ```bash
   cd watershipup
   ```

1. Install the development tools:

   ```bash
   mise install
   ```

1. Initialise the Python environment

   ```bash
   mise exec -- uv sync --locked
   ```

## Running the tests

Once you're set up, the unit tests work out-of-the-box:

```bash
mise run test:unit
```

The integration tests use a real bunny.net storage zone, which you must create and pay for yourself:

1. In the bunny.net dashboard, add a storage zone in Germany. The zone doesn't need replication or a pull zone.
1. Copy `.env.sample` to `.env`.
1. In `.env`, set:
   - `WATERSHIPUP_TEST_ZONE`: the zone's name
   - `WATERSHIPUP_TEST_PASSWORD`: the zone's read-write password

You can now run every test, which also measures coverage:

```bash
mise run test
```

### GitHub Actions

CI runs every test, so it needs the details of the storage zone you created in [Running the tests](#running-the-tests) above.

In *Settings* › *Environments*, create an environment named `integration-testing`, and add these two secrets to it:

- `WATERSHIPUP_TEST_ZONE`: the zone's name
- `WATERSHIPUP_TEST_PASSWORD`: the zone's read-write password

If Dependabot opens pull requests in the repository, add both under *Settings* › *Secrets and variables* › *Dependabot* too, because Dependabot's pull requests can only read Dependabot secrets.

### Forks

GitHub doesn't run workflows in a fork until you turn them on in the *Actions* tab. CI then runs on pushes to `main` and on pull requests, and its test jobs fail until you add both secrets to the fork.

GitHub doesn't give secrets to a pull request from a fork, so its test jobs fail, even when the fork has its own secrets. Before you open a pull request, run `mise run test` against your own zone.

## AI policy

AI-assisted contributions are welcomed.
