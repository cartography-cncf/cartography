## Microsoft Intune Schema

### IntuneTenant

Representation of an Intune Tenant. This node shares the same identity as the Entra/Azure tenant.

> **Ontology Mapping**: This node has the extra labels `AzureTenant` and `Tenant`.

| Field | Description |
|-------|-------------|
| id | Tenant ID (GUID) |
| display_name | Display name of the tenant |

### IntuneManagedDevice

Representation of a [Managed Device](https://learn.microsoft.com/en-us/graph/api/resources/intune-devices-manageddevice?view=graph-rest-1.0) enrolled in Intune.

| Field | Description |
|-------|-------------|
| id | Unique identifier for the managed device |
| device_name | Name of the device |
| user_id | ID of the user associated with the device |
| user_principal_name | UPN of the user associated with the device |
| managed_device_owner_type | Ownership type: `company` or `personal` |
| operating_system | Operating system (e.g., Windows, macOS, iOS) |
| os_version | Operating system version |
| compliance_state | Compliance state: `compliant`, `noncompliant`, `conflict`, `error`, `inGracePeriod`, `configManager`, `unknown` |
| is_encrypted | Whether the device is encrypted |
| jail_broken | Whether the device is jail broken or rooted |
| management_agent | Management channel (e.g., `mdm`, `eas`) |
| manufacturer | Device manufacturer |
| model | Device model |
| serial_number | Serial number |
| imei | IMEI identifier |
| meid | MEID identifier |
| wifi_mac_address | Wi-Fi MAC address |
| ethernet_mac_address | Ethernet MAC address |
| azure_ad_device_id | Azure AD device ID |
| azure_ad_registered | Whether registered in Azure AD |
| device_enrollment_type | How the device was enrolled |
| device_registration_state | Device registration state |
| is_supervised | Whether the device is supervised |
| enrolled_date_time | When the device was enrolled |
| last_sync_date_time | Last successful sync with Intune |
| eas_activated | Whether Exchange ActiveSync is activated |
| eas_device_id | Exchange ActiveSync device ID |
| partner_reported_threat_state | Threat state from Mobile Threat Defense partner |
| total_storage_space_in_bytes | Total storage in bytes |
| free_storage_space_in_bytes | Free storage in bytes |
| physical_memory_in_bytes | Physical memory in bytes |

#### Relationships

- Intune managed devices belong to a tenant

    ```cypher
    (:IntuneTenant)-[:RESOURCE]->(:IntuneManagedDevice)
    ```

- Entra users enroll devices in Intune

    ```cypher
    (:EntraUser)-[:ENROLLED_TO]->(:IntuneManagedDevice)
    ```

### IntuneDetectedApp

Representation of a [Detected App](https://learn.microsoft.com/en-us/graph/api/resources/intune-devices-detectedapp?view=graph-rest-1.0) discovered on managed devices.

| Field | Description |
|-------|-------------|
| id | Unique identifier for the detected app |
| display_name | Name of the discovered application |
| version | Version of the application |
| size_in_byte | Size of the application in bytes |
| device_count | Number of devices with this app installed |
| publisher | Publisher of the application |
| platform | Platform: `windows`, `ios`, `macOS`, `chromeOS`, etc. |

#### Relationships

- Detected apps belong to a tenant

    ```cypher
    (:IntuneTenant)-[:RESOURCE]->(:IntuneDetectedApp)
    ```

- Managed devices have detected apps installed

    ```cypher
    (:IntuneManagedDevice)-[:HAS_APP]->(:IntuneDetectedApp)
    ```

### IntuneCompliancePolicy

Representation of a [Device Compliance Policy](https://learn.microsoft.com/en-us/graph/api/resources/intune-deviceconfig-devicecompliancepolicy?view=graph-rest-1.0) configured in Intune.

| Field | Description |
|-------|-------------|
| id | Unique identifier for the compliance policy |
| display_name | Admin-provided name of the policy |
| description | Admin-provided description |
| platform | Target platform (derived from `@odata.type`) |
| version | Version of the policy |
| created_date_time | When the policy was created |
| last_modified_date_time | When the policy was last modified |

#### Relationships

- Compliance policies belong to a tenant

    ```cypher
    (:IntuneTenant)-[:RESOURCE]->(:IntuneCompliancePolicy)
    ```

- Compliance policies are assigned to Entra groups

    ```cypher
    (:IntuneCompliancePolicy)-[:ASSIGNED_TO]->(:EntraGroup)
    ```
