## OCI Schema

### OCITenancy

Representation of an OCI Tenancy (the root resource).

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | The OCI Tenancy OCID |
| **ocid** | The OCI Tenancy OCID (indexed) |
| name | The name of the tenancy profile |

#### Relationships

- Many node types belong to an `OCITenancy`:

    ```
    (OCITenancy)-[RESOURCE]->(OCIUser)
    (OCITenancy)-[RESOURCE]->(OCIGroup)
    (OCITenancy)-[RESOURCE]->(OCICompartment)
    (OCITenancy)-[RESOURCE]->(OCIPolicy)
    (OCITenancy)-[RESOURCE]->(OCIRegion)
    ```

### OCIUser

Representation of an [OCI User](https://docs.cloud.oracle.com/iaas/api/#/en/identity/20160918/User).

> **Ontology Mapping**: This node has the extra label `UserAccount` to enable cross-platform queries for user accounts across different systems (e.g., OktaUser, GitHubUser, EntraUser).

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | The OCI User OCID |
| **ocid** | The OCI User OCID (indexed) |
| name | The friendly name of the user |
| description | The description of the user |
| **email** | The email address of the user (indexed) |
| compartmentid | The compartment OCID of the user |
| lifecycle_state | The user's current state (CREATING, ACTIVE, INACTIVE, DELETING, DELETED) |
| is_mfa_activated | Flag indicating if MFA has been activated for the user |
| can_use_api_keys | Indicates if the user can use API keys |
| can_use_auth_tokens | Indicates if the user can use auth tokens |
| can_use_console_password | Indicates if the user can log in to the console |
| can_use_customer_secret_keys | Indicates if the user can use customer secret keys |
| can_use_smtp_credentials | Indicates if the user can use SMTP credentials |
| createdate | ISO 8601 date-time when the user was created |

#### Relationships

- OCI Users belong to an OCI Tenancy:

    ```
    (OCITenancy)-[RESOURCE]->(OCIUser)
    ```

- OCI Users can be members of OCI Groups:

    ```
    (OCIUser)-[MEMBER_OCID_GROUP]->(OCIGroup)
    ```

### OCIGroup

Representation of an [OCI Group](https://docs.cloud.oracle.com/iaas/api/#/en/identity/20160918/Group).

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | The OCI Group OCID |
| **ocid** | The OCI Group OCID (indexed) |
| name | The friendly name that identifies the group |
| description | The description of the group |
| compartmentid | The OCID of the tenancy containing the group |
| createdate | ISO 8601 date-time string when the group was created |

#### Relationships

- OCI Groups belong to an OCI Tenancy:

    ```
    (OCITenancy)-[RESOURCE]->(OCIGroup)
    ```

- OCI Users can be members of OCI Groups:

    ```
    (OCIUser)-[MEMBER_OCID_GROUP]->(OCIGroup)
    ```

- OCI Policies can reference OCI Groups:

    ```
    (OCIPolicy)-[OCI_POLICY_REFERENCE]->(OCIGroup)
    ```

### OCICompartment

Representation of an [OCI Compartment](https://docs.cloud.oracle.com/iaas/api/#/en/identity/20160918/Compartment).

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | The OCI Compartment OCID |
| **ocid** | The OCI Compartment OCID (indexed) |
| name | The friendly name of the compartment |
| description | The description of the compartment |
| compartmentid | The parent compartment OCID |
| createdate | ISO 8601 date-time when the compartment was created |

#### Relationships

- OCI Compartments belong to an OCI Tenancy:

    ```
    (OCITenancy)-[RESOURCE]->(OCICompartment)
    ```

- Nested OCI Compartments link to their parent compartment:

    ```
    (OCICompartment)-[PARENT]->(OCICompartment)
    ```

- OCI Compartments have deprecated relationships for backward compatibility:

    ```
    (OCITenancy)-[OCI_COMPARTMENT]->(OCICompartment)
    (OCICompartment)-[OCI_COMPARTMENT]->(OCICompartment)
    ```

- OCI Policies can reference OCI Compartments:

    ```
    (OCIPolicy)-[OCI_POLICY_REFERENCE]->(OCICompartment)
    ```

### OCIPolicy

Representation of an [OCI Policy](https://docs.cloud.oracle.com/iaas/api/#/en/identity/20160918/Policy).

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | The OCI Policy OCID |
| **ocid** | The OCI Policy OCID (indexed) |
| name | The friendly name identifying the policy |
| description | The description of the policy |
| compartmentid | The OCID of the compartment containing the policy |
| statements | An array of policy statements written in the policy language |
| createdate | ISO 8601 date-time when the policy was created |
| updatedate | ISO 8601 date-time when the policy was last updated |

#### Relationships

- OCI Policies belong to an OCI Tenancy:

    ```
    (OCITenancy)-[RESOURCE]->(OCIPolicy)
    ```

- OCI Policies have a deprecated relationship for backward compatibility:

    ```
    (OCITenancy)-[OCI_POLICY]->(OCIPolicy)
    ```

- OCI Policies can reference OCI Groups (derived from parsing policy statements):

    ```
    (OCIPolicy)-[OCI_POLICY_REFERENCE]->(OCIGroup)
    ```

- OCI Policies can reference OCI Compartments (derived from parsing policy statements):

    ```
    (OCIPolicy)-[OCI_POLICY_REFERENCE]->(OCICompartment)
    ```

### OCIRegion

Representation of an OCI Region subscription.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | The region key |
| **regionkey** | The region key (indexed) |
| name | The friendly name of the region |
| ishomeregion | Whether this is the home region for the tenancy |
| status | The region subscription status |

#### Relationships

- OCI Regions belong to an OCI Tenancy:

    ```
    (OCITenancy)-[RESOURCE]->(OCIRegion)
    ```

- OCI Regions have a deprecated relationship for backward compatibility:

    ```
    (OCITenancy)-[OCI_REGION_SUBSCRIPTION]->(OCIRegion)
    ```
