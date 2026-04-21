## Vercel Configuration

Follow these steps to analyze Vercel objects with Cartography.

1. Prepare your Vercel API token
    1. Create an [access token](https://vercel.com/account/tokens) scoped to your team.
    1. Populate an environment variable with the token. Pass the environment variable name via CLI with `--vercel-token-env-var`.
1. Get your Vercel team ID from your team's general settings page at `https://vercel.com/<team-slug>/~/settings` (replace `<team-slug>` with your team's slug) and pass it via CLI with `--vercel-team-id`.
1. Optionally override the API base URL with `--vercel-base-url` (default: `https://api.vercel.com`).
