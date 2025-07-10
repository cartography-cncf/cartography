## SentinelOne Schema

### S1Account

Represents a SentinelOne account, which is the top-level organizational unit for managing SentinelOne resources.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | The unique identifier for the SentinelOne account |
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
