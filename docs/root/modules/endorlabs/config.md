## Endor Labs Configuration

Follow these steps to ingest Endor Labs data with Cartography.

1. Create an API key in the Endor Labs UI under **Settings > Access Control > API Keys**. See [Endor Labs API Keys](https://docs.endorlabs.com/platform-administration/api-keys/) for details.
1. Select the **Read-only** role. Cartography only reads data.
1. Populate environment variables with the API key and secret.
1. Pass the environment variable names and namespace to the CLI args.

```bash
export ENDORLABS_API_KEY="endr+your-api-key"
export ENDORLABS_API_SECRET="endr+your-api-secret"
cartography \
  --endorlabs-api-key-env-var ENDORLABS_API_KEY \
  --endorlabs-api-secret-env-var ENDORLABS_API_SECRET \
  --endorlabs-namespace your-namespace \
  --selected-modules endorlabs
```

The module will sync projects, package versions, dependency metadata, and security findings from the specified namespace.
