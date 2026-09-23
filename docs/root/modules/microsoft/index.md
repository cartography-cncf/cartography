# Microsoft


```{toctree}
config
schema
examples
analysis
```


The `microsoft` module is the top-level umbrella for Microsoft tenant, SaaS, and security control plane data ingested via Microsoft Graph and Defender for Endpoint APIs. It includes:

- **entra**: Entra ID identity objects (users, groups, OUs, applications, service principals, and app role assignments)
- **intune**: Intune managed devices, detected apps, and compliance policies
- **o365**: Office 365 licensing (subscribed SKUs, service plans, and per-user license assignments)
- **defender** (opt-in): Defender for Endpoint machines and unresolved alerts, including machine health, onboarding status, risk, exposure, and alert-to-machine relationships.

Defender uses bulk list APIs without per-device requests. Its machine inventory
covers the tenant's configured Defender retention period; an inventory record can
describe an inactive or discovered machine, so presence alone does not prove that
the endpoint is protected. Only unresolved alerts from Defender for Endpoint are
ingested. Resolved alerts and alerts outside the provider's retention window are
removed on the next successful sync. Alert device evidence links to retained
machine inventory when that machine exists; no placeholder machines are created.

Defender machines link to Intune managed devices using the Microsoft Entra device
ID and tenant ID. Both imports normalize the device ID to an indexed lowercase
lookup key while retaining the original ID. Intune refreshes that key before
Defender runs; empty/all-zero IDs never create associations. That path also reaches Entra users through the existing Intune
enrollment relationship. The API does not provide hardware serial numbers, so
Defender machines do not create canonical `Device` nodes. Canonical devices already
linked to Intune remain reachable through the Intune association. Defender alerts
carry the `SecurityIssue` ontology label with normalized title, severity, status,
type, and first-seen fields. Unknown severity and status values remain unmapped.
Machine first/last-seen and alert creation/update times are native datetimes,
including the ontology first-seen value. Malformed optional timestamps are omitted
with a warning while the inventory is retained. Repeated records or pagination
cursors indicate an unstable snapshot and abort before writes; rerun after
concurrent provider changes settle.

`microsoft` is the canonical top-level module name. `entra` remains accepted as a backward-compatible alias for module selection and ontology source configuration during the migration.

Microsoft and Azure ingestion share `AzureTenant` as the primary tenant node. Microsoft Graph ingestion also adds the `EntraTenant` compatibility label to that node.

See the [configuration docs](config.md), [schema](schema.md), [example queries](examples.md), and [analysis behavior](analysis.md) for details.
