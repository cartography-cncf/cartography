# RunPod Configuration

Configure a RunPod API key and a stable account identifier before running this module.

## Authentication

Create a RunPod API key in the RunPod console, store it in an environment variable,
and pass the environment variable name to Cartography.

## Required Permissions

The configured key needs read access to the RunPod API v2 resources you want to sync.
RunPod scoped keys can deny individual endpoints. Core inventory resources fail loudly
on HTTP authorization or transport errors so Cartography does not clean up from an
incomplete snapshot. Optional resources such as SSH keys, registry credentials, and
catalog data centers skip their cleanup for that run and preserve previous graph data.

## Configure Cartography

| Option | Required | Description |
| --- | --- | --- |
| `--runpod-api-key-env-var` | Yes | Environment variable name containing the RunPod API key. |
| `--runpod-account-id` | Yes | Stable identifier to use as the `RunPodAccount` tenant root. |
| `--runpod-base-url` | No | RunPod API v2 base URL. Defaults to `https://api.runpod.io/v2`. |

`--runpod-account-id` does not need to be a provider-internal ID. It must be stable
and unique in your Cartography graph, for example `prod-runpod` or your RunPod team
name.

## Run Cartography

```bash
RUNPOD_API_KEY=<your-api-key> cartography \
  --runpod-api-key-env-var RUNPOD_API_KEY \
  --runpod-account-id prod-runpod
```

## References

- [RunPod API keys](https://docs.runpod.io/get-started/api-keys)
- [RunPod API v2 documentation](https://docs.runpod.io/api-reference-v2/overview)
