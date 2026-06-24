---
orphan: true
---

## Entra Configuration

The canonical configuration page for this data source is now [Microsoft Configuration](../microsoft/config.md). The `microsoft` module is the top-level Microsoft Graph ingestion module; Entra ID is one of its submodules.

Use these Microsoft credential flags for new configurations:

- `--microsoft-tenant-id`
- `--microsoft-client-id`
- `--microsoft-client-secret-env-var`

The legacy Entra credential flags remain accepted as deprecated aliases until Cartography v1.0.0:

- `--entra-tenant-id`
- `--entra-client-id`
- `--entra-client-secret-env-var`

Do not mix `--microsoft-*` and `--entra-*` credential flags in the same invocation.
