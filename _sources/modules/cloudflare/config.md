# Cloudflare Configuration

## Authentication

Create an API token in Cloudflare under `Manage Account > Account API Token`.
You can also create a personal token under `Profile > API Tokens`. Store the
token in an environment variable.

## Required Permissions

Use the `Read all resources` template or configure equivalent read scopes for
the resources that Cartography should ingest. The individual scopes are:

| Scope | Used for |
| --- | --- |
| Account Settings:Read | Accounts |
| Account Membership:Read | Members and roles |
| Zone:Read | Zones |
| Zone DNS:Read | DNS records |
| Workers R2 Storage:Read | R2 buckets and their custom domains |
| Workers Scripts:Read | Worker scripts |
| Workers Routes:Read | Worker routes |
| Account Rulesets:Read | Account-level rulesets and their rules |
| Zone WAF:Read | Zone-level rulesets and their rules |

The R2 stage degrades instead of failing the run. If the bucket listing is
refused, R2 is skipped with a warning and the Workers and ruleset stages still
run; buckets from earlier runs are left in place rather than deleted. If only the
per-bucket domain lookups are refused, the buckets are ingested with their
internet exposure (`public`, `public_domains`) left unresolved.

R2 buckets are listed once per jurisdiction (`default`, `eu` and `fedramp`), since
each jurisdiction is a separate namespace that a single listing does not cover. The
`eu` and `fedramp` jurisdictions are granted on request, so an account without the
grant answers `403` or `404` there and is treated as holding no bucket in it. Any
other error on a jurisdiction listing holds the R2 cleanup back for that run, so
buckets Cartography could not re-read are not deleted.

## Configure Cartography

Pass the token environment variable name with `--cloudflare-token-env-var`.

## Run Cartography

```bash
cartography \
  --selected-modules cloudflare \
  --cloudflare-token-env-var CLOUDFLARE_TOKEN
```
