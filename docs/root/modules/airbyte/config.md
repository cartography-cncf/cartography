## Airbyte Configuration

Follow these steps to analyze Airbyte objects with Cartography.

1. On your Airbyte admin pannel create a new `application` (note that the application will have the permissions of the user creating the application)
    1. Pass `Client ID` via the CLI paramater `--airbyte-client-id`.
    1. Populate an environment variable with the `Client Secret`. You can pass the environment variable name via CLI with the `--airbyte-client-secret-env-var` parameter.
1. If your are on a self hosted instance you must provide the base URL with the `--airbyte-api-url` parameter
