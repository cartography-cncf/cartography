## Tailscale Configuration

Follow these steps to analyze Tailscale objects with Cartography.

1. Prepare your Tailscale API Key
    1. Create an API Access Token in [Tailscale](https://login.tailscale.com/admin/settings/keys)
    1. Populate an environment variable with the token. You can pass the environment variable name via CLI with the `--tailscale-token-env-var` parameter.
1. Get your organization name from [Tailscale](https://login.tailscale.com/admin/settings/general) and pass it via CLI with the `--tailscale-org` parameter.
1. If your have a self hosted instance, configure the API Url using `--tailscale-base-url` (default: `https://api.tailscale.com/api/v2`)
