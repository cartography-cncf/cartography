## Microsoft Schema

The `microsoft` module is the top-level umbrella for Microsoft tenant, SaaS, and security control plane data ingested via Microsoft Graph. It currently contains the following submodules:

- **entra** — Entra ID identity objects (users, groups, OUs, applications, service principals, app role assignments)
- **intune** — Intune managed devices, detected apps, and compliance policies

See the `entra` schema section above for Entra identity node and relationship definitions. Intune node definitions are documented below.

### IntuneManagedDevice

Representation of a device managed by Microsoft Intune.

| Field | Description |
|-------|-------------|
| id | Unique identifier for the managed device |
| device_name | Name of the device |
| operating_system | Operating system on the device |
| os_version | Operating system version |
| compliance_state | Compliance state of the device |
| enrollment_type | Type of device enrollment |
| owner_type | Owner type of the device |
| user_id | ID of the primary user of the device |
| user_display_name | Display name of the primary user |
| user_principal_name | User principal name of the primary user |
| last_sync_date_time | Date and time of last sync with Intune |
| enrolled_date_time | Date and time device was enrolled |
| serial_number | Serial number of the device |
| managed_device_owner_type | Owner type of the managed device |
| registration_state | Registration state of the device |
| management_state | Management state of the device |
| manufacturer | Manufacturer of the device |
| model | Model of the device |
| total_storage_space_in_bytes | Total storage space in bytes |
| free_storage_space_in_bytes | Free storage space in bytes |
| jail_broken | Whether the device is jail broken |
| is_encrypted | Whether the device is encrypted |
| is_supervised | Whether the device is supervised |
| lastupdated | Timestamp of the last update to this node |
| firstseen | Timestamp of when this node was first seen |

#### Relationships

- `EntraTenant -[:RESOURCE]-> IntuneManagedDevice`

### IntuneDetectedApp

Representation of an application detected on a device managed by Microsoft Intune.

| Field | Description |
|-------|-------------|
| id | Unique identifier for the detected app (composite of tenant, app, device) |
| display_name | Display name of the application |
| version | Version of the application |
| size_in_byte | Size of the application in bytes |
| device_count | Number of devices this app is detected on |
| lastupdated | Timestamp of the last update to this node |
| firstseen | Timestamp of when this node was first seen |

#### Relationships

- `EntraTenant -[:RESOURCE]-> IntuneDetectedApp`
- `IntuneManagedDevice -[:HAS_INSTALLED]-> IntuneDetectedApp`

### IntuneCompliancePolicy

Representation of a device compliance policy in Microsoft Intune.

| Field | Description |
|-------|-------------|
| id | Unique identifier for the compliance policy |
| display_name | Display name of the compliance policy |
| description | Description of the compliance policy |
| created_date_time | Date and time the policy was created |
| last_modified_date_time | Date and time the policy was last modified |
| policy_type | Type of compliance policy |
| lastupdated | Timestamp of the last update to this node |
| firstseen | Timestamp of when this node was first seen |

#### Relationships

- `EntraTenant -[:RESOURCE]-> IntuneCompliancePolicy`
- `IntuneCompliancePolicy -[:APPLIES_TO]-> IntuneManagedDevice`
