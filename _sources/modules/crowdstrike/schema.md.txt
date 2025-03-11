## Crowdstrike Schema

.. _crowdstrike_schema:

### CrowdstrikeHost

Representation of a Crowdstrike Host

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| id | The device ID for this host |
| cid | The customer ID |
| instance\_id | The AWS instance ID associated with this host |
| status | Containment Status of the machine. "Normal" denotes good operations; other values might mean reduced functionality or support. |
| hostname | The name of the machine. |
| machine\_domain | Active Directory domain name. |
| crowdstrike\_first\_seen | Timestamp of device’s first connection to Falcon |
| crowdstrike\_last\_seen | Timestamp of device’s most recent connection to Falcon |
| local\_ip | The device's local IP address. |
| external\_ip | External IP of the device, as seen by CrowdStrike. |
| cpu\_signature | The CPU signature of the device. |
| bios\_manufacturer | Bios manufacture name. |
| bios\_version | Bios version. |
| mac\_address | The MAC address of the device |
| os\_version | Operating system version. |
| os\_build | The build of the OS |
| platform\_id | CrowdStrike agent configuration notes |
| platform\_name | Operating system platform. |
| service\_provider | The service provider for the device. |
| service\_provider\_account\_id | The service provider account ID associated with this device |
| agent\_version | CrowdStrike agent configuration notes |
| system\_manufacturer | Name of system manufacturer |
| system\_product\_name | Name of system product |
| product\_type | The product type |
| product\_type\_desc | Name of product type. |
| provision\_status | The provision status of the device |
| reduced\_functionality\_mode | Reduced functionality mode (RFM) status |
| kernel\_version | Kernel version of the host OS. |
| major\_version | Major version of the Operating System |
| minor\_version | Minor version of the Operating System |
| tags | Grouping tags for the device |
| modified\_timestamp | The last time that the machine record was updated. Can include status like containment status changes or configuration group changes |

#### Relationships

- CrowdstrikeHost has SpotlightVulnerability
    ```
    (CrowdstrikeHost)-[HAS_VULNERABILITY]->(SpotlightVulnerability)
    ```

### SpotlightVulnerability

Representation of a Crowdstrike Vulnerability

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| id | The ID for this vulnerability |
| cid | The customer ID |
| aid | The unique identifier (agent ID) of the sensor where the vulnerability was found. |
| status | The vulnerability’s current status. One of open, closed, reopen, or expired. |
| created\_timestamp | The UTC date and time that the vulnerability was created in Spotlight. |
| closed\_timestamp | The date and time a vulnerability was set to a status of "closed" |
| updated\_timestamp | The UTC date and time of the last update made on a vulnerability. |
| cve\_id | The ID of the CVE. |
| host\_info\_local\_ip | The device’s local IP address. |
| remediation\_ids | The unique IDs of the remediations. |
| app\_product\_name\_version | The name and version of the product associated with the vulnerability. |

#### Relationships

- CrowdstrikeHost has SpotlightVulnerability
    ```
    (CrowdstrikeHost)-[HAS_VULNERABILITY]->(SpotlightVulnerability)
    ```

- SpotlightVulnerability has CVE
    ```
    (SpotlightVulnerability)-[HAS_CVE]->(CVE)
    ```

### CVE::CrowdstrikeFinding

Representation of a CVE

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| id | The ID for this CVE |
| base\_score | Base score of the CVE (float value between 1 and 10). |
| severity | Severity of the CVE. One of CRITICAL, HIGH, MEDIUM, LOW, UNKNOWN, or NONE. |
| exploitability\_score | Numeric value of the most severe known exploit. 0=UNPROVEN; 30=AVAILABLE; 60=EASILY\_ACCESSIBLE; 90=ACTIVELY\_USED |

#### Relationships

- SpotlightVulnerability has CVE
    ```
    (SpotlightVulnerability)-[HAS_CVE]->(CVE)
    ```
