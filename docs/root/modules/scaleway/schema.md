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
PRJ -- RESOURCE --> SG(SecurityGroup)
PRJ -- RESOURCE --> SGR(SecurityGroupRule)
PRJ -- RESOURCE --> BKT(ObjectStorageBucket)
PRJ -- RESOURCE --> VPC(Vpc)
PRJ -- RESOURCE --> PN(PrivateNetwork)
PRJ -- RESOURCE --> SUB(Subnet)
PRJ -- RESOURCE --> IP(IP)
PRJ -- RESOURCE --> PGW(PublicGateway)
PRJ -- RESOURCE --> PAT(PublicGatewayPatRule)
PRJ -- RESOURCE --> LB(LoadBalancer)
PRJ -- RESOURCE --> FE(LBFrontend)
PRJ -- RESOURCE --> BE(LBBackend)
PRJ -- RESOURCE --> DZ(DnsZone)
PRJ -- RESOURCE --> DR(DnsRecord)
PRJ -- RESOURCE --> SEC(Secret)
PRJ -- RESOURCE --> SV(SecretVersion)
PRJ -- RESOURCE --> KEY(Key)
PRJ -- RESOURCE --> KC(KapsuleCluster)
PRJ -- RESOURCE --> KP(KapsulePool)
PRJ -- RESOURCE --> KN(KapsuleNode)
PRJ -- RESOURCE --> CRN(ContainerRegistryNamespace)
PRJ -- RESOURCE --> CIT(ContainerRegistryImageTag)
PRJ -- RESOURCE --> CRI(ContainerRegistryImage)
PRJ -- RESOURCE --> CIL(ContainerRegistryImageLayer)
PRJ -- RESOURCE --> RDB(RdbInstance)
PRJ -- RESOURCE --> RC(RedisCluster)
PRJ -- RESOURCE --> MGO(MongoDBInstance)
PRJ -- RESOURCE --> SFN(ServerlessFunctionNamespace)
PRJ -- RESOURCE --> SF(ServerlessFunction)
PRJ -- RESOURCE --> SCN(ServerlessContainerNamespace)
PRJ -- RESOURCE --> SC(ServerlessContainer)
PRJ -- RESOURCE --> SJ(ServerlessJobDefinition)
INS -- MOUNTS --> VOL
INS -- MEMBER_OF_SCALEWAY_SECURITY_GROUP --> SG
SGR -- MEMBER_OF_SCALEWAY_SECURITY_GROUP --> SG
FIP -- IDENTIFIES --> INS
VOL -- HAS --> SNAP
VPC -- HAS --> PN
PN -- HAS --> SUB
SUB -- HAS --> IP
PGW -- ATTACHED_TO --> PN
PGW -- HAS --> PAT
LB -- HAS --> FE
LB -- HAS --> BE
FE -- ROUTES_TO --> BE
DZ -- HAS_RECORD --> DR
SEC -- HAS --> SV
SEC -- ENCRYPTED_BY --> KEY
KC -- HAS --> KP
KC -- HAS --> KN
KP -- HAS --> KN
KC -- ATTACHED_TO --> PN
CRN -- REPO_IMAGE --> CIT
CIT -- IMAGE --> CRI
CRI -- HAS_LAYER --> CIL
RDB -- ATTACHED_TO --> PN
RC -- ATTACHED_TO --> PN
MGO -- ATTACHED_TO --> PN
SFN -- HAS --> SF
SCN -- HAS --> SC
SF -- ATTACHED_TO --> PN
SC -- ATTACHED_TO --> PN
SC -- HAS_IMAGE --> CRI
USR -- MEMBER_OF --> GRP(ScalewayGroup)
APIKEY(ScalewayApiKey) -- OWNED_BY --> USR
APP -- MEMBER_OF --> GRP(ScalewayGroup)
APIKEY -- OWNED_BY --> APP
POL -- APPLIES_TO --> USR
POL -- APPLIES_TO --> GRP
POL -- APPLIES_TO --> APP
POL -- HAS --> RULE(Rule)
RULE -- SCOPED_TO --> PRJ
USR -- HAS_ROLE --> PS
APP -- HAS_ROLE --> PS
GRP -- HAS_ROLE --> PS
USR -- CAN_ACCESS --> PRJ
APP -- CAN_ACCESS --> PRJ
GRP -- CAN_ACCESS --> PRJ
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
        :ScalewayInstance,
        :ScalewaySecurityGroup,
        :ScalewaySecurityGroupRule,
        :ScalewayObjectStorageBucket,
        :ScalewayVpc,
        :ScalewayPrivateNetwork,
        :ScalewaySubnet,
        :ScalewayIP,
        :ScalewayLoadBalancer,
        :ScalewayLBFrontend,
        :ScalewayLBBackend
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
- `User` owns `ApiKey`.
    ```
    (:ScalewayApiKey)-[:OWNED_BY]->(:ScalewayUser)
    ```
- `User` is granted a `PermissionSet` (canonical `HAS_ROLE`, materialized from the policy/rule graph).
    ```
    (:ScalewayUser)-[:HAS_ROLE]->(:ScalewayPermissionSet)
    ```
- `User` can access a `Project` (materialized scope of the grant; `has_condition` flags condition-gated grants).
    ```
    (:ScalewayUser)-[:CAN_ACCESS]->(:ScalewayProject)
    ```


### ScalewayGroup

Represents a Group in Scaleway.

> **Ontology Mapping**: This node has the extra label `UserGroup` to enable cross-platform queries for user groups across different systems (e.g., AWSGroup, EntraGroup, GoogleWorkspaceGroup).

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
- `Group` is granted a `PermissionSet` (canonical `HAS_ROLE`; members inherit via `MEMBER_OF`).
    ```
    (:ScalewayGroup)-[:HAS_ROLE]->(:ScalewayPermissionSet)
    ```
- `Group` can access a `Project` (materialized scope of the grant).
    ```
    (:ScalewayGroup)-[:CAN_ACCESS]->(:ScalewayProject)
    ```


### ScalewayApplication

Represents an Application (Service Account) in Scaleway

> **Ontology Mapping**: This node has the extra label `ServiceAccount` to enable cross-platform queries for service accounts across different systems (e.g., GCPServiceAccount, KubernetesServiceAccount, OpenAIServiceAccount).

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
- `Application` owns `ApiKey`
    ```
    (:ScalewayApiKey)-[:OWNED_BY]->(:ScalewayApplication)
    ```
- `Application` is granted a `PermissionSet` (canonical `HAS_ROLE`, materialized from the policy/rule graph).
    ```
    (:ScalewayApplication)-[:HAS_ROLE]->(:ScalewayPermissionSet)
    ```
