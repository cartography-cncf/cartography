# CircleCI Configuration

## Authentication

Create a [personal API token](https://app.circleci.com/settings/user/tokens)
in the CircleCI web app and store it in an environment variable.

## Configure Cartography

Pass the token environment variable name with `--circleci-token-env-var`.

## Run Cartography

```bash
cartography \
  --selected-modules circleci \
  --circleci-token-env-var CIRCLECI_TOKEN
```

## Advanced Configuration

Override the API v2 base URL with `--circleci-base-url`. The default is
`https://circleci.com/api/v2`.

Add projects that are not discovered automatically with
`--circleci-project-slugs`. Provide a comma-separated list such as
`gh/my-org/my-repo,gh/my-org/other-repo`.
