## Duo Configuration

Follow these steps to analyze Duo objects with Cartography.

1. Prepare a [admin api creds](https://duo.com/docs/adminapi).
1. Pass the Duo api host name to the `--duo-api-hostname` CLI arg.
1. Populate environment variables with the api key and api secret.
1. Pass that those var names to the `--duo-api-key-env-var` and `--duo-api-secret-env-var` CLI args.
