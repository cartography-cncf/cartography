## Scaleway Schema

```mermaid
graph LR
ORG(Organization) -- RESOURCE --> PRJ(Project)
ORG -- RESOURCE --> APP(Application)
ORG -- RESOURCE --> USR(User)
ORG -- RESOURCE --> GRP(ScalewayGroup)
ORG -- RESOURCE --> APIKEY(ScalewayApiKey)
ORG -- RESOURCE --> POL(Policy)
ORG -- RESOURCE --> RULE(Rule)
ORG -- RESOURCE --> PS(PermissionSet)
PRJ -- RESOURCE --> INS(Instance)
PRJ -- RESOURCE --> FIP(FlexibleIp)
PRJ -- RESOURCE --> VOL(Volume)
PRJ -- RESOURCE --> SNAP(VolumeSnapshot)
INS -- MOUNTS --> VOL
FIP -- IDENTIFIES --> INS
VOL -- HAS --> SNAP
USR -- MEMBER_OF --> GRP(ScalewayGroup)
USR -- HAS --> APIKEY(ScalewayApiKey)
APP -- MEMBER_OF --> GRP(ScalewayGroup)
APP -- HAS --> APIKEY(ScalewayApiKey)
POL -- APPLIES_TO --> USR
POL -- APPLIES_TO --> GRP
POL -- APPLIES_TO --> APP
POL -- HAS --> RULE(Rule)
RULE -- SCOPED_TO --> PRJ
```

### ScalewayOrganization

Represents an Organization in Scaleway.

> **Ontology Mapping**: This node has the extra label `Tenant` to enable cross-platform queries for tenant accounts across different systems (e.g., OktaOrganization, AWSAccount).

| Field      | Description                                  |
|------------|----------------------------------------------|
| id         | ID of the Scaleway Organization              |
| lastupdated| Timestamp of the last update                 |

#### Relationships
- `Project`, `Application`, `User`, `ApiKey`, `Policy`, `Rule`, `PermissionSet` belong to a `ScalewayOrganization`.
    ```
    (:ScalewayOrganization)-[:RESOURCE]->(
        :ScalewayProject,
        :ScalewayApplication,
        :ScalewayUser,
        :ScalewayApiKey,
        :ScalewayPolicy,
        :ScalewayRule,
        :ScalewayPermissionSet
    )
    ```


### ScalewayProject

Represents a Project in Scaleway. Projects are groupings of Scaleway resources.

> **Ontology Mapping**: This node has the extra label `Tenant` to enable cross-platform queries for tenant accounts across different systems (e.g., OktaOrganization, AWSAccount).

| Field       | Description                                  |
|-------------|----------------------------------------------|
| id          | ID of the Scaleway Project                   |
| name        | Name of the project                          |
| created_at  | Creation timestamp                           |
| updated_at  | Last update timestamp                        |
| description | Project description                          |
| lastupdated | Timestamp of the last update                 |

#### Relationships
- A `Project` belongs to a `ScalewayOrganization`.
    ```
    (:ScalewayOrganization)-[:RESOURCE]->(:ScalewayProject)
    ```
- A `Project` has `FlexibleIp`, `ScalewayVolume`, `VolumeSnapshot` and `Instance` as resources.
    ```
    (:ScalewayProject)-[:RESOURCE]->(
        :ScalewayFlexibleIp,
        :ScalewayVolume,
        :ScalewayVolumeSnapshot,
        :ScalewayInstance
    )
    ```


### ScalewayUser

Represents a User in Scaleway.

> **Ontology Mapping**: This node has the extra label `UserAccount` to enable cross-platform queries for user accounts across different systems (e.g., OktaUser, AWSSSOUser).

| Field              | Description                                  |
|--------------------|----------------------------------------------|
| id                 | ID of user.                                  |
| email              | Email of user.                               |
| username           | User identifier unique to the Organization.  |
| first_name         | First name of the user.                      |
| last_name          | Last name of the user.                       |
| phone_number       | Phone number of the user.                    |
| locale             | Locale of the user.                          |
| created_at         | Date user was created.                       |
| updated_at         | Date of last user update.                    |
| deletable          | Deletion status of user. Owners cannot be deleted. |
| last_login_at      | Date of the last login.                      |
| type               | Type of user (`unknown_type`, `guest`, `owner`, `member`)    |
| status             | Status of user invitation (`unknown_status`, `invitation_pending`, `activated`) |
| mfa                | Defines whether MFA is enabled.              |
| account_root_user_id| ID of the account root user associated with the user. |
| tags               | Tags associated with the user.               |
| locked             | Defines whether the user is locked.          |
| lastupdated        | Timestamp of the last update                 |


