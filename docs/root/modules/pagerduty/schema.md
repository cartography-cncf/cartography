## Pagerduty Schema

### PagerDutyEscalationPolicy

Representation of a [PagerDuty Escalation Policy](https://developer.pagerduty.com/api-reference/c2NoOjI3NDgwMjE-escalation-policy)

| Field | Description |
|-------|--------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| id | The ID of the escalation policy |
| html\_url | the API show URL at which the object is accessible |
| type | The type of this pagerduty object (escalation\_policy) |
| summary | A short-form, server-generated string that provides succinct, important information about an object suitable for primary labeling of an entity in a client. In many cases, this will be identical to name, though it is not intended to be an identifier. |
| on\_call\_handoff\_notifications | Determines how on call handoff notifications will be sent for users on the escalation policy. Defaults to "if\_has\_services". |
| name | The name of the escalation policy. |
| num\_loops | The number of times the escalation policy will repeat after reaching the end of its escalation. |

#### Relationships

- A PagerDutyEscalationPolicy has PagerDutyEscalationPolicyRules

    ```
    (PagerDutyEscalationPolicy)-[HAS\_RULE]->(PagerDutyEscalationPolicyRule)
    ```

- A PagerDutyEscalationPolicy is associated with PagerDutyUsers

    ```
    (PagerDutyEscalationPolicy)-[ASSOCIATED\_WITH]->(PagerDutyUser)
    ```

- A PagerDutyEscalationPolicy is associated with PagerDutySchedules

    ```
    (PagerDutyEscalationPolicy)-[ASSOCIATED\_WITH]->(PagerDutySchedule)
    ```

- A PagerDutyEscalationPolicy is associated with PagerDutyServices

    ```
    (PagerDutyEscalationPolicy)-[ASSOCIATED\_WITH]->(PagerDutyService)
    ```

- A PagerDutyEscalationPolicy is associated with PagerDutyTeams

    ```
    (PagerDutyEscalationPolicy)-[ASSOCIATED\_WITH]->(PagerDutyTeam)
    ```

### PagerDutySchedule

Representation of a [PagerDuty Schedule](https://developer.pagerduty.com/api-reference/c2NoOjI3NDgwMzU-schedule)

| Field | Description |
|-------|--------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| id | The ID of the schedule |
| html\_url | the API show URL at which the object is accessible |
| type | The type of this pagerduty object (schedule) |
| summary | A short-form, server-generated string that provides succinct, important information about an object suitable for primary labeling of an entity in a client. In many cases, this will be identical to name, though it is not intended to be an identifier. |
| name | The name of the schedule. |
| time\_zone | The time zone of the schedule |
| description | The description of the schedule |

#### Relationships

- A PagerDutySchedule has PagerDutyScheduleLayers

    ```
    (PagerDutySchedule)-[HAS\_LAYER]->(PagerDutyScheduleLayer)
    ```

### PagerDutyScheduleLayer

Representation of a layer in a [PagerDuty Schedule](https://developer.pagerduty.com/api-reference/c2NoOjI3NDgwMzU-schedule)

| Field | Description |
|-------|--------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| id | The ID of the schedule layer |
| schedule\_id | The ID of the schedule this layer is attached to. |
| start | The start time of this layer |
| end | The end time of this layer. If null, the layer does not end. |
| rotation\_virtual\_start | The effective start time of the layer. This can be before the start time of the schedule. |
| rotation\_turn\_length\_seconds | The duration of each on-call shift in seconds. |

#### Relationships

No relationships originating from PagerDutyScheduleLayer

### PagerDutyService

Representation of a [PagerDuty Service](https://developer.pagerduty.com/api-reference/c2NoOjI3NDgwMjc-service)

| Field | Description |
|-------|--------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| id | The ID of the service |
| html\_url | the API show URL at which the object is accessible |
| type | The type of this pagerduty object (service) |
| summary | A short-form, server-generated string that provides succinct, important information about an object suitable for primary labeling of an entity in a client. In many cases, this will be identical to name, though it is not intended to be an identifier. |
| name | The name of this service |
| description | The user-provided description of the service. |
| auto\_resolve\_timeout | Time in seconds that an incident is automatically resolved if left open for that long. Value is null if the feature is disabled. Value must not be negative. Setting this field to 0, null (or unset in POST request) will disable the feature. |
| acknowledgement\_timeout | Time in seconds that an incident changes to the Triggered State after being Acknowledged. Value is null if the feature is disabled. Value must not be negative. Setting this field to 0, null (or unset in POST request) will disable the feature. |
| created\_at | The date/time when this service was created |
| status | The current state of the Service. |
| alert\_creation | Whether a service creates only incidents, or both alerts and incidents. A service must create alerts in order to enable incident merging. |
| alert\_grouping\_parameters\_type | The type of Alert Grouping. |
| incident\_urgency\_rule\_type | The type of incident urgency: whether it's constant, or it's dependent on the support hours. |
| incident\_urgency\_rule\_during\_support\_hours\_type | The type of incident urgency: whether it's constant, or it's dependent on the support hours. |
| incident\_urgency\_rule\_during\_support\_hours\_urgency | The incidents' urgency, if type is constant. |
| incident\_urgency\_rule\_outside\_support\_hours\_type | The type of incident urgency: whether it's constant, or it's dependent on the support hours. |
| incident\_urgency\_rule\_outside\_support\_hours\_urgency | The incidents' urgency, if type is constant. |
| support\_hours\_type | The type of support hours |
| support\_hours\_time\_zone | The time zone for the support hours |
| support\_hours\_start\_time | The support hours' starting time of day (date portion is ignored) |
| support\_hours\_end\_time | support\_hours\_end\_time |
| support\_hours\_days\_of\_week | (no description) |

#### Relationships

- A PagerDutyService has PagerDutyIntegrations

    ```
    (PagerDutyService)-[HAS\_INTEGRATION]->(PagerDutyIntegration)
    ```

### PagerDutyIntegration

Representation of a [PagerDuty Integration](https://developer.pagerduty.com/api-reference/c2NoOjI3NDgwMzA-integration)

| Field | Description |
|-------|--------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| id | The ID of the integration |
| html\_url | the API show URL at which the object is accessible |
| type | The type of this pagerduty object (integration) |
| summary | A short-form, server-generated string that provides succinct, important information about an object suitable for primary labeling of an entity in a client. In many cases, this will be identical to name, though it is not intended to be an identifier. |
| name | The name of this integration |
| created\_at | The date/time when this integration was created. |

#### Relationships

- A PagerDutyIntegration has PagerDutyVendors

    ```
    (PagerDutyIntegration)-[HAS\_VENDOR]->(PagerDutyVendor)
    ```

### PagerDutyTeam

Representation of a [PagerDuty Team](https://developer.pagerduty.com/api-reference/c2NoOjI3NDgwMTc-team)

| Field | Description |
|-------|--------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| id | The ID of the team |
| html\_url | the API show URL at which the object is accessible |
| type | The type of this pagerduty object (team) |
| summary | A short-form, server-generated string that provides succinct, important information about an object suitable for primary labeling of an entity in a client. In many cases, this will be identical to name, though it is not intended to be an identifier. |
| name | The name of the team |
| description | The description of the team |
| default\_role | (no description, but returned by API) |

#### Relationships

- A PagerDutyTeam is associated with PagerDutyServices

    ```
    (PagerDutyTeam)-[ASSOCIATED\_WITH]->(PagerDutyServices)
    ```

### PagerDutyUser

Representation of a [PagerDuty User](https://developer.pagerduty.com/api-reference/c2NoOjI3NDgwMTU-user)

| Field | Description |
|-------|--------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| id | The ID of the user |
| html\_url | the API show URL at which the object is accessible |
| type | The type of this pagerduty object (user) |
| summary | A short-form, server-generated string that provides succinct, important information about an object suitable for primary labeling of an entity in a client. In many cases, this will be identical to name, though it is not intended to be an identifier. |
| name | The name of the user |
| email | The user's email address
| time\_zone | The preferred time zone name. If null, the account's time zone will be used. |
| color | The schedule color |
| role | The user role. Account must have the read\_only\_users ability to set a user as a read\_only\_user or a read\_only\_limited\_user, and must have advanced permissions abilities to set a user as observer or restricted\_access. |
| avatar\_url | The URL of the user's avatar. |
| description | The user's bio. |
| invitation\_sent | If true, the user has an outstanding invitation. |
| job\_title | The user's title |

#### Relationships

- A PagerDutyUser is a member of PagerDutySchedules

    ```
    (PagerDutyUser)-[MEMBER\_OF]->(PagerDutySchedule)
    ```

- A PagerDutyUser is a member of PagerDutyScheduleLayers

    ```
    (PagerDutyUser)-[MEMBER\_OF]->(PagerDutyScheduleLayer)
    ```

- A PagerDutyUser is a member of PagerDutyTeams

    ```
    (PagerDutyUser)-[MEMBER\_OF]->(PagerDutyTeam)
    ```
