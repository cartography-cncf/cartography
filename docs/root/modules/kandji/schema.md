## Kandji Schema

### KandjiTenant

Representation of a Kandji Tenant.

> **Ontology Mapping**: This node has the extra label `Tenant` to enable cross-platform queries for tenant accounts across different systems (e.g., OktaOrganization, AWSAccount).

|Field | Description|
|-------|-------------|
| id | Kandji Tenant id e.g. "company name"|

### KandjiDevice

Representation of a Kandji device.

> **Ontology Mapping**: This node has the extra label `Device` to enable cross-platform queries for devices across different systems (e.g., BigfixComputer, CrowdstrikeHost, TailscaleDevice).

|Field | Description|
|-------|-------------|
|id | same as device_id|
|device_id | Kandji device id|
|device_name | The friendly name of the device|
|last_check_in | Last time the device checked-in with Kandji|
|model | Model of the device|
|os_version | OS version running on the device |
|platform | Should be Mac for all devices|
|serial_number | Serial number of the device|

#### Relationships

- Kandji devices are enrolled to a Kandji Tenant

    ```
    (KandjiDevice)<-[RESOURCE]-(KandjiTenant)
    ```