#### Relationships
- `User` belongs to a `Organization`.
    ```
    (:ScalewayOrganization)-[:RESOURCE]->(:ScalewayUser)
    ```
- `User` is Member of `Group`.
    ```
    (:ScalewayUser)-[:MEMBER_OF]->(:ScalewayGroup)
    ```
- `User` has `ApiKey`.
    ```
    (:ScalewayUser)-[:HAS]->(:ScalewayApiKey)
    ```


### ScalewayGroup

Represents a Group in Scaleway.

| Field       | Description                                  |
|-------------|----------------------------------------------|
| id          | ID of the Group                              |
| created_at  | Date and time of group creation.             |
| updated_at  | Date and time of last group update.          |
| name        | Name of the group.                           |
| description | Description of the group.                    |
| tags        | Tags associated to the group.                |
| editable    | Defines whether or not the group is editable. |
| deletable   | Defines whether or not the group is deletable. |
| managed     | Defines whether or not the group is managed. |
| lastupdated | Timestamp of the last update                 |

#### Relationships
- `Group` belongs to an `Organization`
    ```
    (:ScalewayOrganization)-[:RESOURCE]->(:ScalewayGroup)
    ```
- `Group` has members: `User` and `Application`
    ```
    (:ScalewayUser)-[:MEMBER_OF]->(:ScalewayGroup)
    (:ScalewayApplication)-[:MEMBER_OF]->(:ScalewayGroup)
    ```


### ScalewayApplication

Represents an Application (Service Account) in Scaleway

| Field       | Description                                  |
|-------------|----------------------------------------------|
| id          | ID of the application.                       |
| name        | Name of the application.                     |
| description | Description of the application.              |
| created_at  | Date and time application was created.       |
| updated_at  | Date and time of last application update.    |
| editable    | Defines whether or not the application is editable. |
| deletable   | Defines whether or not the application is deletable. |
| managed     | Defines whether or not the application is managed. |
| tags        | Tags associated with the user. |
| lastupdated | Timestamp of the last update |


#### Relationships
- `Application` belongs to a `Organization`.
    ```
    (:ScalewayOrganization)-[:RESOURCE]->(:ScalewayApplication)
    ```
- `Application` is member of a `Group`
    ```
    (:ScalewayApplication)-[:MEMBER_OF]->(:ScalewayGroup)
    ```
- `Application` has `ApiKey`
    ```
    (:ScalewayApplication)-[:HAS]->(:ScalewayApiKey)
    ```

### ScalewayApiKey

Represents an ApiKey in Scaleway.

> **Ontology Mapping**: This node has the extra label `APIKey` to enable cross-platform queries for API keys across different systems (e.g., OpenAIApiKey, AnthropicApiKey).

| Field            | Description                                  |
|------------------|----------------------------------------------|
| id               | Access key of the API key.                   |
| description      | Description of API key.                      |
| created_at       | Date and time of API key creation.           |
| updated_at       | Date and time of last API key update.        |
| expires_at       |  Date and time of API key expiration.        |
| default_project_id| Default Project ID specified for this API key. |
| editable         | Defines whether or not the API key is editable. |
| deletable        | Defines whether or not the API key is deletable. |
| managed          | Defines whether or not the API key is managed. |
| creation_ip      | IP address of the device that created the API key. |
| lastupdated      | Timestamp of the last update                 |

#### Relationships
- `ApiKey` belongs to an `Organization`.
    ```
    (:ScalewayOrganization)-[:RESOURCE]->(:ScalewayApiKey)
    ```
- `ApiKey` is owned by a `User` or an `Application`
    ```
    (:ScalewayUser)-[:HAS]->(:ScalewayApiKey)
    (:ScalewayApplication)-[:HAS]->(:ScalewayApiKey)
    ```


### ScalewayPolicy

Represents an IAM Policy in Scaleway. Policies define permissions for users, groups, or applications.

