## Pagerduty Configuration

.. _pagerduty_config:

Follow these steps to analyze PagerDuty objects with Cartography.

1. Prepare your PagerDuty API key.
    1. Generate your API token by following the steps from the PagerDuty [Generating API Keys documentation](https://support.pagerduty.com/docs/generating-api-keys)
    1. Populate an environment variable with the API key. You can pass the environment variable name via CLI with the `--pagerduty-api-key-env-var` parameter.
    1. You can set the timeout for pagerduty requests via the CLI with `--pagerduty-request-timeout` parameter.
