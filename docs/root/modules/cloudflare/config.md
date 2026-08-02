# Cloudflare Configuration

## Authentication

Create an API token in Cloudflare under `Manage Account > Account API Token`.
You can also create a personal token under `Profile > API Tokens`. Store the
token in an environment variable.

## Required Permissions

Use the `Read all resources` template or configure equivalent read scopes for
the resources that Cartography should ingest.

## Configure Cartography

Pass the token environment variable name with `--cloudflare-token-env-var`.

## Run Cartography

```bash
cartography \
  --selected-modules cloudflare \
  --cloudflare-token-env-var CLOUDFLARE_TOKEN
```
