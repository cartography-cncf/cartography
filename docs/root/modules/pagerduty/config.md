## Pagerduty Configuration

Follow these steps to analyze PagerDuty objects with Cartography.

1. Prepare your PagerDuty API key.
    1. Generate your API token by following the steps from the PagerDuty [Generating API Keys documentation](https://support.pagerduty.com/docs/generating-api-keys)
    1. Populate the `CARTOGRAPHY_PAGERDUTY__API_KEY` environment variable with the API key.
    1. You can set the timeout for pagerduty requests using the `CARTOGRAPHY_COMMON__HTTP_TIMEOUT` variable.


### Cartography Configuration

| **Name** | **Type** | **Description** |
|----------|----------|-----------------|
| **CARTOGRAPHY_PAGERDUTY__API_KEY** | `str` | The pagerduty API key for authentication. |
