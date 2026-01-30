## Semgrep Configuration

Follow these steps to ingest Semgrep findings with Cartography.

1. Create a token with *Agent (CI)* and *Web API scopes* [Creating a SEMGREP_APP_TOKEN](https://semgrep.dev/docs/semgrep-ci/running-semgrep-ci-with-semgrep-cloud-platform/#creating-a-semgrep_app_token).
1. Populate an environment variable with the secrets value of the token
1. Pass the environment variable name to the `--semgrep-app-token-env-var` CLI arg.

In order to ingest Semgrep dependencies with Cartography, additional steps are needed:

1. Determine which language ecosystems you'd like to ingest.
See the full list of supported ecosystems in source code at cartography.intel.semgrep.dependencies.
1. Pass the list of ecosystems as a comma-separated string (e.g. `gomod,npm`) to the `--semgrep-dependency-ecosystems` CLI arg.