| Field             | Description                                  |
|-------------------|----------------------------------------------|
| id                | ID of the policy.                            |
| name              | Name of the policy.                          |
| description       | Description of the policy.                   |
| created_at        | Date and time of policy creation.            |
| updated_at        | Date and time of last policy update.         |
| editable          | Defines whether or not the policy is editable. |
| deletable         | Defines whether or not the policy is deletable. |
| managed           | Defines whether or not the policy is managed. |
| tags              | Tags associated with the policy.             |
| nb_rules          | Number of rules in the policy.               |
| nb_scopes         | Number of scopes in the policy.              |
| nb_permission_sets| Number of permission sets in the policy.     |
| no_principal      | True if the policy has no principal attached. |
| lastupdated       | Timestamp of the last update                 |

#### Relationships
- `Policy` belongs to an `Organization`.
    ```
    (:ScalewayOrganization)-[:RESOURCE]->(:ScalewayPolicy)
    ```
- `Policy` applies to a `User`, `Group`, or `Application`.
    ```
    (:ScalewayPolicy)-[:APPLIES_TO]->(:ScalewayUser)
    (:ScalewayPolicy)-[:APPLIES_TO]->(:ScalewayGroup)
    (:ScalewayPolicy)-[:APPLIES_TO]->(:ScalewayApplication)
    ```
- `Policy` has `Rule`s.
    ```
    (:ScalewayPolicy)-[:HAS]->(:ScalewayRule)
    ```


### ScalewayRule

Represents an IAM Rule within a Policy. Rules define which permission sets apply and to which projects.

| Field                    | Description                                  |
|--------------------------|----------------------------------------------|
| id                       | ID of the rule.                              |
| permission_sets_scope_type | Scope type of the permission sets.         |
| condition                | Condition for the rule.                      |
| permission_set_names     | Names of the permission sets granted by this rule. |
| lastupdated              | Timestamp of the last update                 |

#### Relationships
- `Rule` belongs to an `Organization`.
    ```
    (:ScalewayOrganization)-[:RESOURCE]->(:ScalewayRule)
    ```
- `Rule` belongs to a `Policy`.
    ```
    (:ScalewayPolicy)-[:HAS]->(:ScalewayRule)
    ```
- `Rule` is scoped to `Project`s.
    ```
    (:ScalewayRule)-[:SCOPED_TO]->(:ScalewayProject)
    ```


### ScalewayPermissionSet

Represents a Permission Set in Scaleway. Permission sets are predefined collections of permissions.

| Field       | Description                                  |
|-------------|----------------------------------------------|
| id          | ID of the permission set.                    |
| name        | Name of the permission set.                  |
| scope_type  | Scope type of the permission set.            |
| description | Description of the permission set.           |
| categories  | Categories of the permission set.            |
| lastupdated | Timestamp of the last update                 |

#### Relationships
- `PermissionSet` belongs to an `Organization`.
    ```
    (:ScalewayOrganization)-[:RESOURCE]->(:ScalewayPermissionSet)
    ```


### ScalewayVolume

Volumes are storage space used by your Instances. You can attach several volumes to an Instance.

| Field           | Description                                  |
|-----------------|----------------------------------------------|
| id              | Volume unique ID.                            |
| name            | Volume name.                                 |
| export_uri      | Show the volume NBD export URI.              |
| size            | Volume disk size. (in bytes)                 |
| volume_type     | Volume type (`l_ssd`, `b_ssd`, `unified`, `scratch`, `sbs_volume`, `sbs_snapshot`) |
| creation_date   | Volume creation date.                        |
| modification_date| Volume modification date.                   |
| tags            | Volume tags.                                 |
| state           | Volume state (`available`, `snapshotting`, `fetching`, `resizing`, `saving`, `hotsyncing`, `error`) |
| zone            | Zone in which the volume is located.         |
| lastupdated     | Timestamp of the last update                 |

#### Relationships
- `Volume` belongs to a `Project`.
    ```
    (:ScalewayProject)-[:RESOURCE]->(:ScalewayVolume)
    ```
- `Volume` has `VolumeSnapshot`
    ```
    (:ScalewayVolume)-[:HAS]->(:ScalewayVolumeSnapshot)
    ```


### ScalewayVolumeSnapshot

A snapshot takes a picture of a volume at one specific point in time. For a complete backup of your Instance, you can create an image.

| Field           | Description                                  |
|-----------------|----------------------------------------------|
| id              | Snapshot ID.                                 |
| name            | Snapshot name.                               |
| tags            | Snapshot tags.                               |
| volume_type     | Snapshot volume type (`l_ssd`, `b_ssd`, `unified`, `scratch`, `sbs_volume`, `sbs_snapshot`) |
| size            | Snapshot size. (in bytes)                    |
| state           | Snapshot state (`available`, `snapshotting`, `error`, `invalid_data`, `importing`, `exporting`) |
| creation_date   | Snapshot creation date.                      |
| modification_date | Snapshot modification date.                |
| error_reason    | Reason for the failed snapshot import.       |
| zone            | Snapshot zone.                               |
| lastupdated     | Timestamp of the last update                 |


