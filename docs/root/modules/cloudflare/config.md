## Cloudflare Configuration

Follow these steps to analyze Cloudflare objects with Cartography.

1. Create an ApiToken in Cloudflare
    1. Go to `Manage Account > Account API Token` and create a new API Token (you can also use a personal ApiToken in `Profile > API Tokens`)
    1. You can either use the `Read all resouces` template or configure each scope
    1. Populate an environment variable with the ApiToken. You can pass the environment variable name via CLI with the `--cloudflare-token-env-var` parameter
