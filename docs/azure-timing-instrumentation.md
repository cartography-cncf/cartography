# Azure Service Timing Instrumentation

## Overview

Every Azure service sync emits structured JSON log events. These are queryable in CloudWatch to identify slow services, throttled subscriptions, and failed syncs without any code changes after the fact.

## Log Events

### `azure_service_timing`

Emitted once per service per subscription run (both sequential and parallel modes).

```json
{
  "event": "azure_service_timing",
  "subscription_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "service": "compute",
  "run_mode": "sequential",
  "duration_seconds": 42.7,
  "status": "success",
  "request_count": 18,
  "throttle_count": 0,
  "retry_count": 0
}
```

On failure:

```json
{
  "event": "azure_service_timing",
  "subscription_id": "...",
  "service": "storage",
  "run_mode": "sequential",
  "duration_seconds": 3.1,
  "status": "error",
  "request_count": 2,
  "throttle_count": 0,
  "retry_count": 0,
  "error_type": "HttpResponseError",
  "error_message": "Operation returned an invalid status 'Forbidden'"
}
```

| Field | Type | Description |
|---|---|---|
| `service` | string | cartography resource function name (e.g. `compute`, `storage`, `iam`) |
| `run_mode` | string | `sequential` or `parallel` |
| `duration_seconds` | float | wall-clock time for the full service sync, **including failures** |
| `status` | string | `success` or `error` |
| `request_count` | int | total HTTP requests to Azure API (proxy for pagination depth) |
| `throttle_count` | int | number of HTTP 429 responses received |
| `retry_count` | int | number of responses with `Retry-After` / `x-ms-retry-after-ms` headers |
| `error_type` | string | exception class name (only on `status=error`) |
| `error_message` | string | exception message (only on `status=error`) |

### `azure_subscription_timing_summary`

Emitted once per subscription after all services finish.

```json
{
  "event": "azure_subscription_timing_summary",
  "subscription_id": "...",
  "run_mode": "sequential",
  "total_duration_seconds": 312.4,
  "service_timings": {"compute": 42.7, "storage": 3.1, "sql": 120.0},
  "slowest_service": "sql",
  "failed_services": {"storage": "HttpResponseError"}
}
```

| Field | Type | Description |
|---|---|---|
| `run_mode` | string | `sequential` or `parallel` |
| `total_duration_seconds` | float | wall-clock from first service start to last finish |
| `service_timings` | object | `{service: duration_seconds}` for all attempted services |
| `slowest_service` | string | service with highest `duration_seconds` |
| `failed_services` | object | `{service: error_type}` for services that raised exceptions |

---

## How HTTP Stats Are Collected (`AzureTimingPolicy`)

`cartography/intel/azure/util/timing.py` contains an Azure SDK pipeline policy (`AzureTimingPolicy`) that is injected into management clients via `per_call_policies`. It reads from a thread-local `ServiceTimingContext` on every HTTP request/response — no locking required.

**To enable HTTP stats for a service**, change its `get_client()`:

```python
# Before
def get_client(credentials, subscription_id):
    return ComputeManagementClient(credentials, subscription_id)

# After
def get_client(credentials, subscription_id):
    from cartography.intel.azure.util.timing import get_timing_policy
    return ComputeManagementClient(credentials, subscription_id, per_call_policies=[get_timing_policy()])
```

Currently enabled: **compute** (`cartography/intel/azure/compute.py`).

Services not yet instrumented will show `request_count=0`, `throttle_count=0`, `retry_count=0` even if they made API calls — this is a data gap, not a bug.

---

## Downloading Logs from CloudWatch

```bash
python scripts/download_azure_timing_logs.py \
  --log-group /ecs/cartography \
  --hours 24 \
  --output timing.json

# summary events only (one per subscription run)
python scripts/download_azure_timing_logs.py \
  --log-group /ecs/cartography \
  --summary-only --hours 48
```

The script prints a per-service stats table to stderr immediately:

```
  service                        runs      min      avg      max
  ------------------------------ -----   ------   ------   ------
  sql                               12    85.2    112.4    201.7
  compute                           12    30.1     42.3     61.0
```

See `scripts/download_azure_timing_logs.py --help` for all options.

---

## Debugging a Slow Service

1. Download logs for the suspect time window.
2. Filter `azure_service_timing` events for the slow service.
3. Check `request_count` — high values mean many paginated API calls (large subscription).
4. Check `throttle_count` / `retry_count` — non-zero means Azure rate-limited the sync.
5. If `throttle_count > 0`, the service is hitting Azure API limits. Options:
   - Add a delay between pages in the resource function.
   - Use `regions` filter to reduce scope.
   - Stagger subscriptions to avoid concurrent throttling.
6. If `throttle_count == 0` but `duration_seconds` is high, the bottleneck is data volume (many resources to sync) or Neo4j write latency — not Azure API limits.

---

## Adding More Instrumentation

### Per-SDK-client HTTP stats

Add `per_call_policies=[get_timing_policy()]` to any `*ManagementClient` constructor. The policy is a stateless singleton — safe to share.

### Item/page counts from resource functions

For finer granularity, resource functions can report item counts back to the context:

```python
from cartography.intel.azure.util.timing import get_current_context

def get_vm_list(credentials, subscription_id, regions, common_job_parameters):
    client = get_client(credentials, subscription_id)
    items = list(client.virtual_machines.list_all())
    ctx = get_current_context()
    if ctx is not None:
        ctx.item_count = len(items)   # add item_count field to ServiceTimingContext first
    ...
```

This is opt-in per resource function and does not require changes to `__init__.py`.