- `Application` can access a `Project` (materialized scope of the grant).
    ```
    (:ScalewayApplication)-[:CAN_ACCESS]->(:ScalewayProject)
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
    (:ScalewayApiKey)-[:OWNED_BY]->(:ScalewayUser)
    (:ScalewayApiKey)-[:OWNED_BY]->(:ScalewayApplication)
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

> **Ontology Mapping**: This node has the extra label `PermissionRole` to enable cross-platform queries for roles across different systems (e.g., AWSRole, GCPRole, AzureRoleDefinition).

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
- Principals (`User`, `Application`, `Group`) are granted a `PermissionSet` via the canonical `HAS_ROLE` edge, materialized from the policy/rule graph.
    ```
    (:ScalewayUser)-[:HAS_ROLE]->(:ScalewayPermissionSet)
    (:ScalewayApplication)-[:HAS_ROLE]->(:ScalewayPermissionSet)
    (:ScalewayGroup)-[:HAS_ROLE]->(:ScalewayPermissionSet)
    ```


### ScalewaySSHKey

Represents an SSH key registered in Scaleway IAM.

| Field       | Description                                  |
|-------------|----------------------------------------------|
| id          | ID of the SSH key.                           |
| name        | Name of the SSH key.                         |
| public_key  | Public key material.                         |
| fingerprint | Fingerprint of the SSH key.                  |
| disabled    | Defines whether or not the SSH key is disabled. |
| created_at  | Date and time of SSH key creation.           |
| updated_at  | Date and time of last SSH key update.        |
| lastupdated | Timestamp of the last update                 |

#### Relationships
- `SSHKey` belongs to an `Organization`.
    ```
    (:ScalewayOrganization)-[:RESOURCE]->(:ScalewaySSHKey)
    ```
- `SSHKey` belongs to a `Project`.
    ```
    (:ScalewayProject)-[:RESOURCE]->(:ScalewaySSHKey)
    ```


### ScalewayVolume

Volumes are storage space used by your Instances. You can attach several volumes to an Instance.

> **Ontology Mapping**: This node has the extra label `BlockStorage` to enable cross-platform queries for block storage volumes across different systems (e.g., AWSEBSVolume, AzureDisk).

| Field           | Description                                  |
|-----------------|----------------------------------------------|
| id              | Volume unique ID.                            |
| name            | Volume name.                                 |
| export_uri      | Show the volume NBD export URI.              |
| size            | Volume disk size. (in bytes)                 |
| size_gb         | Volume disk size derived in gigabytes (rounded from `size`). |
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

> **Ontology Mapping**: This node has the extra label `Snapshot` and normalized `_ont_*` properties to enable cross-platform queries for volume/database snapshots across different systems (e.g., AWSEBSSnapshot, AWSRDSSnapshot, AzureSnapshot).

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

> **Ontology Mapping**: This node has the extra label `ComputeInstance` to enable cross-platform queries for compute instances across different systems (e.g., AWSEC2Instance, DigitalOceanDroplet).

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
- `Instance` is a member of a `SecurityGroup`
    ```
    (:ScalewayInstance)-[:MEMBER_OF_SCALEWAY_SECURITY_GROUP]->(:ScalewaySecurityGroup)
    ```


### ScalewaySecurityGroup

A Security Group is a set of firewall rules that controls inbound and outbound traffic for the Instances attached to it.

> **Ontology Mapping**: This node has the extra label `NetworkAccessControl` to enable cross-platform queries for firewall constructs across different systems (e.g., AWSEC2SecurityGroup, AzureNetworkSecurityGroup, GCPFirewall).

| Field      | Description                                  |
|------------|----------------------------------------------|
| id         | Security Group unique ID.                    |
| name       | Security Group name.                          |
| description | Security Group description.                 |
| enable_default_security | True if SMTP is blocked on IPv4 and IPv6. |
| inbound_default_policy | Default inbound policy (`accept`, `drop`). |
| outbound_default_policy | Default outbound policy (`accept`, `drop`). |
| stateful   | True if the Security Group is stateful.       |
| project_default | True if it is the default Security Group for the Project. |
| organization_default | True if it is the default Security Group for the Organization. |
| tags       | Tags associated with the Security Group.     |
| state      | Security Group state.                         |
| zone       | Zone in which the Security Group is located.  |
| creation_date | Security Group creation date.             |
| modification_date | Security Group modification date.     |
| lastupdated | Timestamp of the last update                 |

#### Relationships
- A `SecurityGroup` belongs to a `Project`
    ```
    (:ScalewayProject)-[:RESOURCE]->(:ScalewaySecurityGroup)
    ```
- An `Instance` is a member of a `SecurityGroup`
    ```
    (:ScalewayInstance)-[:MEMBER_OF_SCALEWAY_SECURITY_GROUP]->(:ScalewaySecurityGroup)
    ```
- A `SecurityGroupRule` is a member of a `SecurityGroup`
    ```
    (:ScalewaySecurityGroupRule)-[:MEMBER_OF_SCALEWAY_SECURITY_GROUP]->(:ScalewaySecurityGroup)
    ```


### ScalewaySecurityGroupRule

A Security Group Rule is a single firewall rule (inbound or outbound) belonging to a Security Group.

> **Ontology Mapping**: This node has the extra label `IpRule`, plus `IpPermissionInbound` or `IpPermissionEgress` depending on its direction, to enable cross-platform queries for firewall rules across different systems (e.g., AWSIpRule, AzureNetworkSecurityRule, GCPIpRule).

| Field      | Description                                  |
|------------|----------------------------------------------|
| id         | Rule unique ID.                              |
| protocol   | Protocol the rule applies to (`tcp`, `udp`, `icmp`, `any`). |
| direction  | Rule direction (`inbound`, `outbound`).       |
| action     | Action taken on matching traffic (`accept`, `drop`). |
| ip_range   | IP range the rule applies to (CIDR notation). |
| dest_port_from | Beginning of the destination port range.  |
| dest_port_to | End of the destination port range.         |
| position   | Rule position (evaluation order).             |
| editable   | True if the rule is editable.                 |
| zone       | Zone in which the rule is located.            |
| lastupdated | Timestamp of the last update                 |

#### Relationships
- A `SecurityGroupRule` belongs to a `Project`
    ```
    (:ScalewayProject)-[:RESOURCE]->(:ScalewaySecurityGroupRule)
    ```
- A `SecurityGroupRule` is a member of a `SecurityGroup`
    ```
    (:ScalewaySecurityGroupRule)-[:MEMBER_OF_SCALEWAY_SECURITY_GROUP]->(:ScalewaySecurityGroup)
    ```

### ScalewayElasticMetalServer

Represents an Elastic Metal (bare-metal) server in Scaleway.

> **Ontology Mapping**: This node has the extra label `ComputeInstance` to enable cross-platform queries for compute instances across different providers.

| Field       | Description                                  |
|-------------|----------------------------------------------|
| id          | ID of the server.                            |
| name        | Name of the server.                          |
| description | Description of the server.                   |
| tags        | Tags attached to the server.                 |
| status      | Status of the server.                        |
| offer_id    | Offer ID of the server.                      |
| offer_name  | Offer name of the server.                    |
| domain      | Domain of the server.                        |
| boot_type   | Boot type of the server.                     |
| ping_status | Status of the server ping.                   |
| protected   | If enabled, the server can not be deleted.   |
| ips         | Public IP addresses attached to the server.  |
| public_ip   | First public IP (scalar, for ontology).      |
| zone        | Zone in which the server is located.         |
| created_at  | Date and time of server creation.            |
| updated_at  | Date and time of last server update.         |
| lastupdated | Timestamp of the last update                 |

#### Relationships
- An `ElasticMetalServer` belongs to a `Project`.
    ```
    (:ScalewayProject)-[:RESOURCE]->(:ScalewayElasticMetalServer)
    ```


### ScalewayAppleSiliconServer

Represents an Apple silicon (Mac mini) server in Scaleway.

> **Ontology Mapping**: This node has the extra label `ComputeInstance` to enable cross-platform queries for compute instances across different providers.

| Field                | Description                             |
|----------------------|-----------------------------------------|
| id                   | ID of the server.                       |
| name                 | Name of the server.                     |
| type                 | Commercial type of the server.          |
| tags                 | Tags attached to the server.            |
| status               | Status of the server.                   |
| ip                   | Public IP address of the server.        |
| vpc_status           | Private network status of the server.   |
| public_bandwidth_bps | Public bandwidth in bits per second.    |
| deletion_scheduled   | Whether deletion is scheduled.          |
| delivered            | Whether the server has been delivered.  |
| zone                 | Zone in which the server is located.    |
| created_at           | Date and time of server creation.       |
| updated_at           | Date and time of last server update.    |
| deletable_at         | Date and time the server can be deleted.|
| lastupdated          | Timestamp of the last update            |

#### Relationships
- An `AppleSiliconServer` belongs to a `Project`.
    ```
    (:ScalewayProject)-[:RESOURCE]->(:ScalewayAppleSiliconServer)
    ```


### ScalewayDediboxServer

Represents a Dedibox (dedicated) server in Scaleway.

> **Ontology Mapping**: This node has the extra label `ComputeInstance` to enable cross-platform queries for compute instances across different providers.

| Field           | Description                              |
|-----------------|------------------------------------------|
| id              | ID of the server (stringified).          |
| hostname        | Hostname of the server.                  |
| datacenter_name | Datacenter hosting the server.           |
| offer_id        | Offer ID of the server.                  |
| offer_name      | Offer name of the server.                |
| status          | Status of the server.                    |
| ips             | Public IP addresses of the server.       |
| public_ip       | First public IP (scalar, for ontology).  |
| is_outsourced   | Whether the server is outsourced.        |
| is_hds          | Whether the server is HDS certified.     |
| zone            | Zone in which the server is located.     |
| created_at      | Date and time of server creation.        |
| updated_at      | Date and time of last server update.     |
| expired_at      | Date and time the server expires.        |
| lastupdated     | Timestamp of the last update             |

#### Relationships
- A `DediboxServer` belongs to a `Project`.
    ```
    (:ScalewayProject)-[:RESOURCE]->(:ScalewayDediboxServer)
    ```

### ScalewayObjectStorageBucket

An Object Storage bucket is an S3-compatible container for objects. Scaleway Object Storage is not exposed by the Scaleway Python SDK, so it is collected through the regional S3-compatible endpoints.

> **Ontology Mapping**: This node has the extra label `ObjectStorage` to enable cross-platform queries for object storage across different systems (e.g., AWSS3Bucket, GCPBucket).

| Field      | Description                                  |
|------------|----------------------------------------------|
| id         | Bucket name (globally unique).               |
| name       | Bucket name.                                 |
| region     | Region the bucket lives in (`fr-par`, `nl-ams`, `pl-waw`, `it-mil`). |
| endpoint   | Public S3 endpoint URL of the bucket.        |
| creation_date | Bucket creation date.                     |
| tags       | Bucket tags (`key=value`).                   |
| versioning_status | Versioning status (`Enabled`, `Suspended`, or unset). |
| acl_public | True if the bucket ACL grants access to `AllUsers` / `AuthenticatedUsers` (null if the ACL could not be read). |
| anonymous_access | True if the bucket policy grants anonymous (internet) access (null if the policy could not be read). |
| anonymous_actions | Actions granted to anonymous principals by the bucket policy. |
| public     | Combined public-exposure signal: `acl_public` OR `anonymous_access`; null when both sources were unreadable. |
| lastupdated | Timestamp of the last update                 |

#### Relationships
- An `ObjectStorageBucket` belongs to a `Project`
    ```
    (:ScalewayProject)-[:RESOURCE]->(:ScalewayObjectStorageBucket)
    ```

### ScalewayVpc

A VPC (Virtual Private Cloud) is a regional, isolated network that groups Private Networks.

> **Ontology Mapping**: This node has the extra label `VirtualNetwork` to enable cross-platform queries for virtual networks across different systems (e.g., AWSVpc, GCPVpc, AzureVirtualNetwork).

| Field      | Description                                  |
|------------|----------------------------------------------|
| id         | VPC unique ID.                               |
| name       | VPC name.                                    |
| region     | Region the VPC lives in.                     |
| tags       | Tags associated with the VPC.                |
| is_default | True if it is the default VPC of the Project. |
| private_network_count | Number of Private Networks in the VPC. |
| routing_enabled | True if routing between Private Networks is enabled. |
| custom_routes_propagation_enabled | True if custom routes are propagated. |
| created_at | VPC creation date.                           |
| updated_at | VPC last update date.                        |
| lastupdated | Timestamp of the last update                 |

#### Relationships
- A `Vpc` belongs to a `Project`
    ```
    (:ScalewayProject)-[:RESOURCE]->(:ScalewayVpc)
    ```
- A `Vpc` has `PrivateNetwork`
    ```
    (:ScalewayVpc)-[:HAS]->(:ScalewayPrivateNetwork)
    ```

### ScalewayPrivateNetwork

A Private Network is a layer-2 network within a VPC that Instances and other resources attach to.

| Field      | Description                                  |
|------------|----------------------------------------------|
| id         | Private Network unique ID.                   |
| name       | Private Network name.                        |
| region     | Region the Private Network lives in.         |
| tags       | Tags associated with the Private Network.    |
| vpc_id     | ID of the VPC the Private Network belongs to. |
| dhcp_enabled | True if managed DHCP is enabled.           |
| default_route_propagation_enabled | True if the default route is propagated. |
| created_at | Private Network creation date.               |
| updated_at | Private Network last update date.            |
| lastupdated | Timestamp of the last update                 |

#### Relationships
- A `PrivateNetwork` belongs to a `Project`
    ```
    (:ScalewayProject)-[:RESOURCE]->(:ScalewayPrivateNetwork)
    ```
- A `Vpc` has `PrivateNetwork`
    ```
    (:ScalewayVpc)-[:HAS]->(:ScalewayPrivateNetwork)
    ```
- A `PrivateNetwork` has `Subnet`
    ```
    (:ScalewayPrivateNetwork)-[:HAS]->(:ScalewaySubnet)
    ```

### ScalewaySubnet

A Subnet is a CIDR block (IPv4 or IPv6) belonging to a Private Network.

> **Ontology Mapping**: This node has the extra label `Subnet` to enable cross-platform queries for subnets across different systems (e.g., AWSEC2Subnet, GCPSubnet, AzureSubnet).

| Field      | Description                                  |
|------------|----------------------------------------------|
| id         | Subnet unique ID.                            |
| subnet     | CIDR block of the subnet.                    |
| private_network_id | ID of the Private Network the subnet belongs to. |
| vpc_id     | ID of the VPC the subnet belongs to.         |
| created_at | Subnet creation date.                        |
| updated_at | Subnet last update date.                     |
| lastupdated | Timestamp of the last update                 |

#### Relationships
- A `Subnet` belongs to a `Project`
    ```
    (:ScalewayProject)-[:RESOURCE]->(:ScalewaySubnet)
    ```
- A `PrivateNetwork` has `Subnet`
    ```
    (:ScalewayPrivateNetwork)-[:HAS]->(:ScalewaySubnet)
    ```

### ScalewayIP

An IP is an IPAM-managed IP address (IPv4 or IPv6) allocated within a Private Network and optionally attached to a resource.

| Field      | Description                                  |
|------------|----------------------------------------------|
| id         | IP unique ID.                                |
| address    | The IP address (CIDR notation).              |
| is_ipv6    | True if the address is IPv6.                 |
| tags       | Tags associated with the IP.                 |
| region     | Region the IP lives in.                      |
| zone       | Zone the IP lives in (when zonal).           |
| source_private_network_id | ID of the Private Network the IP was booked in. |
| source_subnet_id | ID of the subnet the IP was booked in.  |
| source_vpc_id | ID of the VPC the IP was booked in.       |
| resource_type | Type of resource the IP is attached to (e.g. `instance_private_nic`). |
| resource_id | ID of the resource the IP is attached to.   |
| resource_name | Name of the resource the IP is attached to. |
| resource_mac_address | MAC address of the resource the IP is attached to. |
| created_at | IP creation date.                            |
| updated_at | IP last update date.                         |
| lastupdated | Timestamp of the last update                 |

#### Relationships
- An `IP` belongs to a `Project`
    ```
    (:ScalewayProject)-[:RESOURCE]->(:ScalewayIP)
    ```
- A `Subnet` has `IP`
    ```
    (:ScalewaySubnet)-[:HAS]->(:ScalewayIP)
    ```

### ScalewayPublicGateway

Represents a Scaleway Public Gateway: a managed NAT gateway providing internet egress (and optional SSH bastion) to instances on attached private networks.

| Field      | Description                                  |
|------------|----------------------------------------------|
| id         | Gateway UUID.                                |
| name       | Gateway name.                                |
| type_      | Commercial gateway type (e.g. `VPC-GW-S`).   |
| bandwidth  | Gateway bandwidth in Mbps.                   |
| status     | Gateway status (`running`, `stopped`, ...).  |
| tags       | Gateway tags.                                |
| ipv4_address | Public egress IP of the gateway.           |
| bastion_enabled | True if the SSH bastion is enabled.      |
| bastion_port | Port the SSH bastion listens on.           |
| bastion_allowed_ips | CIDRs allowed to reach the bastion, if restricted. |
| smtp_enabled | True if outbound SMTP is allowed.          |
| is_legacy  | True if this is a legacy (v1) gateway.       |
| version    | Gateway software version.                    |
| zone       | Zone the gateway lives in.                   |
| created_at | Creation timestamp.                          |
| updated_at | Last update timestamp.                       |
| lastupdated | Timestamp of the last update                |

#### Relationships
- A `PublicGateway` belongs to a `Project`.
    ```
    (:ScalewayProject)-[:RESOURCE]->(:ScalewayPublicGateway)
    ```
- A `PublicGateway` provides NAT / egress to one or more `PrivateNetwork`s.
    ```
    (:ScalewayPublicGateway)-[:ATTACHED_TO]->(:ScalewayPrivateNetwork)
    ```
- A `PublicGateway` has `PublicGatewayPatRule` port-forwarding rules.
    ```
    (:ScalewayPublicGateway)-[:HAS]->(:ScalewayPublicGatewayPatRule)
    ```


### ScalewayPublicGatewayPatRule

Represents a PAT (Port Address Translation) rule on a Public Gateway: it forwards a public port on the gateway's IP to a private IP/port, exposing an internal service to the internet.

| Field      | Description                                  |
|------------|----------------------------------------------|
| id         | PAT rule UUID.                               |
| public_port | Public port on the gateway IP.              |
| private_ip | Destination private IP.                      |
| private_port | Destination private port.                  |
| protocol   | Forwarded protocol (`tcp`, `udp`, `both`).   |
| zone       | Zone the rule lives in.                      |
| created_at | Creation timestamp.                          |
| updated_at | Last update timestamp.                       |
| lastupdated | Timestamp of the last update                |

#### Relationships
- A `PublicGatewayPatRule` belongs to a `Project`.
    ```
    (:ScalewayProject)-[:RESOURCE]->(:ScalewayPublicGatewayPatRule)
    ```
- A `PublicGatewayPatRule` is defined on a `PublicGateway`.
    ```
    (:ScalewayPublicGateway)-[:HAS]->(:ScalewayPublicGatewayPatRule)
    ```

### ScalewayLoadBalancer

A Load Balancer distributes incoming traffic across backend servers. Its public IP(s) make it an internet-facing entry point.

> **Ontology Mapping**: This node has the extra label `LoadBalancer` to enable cross-platform queries for load balancers across different systems (e.g., AWSLoadBalancerV2, GCPForwardingRule, AzureLoadBalancer).

| Field      | Description                                  |
|------------|----------------------------------------------|
| id         | Load Balancer unique ID.                     |
| name       | Load Balancer name.                          |
| description | Load Balancer description.                  |
| status     | Load Balancer status (e.g. `ready`).          |
| type       | Load Balancer commercial type (e.g. `LB-S`). |
| tags       | Tags associated with the Load Balancer.       |
| frontend_count | Number of frontends.                      |
| backend_count | Number of backends.                        |
| private_network_count | Number of attached Private Networks. |
| route_count | Number of routes.                            |
| ssl_compatibility_level | SSL compatibility level.          |
| ip_address | Primary public IP address (first entry of `ip_addresses`). |
| ip_addresses | All public IP addresses of the Load Balancer. |
| zone       | Zone the Load Balancer lives in.              |
| region     | Region the Load Balancer lives in.            |
| created_at | Load Balancer creation date.                  |
| updated_at | Load Balancer last update date.               |
| lastupdated | Timestamp of the last update                 |

#### Relationships
- A `LoadBalancer` belongs to a `Project`
    ```
    (:ScalewayProject)-[:RESOURCE]->(:ScalewayLoadBalancer)
    ```
- A `LoadBalancer` has `LBFrontend` and `LBBackend`
    ```
    (:ScalewayLoadBalancer)-[:HAS]->(:ScalewayLBFrontend)
    (:ScalewayLoadBalancer)-[:HAS]->(:ScalewayLBBackend)
    ```

### ScalewayLBFrontend

A Frontend defines an inbound listener (port) on a Load Balancer and the backend it routes to.

| Field      | Description                                  |
|------------|----------------------------------------------|
| id         | Frontend unique ID.                          |
| name       | Frontend name.                               |
| inbound_port | Port the frontend listens on.              |
| certificate_ids | IDs of the TLS certificates attached.    |
| enable_http3 | True if HTTP/3 is enabled.                  |
| enable_access_logs | True if access logs are enabled.      |
| timeout_client | Client inactivity timeout.                |
| connection_rate_limit | Per-source connection rate limit.   |
| created_at | Frontend creation date.                      |
| updated_at | Frontend last update date.                   |
| lastupdated | Timestamp of the last update                 |

#### Relationships
- A `LBFrontend` belongs to a `Project`
    ```
    (:ScalewayProject)-[:RESOURCE]->(:ScalewayLBFrontend)
    ```
- A `LoadBalancer` has `LBFrontend`
    ```
    (:ScalewayLoadBalancer)-[:HAS]->(:ScalewayLBFrontend)
    ```
- A `LBFrontend` routes to a `LBBackend`
    ```
    (:ScalewayLBFrontend)-[:ROUTES_TO]->(:ScalewayLBBackend)
    ```

### ScalewayLBBackend

A Backend defines a pool of servers and the forwarding / health-check configuration a Load Balancer uses to reach them.

| Field      | Description                                  |
|------------|----------------------------------------------|
| id         | Backend unique ID.                           |
| name       | Backend name.                                |
| forward_protocol | Protocol used to forward traffic (`tcp`, `http`). |
| forward_port | Port traffic is forwarded to.              |
| forward_port_algorithm | Load-balancing algorithm (e.g. `roundrobin`). |
| sticky_sessions | Sticky-session mode.                     |
| on_marked_down_action | Action when a server is marked down. |
| proxy_protocol | Proxy protocol mode.                      |
| pool       | List of backend server IP addresses.          |
| health_check_port | Port used for health checks.           |
| health_check_delay | Delay between health checks.          |
| health_check_max_retries | Max health-check retries before marking down. |
| timeout_server | Server inactivity timeout.                |
| timeout_connect | Connection timeout.                      |
| ssl_bridging | True if SSL bridging to the backend is enabled. |
| created_at | Backend creation date.                       |
| updated_at | Backend last update date.                    |
| lastupdated | Timestamp of the last update                 |

#### Relationships
- A `LBBackend` belongs to a `Project`
    ```
    (:ScalewayProject)-[:RESOURCE]->(:ScalewayLBBackend)
    ```
- A `LoadBalancer` has `LBBackend`
    ```
    (:ScalewayLoadBalancer)-[:HAS]->(:ScalewayLBBackend)
    ```
- A `LBFrontend` routes to a `LBBackend`
    ```
    (:ScalewayLBFrontend)-[:ROUTES_TO]->(:ScalewayLBBackend)
    ```


### ScalewayDnsZone

Represents a DNS zone managed by Scaleway Domains & DNS. The zone's ID is composed from `{subdomain}.{domain}` (or just `{domain}` for apex zones), which is the value the Scaleway API itself uses as the zone path parameter.

> **Ontology Mapping**: This node has the extra label `DNSZone` to enable cross-platform queries for DNS zones across different systems (e.g., AWSDNSZone, GCPDNSZone).

| Field      | Description                                  |
|------------|----------------------------------------------|
| id         | Full zone name (`subdomain.domain` or `domain`). |
| domain     | Apex domain of the zone.                     |
| subdomain  | Subdomain within the apex (empty for the apex zone itself). |
| status     | Zone status (`active`, `pending`, `error`, ...). |
| message    | Status message returned by the API.          |
| ns         | Authoritative name servers currently configured for the zone. |
| ns_default | Default Scaleway name servers.               |
| ns_master  | Master name servers.                         |
| linked_products | Scaleway products linked to this zone.  |
| updated_at | Zone last update date.                       |
| lastupdated | Timestamp of the last update                 |

#### Relationships
- A `DnsZone` belongs to a `Project`
    ```
    (:ScalewayProject)-[:RESOURCE]->(:ScalewayDnsZone)
    ```


### ScalewayDnsRecord

Represents an individual DNS record within a `ScalewayDnsZone`.

> **Ontology Mapping**: This node has the extra label `DNSRecord` to enable cross-platform queries for DNS records across different systems.

| Field      | Description                                  |
|------------|----------------------------------------------|
| id         | Record unique ID.                            |
| name       | Record name (relative to its zone).          |
| type       | Record type (`a`, `aaaa`, `cname`, `mx`, ...). |
| data       | Record data (target IP, hostname, value, ...). |
| ttl        | Record TTL in seconds.                       |
| priority   | Record priority (relevant for MX/SRV).       |
| comment    | Free-form record comment.                    |
| updated_at | Record last update date.                     |
| lastupdated | Timestamp of the last update                 |

#### Relationships
- A `DnsRecord` belongs to a `Project`
    ```
    (:ScalewayProject)-[:RESOURCE]->(:ScalewayDnsRecord)
    ```
- A `DnsZone` has `DnsRecord`s
    ```
    (:ScalewayDnsZone)-[:HAS_RECORD]->(:ScalewayDnsRecord)
    ```


### ScalewaySecret

Represents a secret managed by Scaleway Secret Manager.

> **Ontology Mapping**: This node has the extra label `Secret` to enable cross-platform queries for secrets across different systems (e.g., AWSSecret, GCPSecretManagerSecret).

| Field      | Description                                  |
|------------|----------------------------------------------|
| id         | Secret unique ID.                            |
| name       | Secret name.                                 |
| status     | Secret status (`ready`, `locked`, ...).      |
| type       | Secret type (`opaque`, `basic_credentials`, `ssh_key`, ...). |
| path       | Folder path of the secret.                   |
| tags       | Secret tags.                                 |
| version_count | Number of versions on this secret.        |
| managed    | True if the secret is managed by another Scaleway product. |
| protected  | True if the secret is protected against deletion. |
| description | Secret description.                         |
| region     | Region the secret lives in.                  |
| key_id     | ID of the Key Manager key encrypting this secret (if any). |
| used_by    | Scaleway products using this secret.         |
| deletion_requested_at | Timestamp when deletion was requested. |
| created_at | Secret creation date.                        |
| updated_at | Secret last update date.                     |
| lastupdated | Timestamp of the last update                 |

#### Relationships
- A `Secret` belongs to a `Project`
    ```
    (:ScalewayProject)-[:RESOURCE]->(:ScalewaySecret)
    ```
- A `Secret` may be encrypted by a `Key`
    ```
    (:ScalewaySecret)-[:ENCRYPTED_BY]->(:ScalewayKey)
    ```


### ScalewaySecretVersion

Represents a version of a `ScalewaySecret`. The version's ID is composed as `{secret_id}/{revision}` since Scaleway does not expose a provider-side version ID.

| Field      | Description                                  |
|------------|----------------------------------------------|
| id         | `{secret_id}/{revision}`.                    |
| revision   | Monotonic revision number.                   |
| status     | Version status (`enabled`, `disabled`, `destroyed`, ...). |
| latest     | True if this version is the latest for its secret. |
| description | Version description.                        |
| region     | Region the version lives in.                 |
| deletion_requested_at | Timestamp when deletion was requested. |
| deleted_at | Deletion date (when the version is destroyed). |
| created_at | Version creation date.                       |
| updated_at | Version last update date.                    |
| lastupdated | Timestamp of the last update                 |

#### Relationships
- A `SecretVersion` belongs to a `Project`
    ```
    (:ScalewayProject)-[:RESOURCE]->(:ScalewaySecretVersion)
    ```
- A `Secret` has `SecretVersion`s
    ```
    (:ScalewaySecret)-[:HAS]->(:ScalewaySecretVersion)
    ```


### ScalewayKey

Represents a Scaleway Key Manager key.

> **Ontology Mapping**: This node has the extra label `EncryptionKey` to enable cross-platform queries for encryption keys across different systems (e.g., AWSKMSKey, GCPCryptoKey).

| Field      | Description                                  |
|------------|----------------------------------------------|
| id         | Key unique ID.                               |
| name       | Key name.                                    |
| description | Key description.                            |
| state      | Key state (`enabled`, `disabled`, `pending_deletion`, ...). |
| usage_type | Active key usage category (`symmetric_encryption`, `asymmetric_encryption`, `asymmetric_signing`). |
| usage_algorithm | Algorithm corresponding to `usage_type` (e.g. `aes_256_gcm`). |
| origin     | Key material origin (`scaleway_kms`, `external`).  |
| region     | Region the key lives in.                     |
| tags       | Key tags.                                    |
| rotation_count | Number of times the key has been rotated. |
| protected  | True if the key is protected against deletion. |
| locked     | True if the key is locked.                   |
| rotation_period | Automatic rotation period (ISO 8601 duration). |
| rotation_next_at | Next scheduled rotation timestamp.      |
| rotated_at | Last rotation date.                          |
| deletion_requested_at | Timestamp when deletion was requested. |
| created_at | Key creation date.                           |
| updated_at | Key last update date.                        |
| lastupdated | Timestamp of the last update                 |

#### Relationships
- A `Key` belongs to a `Project`
    ```
    (:ScalewayProject)-[:RESOURCE]->(:ScalewayKey)
    ```
- A `Secret` may be encrypted by a `Key`
    ```
    (:ScalewaySecret)-[:ENCRYPTED_BY]->(:ScalewayKey)
    ```


### ScalewayKapsuleCluster

Represents a Scaleway Kapsule (managed Kubernetes) cluster.

> **Ontology Mapping**: This node has the extra label `ComputeCluster` to enable cross-platform queries for compute clusters across different systems (e.g., AWSEKSCluster, GKECluster, AzureKubernetesCluster).

| Field      | Description                                  |
|------------|----------------------------------------------|
| id         | Cluster UUID.                                |
| name       | Cluster name.                                |
| description | Cluster description.                        |
| status     | Cluster status (`ready`, `creating`, ...).   |
| type       | Cluster offer type (e.g. `kapsule`, `multicloud`). |
| version    | Kubernetes version.                          |
| cni        | CNI plugin (`cilium`, `calico`, ...).        |
| cluster_url | API server URL.                             |
| dns_wildcard | Wildcard DNS name pointing at the cluster. |
| upgrade_available | True if a newer Kubernetes version is offered. |
| pod_cidr   | Pod IP range.                                |
| service_cidr | Service IP range.                          |
| service_dns_ip | In-cluster DNS service IP.               |
| private_network_id | ID of the VPC private network this cluster is attached to (if any). |
| apiserver_cert_sans | Extra SANs added to the apiserver cert. |
| feature_gates | List of enabled Kubernetes feature gates. |
| admission_plugins | List of enabled admission plugins.    |
| tags       | Cluster tags.                                |
| region     | Region the cluster lives in.                 |
| created_at | Creation timestamp.                          |
| updated_at | Last update timestamp.                       |
| lastupdated | Timestamp of the last update                |

#### Relationships
- A `KapsuleCluster` belongs to a `Project`.
    ```
    (:ScalewayProject)-[:RESOURCE]->(:ScalewayKapsuleCluster)
    ```
- A `KapsuleCluster` may be attached to a `PrivateNetwork`.
    ```
    (:ScalewayKapsuleCluster)-[:ATTACHED_TO]->(:ScalewayPrivateNetwork)
    ```
- A `KapsuleCluster` has `KapsulePool` and `KapsuleNode` resources.
    ```
    (:ScalewayKapsuleCluster)-[:HAS]->(:ScalewayKapsulePool)
    (:ScalewayKapsuleCluster)-[:HAS]->(:ScalewayKapsuleNode)
    ```


### ScalewayKapsulePool

Represents a Kapsule node pool: a homogeneous group of nodes provisioned for a Kapsule cluster.

| Field      | Description                                  |
|------------|----------------------------------------------|
| id         | Pool UUID.                                   |
| name       | Pool name.                                   |
| status     | Pool status.                                 |
| version    | Kubernetes version of the pool.              |
| node_type  | Scaleway instance commercial type used for nodes (e.g. `DEV1-M`). |
| autoscaling | True if the pool autoscales.                |
| size       | Current size of the pool.                    |
| min_size   | Minimum size for autoscaling.                |
| max_size   | Maximum size for autoscaling.                |
| container_runtime | Container runtime (`containerd`, ...). |
| autohealing | True if autohealing is enabled.             |
| root_volume_type | Root volume type for nodes.             |
| root_volume_size | Root volume size in bytes.              |
| public_ip_disabled | True if nodes have no public IP.      |
| placement_group_id | ID of the placement group, if any.    |
| security_group_id | Security group applied to the nodes.   |
| tags       | Pool tags.                                   |
| zone       | Zone the pool's nodes live in.               |
| region     | Region the pool lives in.                    |
| created_at | Creation timestamp.                          |
| updated_at | Last update timestamp.                       |
| lastupdated | Timestamp of the last update                |

#### Relationships
- A `KapsulePool` belongs to a `Project`.
    ```
    (:ScalewayProject)-[:RESOURCE]->(:ScalewayKapsulePool)
    ```
- A `KapsulePool` is part of a `KapsuleCluster`.
    ```
    (:ScalewayKapsuleCluster)-[:HAS]->(:ScalewayKapsulePool)
    ```
- A `KapsulePool` has `KapsuleNode` members.
    ```
    (:ScalewayKapsulePool)-[:HAS]->(:ScalewayKapsuleNode)
    ```


### ScalewayKapsuleNode

Represents a single node in a Kapsule pool.

| Field      | Description                                  |
|------------|----------------------------------------------|
| id         | Node UUID.                                   |
| name       | Node name.                                   |
| status     | Node status (`ready`, `not_ready`, ...).     |
| provider_id | Provider-side identifier for the backing instance (e.g. `scaleway://instance/<zone>/<id>`). |
| public_ip_v4 | Public IPv4 address.                       |
| public_ip_v6 | Public IPv6 address.                       |
| error_message | Last error message reported by the node.  |
| region     | Region the node lives in.                    |
| created_at | Creation timestamp.                          |
| updated_at | Last update timestamp.                       |
| lastupdated | Timestamp of the last update                |

