# BigFix Configuration

## Authentication

Prepare a read-only BigFix username and password. Store the password in an
environment variable.

## Configure Cartography

Pass the username with `--bigfix-username`, the password environment variable
name with `--bigfix-password-env-var`, and the BigFix API URL with
`--bigfix-root-url`.

## Run Cartography

```bash
cartography \
  --selected-modules bigfix \
  --bigfix-username "$BIGFIX_USERNAME" \
  --bigfix-password-env-var BIGFIX_PASSWORD \
  --bigfix-root-url "$BIGFIX_ROOT_URL"
```
