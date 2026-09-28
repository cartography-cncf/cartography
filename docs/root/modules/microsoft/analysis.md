# Microsoft Analysis

## Intune Compliance Policy Resolution

The `Intune compliance policy to device resolution` analysis job creates `(:IntuneCompliancePolicy)-[:APPLIES_TO]->(:IntuneManagedDevice)` relationships.

It applies a policy to:

1. Devices enrolled by users who belong to an assigned Entra group.
1. Every enrolled user's device when `applies_to_all_users` is true.
1. Every managed device in the tenant when `applies_to_all_devices` is true.

The job considers only policies and devices refreshed during the current tenant sync. It creates current relationships before removing stale `APPLIES_TO` relationships within that tenant.
