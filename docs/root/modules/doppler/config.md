## Doppler Configuration

Follow these steps to analyze Doppler objects with Cartography.

1. Prepare your Doppler API token.
    1. Create a token in the [Doppler Dashboard](https://dashboard.doppler.com/). A
       **Personal token** or a **Service Account token** with read access to the
       workplace works; the module only issues `GET` requests.
    1. Populate an environment variable with the token. You can pass the environment
       variable name via CLI with the `--doppler-apikey-env-var` parameter.

Example:

```bash
export DOPPLER_TOKEN="dp.pt.xxxxxxxx"
cartography --doppler-apikey-env-var DOPPLER_TOKEN
```

> **Note**: Cartography never ingests Doppler secret *values*. Only secret names are
> stored, and webhook secrets are excluded.