#### Relationships
- A `KapsuleNode` belongs to a `Project`.
    ```
    (:ScalewayProject)-[:RESOURCE]->(:ScalewayKapsuleNode)
    ```
- A `KapsuleNode` is part of a `KapsulePool` and a `KapsuleCluster`.
    ```
    (:ScalewayKapsulePool)-[:HAS]->(:ScalewayKapsuleNode)
    (:ScalewayKapsuleCluster)-[:HAS]->(:ScalewayKapsuleNode)
    ```


### ScalewayContainerRegistryNamespace

Represents a Scaleway Container Registry namespace (top-level repository scope).

> **Ontology Mapping**: This node has the extra label `ContainerRegistry` to enable cross-platform queries for container registries across different systems (e.g., AWSECRRepository, GCPArtifactRegistryRepository, GitHubPackage).

| Field      | Description                                  |
|------------|----------------------------------------------|
| id         | Namespace UUID.                              |
| name       | Namespace name.                              |
| description | Namespace description.                      |
| status     | Namespace status.                            |
| status_message | Human-readable status message.           |
| endpoint   | Registry endpoint (e.g. `rg.fr-par.scw.cloud/<name>`). |
| is_public  | True if the namespace allows unauthenticated reads. |
| size       | Total size in bytes of stored images.        |
| image_count | Number of images in the namespace.          |
| region     | Region the namespace lives in.               |
| created_at | Creation timestamp.                          |
| updated_at | Last update timestamp.                       |
| lastupdated | Timestamp of the last update                |

