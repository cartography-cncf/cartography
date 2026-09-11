# Vercel Configuration

## Authentication

Create an [access token](https://vercel.com/account/tokens) scoped to your team
and store it in an environment variable.

## Configure Cartography

Pass the token environment variable name with `--vercel-token-env-var`.

Get your Vercel team ID from your team's general settings page at
`https://vercel.com/<team-slug>/~/settings`, replacing `<team-slug>` with your
team's slug. Pass the ID with `--vercel-team-id`.

## Run Cartography

```bash
export VERCEL_TOKEN="<token>"

cartography \
  --selected-modules vercel \
  --vercel-token-env-var VERCEL_TOKEN \
  --vercel-team-id "<team-id>"
```

## Advanced Configuration

Override the API base URL with `--vercel-base-url`. It defaults to
`https://api.vercel.com`.
