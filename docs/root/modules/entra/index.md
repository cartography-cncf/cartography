# Microsoft Entra (formerly Azure AD)


```{toctree}
config
schema
examples
```


Microsoft Entra (formerly Azure Active Directory) is Microsoft's cloud-based identity and access management service. Cartography can ingest data from Entra to provide visibility into users, groups, applications, service principals, and tenants in your organization.

This module also includes Microsoft Intune support, ingesting managed devices, detected apps, and compliance policies. Intune uses the same Entra credentials and requires the following additional Microsoft Graph API permissions:

- `DeviceManagementManagedDevices.Read.All` — for managed devices and detected apps
- `DeviceManagementConfiguration.Read.All` — for compliance policies