#### Relationships
- A `ContainerRegistryNamespace` belongs to a `Project`.
    ```
    (:ScalewayProject)-[:RESOURCE]->(:ScalewayContainerRegistryNamespace)
    ```
- A `ContainerRegistryNamespace` exposes image tags (canonical `REPO_IMAGE` registry -> tag edge).
    ```
    (:ScalewayContainerRegistryNamespace)-[:REPO_IMAGE]->(:ScalewayContainerRegistryImageTag)
    ```


### ScalewayContainerRegistryImageTag

Represents a tag (a named pointer such as `latest` or `v1.2.3`) inside a Container Registry namespace, resolving to a specific image digest. Scaleway's namespace is the registry (like a GCP Artifact Registry repository), so the "named image" from `list_images` is not modeled as its own node; its name and visibility are denormalized onto the tag.

> **Ontology Mapping**: This node has the extra label `ImageTag` to enable cross-platform queries for image tags across registries (e.g. AWSECRRepositoryImage, GCPArtifactRegistryRepositoryImage, GitLabContainerRepositoryTag).

| Field      | Description                                  |
|------------|----------------------------------------------|
| id         | Tag UUID.                                    |
| name       | Tag string (e.g. `latest`).                  |
| image_name | Name of the repository (named image) the tag belongs to. |
| uri        | Full pull URI, e.g. `rg.fr-par.scw.cloud/<namespace>/<image>:<tag>`. |
| digest     | Digest (sha256) the tag resolves to.         |
| status     | Tag status.                                  |
| visibility | Per-image visibility (`public`, `private`, `inherit`). Combined with the namespace `is_public` flag to derive effective exposure. |
| created_at | Creation timestamp.                          |
| updated_at | Last update timestamp.                       |
| lastupdated | Timestamp of the last update                |

