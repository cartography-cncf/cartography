## Crowdstrike Configuration

.. _crowdstrike_config:

Follow these steps to analyze Crowdstrike falcon objects in Cartography.

1. Prepare an API key for crowdstrike falcon
    1. Crowdstrike's documentation is private, so please see your instance's documentation on how to generate an API key.
    1. Populate an environment variable with the Client ID. You can pass the environment variable name via CLI with the `--crowdstrike-client-id-env-var` parameter.
    1. Populate an environment variable with the Client Secret. You can pass the environment variable name via CLI with the `--crowdstrike-client-secret-env-var` parameter.
    1. If you are using a self-hosted version of crowdstrike, you can change the API url, by passing it into the CLI with the `--crowdstrike-api-url` parameter.
