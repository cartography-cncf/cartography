## Semgrep Configuration

.. _semgrep_config:

Follow these steps to ingest Semgrep findings with Cartography.

1. Create a token with *Agent (CI)* and *Web API scopes* [Creating a SEMGREP_APP_TOKEN](https://semgrep.dev/docs/semgrep-ci/running-semgrep-ci-with-semgrep-cloud-platform/#creating-a-semgrep_app_token).
1. Populate an environment variable with the secrets value of the token
1. Pass the environment variable name to the `--semgrep-app-token-env-var` CLI arg.
