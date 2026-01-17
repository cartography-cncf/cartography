# MDE Graph Schema

## Nodes

### MDETenant
Represents a unique Microsoft Defender for Endpoint / Entra ID tenant.
* **id**: The Tenant ID.
* **name**: The display name of the tenant.
* **lastupdated**: Internal Cartography timestamp.

### MDEDevice
Represents an endpoint (Workstation, Server, or VM) managed by MDE.
* **id**: The unique MachineId from MDE.
* **aad_device_id**: The Azure Active Directory ID used for infrastructure correlation.
* **computer_name**: The hostname/DNS name of the device.
* **risk_score**: The calculated risk level (High, Medium, Low).

## Relationships

| Start Node | Relationship | End Node | Description |
| :--- | :--- | :--- | :--- |
| `AzureVirtualMachine` | `HAS_MDE_AGENT` | `MDEDevice` | Links Azure VMs to MDE agents via `aad_device_id`. |
| `MDETenant` | `RESOURCE` | `MDEDevice` | Indicates that the device belongs to the tenant. |

## Enrichment Logic
* **Risk-Based Tagging**: If an `MDEDevice` has a `risk_score` of "High", the linked `AzureVirtualMachine` is enriched with the property `risk_tag: "CRITICAL_ASSET"`.