#### Relationships
- An `ImageTag` belongs to a `Project`.
    ```
    (:ScalewayProject)-[:RESOURCE]->(:ScalewayContainerRegistryImageTag)
    ```
- An `ImageTag` lives in a `ContainerRegistryNamespace` (canonical `REPO_IMAGE` registry -> tag edge).
    ```
    (:ScalewayContainerRegistryNamespace)-[:REPO_IMAGE]->(:ScalewayContainerRegistryImageTag)
    ```
- An `ImageTag` resolves to a digest-addressed `Image`.
    ```
    (:ScalewayContainerRegistryImageTag)-[:IMAGE]->(:ScalewayContainerRegistryImage)
    ```


### ScalewayContainerRegistryImage

Represents the digest-addressed image content in a Container Registry. Deduplicated by digest, so multiple tags (and repositories) referencing the same digest share one node.

> **Ontology Mapping**: This node has the extra label `Image` to enable cross-platform queries for container images across registries (e.g. AWSECRImage, GCPArtifactRegistryImage, GitLabContainerImage). It is the join target for `(:Container|:Function)-[:HAS_IMAGE]->(:Image)` and `RESOLVED_IMAGE`.

Provenance and layer fields are populated from the OCI registry endpoint by the supply-chain enrichment.

| Field      | Description                                  |
|------------|----------------------------------------------|
| id         | Image digest (sha256).                       |
| digest     | Image digest (sha256).                       |
| layer_diff_ids | Ordered uncompressed layer digests (from the OCI image config). |
| source_uri | Source VCS repository URL the image was built from (OCI label/annotation or SLSA attestation). Match key for `PACKAGED_FROM`. |
| source_revision | Source commit the image was built from.   |
| source_file | Dockerfile path within the source repository. |
| lastupdated | Timestamp of the last update                |