#### Relationships
- `VolumeSnapshot` belongs to a `Project`.
    ```
    (:ScalewayProject)-[:RESOURCE]->(:ScalewayVolumeSnapshot)
    ```
- `Volume` has `VolumeSnapshot`
    ```
    (:ScalewayVolume)-[:HAS]->(:ScalewayVolumeSnapshot)
    ```


### ScalewayFlexibleIp

Flexible IP addresses are public IP addresses that you can hold independently of any Instance. By default, a Scaleway Instance's public IP is also a flexible IP address.

| Field      | Description                                  |
|------------|----------------------------------------------|
| id         | Flexible IP ID                               |
| address    | IP address                                   |
| reverse    | Reverse DNS                                  |
| tags       | Tags for the IP                              |
| type       | Type of IP (`unknown_iptype`, `routed_ipv4`, `routed_ipv6`) |
| state      | State of the IP (`unknown_state`, `detached`, `attached`, `pending`, `error`) |
| prefix     | IP Network                                   |
| ipam_id    | IPAM ID (UUI Format)                         |
| zone       | AZ of the IP                                 |
| lastupdated| Timestamp of the last update                 |

#### Relationships
- `FlexibleIp` belongs to a `Project`.
    ```
    (:ScalewayProject)-[:RESOURCE]->(:ScalewayFlexibleIp)
    ```
- `FlexibleIp` identifies an `Instance`
    ```
    (:ScalewayFlexibleIp)-[:IDENTIFIES]->(:ScalewayInstance)
    ```

### ScalewayInstance

An Instance is a virtual computing unit that provides resources, such as processing power, memory, and network connectivity, to run your applications.

> **Ontology Mapping**: This node has the extra label `ComputeInstance` to enable cross-platform queries for compute instances across different systems (e.g., EC2Instance, DigitalOceanDroplet).

| Field      | Description                                  |
|------------|----------------------------------------------|
| id         | Instance unique ID.                          |
| name       | Instance name.                               |
| tags       | Tags associated with the Instance.           |
| commercial_type | Instance commercial type (eg. GP1-M).   |
| creation_date | Instance creation date.                   |
| dynamic_ip_required | True if a dynamic IPv4 is required. |
| routed_ip_enabled | True to configure the instance so it uses the routed IP mode. Use of routed_ip_enabled as False is deprecated. |
| enable_ipv6 | True if IPv6 is enabled (deprecated and always False when routed_ip_enabled is True). |
| hostname   | Instance host name.                          |
| private_ip | Private IP address of the Instance (deprecated and always null when routed_ip_enabled is True). |
| mac_address | The server's MAC address.                   |
| modification_date | Instance modification date.           |
| state      | Instance state (`running`, `stopped`, `stopped in place`, `starting`, `stopping`, `locked`) |
| location_cluster_id | Instance location, cluster ID       |
| location_hypervisor_id | Instance locationm, hypervisor ID |
| location_node_id | Instance location, node ID             |
| location_platform_id | Instance location, plateform ID    |
| ipv6_address | Instance IPv6 IP-Address.                  |
| ipv6_gateway | IPv6 IP-addresses gateway.                 |
| ipv6_netmask | IPv6 IP-addresses CIDR netmask.            |
| boot_type  | Instance boot type (`local`, `bootscript`, `rescue`) |
| state_detail | Detailed information about the Instance state. |
| arch       | Instance architecture (`unknown_arch`, `x86_64`, `arm`, `arm64`) |
| private_nics | Instance private NICs.                     |
| zone       | Zone in which the Instance is located.       |
| end_of_service | True if the Instance type has reached end of service. |
| lastupdated | Timestamp of the last update                 |

#### Relationships
- `Instance` belongs to a `Project`
    ```
    (:ScalewayProject)-[:RESOURCE]->(:ScalewayInstance)
    ```
- `Instance` mounts `Volume`
    ```
    (:ScalewayInstance)-[:MOUNTS]->(:ScalewayVolume)
    ```
- `Instance` is identified by `FlexibleIp`
    ```
    (:ScalewayFlexibleIp)-[:IDENTIFIES]->(:ScalewayInstance)
    ```
