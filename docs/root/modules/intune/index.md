# Microsoft Intune

```{toctree}
schema
```

Microsoft Intune is Microsoft's cloud-based endpoint management service. Cartography can ingest data from Intune to provide visibility into managed devices, compliance policies, and detected applications in your organization.

Intune uses the same credentials as the Entra module (`entra_tenant_id`, `entra_client_id`, `entra_client_secret`). The app registration requires the following additional Microsoft Graph API permissions:

- `DeviceManagementManagedDevices.Read.All` — for managed devices and detected apps
- `DeviceManagementConfiguration.Read.All` — for compliance policies
