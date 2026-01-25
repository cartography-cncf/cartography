## SentinelOne Schema

### S1Account

Represents a SentinelOne account, which is the top-level organizational unit for managing SentinelOne resources.

> **Ontology Mapping**: This node has the extra label `Tenant` to enable cross-platform queries for tenant accounts across different systems (e.g., OktaOrganization, AWSAccount).

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | The unique identifier for the SentinelOne account. |
| **name** | The name of the SentinelOne account |
| account_type | The type of account (e.g., Trial, Paid) |
| active_agents | Number of active agents in the account |
| created_at | ISO 8601 timestamp of when the account was created |
| expiration | ISO 8601 timestamp of when the account expires |
| number_of_sites | Number of sites configured in the account |
| state | Current state of the account (e.g., Active, Deleted, Expired) |

#### Relationships

- A S1Account contains S1Agents.

    ```
    (S1Account)-[RESOURCE]->(S1Agent)
    ```

- A S1Account contains S1Applications.

    ```
    (S1Account)-[RESOURCE]->(S1Application)
    ```

- A S1Account contains S1ApplicationVersions.

    ```
    (S1Account)-[RESOURCE]->(S1ApplicationVersion)
    ```

- A S1Account has security risks through S1AppFindings.

    ```
    (S1Account)-[RESOURCE]->(S1AppFinding)
    ```

### S1Agent

Represents a SentinelOne agent installed on an endpoint device.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | The unique identifier for the SentinelOne agent |
| **uuid** | The UUID of the agent |
| **computer_name** | The name of the computer where the agent is installed |
| **serial_number** | The serial number of the endpoint device |
| firewall_enabled | Boolean indicating if the firewall is enabled |
| os_name | The name of the operating system |
| os_revision | The operating system revision/version |
| domain | The domain the computer belongs to |
| last_active | ISO 8601 timestamp of when the agent was last active |
| last_successful_scan | ISO 8601 timestamp of the last successful scan |
| scan_status | Status of the last scan |

#### Relationships

- A S1Agent belongs to a S1Account.

    ```
    (S1Agent)<-[RESOURCE]-(S1Account)
    ```

- A S1Agent has installed S1ApplicationVersions.

    ```
    (S1Agent)-[HAS_INSTALLED]->(S1ApplicationVersion)
    ```

- A S1Agent is affected by S1AppFindings.

    ```
    (S1Agent)<-[AFFECTS]-(S1AppFinding)
    ```

### S1Application

Represents an application managed by SentinelOne.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | The unique identifier for the application (normalized vendor:name) |
| **name** | The name of the application |
| **vendor** | The vendor of the application |

#### Relationships

- A S1Application belongs to a S1Account.

    ```
    (S1Application)<-[RESOURCE]-(S1Account)
    ```

- A S1Application has S1ApplicationVersions.

    ```
    (S1Application)-[VERSION]->(S1ApplicationVersion)
    ```

### S1ApplicationVersion

Represents a specific version of an application.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | The unique identifier for the application version (normalized vendor:name:version) |
| **version** | The version string |
| application_name | The name of the application |
| application_vendor | The vendor of the application |

#### Relationships

- A S1ApplicationVersion belongs to a S1Account.

    ```
    (S1ApplicationVersion)<-[RESOURCE]-(S1Account)
    ```

- A S1ApplicationVersion is installed on S1Agents.

    ```
    (S1Agent)-[HAS_INSTALLED]->(S1ApplicationVersion)
    ```

    The HAS_INSTALLED relationship includes additional properties:

    | Property | Description |
    |----------|-------------|
    | installeddatetime | ISO 8601 timestamp of when the application was installed |
    | installationpath | The file system path where the application is installed |

- A S1ApplicationVersion belongs to a S1Application.

    ```
    (S1Application)-[VERSION]->(S1ApplicationVersion)
    ```

- A S1ApplicationVersion is affected by S1AppFindings.

    ```
    (S1AppFinding)-[AFFECTS]->(S1ApplicationVersion)
    ```

### S1AppFinding

Represents a specific **instance** of a vulnerability detection (finding) on a specific endpoint. Unlike generic CVE definitions, each `S1AppFinding` node represents a unique finding on a specific agent.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | The unique identifier for the specific finding instance (API ID) |
| **cve_id** | The CVE identifier (e.g., CVE-2023-12345) |
| risk_score | Risk score |
| report_confidence | Confidence level of the report |
| days_detected | Number of days since detection |
| detection_date | ISO 8601 timestamp of detection (e.g. 2018-02-27T04:49:26.257525Z) |
| last_scan_date | ISO 8601 timestamp of last scan (e.g. 2018-02-27T04:49:26.257525Z) |
| last_scan_result | Result of the last scan |
| status | Status of the finding (e.g., Active) |
| mitigation_status | Status of mitigation |
| mitigation_status_reason | Reason for mitigation status |
| mitigation_status_changed_by | User who changed mitigation status |
| mitigation_status_change_time | Time of mitigation status change |
| marked_by | User who marked the finding |
| marked_date | Date when finding was marked |
| mark_type_description | Description of mark type |
| reason | Reason for the finding |
| remediation_level | Remediation level of the finding |

#### Relationships

- A S1AppFinding belongs to a S1Account (scoped cleanup).

    ```
    (S1Account)-[RESOURCE]->(S1AppFinding)
    ```

- A S1AppFinding affects a specific S1Agent (the endpoint where it was found).

    ```
    (S1AppFinding)-[AFFECTS]->(S1Agent)
    ```

- A S1AppFinding affects a specific S1ApplicationVersion (the vulnerable software).

    ```
    (S1AppFinding)-[AFFECTS]->(S1ApplicationVersion)
    ```

- A S1AppFinding is linked to a generic CVE definition.

    ```
    (S1AppFinding)-[LINKED_TO]->(CVE)
    ```
