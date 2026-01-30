## OCI Schema

### OCITenancy

Representation of an OCI Tenancy.

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job discovered this node|
|name| The name of the account|
|lastupdated| Timestamp of the last time the node was updated|
|**ocid**| The OCI Tenancy ID number|

#### Relationships
- Many node types belong to an `OCI Tenancy`.

	```
	(OCITenancy)-[RESOURCE]->(OCIUser,
                              OCIGroup,
                              OCICompartment)
	```
- An `OCIPolicy` node is defined for an `OCITenancy`.

	```
	(OCITenancy)-[OCI_POLICY]->(OCIPolicy)
	```

 ### OCICompartment
Representation of an [OCICompartment](https://docs.cloud.oracle.com/iaas/api/#/en/identity/20160918/Compartment)
/ Field / Description /
/-------/-------------/
/ firstseen / Timestamp of when a sync job first discovered this node  /
/ lastupdated /  Timestamp of the last time the node was updated /
/ compartmentid / The compartment id of the compartment /
/ name / The friendly name of the compartment  /
/ description / The description the compartment /
/ createdate / ISO 8601 date-time when the compartment was created /
/ **ocid** / OCI-unique identifier for this object /

- OCI Compartments can be members of OCI Compartments (up to 6 levels deep).

	```
	(OCICompartment)-[OCI_SUB_COMPARTMENT]->(OCICompartment)
	```

- OCI Tenancy's contain OCI Compartments.

	```
	(OCITenancy)-[RESOURCE]->(OCICompartment)
	```
- OCI Compartments can contain OCI Policies.

	```
	(OCICompartment)-[OCI_POLICY]->(OCIPolicy)
	```


### OCIUser
Representation of an [OCIUser](https://docs.cloud.oracle.com/iaas/api/#/en/identity/20160918/User).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| compartmentid | The compartment id of the user |
| name | The friendly name of the user |
| description | The description of the user |
| email | The description of the user |
| lifecycle_state | The user's current state. After creating a user, make sure its lifecycleState changes from CREATING to ACTIVE before using it. |
| is_mfa_activated | Flag indicates if MFA has been activated for the user. |
| can_use_api_keys | Indicates if the user can use API keys. |
| can_use_auth_tokens | Indicates if the user can use SWIFT passwords / auth tokens. |
| can_use_console_password | Indicates if the user can log in to the console. |
| can_use_customer_secret_keys | Indicates if the user can use SigV4 symmetric keys.Indicates if the user can use SigV4 symmetric keys.Indicates if the user can use SigV4 symmetric keys. |
| can_use_smtp_credentials | Indicates if the user can use SMTP passwords. |
| createdate | ISO 8601 date-time when the user was created |
| **ocid** | OCI-unique identifier for this object

#### Relationships\
- OCI Users can be members of OCI Groups.

	```
	(OCIUser)-[MEMBER_OCI_GROUP]->(OCIGroup)
	```

- OCI Tenancy's contain OCI Users.

	```
	(OCITenancy)-[OCI_POLICY]->(OCIUser)
	```

### OCIGroup

Representation of OCI [IAM Groups](https://docs.cloud.oracle.com/iaas/api/#/en/identity/20160918/Group).

| Field | Description |
|-------|-------------|
|firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated|  Timestamp of the last time the node was updated |
| compartmentid | The OCID of the tenancy containing the group |
| name | The friendly name that identifies the group|
| description | The description the group |
| createdate| ISO 8601 date-time string when the group was created |
|**ocid** | The OCI-global identifier for this group |

#### Relationships
- OCIUsers can be members of OCIGroups.

	```
	(OCIUser)-[MEMBER_OCI_GROUP]->(OCIGroup)
	```

- OCIGroups belong to OCITenancy's.

	```
	(OCITenancy)-[RESOURCE]->(OCIGroup)
	```

### OCIPolicy

Representation of an [OCI Policy](https://docs.cloud.oracle.com/iaas/api/#/en/identity/20160918/Policy).

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| compartmentid | The OCID of the compartment containing the policy |
| statements | An array of one or more policy statements written in the policy language.  |
| description | The description the policy |
| updatedate | ISO 8601 date-time when the policy was last updated |
| name | The friendly name (not ocid) identifying the policy |
| createdate | ISO 8601 date-time when the policy was created|
| **ocid** | The OCI-unique identifier for this object |

#### Relationships

- An `OCIPolicy` node is defined in an `OCITenancy`.

	```
	(OCITenancy)-[OCI_POLICY]->(OCIPolicy)
	```

- An `OCIPolicy` node is defined in an `OCICompartment`.

	```
	(OCICompartment)-[OCI_POLICY]->(OCIPolicy)
	```


- An `OCIPolicy` node is defined in an `OCITenancy`.

	```
	(OCITenancy)-[OCI_POLICY]->(OCIPolicy)
	```

- An `OCIPolicy` node can reference an `OCICompartment`.

	```
	(OCIPolicy)-[OCI_POLICY_REFERENCE]->(OCICompartment)
	```

- An `OCIPolicy` node can reference an `OCIGroup`.

	```
	(OCIPolicy)-[OCI_POLICY_REFERENCE]->(OCIGroup)
	```

### OCIRegion
| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| name | The key (not ocid) identifying the region |
| name | The friendly name (not ocid) identifying the region |

- An `OCITenancy` node can reference an `OCIRegion`.

	```
	(OCIPolicy)-[OCI_POLICY_REFERENCE]->(OCIGroup)
	```
 - Many node types belong to an `OCIRegion`.

	```
	(OCITenancy)<-[OCI_REGION]-(OCIUser,
                              OCIGroup,
                              OCICompartment)
	```
