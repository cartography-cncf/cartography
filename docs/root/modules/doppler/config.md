## Doppler Configuration

Follow these steps to analyze Doppler objects with Cartography.

1. Prepare your Doppler API token. The module only issues `GET` requests and needs
   workplace-wide read access, so use one of:
    - A **Personal token** (recommended, available on all plans): in the
      [Doppler Dashboard](https://dashboard.doppler.com/) go to **Tokens** and create
      a token under the **Personal** tab. It carries your account's read access to the
      whole workplace.
    - A **Service Account token** (requires a paid Team plan): create the service
      account under **Team → Service Accounts**, give it a workplace role with read
      access, then generate its API token.

   Do not use a config-scoped **Service Token** (the "Service" tab under **Tokens**):
   it only grants access to a single config's secrets and cannot list workplace
   resources.
1. Populate an environment variable with the token. You can pass the environment
   variable name via CLI with the `--doppler-apikey-env-var` parameter.

Example:

```bash
export DOPPLER_TOKEN="dp.pt.xxxxxxxx"
cartography --doppler-apikey-env-var DOPPLER_TOKEN
```

> **Note**: Cartography never ingests Doppler secret *values*. Only secret names are
> stored, and webhook secrets are excluded.
