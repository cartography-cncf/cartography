# DigitalOcean Configuration

## Authentication

In your DigitalOcean account, open `API > Tokens` and generate a personal
access token. See the
[DigitalOcean token page](https://cloud.digitalocean.com/account/api/tokens)
for current instructions. Store the token in an environment variable.

## Required Permissions

Set the personal access token scope to `READ`.

## Configure Cartography

Pass the token environment variable name with
`--digitalocean-token-env-var`.

## Run Cartography

```bash
cartography \
  --selected-modules digitalocean \
  --digitalocean-token-env-var DIGITALOCEAN_TOKEN
```
