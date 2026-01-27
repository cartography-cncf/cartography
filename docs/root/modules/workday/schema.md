## Workday Schema

```mermaid
graph LR

H(WorkdayHuman) -- MEMBER_OF_ORGANIZATION --> O(WorkdayOrganization)
H -- REPORTS_TO --> H2(WorkdayHuman)
```

### WorkdayHuman

Representation of a person in Workday. WorkdayHuman nodes include the `Human` label for cross-module identity integration.

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first created this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| **id** | Employee ID from Workday |
| **employee_id** | Employee ID (indexed for lookups) |
| **name** | Employee's full name |
| **email** | Work email address (indexed for cross-module relationships) |
| **title** | Job title/business title |
| **worker_type** | Type of worker (Employee, Contractor, etc.) |
| **location** | Office or work location |
| **country** | Country from work address |
| **cost_center** | Cost center code |
| **function** | Functional area |
| **sub_function** | Sub-functional area |
| **team** | Team name |
| **sub_team** | Sub-team name |
| **company** | Company or legal entity name |
| **source** | Always `"WORKDAY"` to identify data source |

#### Relationships

- WorkdayHumans are members of WorkdayOrganizations

    ```
    (WorkdayHuman)-[MEMBER_OF_ORGANIZATION]->(WorkdayOrganization)
    ```

- WorkdayHumans report to other WorkdayHumans (manager hierarchy)

    ```
    (WorkdayHuman)-[REPORTS_TO]->(WorkdayHuman)
    ```

#### Human Label Integration

WorkdayHuman nodes include the `Human` label, enabling cross-module identity queries with Duo, Okta, and other identity sources.

### WorkdayOrganization

Representation of a supervisory organization or department in Workday.

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first created this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| **id** | Organization name |
| **name** | Organization name |

#### Relationships

```
(WorkdayHuman)-[MEMBER_OF_ORGANIZATION]->(WorkdayOrganization)
```
