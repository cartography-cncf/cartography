## Kandji Schema

### KandjiTenant

Representation of a Kandji Tenant.

|Field | Description|
|-------|-------------|
| id | Kandji Tenant id e.g. "company name"|

### KandjiDevice

Representation of a Kandji device.

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
    (KandjiDevice)-[ENROLLED_TO]->(KandjiTenant)
    ```