#### Relationships
- An `Image` belongs to a `Project`.
    ```
    (:ScalewayProject)-[:RESOURCE]->(:ScalewayContainerRegistryImage)
    ```
- Tags resolve to an `Image`.
    ```
    (:ScalewayContainerRegistryImageTag)-[:IMAGE]->(:ScalewayContainerRegistryImage)
    ```
- An `Image` is composed of filesystem layers.
    ```
    (:ScalewayContainerRegistryImage)-[:HAS_LAYER]->(:ScalewayContainerRegistryImageLayer)
    ```
- An `Image` is built from a source repository (code-to-cloud, drawn by the GitHub/GitLab supply-chain matchers from `source_uri` or layer analysis).
    ```
    (:ScalewayContainerRegistryImage)-[:PACKAGED_FROM]->(:GitHubRepository)
    (:ScalewayContainerRegistryImage)-[:PACKAGED_FROM]->(:GitLabProject)
    ```


### ScalewayContainerRegistryImageLayer

Represents a filesystem layer of a container image, keyed by its uncompressed digest (`diff_id`) and shared across images that reuse it.

> **Ontology Mapping**: This node has the extra label `ImageLayer` to enable cross-platform queries and the supply-chain dockerfile matcher (e.g. AWSECRImageLayer, GCPArtifactRegistryImageLayer).

| Field      | Description                                  |
|------------|----------------------------------------------|
| id         | Layer diff_id (sha256).                      |
| diff_id    | Uncompressed layer digest (sha256).          |
| history    | Build command (`created_by`) that produced the layer. |
| is_empty   | Whether the layer is an empty (metadata-only) layer. |
| lastupdated | Timestamp of the last update                |

#### Relationships
- A layer belongs to a `Project`.
    ```
    (:ScalewayProject)-[:RESOURCE]->(:ScalewayContainerRegistryImageLayer)
    ```
- An `Image` is composed of layers.
    ```
    (:ScalewayContainerRegistryImage)-[:HAS_LAYER]->(:ScalewayContainerRegistryImageLayer)
    ```


### ScalewayRdbInstance

Represents a managed PostgreSQL / MySQL database instance (Scaleway "Managed Database for PostgreSQL and MySQL").

> **Ontology Mapping**: This node has the extra label `Database` to enable cross-platform queries for databases across providers (e.g. AWSRDSInstance, GCPCloudSQLInstance, AzureSQLDatabase).

| Field      | Description                                  |
|------------|----------------------------------------------|
| id         | Instance UUID.                               |
| name       | Instance name.                               |
| status     | Instance status (`ready`, `provisioning`, ...). |
| engine     | Engine and version (e.g. `PostgreSQL-15`, `MySQL-8`). |
| node_type  | Commercial node type (e.g. `DB-DEV-S`).      |
| is_ha_cluster | True if the instance runs in high-availability mode. |
| encryption_at_rest_enabled | True if encryption at rest is enabled. |
| volume_type | Storage volume type (`lssd`, `bssd`, `sbs_5k`, ...). |
| volume_size | Storage volume size in bytes.               |
| backup_schedule_disabled | True if automated backups are disabled. |
| backup_schedule_retention_days | Backup retention in days, when configured. |
| backup_same_region | True if backups are stored in the same region as the instance. |
| tags       | Instance tags.                               |
| is_public  | True if the instance exposes a publicly reachable endpoint (load balancer or direct access). |
| public_endpoint_ip | IP of the public endpoint, if any.    |
| public_endpoint_hostname | Hostname of the public endpoint, if any. |
| public_endpoint_port | Port of the public endpoint, if any. |
| private_endpoint_ip | IP of the first private-network endpoint, if any. |
| private_endpoint_port | Port of the first private-network endpoint, if any. |
| region     | Region the instance lives in.                |
| created_at | Creation timestamp.                          |
| lastupdated | Timestamp of the last update.               |

#### Relationships
- An `RdbInstance` belongs to a `Project`.
    ```
    (:ScalewayProject)-[:RESOURCE]->(:ScalewayRdbInstance)
    ```
- An `RdbInstance` may be attached to one or more `PrivateNetwork`s.
    ```
    (:ScalewayRdbInstance)-[:ATTACHED_TO]->(:ScalewayPrivateNetwork)
    ```


### ScalewayRedisCluster

Represents a managed Redis cluster (Scaleway "Managed Database for Redis").

> **Ontology Mapping**: This node has the extra label `Database` to enable cross-platform queries for databases across providers.

