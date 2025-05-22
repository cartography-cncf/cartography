## Tailscale Configuration

Follow these steps to analyze Tailscale objects with Cartography.

1. Prepare your Tailscale API Key
    1. Create an API Access Token in [Tailscale](https://login.tailscale.com/admin/settings/keys)
    1. Populate the `CARTOGRAPHY_TAILSCALE__TOKEN` environment variable with the token.
1. Get your organization name from [Tailscale](https://login.tailscale.com/admin/settings/general) and pass it via CLI with the `CARTOGRAPHY_TAILSCALE__ORG` env variable.
1. If your have a self hosted instance, configure the API Url using `--tailscale-base-url`


### Cartography Configuration

| **Name** | **Type** | **Description** |
|----------|----------|-----------------|
| **CARTOGRAPHY_TAILSCALE__TOKEN** | `str` | The Tailscale Token for authentication. |
| **CARTOGRAPHY_TAILSCALE__ORG** | `str` | The name of the Tailscale organization to sync. |
| **CARTOGRAPHY_TAILSCALE__BASE_URL** | `str` | The base URL for the Tailscale API. (default: `https://api.tailscale.com/api/v2`) |
