## SentinelOne Schema

### S1Account

Represents a SentinelOne account, which is the top-level organizational unit for managing SentinelOne resources.

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

- A S1Account has security risks through S1CVEs.

    ```
    (S1Account)-[RISK]->(S1CVE)
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
| scan_status | Current scan status of the agent |

#### Relationships

- A S1Agent belongs to a S1Account.

    ```
    (S1Agent)-[RESOURCE]->(S1Account)
    ```

- A S1Agent has installed application versions.

    ```
    (S1Agent)-[HAS_INSTALLED]->(S1ApplicationVersion)
    ```

### S1Application

Represents an application discovered in the SentinelOne environment.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | The unique identifier for the application (normalized vendor:name) |
| **name** | The name of the application |
| **vendor** | The vendor/publisher of the application |

#### Relationships

- A S1Application belongs to a S1Account.

    ```
    (S1Application)-[RESOURCE]->(S1Account)
    ```

- A S1Application has versions.

    ```
    (S1Application)-[VERSION]->(S1ApplicationVersion)
    ```

### S1ApplicationVersion

Represents a specific version of an application installed on SentinelOne agents.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | The unique identifier for the application version (normalized vendor:name:version) |
| **application_name** | The name of the application |
| **application_vendor** | The vendor/publisher of the application |
| **version** | The version string of the application |

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

- A S1ApplicationVersion can be affected by S1CVEs.

    ```
    (S1CVE)-[AFFECTS]->(S1ApplicationVersion)
    ```

### S1CVE

Represents a Common Vulnerability and Exposure (CVE) discovered in applications managed by SentinelOne.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | The unique identifier for the S1CVE record. Format: `S1\|{cve_id}`. |
| **cve_id** | The CVE identifier (e.g., CVE-2023-12345) |
| base_score | The CVSS base score for the vulnerability |
| cvss_version | The version of CVSS used for scoring |
| published_date | ISO 8601 timestamp of when the CVE was published |
| severity | The severity level of the vulnerability (e.g., Critical, High, Medium, Low) |

#### Relationships

- A S1CVE belongs to a S1Account.

    ```
    (S1Account)-[RISK]->(S1CVE)
    ```

- A S1CVE affects a S1ApplicationVersion.

    ```
    (S1CVE)-[AFFECTS]->(S1ApplicationVersion)
    ```

    The AFFECTS relationship includes additional properties specific to each CVE finding:

    | Property | Description |
    |----------|-------------|
    | days_detected | Number of days since the CVE was first detected in this application version |
    | detection_date | ISO 8601 timestamp of when the CVE was first detected |
    | last_scan_date | ISO 8601 timestamp of the last scan that detected this CVE |
    | last_scan_result | Result of the last scan for this CVE |
    | status | Current status of the CVE finding (e.g., Active, Resolved) |