| Field      | Description                                  |
|------------|----------------------------------------------|
| id         | Cluster UUID.                                |
| name       | Cluster name.                                |
| status     | Cluster status.                              |
| version    | Redis version (e.g. `7.0.5`).                |
| node_type  | Commercial node type.                        |
| cluster_size | Number of nodes in the cluster.            |
| tls_enabled | True if TLS is enabled for client traffic.  |
| user_name  | Default admin user.                          |
| tags       | Cluster tags.                                |
| is_public  | True if the cluster exposes a publicly reachable endpoint. |
| public_endpoint_ip | IP of the public endpoint, if any.    |
| public_endpoint_port | Port of the public endpoint, if any. |
| private_endpoint_ip | IP of the first private-network endpoint, if any. |
| private_endpoint_port | Port of the first private-network endpoint, if any. |
| zone       | Zone the cluster lives in.                   |
| created_at | Creation timestamp.                          |
| updated_at | Last update timestamp.                       |
| lastupdated | Timestamp of the last update.               |

#### Relationships
- A `RedisCluster` belongs to a `Project`.
    ```
    (:ScalewayProject)-[:RESOURCE]->(:ScalewayRedisCluster)
    ```
- A `RedisCluster` may be attached to one or more `PrivateNetwork`s.
    ```
    (:ScalewayRedisCluster)-[:ATTACHED_TO]->(:ScalewayPrivateNetwork)
    ```


### ScalewayMongoDBInstance

Represents a managed MongoDB instance (Scaleway "Managed Database for MongoDB").

> **Ontology Mapping**: This node has the extra label `Database` to enable cross-platform queries for databases across providers.

| Field      | Description                                  |
|------------|----------------------------------------------|
| id         | Instance UUID.                               |
| name       | Instance name.                               |
| status     | Instance status.                             |
| version    | MongoDB version (e.g. `7.0`).                |
| node_type  | Commercial node type.                        |
| node_amount | Number of nodes in the deployment.          |
| volume_type | Storage volume type.                        |
| volume_size | Storage volume size in bytes.               |
| tags       | Instance tags.                               |
| is_public  | True if the instance exposes a publicly reachable endpoint. |
| public_endpoint_dns | DNS record for the public endpoint, if any. |
| public_endpoint_port | Port of the public endpoint, if any. |
| private_endpoint_dns | DNS record for the first private-network endpoint, if any. |
| private_endpoint_port | Port of the first private-network endpoint, if any. |
| region     | Region the instance lives in.                |
| created_at | Creation timestamp.                          |
| lastupdated | Timestamp of the last update.               |

#### Relationships
- A `MongoDBInstance` belongs to a `Project`.
    ```
    (:ScalewayProject)-[:RESOURCE]->(:ScalewayMongoDBInstance)
    ```
- A `MongoDBInstance` may be attached to one or more `PrivateNetwork`s.
    ```
    (:ScalewayMongoDBInstance)-[:ATTACHED_TO]->(:ScalewayPrivateNetwork)
    ```


### ScalewayServerlessFunctionNamespace

Represents a Scaleway Serverless Functions namespace (project-scoped grouping of functions, backed by a hidden container registry namespace).

> **Ontology Mapping**: This node has the extra label `ComputeNamespace` to enable cross-platform queries for compute namespaces across different systems (e.g., KubernetesNamespace).

| Field      | Description                                  |
|------------|----------------------------------------------|
| id         | Namespace UUID.                              |
| name       | Namespace name.                              |
| description | Namespace description.                      |
| status     | Namespace status.                            |
| error_message | Human-readable error message, if any.     |
| registry_namespace_id | UUID of the backing container registry namespace. |
| registry_endpoint | Endpoint of the backing container registry. |
| vpc_integration_activated | True if the namespace can reach a VPC private network. |
| region     | Region the namespace lives in.               |
| tags       | Namespace tags.                              |
| created_at | Creation timestamp.                          |
| updated_at | Last update timestamp.                       |
| lastupdated | Timestamp of the last update                |

#### Relationships
- A `ServerlessFunctionNamespace` belongs to a `Project`.
    ```
    (:ScalewayProject)-[:RESOURCE]->(:ScalewayServerlessFunctionNamespace)
    ```
- A `ServerlessFunctionNamespace` has `ServerlessFunction` members.
    ```
    (:ScalewayServerlessFunctionNamespace)-[:HAS]->(:ScalewayServerlessFunction)
    ```


### ScalewayServerlessFunction

Represents a Scaleway Serverless Function.

> **Ontology Mapping**: This node has the extra label `Function` to enable cross-platform queries for functions across different systems (e.g., AWSLambda, GCPCloudFunction, AzureFunctionApp).

| Field      | Description                                  |
|------------|----------------------------------------------|
| id         | Function UUID.                               |
| name       | Function name.                               |
| status     | Function status.                             |
| runtime    | Runtime (e.g. `python311`, `node20`).        |
| handler    | Function entrypoint handler.                 |
| privacy    | Invocation privacy (`public` allows unauthenticated invokes, `private` requires a token). |
| domain_name | Auto-assigned invocation domain.            |
| http_option | `enabled` allows plain HTTP; `redirected` forces HTTPS. |
| sandbox    | Sandbox generation (`v1`, `v2`).             |
| min_scale  | Minimum number of instances.                 |
| max_scale  | Maximum number of instances.                 |
| memory_limit | Memory limit in MB.                        |
| cpu_limit  | CPU limit in mvCPU.                          |
| timeout    | Invocation timeout (e.g. `300s`).            |
| region     | Region the function lives in.                |
| tags       | Function tags.                               |
| created_at | Creation timestamp.                          |
| updated_at | Last update timestamp.                       |
| lastupdated | Timestamp of the last update                |

#### Relationships
- A `ServerlessFunction` belongs to a `Project`.
    ```
    (:ScalewayProject)-[:RESOURCE]->(:ScalewayServerlessFunction)
    ```
- A `ServerlessFunction` lives in a `ServerlessFunctionNamespace`.
    ```
    (:ScalewayServerlessFunctionNamespace)-[:HAS]->(:ScalewayServerlessFunction)
    ```
- A `ServerlessFunction` may be attached to a `PrivateNetwork`.
    ```
    (:ScalewayServerlessFunction)-[:ATTACHED_TO]->(:ScalewayPrivateNetwork)
    ```


### ScalewayServerlessContainerNamespace

Represents a Scaleway Serverless Containers namespace (project-scoped grouping of containers, backed by a hidden container registry namespace).

> **Ontology Mapping**: This node has the extra label `ComputeNamespace` to enable cross-platform queries for compute namespaces across different systems (e.g., KubernetesNamespace).

| Field      | Description                                  |
|------------|----------------------------------------------|
| id         | Namespace UUID.                              |
| name       | Namespace name.                              |
| description | Namespace description.                      |
| status     | Namespace status.                            |
| error_message | Human-readable error message, if any.     |
| registry_namespace_id | UUID of the backing container registry namespace. |
| registry_endpoint | Endpoint of the backing container registry. |
| vpc_integration_activated | True if the namespace can reach a VPC private network. |
| region     | Region the namespace lives in.               |
| tags       | Namespace tags.                              |
| created_at | Creation timestamp.                          |
| updated_at | Last update timestamp.                       |
| lastupdated | Timestamp of the last update                |

#### Relationships
- A `ServerlessContainerNamespace` belongs to a `Project`.
    ```
    (:ScalewayProject)-[:RESOURCE]->(:ScalewayServerlessContainerNamespace)
    ```
- A `ServerlessContainerNamespace` has `ServerlessContainer` members.
    ```
    (:ScalewayServerlessContainerNamespace)-[:HAS]->(:ScalewayServerlessContainer)
    ```


### ScalewayServerlessContainer

Represents a Scaleway Serverless Container (a managed, autoscaled container service that runs a single container).

> **Ontology Mapping**: This node has the extra labels `ComputeService` (cross-platform container services, e.g. AWSECSService, GCPCloudRunService) and `Container` (the running container, so the shared `RESOLVED_IMAGE` analysis reaches it via `HAS_IMAGE`).

| Field      | Description                                  |
|------------|----------------------------------------------|
| id         | Container UUID.                              |
| name       | Container name.                              |
| status     | Container status.                            |
| registry_image | Container image pull URI.                |
| image_digest | Digest the `registry_image` resolves to, populated at ingest from the container-registry sync. |
| privacy    | Invocation privacy (`public` allows unauthenticated invokes, `private` requires a token). |
| domain_name | Auto-assigned invocation domain.            |
| http_option | `enabled` allows plain HTTP; `redirected` forces HTTPS. |
| protocol   | Serving protocol (`http1`, `h2c`).           |
| port       | Container listening port.                    |
| sandbox    | Sandbox generation (`v1`, `v2`).             |
| min_scale  | Minimum number of instances.                 |
| max_scale  | Maximum number of instances.                 |
| max_concurrency | Max concurrent requests per instance.   |
| memory_limit | Memory limit in MB.                        |
| cpu_limit  | CPU limit in mvCPU.                          |
| timeout    | Invocation timeout (e.g. `300s`).            |
| region     | Region the container lives in.               |
| tags       | Container tags.                              |
| created_at | Creation timestamp.                          |
| updated_at | Last update timestamp.                       |
| lastupdated | Timestamp of the last update                |

