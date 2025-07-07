## Tailscale Configuration

Follow these steps to analyze Tailscale objects with Cartography.

1. Prepare your Tailscale token
    1. Create an API Access Token or OAuth token in [Tailscale](https://login.tailscale.com/admin/settings/keys).
       OAuth tokens start with `tskey-client-`.
    1. Populate an environment variable with the token. You can pass the environment variable name via CLI with the `--tailscale-token-env-var` parameter.
    1. **Scopes required**: `devices:core:read`, `devices:posture_attributes:read`, and `users:read`.
1. Get your organization name from [Tailscale](https://login.tailscale.com/admin/settings/general) and pass it via CLI with the `--tailscale-org` parameter. If using an OAuth token, this flag is optional and Cartography will auto-detect the tailnet.
1. If your have a self hosted instance, configure the API Url using `--tailscale-base-url` (default: `https://api.tailscale.com/api/v2`)
