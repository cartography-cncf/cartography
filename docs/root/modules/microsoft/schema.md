## Microsoft Schema

The `microsoft` module is the top-level umbrella for Microsoft tenant, SaaS, and security control plane data ingested via Microsoft Graph. It currently contains the following submodules:

- **entra** — Entra ID identity objects (users, groups, OUs, applications, service principals, app role assignments). See the `entra` schema section for node and relationship definitions.
- **intune** — Intune managed devices, detected apps, and compliance policies (documented below).

### IntuneManagedDevice

Representation of a device managed by Microsoft Intune.

| Field | Description |
|-------|-------------|
| id | Unique identifier for the managed device |
| device_name | Name of the device |
| user_id | ID of the primary user of the device |
| user_principal_name | User principal name of the primary user |
| managed_device_owner_type | Owner type of the managed device |
| operating_system | Operating system on the device |
| os_version | Operating system version |
| compliance_state | Compliance state of the device |
| is_encrypted | Whether the device is encrypted |
| jail_broken | Whether the device is jail broken |
| management_agent | Management agent used for the device |
| manufacturer | Manufacturer of the device |
| model | Model of the device |
| serial_number | Serial number of the device |
| imei | IMEI of the device |
| meid | MEID of the device |
| wifi_mac_address | Wi-Fi MAC address of the device |
| ethernet_mac_address | Ethernet MAC address of the device |
| azure_ad_device_id | Azure AD device ID |
| azure_ad_registered | Whether the device is Azure AD registered |
| device_enrollment_type | Type of device enrollment |
| device_registration_state | Registration state of the device |
| is_supervised | Whether the device is supervised |
| enrolled_date_time | Date and time device was enrolled |
| last_sync_date_time | Date and time of last sync with Intune |
| eas_activated | Whether Exchange ActiveSync is activated |
| eas_device_id | Exchange ActiveSync device ID |
| partner_reported_threat_state | Threat state reported by device partner |
| total_storage_space_in_bytes | Total storage space in bytes |
| free_storage_space_in_bytes | Free storage space in bytes |
| physical_memory_in_bytes | Physical memory in bytes |
| lastupdated | Timestamp of the last update to this node |
| firstseen | Timestamp of when this node was first seen |

#### Relationships

- `EntraTenant -[:RESOURCE]-> IntuneManagedDevice`
- `EntraUser -[:ENROLLED_TO]-> IntuneManagedDevice`

### IntuneDetectedApp

Representation of an application detected on a device managed by Microsoft Intune.

| Field | Description |
|-------|-------------|
| id | Intune report `ApplicationKey` for the detected app |
| application_id | Intune report `ApplicationId` when the report includes one |
| display_name | Display name of the application |
| version | Version of the application |
| device_count | Number of devices this app is detected on |
| publisher | Publisher of the application |
| platform | Platform the application runs on |
| lastupdated | Timestamp of the last update to this node |
| firstseen | Timestamp of when this node was first seen |

#### Relationships

- `EntraTenant -[:RESOURCE]-> IntuneDetectedApp`
- `IntuneManagedDevice -[:HAS_APP]-> IntuneDetectedApp`

### IntuneCompliancePolicy

Representation of a device compliance policy in Microsoft Intune.

| Field | Description |
|-------|-------------|
| id | Unique identifier for the compliance policy |
| display_name | Display name of the compliance policy |
| description | Description of the compliance policy |
| platform | Platform the policy applies to |
| version | Version of the compliance policy |
| created_date_time | Date and time the policy was created |
| last_modified_date_time | Date and time the policy was last modified |
| applies_to_all_users | Whether the policy applies to all users |
| applies_to_all_devices | Whether the policy applies to all devices |
| lastupdated | Timestamp of the last update to this node |
| firstseen | Timestamp of when this node was first seen |

#### Relationships

- `EntraTenant -[:RESOURCE]-> IntuneCompliancePolicy`
- `IntuneCompliancePolicy -[:ASSIGNED_TO]-> EntraGroup`