#### Relationships
- A `ServerlessContainer` belongs to a `Project`.
    ```
    (:ScalewayProject)-[:RESOURCE]->(:ScalewayServerlessContainer)
    ```
- A `ServerlessContainer` lives in a `ServerlessContainerNamespace`.
    ```
    (:ScalewayServerlessContainerNamespace)-[:HAS]->(:ScalewayServerlessContainer)
    ```
- A `ServerlessContainer` may be attached to a `PrivateNetwork`.
    ```
    (:ScalewayServerlessContainer)-[:ATTACHED_TO]->(:ScalewayPrivateNetwork)
    ```
- A `ServerlessContainer` runs a digest-addressed `Image` (its `registry_image` resolved to a digest). Feeds the shared `RESOLVED_IMAGE` analysis.
    ```
    (:ScalewayServerlessContainer)-[:HAS_IMAGE]->(:ScalewayContainerRegistryImage)
    ```


### ScalewayServerlessJobDefinition

Represents a Scaleway Serverless Job definition (a runnable, optionally scheduled, container job).

| Field      | Description                                  |
|------------|----------------------------------------------|
| id         | Job definition UUID.                         |
| name       | Job definition name.                         |
| description | Job description.                            |
| image_uri  | Container image URI executed by the job.     |
| command    | Command run inside the container.            |
| cpu_limit  | CPU limit in mvCPU.                          |
| memory_limit | Memory limit in MB.                        |
| local_storage_capacity | Local storage capacity in MB.     |
| job_timeout | Per-run timeout (e.g. `3600s`).             |
| cron_schedule | Cron expression, if the job is scheduled. |
| cron_timezone | Timezone for the cron schedule.           |
| region     | Region the job lives in.                     |
| created_at | Creation timestamp.                          |
| updated_at | Last update timestamp.                       |
| lastupdated | Timestamp of the last update                |

#### Relationships
- A `ServerlessJobDefinition` belongs to a `Project`.
    ```
    (:ScalewayProject)-[:RESOURCE]->(:ScalewayServerlessJobDefinition)
    ```


### ScalewayFileSystem

Represents a File Storage file system in Scaleway.

> **Ontology Mapping**: This node has the extra label `FileStorage` to enable cross-platform queries for managed file storage across different providers.

| Field                 | Description                            |
|-----------------------|----------------------------------------|
| id                    | ID of the file system.                 |
| name                  | Name of the file system.               |
| size                  | Size of the file system in bytes.      |
| status                | Status of the file system.             |
| tags                  | Tags attached to the file system.      |
| number_of_attachments | Number of resources it is attached to. |
| region                | Region the file system lives in.       |
| created_at            | Creation timestamp.                    |
| updated_at            | Last update timestamp.                 |
| lastupdated           | Timestamp of the last update           |

#### Relationships
- A `FileSystem` belongs to a `Project`.
    ```
    (:ScalewayProject)-[:RESOURCE]->(:ScalewayFileSystem)
    ```


### ScalewayDataWarehouseDeployment

Represents a Data Warehouse (ClickHouse) deployment in Scaleway.

> **Ontology Mapping**: This node has the extra label `Database`.

| Field         | Description                                  |
|---------------|----------------------------------------------|
| id            | ID of the deployment.                        |
| name          | Name of the deployment.                      |
| status        | Status of the deployment.                    |
| tags          | Tags attached to the deployment.             |
| version       | Engine version.                              |
| replica_count | Number of replicas.                          |
| shard_count   | Number of shards.                            |
| cpu_min       | Minimum vCPU.                                |
| cpu_max       | Maximum vCPU.                                |
| ram_per_cpu   | RAM per vCPU.                                |
| is_public     | True if any endpoint is public-facing.       |
| region        | Region the deployment lives in.              |
| created_at    | Creation timestamp.                          |
| updated_at    | Last update timestamp.                       |
| lastupdated   | Timestamp of the last update                 |

#### Relationships
- A `DataWarehouseDeployment` belongs to a `Project`.
    ```
    (:ScalewayProject)-[:RESOURCE]->(:ScalewayDataWarehouseDeployment)
    ```


### ScalewayServerlessSQLDatabase

Represents a Serverless SQL Database (PostgreSQL) in Scaleway.

> **Ontology Mapping**: This node has the extra label `Database`.

| Field                | Description                            |
|----------------------|----------------------------------------|
| id                   | ID of the database.                    |
| name                 | Name of the database.                  |
| status               | Status of the database.                |
| endpoint             | Connection endpoint URL.               |
| is_public            | True if reachable over a public endpoint. |
| cpu_min              | Minimum vCPU.                          |
| cpu_max              | Maximum vCPU.                          |
| cpu_current          | Current vCPU.                          |
| started              | Whether the database is started.       |
| engine_major_version | Major engine version.                  |
| region               | Region the database lives in.          |
| created_at           | Creation timestamp.                    |
| lastupdated          | Timestamp of the last update           |

#### Relationships
- A `ServerlessSQLDatabase` belongs to a `Project`.
    ```
    (:ScalewayProject)-[:RESOURCE]->(:ScalewayServerlessSQLDatabase)
    ```


### ScalewaySearchDeployment

Represents a managed OpenSearch deployment (SearchDB) in Scaleway.

> **Ontology Mapping**: This node has the extra label `Database`.

| Field       | Description                                  |
|-------------|----------------------------------------------|
| id          | ID of the deployment.                        |
| name        | Name of the deployment.                      |
| status      | Status of the deployment.                    |
| tags        | Tags attached to the deployment.             |
| node_amount | Number of nodes.                             |
| node_type   | Node type.                                   |
| version     | Engine version.                              |
| is_public   | True if any endpoint is public-facing.       |
| region      | Region the deployment lives in.              |
| created_at  | Creation timestamp.                          |
| updated_at  | Last update timestamp.                       |
| lastupdated | Timestamp of the last update                 |

#### Relationships
- A `SearchDeployment` belongs to a `Project`.
    ```
    (:ScalewayProject)-[:RESOURCE]->(:ScalewaySearchDeployment)
    ```


### ScalewayElasticMetalFlexibleIp

Represents a flexible (portable) public IP for Elastic Metal servers in Scaleway.

| Field       | Description                                  |
|-------------|----------------------------------------------|
| id          | ID of the flexible IP.                       |
| description | Description of the flexible IP.              |
| tags        | Tags attached to the flexible IP.            |
| status      | Status of the flexible IP.                   |
| ip_address  | The IP address.                              |
| reverse     | Reverse DNS value.                           |
| server_id   | ID of the server the IP is attached to.      |
| zone        | Availability zone.                           |
| created_at  | Creation timestamp.                          |
| updated_at  | Last update timestamp.                       |
| lastupdated | Timestamp of the last update                 |

#### Relationships
- An `ElasticMetalFlexibleIp` belongs to a `Project`.
    ```
    (:ScalewayProject)-[:RESOURCE]->(:ScalewayElasticMetalFlexibleIp)
    ```
- An `ElasticMetalFlexibleIp` identifies an `ElasticMetalServer`.
    ```
    (:ScalewayElasticMetalFlexibleIp)-[:IDENTIFIES]->(:ScalewayElasticMetalServer)
    ```


### ScalewayRegisteredDomain

Represents a domain registered with the Scaleway registrar.

| Field                               | Description                     |
|-------------------------------------|---------------------------------|
| id                                  | Domain name (unique id).        |
| name                                | Domain name.                    |
| status                              | Status of the domain.           |
| registrar                           | Registrar of the domain.        |
| is_external                         | Whether the domain is external. |
| epp_code                            | EPP status codes.               |
| auto_renew_status                   | Auto-renewal status.            |
| dnssec_status                       | DNSSEC status.                  |
| external_domain_registration_status | External registration status.  |
| transfer_registration_status        | Transfer registration status.   |
| expired_at                          | Expiration timestamp.           |
| created_at                          | Creation timestamp.             |
| updated_at                          | Last update timestamp.          |
| lastupdated                         | Timestamp of the last update    |

#### Relationships
- A `RegisteredDomain` belongs to an `Organization`.
    ```
    (:ScalewayOrganization)-[:RESOURCE]->(:ScalewayRegisteredDomain)
    ```
- A `RegisteredDomain` belongs to a `Project`.
    ```
    (:ScalewayProject)-[:RESOURCE]->(:ScalewayRegisteredDomain)
    ```
