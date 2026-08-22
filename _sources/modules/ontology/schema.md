<!-- Generated from the data model. Do not edit manually. -->

## Ontology Schema

The ontology combines dedicated abstract nodes with semantic labels applied directly to provider-specific nodes.

Canonical relationship constraints validate the names and directions of existing relationships. They do not create relationships.

```mermaid
graph LR
    AIModel -- BASED_ON --> AIModel
    AIModel -- CUSTOM --> AIModel
    AIModel -- DETECTED_IN --> CodeRepository
    AIModel -- DETECTED_IN --> Image
    AIModel -- EXPOSES_TOOL --> AIModel
    AIModel -- HAS_EXECUTION_ROLE --> PermissionRole
    AIModel -- REFERENCES_ARTIFACTS_IN --> ObjectStorage
    AIModel -- STORED_IN --> ObjectStorage
    AIModel -- TRAINED_FROM --> ObjectStorage
    AIModel -- USES_MODEL --> AIModel
    AIModel -- USES_TOOL --> AIModel
    APIKey -- CAN_ACCESS --> CodeRepository
    APIKey -- OWNED_BY --> ServiceAccount
    APIKey -- OWNED_BY --> UserAccount
    APIKey -- RESTRICTED_TO --> PermissionRole
    BbotIPAddress -- MATCHES_PUBLIC_IP --> PublicIP
    BlockStorage -- ATTACHED_TO --> ComputeInstance
    BlockStorage -- HAS --> Snapshot
    BlockStorage -- TAGGED --> Tag
    CICDPipeline -- ASSUMES --> PermissionRole
    CICDPipeline -- REFERENCES_SECRET --> Secret
    CVE -- AFFECTS --> ComputeInstance
    CVE -- AFFECTS --> ContainerRegistry
    CVE -- AFFECTS --> Device
    CVE -- AFFECTS --> Image
    CVE -- AFFECTS --> ImageAttestation
    CVE -- AFFECTS --> ImageManifestList
    CVE -- AFFECTS --> PackageVersion
    CVE -- ASSIGNED_TO --> UserAccount
    CVE -- DISMISSED_BY --> UserAccount
    CVE -- FOUND_IN --> CodeRepository
    CVE -- LINKED_TO --> CVE
    CVE -- LINKED_TO --> SecurityIssue
    CodeRepository -- ASSUMED_ROLE_WITH_WEB_IDENTITY --> PermissionRole
    CodeRepository -- HAS_PACKAGE --> ContainerRegistry
    CodeRepository -- HAS_SECRET --> Secret
    CodeRepository -- HAS_WORKFLOW --> CICDPipeline
    CodeRepository -- MEMBER_OF --> UserGroup
    CodeRepository -- OWNER --> Tenant
    CodeRepository -- OWNER --> UserAccount
    CodeRepository -- RESOURCE --> CICDPipeline
    ComputeCluster -- HAS_SERVICE --> ComputeService
    ComputeCluster -- HAS_TASK --> ComputePod
    ComputeCluster -- LABELED --> Tag
    ComputeCluster -- MAPS_TO --> ComputeCluster
    ComputeCluster -- RESOURCE --> ComputeNamespace
    ComputeCluster -- RESOURCE --> ComputePod
    ComputeCluster -- RESOURCE --> ComputeService
    ComputeCluster -- RESOURCE --> Container
    ComputeCluster -- RESOURCE --> IdentityProvider
    ComputeCluster -- RESOURCE --> PermissionRole
    ComputeCluster -- RESOURCE --> Secret
    ComputeCluster -- RESOURCE --> ServiceAccount
    ComputeCluster -- RESOURCE --> UserAccount
    ComputeCluster -- RESOURCE --> UserGroup
    ComputeCluster -- TAGGED --> Tag
    ComputeCluster -- TRUSTS --> IdentityProvider
    ComputeInstance -- ASSUMES --> PermissionRole
    ComputeInstance -- LABELED --> Tag
    ComputeInstance -- MEMBER_OF_EC2_SECURITY_GROUP --> NetworkAccessControl
    ComputeInstance -- MEMBER_OF_EKS_CLUSTER --> ComputeCluster
    ComputeInstance -- MEMBER_OF_GCP_VPC --> VirtualNetwork
    ComputeInstance -- MEMBER_OF_SCALEWAY_SECURITY_GROUP --> NetworkAccessControl
    ComputeInstance -- MOUNTS --> BlockStorage
    ComputeInstance -- PART_OF_SUBNET --> Subnet
    ComputeInstance -- RESOURCE --> Tenant
    ComputeInstance -- RUNS_AS --> ServiceAccount
    ComputeInstance -- STS_ASSUMEROLE_ALLOW --> PermissionRole
    ComputeInstance -- TAGGED --> Tag
    ComputeInstance -- USES_SECRET --> Secret
    ComputeNamespace -- CONTAINS --> ComputePod
    ComputeNamespace -- CONTAINS --> Container
    ComputeNamespace -- CONTAINS --> PermissionRole
    ComputeNamespace -- CONTAINS --> Secret
    ComputeNamespace -- CONTAINS --> ServiceAccount
    ComputeNamespace -- HAS --> ComputeService
    ComputeNamespace -- HAS --> Container
    ComputeNamespace -- HAS --> Function
    ComputeNamespace -- WORKLOAD_PARENT --> ComputeCluster
    ComputePod -- ATTACHED_TO --> Subnet
    ComputePod -- CONTAINS --> Container
    ComputePod -- HAS_CONTAINER --> Container
    ComputePod -- RUNS_AS --> ServiceAccount
    ComputePod -- TAGGED --> Tag
    ComputePod -- USES_SECRET --> Secret
    ComputePod -- USES_SECRET_ENV --> Secret
    ComputePod -- USES_SECRET_VOLUME --> Secret
    ComputePod -- USES_SERVICE_ACCOUNT --> ServiceAccount
    ComputePod -- WORKLOAD_PARENT --> ComputeCluster
    ComputePod -- WORKLOAD_PARENT --> ComputeNamespace
    ComputePod -- WORKLOAD_PARENT --> ComputeService
    ComputeService -- CONTAINS --> Container
    ComputeService -- DEPLOYED_FROM --> CodeRepository
    ComputeService -- EXPOSE --> DNSZone
    ComputeService -- HAS_CERTIFICATE --> Certificate
    ComputeService -- HAS_DATABASE_BRANCH --> Database
    ComputeService -- HAS_DEV_SERVER --> ComputeInstance
    ComputeService -- HAS_DNS_ZONE --> DNSZone
    ComputeService -- HAS_ENV_VAR --> Secret
    ComputeService -- HAS_FUNCTION --> Function
    ComputeService -- HAS_IMAGE --> Image
    ComputeService -- HAS_RUNTIME_IMAGE --> Image
    ComputeService -- HAS_SERVICE_INSTANCE --> ThirdPartyApp
    ComputeService -- HAS_TASK --> ComputePod
    ComputeService -- LABELED --> Tag
    ComputeService -- MOUNTS --> BlockStorage
    ComputeService -- RUNS_AS --> ServiceAccount
    ComputeService -- TAGGED --> Tag
    ComputeService -- USES_SECRET --> Secret
    ComputeService -- USES_SERVICE_ACCOUNT --> ServiceAccount
    ComputeService -- USES_WAREHOUSE --> ComputeCluster
    ComputeService -- WORKLOAD_PARENT --> ComputeCluster
    ComputeService -- WORKLOAD_PARENT --> ComputeNamespace
    ComputeService -- WORKLOAD_PARENT --> ComputeService
    Container -- HAS_IMAGE --> Image
    Container -- HAS_IMAGE --> ImageAttestation
    Container -- HAS_IMAGE --> ImageManifestList
    Container -- RESOLVED_IMAGE --> Image
    Container -- TAGGED --> Tag
    Container -- WORKLOAD_PARENT --> ComputePod
    Container -- WORKLOAD_PARENT --> ComputeService
    ContainerRegistry -- CONTAINS --> Image
    ContainerRegistry -- CONTAINS --> ImageTag
    ContainerRegistry -- HAS_IMAGE --> Image
    ContainerRegistry -- HAS_IMAGE --> ImageManifestList
    ContainerRegistry -- HAS_TAG --> ImageTag
    ContainerRegistry -- REPO_IMAGE --> ImageTag
    ContainerRegistry -- TAGGED --> Tag
    DNSRecord -- DISCOVERED_FROM --> DNSRecord
    DNSRecord -- DISCOVERED_FROM --> SecurityIssue
    DNSRecord -- DNS_POINTS_TO --> AWSCloudFrontDistribution
    DNSRecord -- DNS_POINTS_TO --> AzureAppService
    DNSRecord -- DNS_POINTS_TO --> ComputeInstance
    DNSRecord -- DNS_POINTS_TO --> DNSRecord
    DNSRecord -- DNS_POINTS_TO --> Database
    DNSRecord -- DNS_POINTS_TO --> Function
    DNSRecord -- DNS_POINTS_TO --> KubernetesIngress
    DNSRecord -- DNS_POINTS_TO --> LoadBalancer
    DNSRecord -- MATCHES_DNS_RECORD --> DNSRecord
    DNSRecord -- MEMBER_OF_DNS_ZONE --> DNSZone
    DNSRecord -- POINTS_TO --> Tenant
    DNSRecord -- RESOLVES_TO --> DNSRecord
    DNSZone -- HAS_DNS_RECORD --> DNSRecord
    DNSZone -- HAS_R2_CUSTOM_DOMAIN --> ObjectStorage
    DNSZone -- HAS_RECORD --> DNSRecord
    DNSZone -- HAS_RULESET --> NetworkAccessControl
    DNSZone -- LABELED --> Tag
    DNSZone -- RESOURCE --> DNSRecord
    DNSZone -- SUBZONE --> DNSZone
    DNSZone -- TAGGED --> Tag
    Database -- ASSOCIATED_WITH --> VirtualNetwork
    Database -- BACKED_BY --> ObjectStorage
    Database -- CONTAINS --> Database
    Database -- CONTAINS --> ObjectStorage
    Database -- CONTAINS --> PermissionRole
    Database -- ENCRYPTED_BY --> EncryptionKey
    Database -- HAS_SNAPSHOT --> Snapshot
    Database -- IS_READ_REPLICA_OF --> Database
    Database -- LABELED --> Tag
    Database -- MEMBER_OF_EC2_SECURITY_GROUP --> NetworkAccessControl
    Database -- PART_OF_SUBNET --> Subnet
    Database -- TAGGED --> Tag
    Database -- USES_SERVICE_ACCOUNT --> ServiceAccount
    Device -- OBSERVED_AS --> BigfixComputer
    Device -- OBSERVED_AS --> CrowdstrikeHost
    Device -- OBSERVED_AS --> DuoEndpoint
    Device -- OBSERVED_AS --> DuoPhone
    Device -- OBSERVED_AS --> GoogleWorkspaceDevice
    Device -- OBSERVED_AS --> IntuneManagedDevice
    Device -- OBSERVED_AS --> JamfComputer
    Device -- OBSERVED_AS --> JamfMobileDevice
    Device -- OBSERVED_AS --> JumpCloudSystem
    Device -- OBSERVED_AS --> KandjiDevice
    Device -- OBSERVED_AS --> MiradoreDevice
    Device -- OBSERVED_AS --> S1Agent
    Device -- OBSERVED_AS --> SnipeitAsset
    Device -- OBSERVED_AS --> TailscaleDevice
    EncryptionKey -- TAGGED --> Tag
    FileStorage -- BACKED_BY --> ObjectStorage
    FileStorage -- CREATED_BY --> UserAccount
    FileStorage -- ENCRYPTED_BY --> EncryptionKey
    Function -- ASSUMES --> PermissionRole
    Function -- HAS --> Image
    Function -- HAS --> ImageAttestation
    Function -- HAS --> ImageManifestList
    Function -- HAS_IMAGE --> Image
    Function -- HAS_IMAGE --> ImageAttestation
    Function -- HAS_IMAGE --> ImageManifestList
    Function -- LABELED --> Tag
    Function -- RESOLVED_IMAGE --> Image
    Function -- RUNS_AS --> ServiceAccount
    Function -- TAGGED --> Tag
    Function -- USES_SECRET --> Secret
    Function -- WORKLOAD_PARENT --> ComputeService
    IdentityProvider -- GOVERNED_BY --> NetworkAccessControl
    IdentityProvider -- RUNS_AS_ROLE --> PermissionRole
    Image -- ATTESTS --> Image
    Image -- ATTESTS --> ImageAttestation
    Image -- ATTESTS --> ImageManifestList
    Image -- BUILT_FROM --> Image
    Image -- BUILT_FROM --> ImageAttestation
    Image -- BUILT_FROM --> ImageManifestList
    Image -- CONTAINS_IMAGE --> Image
    Image -- CONTAINS_IMAGE --> ImageAttestation
    Image -- CONTAINS_IMAGE --> ImageManifestList
    Image -- HAS_LAYER --> ImageLayer
    Image -- HEAD --> ImageLayer
    Image -- PACKAGED_BY --> CICDPipeline
    Image -- PACKAGED_FROM --> CodeRepository
    Image -- TAIL --> ImageLayer
    ImageAttestation -- ATTESTS --> Image
    ImageAttestation -- ATTESTS --> ImageAttestation
    ImageAttestation -- ATTESTS --> ImageManifestList
    ImageAttestation -- BUILT_FROM --> Image
    ImageAttestation -- BUILT_FROM --> ImageAttestation
    ImageAttestation -- BUILT_FROM --> ImageManifestList
    ImageAttestation -- CONTAINS_IMAGE --> Image
    ImageAttestation -- CONTAINS_IMAGE --> ImageAttestation
    ImageAttestation -- CONTAINS_IMAGE --> ImageManifestList
    ImageAttestation -- HAS_LAYER --> ImageLayer
    ImageAttestation -- HEAD --> ImageLayer
    ImageAttestation -- TAIL --> ImageLayer
    ImageLayer -- NEXT --> ImageLayer
    ImageManifestList -- ATTESTS --> Image
    ImageManifestList -- ATTESTS --> ImageAttestation
    ImageManifestList -- ATTESTS --> ImageManifestList
    ImageManifestList -- BUILT_FROM --> Image
    ImageManifestList -- BUILT_FROM --> ImageAttestation
    ImageManifestList -- BUILT_FROM --> ImageManifestList
    ImageManifestList -- CONTAINS_IMAGE --> Image
    ImageManifestList -- CONTAINS_IMAGE --> ImageAttestation
    ImageManifestList -- CONTAINS_IMAGE --> ImageManifestList
    ImageManifestList -- HAS_LAYER --> ImageLayer
    ImageManifestList -- HEAD --> ImageLayer
    ImageManifestList -- TAIL --> ImageLayer
    ImageTag -- IMAGE --> Image
    ImageTag -- IMAGE --> ImageAttestation
    ImageTag -- IMAGE --> ImageManifestList
    ImageTag -- REFERENCES --> Image
    ImageTag -- REFERENCES --> ImageManifestList
    LoadBalancer -- EXPOSE --> ComputeInstance
    LoadBalancer -- EXPOSE --> ComputePod
    LoadBalancer -- EXPOSE --> Container
    LoadBalancer -- EXPOSE --> Function
    LoadBalancer -- EXPOSE --> LoadBalancer
    LoadBalancer -- IN_SUBNET --> Subnet
    LoadBalancer -- MEMBER_OF_EC2_SECURITY_GROUP --> NetworkAccessControl
    LoadBalancer -- PART_OF_SUBNET --> Subnet
    LoadBalancer -- SOURCE_SECURITY_GROUP --> NetworkAccessControl
    LoadBalancer -- SUBNET --> Subnet
    LoadBalancer -- TAGGED --> Tag
    NetworkAccessControl -- ALLOWS --> NetworkAccessControl
    NetworkAccessControl -- ALLOWS_TRAFFIC_FROM --> NetworkAccessControl
    NetworkAccessControl -- BLOCKS --> NetworkAccessControl
    NetworkAccessControl -- FIREWALL_INGRESS --> ComputeInstance
    NetworkAccessControl -- MEMBER_OF --> VirtualNetwork
    NetworkAccessControl -- PROTECTS --> LoadBalancer
    NetworkAccessControl -- TAGGED --> Tag
    ObjectStorage -- BACKED_BY --> ObjectStorage
    ObjectStorage -- ENCRYPTED_BY --> EncryptionKey
    ObjectStorage -- LABELED --> Tag
    ObjectStorage -- TAGGED --> Tag
    Package -- HAS_VERSION --> PackageVersion
    PackageVersion -- DEPENDS_ON --> PackageVersion
    PackageVersion -- DEPLOYED --> Image
    PackageVersion -- DETECTED_AS --> GitHubDependency
    PackageVersion -- DETECTED_AS --> GitLabDependency
    PackageVersion -- DETECTED_AS --> SemgrepDependency
    PackageVersion -- DETECTED_AS --> SocketDevDependency
    PackageVersion -- DETECTED_AS --> SyftPackage
    PackageVersion -- DETECTED_AS --> TrivyPackage
    PackageVersion -- SHOULD_UPDATE_TO --> TrivyFix
    PermissionRole -- ALLOWED_BY --> UserAccount
    PermissionRole -- ALLOWED_BY --> UserGroup
    PermissionRole -- ASSIGNED_TO_ROLE --> PermissionRole
    PermissionRole -- INCLUDES --> PermissionRole
    PermissionRole -- MAPS_TO --> UserAccount
    PermissionRole -- MAPS_TO --> UserGroup
    PermissionRole -- OCI_POLICY_REFERENCE --> UserGroup
    PermissionRole -- TAGGED --> Tag
    PublicIP -- POINTS_TO --> ComputeInstance
    PublicIP -- POINTS_TO --> Device
    PublicIP -- POINTS_TO --> LoadBalancer
    PublicIP -- RESERVED_BY --> AWSElasticIPAddress
    PublicIP -- RESERVED_BY --> AzurePublicIPAddress
    PublicIP -- RESERVED_BY --> GCPNicAccessConfig
    PublicIP -- RESERVED_BY --> ScalewayElasticMetalFlexibleIp
    PublicIP -- RESERVED_BY --> ScalewayFlexibleIp
    Secret -- CREATED_BY --> UserAccount
    Secret -- ENCRYPTED_BY --> EncryptionKey
    Secret -- LABELED --> Tag
    Secret -- TAGGED --> Tag
    Secret -- UPDATED_BY --> UserAccount
    Secret -- USES_INTEGRATION --> IdentityProvider
    SecurityIssue -- AFFECTS --> APIKey
    SecurityIssue -- AFFECTS --> CICDPipeline
    SecurityIssue -- AFFECTS --> ComputeCluster
    SecurityIssue -- AFFECTS --> ComputeInstance
    SecurityIssue -- AFFECTS --> ContainerRegistry
    SecurityIssue -- AFFECTS --> DNSRecord
    SecurityIssue -- AFFECTS --> Database
    SecurityIssue -- AFFECTS --> Image
    SecurityIssue -- AFFECTS --> ImageAttestation
    SecurityIssue -- AFFECTS --> ImageManifestList
    SecurityIssue -- AFFECTS --> ObjectStorage
    SecurityIssue -- AFFECTS --> PackageVersion
    SecurityIssue -- AFFECTS --> PermissionRole
    SecurityIssue -- AFFECTS --> UserAccount
    SecurityIssue -- ASSIGNED_TO --> UserAccount
    SecurityIssue -- DISCOVERED_FROM --> DNSRecord
    SecurityIssue -- DISCOVERED_FROM --> SecurityIssue
    SecurityIssue -- DISMISSED_BY --> UserAccount
    SecurityIssue -- FOUND_IN --> CodeRepository
    SecurityIssue -- LINKED_TO --> CVE
    SecurityIssue -- REMOTE_ACCOUNT --> Tenant
    SecurityIssue -- TAGGED --> Tag
    ServiceAccount -- ASSIGNED_TO --> Tenant
    ServiceAccount -- ASSUMES_ROLE --> PermissionRole
    ServiceAccount -- CAN_ACCESS --> Tenant
    ServiceAccount -- CREATED_BY --> UserAccount
    ServiceAccount -- GOVERNED_BY --> NetworkAccessControl
    ServiceAccount -- HAS --> APIKey
    ServiceAccount -- HAS_KEY --> APIKey
    ServiceAccount -- HAS_ROLE --> PermissionRole
    ServiceAccount -- MEMBER_OF --> UserGroup
    ServiceAccount -- OWNS --> APIKey
    ServiceAccount -- WORKLOAD_IDENTITY_BINDING --> ServiceAccount
    Snapshot -- CREATED_FROM --> BlockStorage
    Snapshot -- IS_SNAPSHOT_SOURCE --> Database
    Snapshot -- TAGGED --> Tag
    Subnet -- ASSOCIATED_WITH --> NetworkAccessControl
    Subnet -- MEMBER_OF_AWS_VPC --> VirtualNetwork
    Subnet -- RESOURCE --> LoadBalancer
    Subnet -- TAGGED --> Tag
    TailscaleDevice -- IS_INSTANCE --> ComputeInstance
    Tenant -- ASSOCIATED_WITH --> Tenant
    Tenant -- GOVERNED_BY --> NetworkAccessControl
    Tenant -- HAS --> PermissionRole
    Tenant -- HAS_ASSESSMENT --> SecurityIssue
    Tenant -- HAS_USER --> UserAccount
    Tenant -- MEMBER --> CVE
    Tenant -- MEMBER --> SecurityIssue
    Tenant -- OWNS --> APIKey
    Tenant -- PARENT --> Tenant
    Tenant -- RESOURCE --> AIModel
    Tenant -- RESOURCE --> APIKey
    Tenant -- RESOURCE --> BlockStorage
    Tenant -- RESOURCE --> CICDPipeline
    Tenant -- RESOURCE --> CVE
    Tenant -- RESOURCE --> Certificate
    Tenant -- RESOURCE --> ComputeCluster
    Tenant -- RESOURCE --> ComputeInstance
    Tenant -- RESOURCE --> ComputeNamespace
    Tenant -- RESOURCE --> ComputePod
    Tenant -- RESOURCE --> ComputeService
    Tenant -- RESOURCE --> Container
    Tenant -- RESOURCE --> ContainerRegistry
    Tenant -- RESOURCE --> DNSRecord
    Tenant -- RESOURCE --> DNSZone
    Tenant -- RESOURCE --> Database
    Tenant -- RESOURCE --> EncryptionKey
    Tenant -- RESOURCE --> FileStorage
    Tenant -- RESOURCE --> Function
    Tenant -- RESOURCE --> IdentityProvider
    Tenant -- RESOURCE --> Image
    Tenant -- RESOURCE --> ImageAttestation
    Tenant -- RESOURCE --> ImageLayer
    Tenant -- RESOURCE --> ImageManifestList
    Tenant -- RESOURCE --> ImageTag
    Tenant -- RESOURCE --> LoadBalancer
    Tenant -- RESOURCE --> NetworkAccessControl
    Tenant -- RESOURCE --> ObjectStorage
    Tenant -- RESOURCE --> PermissionRole
    Tenant -- RESOURCE --> Secret
    Tenant -- RESOURCE --> SecurityIssue
    Tenant -- RESOURCE --> ServiceAccount
    Tenant -- RESOURCE --> Snapshot
    Tenant -- RESOURCE --> Subnet
    Tenant -- RESOURCE --> Tag
    Tenant -- RESOURCE --> Tenant
    Tenant -- RESOURCE --> ThirdPartyApp
    Tenant -- RESOURCE --> UserAccount
    Tenant -- RESOURCE --> UserGroup
    Tenant -- RESOURCE --> VirtualNetwork
    ThirdPartyApp -- BELONGS_TO --> Tenant
    ThirdPartyApp -- CREATED --> UserGroup
    ThirdPartyApp -- DEFINES --> PermissionRole
    ThirdPartyApp -- HAS_SECRET --> APIKey
    ThirdPartyApp -- HAS_SERVICE_ACCOUNT --> UserAccount
    ThirdPartyApp -- MEMBER_OF --> UserGroup
    ThirdPartyApp -- SERVICE_PRINCIPAL --> ServiceAccount
    User -- AUTHORIZED --> ThirdPartyApp
    User -- HAS_ACCOUNT --> UserAccount
    User -- OWNS --> APIKey
    User -- OWNS --> Device
    UserAccount -- ADMIN_OF --> Tenant
    UserAccount -- ADMIN_OF --> UserGroup
    UserAccount -- ASSIGNED_TO --> Tenant
    UserAccount -- ASSUMED_ROLE_WITH_SAML --> PermissionRole
    UserAccount -- ASSUME_ROLE --> PermissionRole
    UserAccount -- AUTHORIZED --> ThirdPartyApp
    UserAccount -- AWS_ACCESS_KEY --> APIKey
    UserAccount -- BELONGS_TO --> Tenant
    UserAccount -- CAN_ACCESS --> Tenant
    UserAccount -- CAN_ASSUME_IDENTITY --> UserAccount
    UserAccount -- CAN_SIGN_ON_TO --> UserAccount
    UserAccount -- COMMITTED_TO --> CodeRepository
    UserAccount -- CREATED --> UserGroup
    UserAccount -- DIRECT_COLLAB_ADMIN --> CodeRepository
    UserAccount -- DIRECT_COLLAB_MAINTAIN --> CodeRepository
    UserAccount -- DIRECT_COLLAB_READ --> CodeRepository
    UserAccount -- DIRECT_COLLAB_TRIAGE --> CodeRepository
    UserAccount -- DIRECT_COLLAB_WRITE --> CodeRepository
    UserAccount -- GOVERNED_BY --> NetworkAccessControl
    UserAccount -- HAS --> APIKey
    UserAccount -- HAS_IDENTITY --> IdentityProvider
    UserAccount -- HAS_PERMISSION_SET --> PermissionRole
    UserAccount -- HAS_ROLE --> PermissionRole
    UserAccount -- INHERITED_MEMBER_OF --> UserGroup
    UserAccount -- INHERITED_OWNER_OF --> UserGroup
    UserAccount -- MAINTAINER --> UserGroup
    UserAccount -- MAPS_TO --> UserAccount
    UserAccount -- MAPS_TO --> UserGroup
    UserAccount -- MEMBER --> UserGroup
    UserAccount -- MEMBER_AWS_GROUP --> UserGroup
    UserAccount -- MEMBER_GSUITE_GROUP --> UserGroup
    UserAccount -- MEMBER_OCID_GROUP --> UserGroup
    UserAccount -- MEMBER_OF --> Tenant
    UserAccount -- MEMBER_OF --> UserGroup
    UserAccount -- MEMBER_OF_DUO_GROUP --> UserGroup
    UserAccount -- MEMBER_OF_SSO_GROUP --> UserGroup
    UserAccount -- OUTSIDE_COLLAB_ADMIN --> CodeRepository
    UserAccount -- OUTSIDE_COLLAB_MAINTAIN --> CodeRepository
    UserAccount -- OUTSIDE_COLLAB_READ --> CodeRepository
    UserAccount -- OUTSIDE_COLLAB_TRIAGE --> CodeRepository
    UserAccount -- OUTSIDE_COLLAB_WRITE --> CodeRepository
    UserAccount -- OWNER_GSUITE_GROUP --> UserGroup
    UserAccount -- OWNER_OF --> UserGroup
    UserAccount -- OWNS --> APIKey
    UserAccount -- REPORTS_TO --> UserAccount
    UserAccount -- RESOURCE --> Tenant
    UserAccount -- TAGGED --> Tag
    UserAccount -- UNAFFILIATED --> Tenant
    UserAccount -- USES --> ThirdPartyApp
    UserGroup -- ADMIN --> CodeRepository
    UserGroup -- ASSIGNED_TO --> Tenant
    UserGroup -- CAN_ACCESS --> CodeRepository
    UserGroup -- CAN_ACCESS --> Tenant
    UserGroup -- GRANTS --> PermissionRole
    UserGroup -- HAS_MEMBER --> UserAccount
    UserGroup -- HAS_PERMISSION_SET --> PermissionRole
    UserGroup -- HAS_ROLE --> PermissionRole
    UserGroup -- INHERITED_MEMBER_OF --> UserGroup
    UserGroup -- INHERITED_OWNER_OF --> UserGroup
    UserGroup -- MAINTAIN --> CodeRepository
    UserGroup -- MEMBER_GSUITE_GROUP --> UserGroup
    UserGroup -- MEMBER_OF --> UserGroup
    UserGroup -- MEMBER_OF_TEAM --> UserGroup
    UserGroup -- OWNER_GSUITE_GROUP --> UserGroup
    UserGroup -- OWNER_OF --> UserGroup
    UserGroup -- READ --> CodeRepository
    UserGroup -- SUBGROUP_OF --> UserGroup
    UserGroup -- TRIAGE --> CodeRepository
    UserGroup -- WRITE --> CodeRepository
    VirtualNetwork -- CONTAINS --> Subnet
    VirtualNetwork -- HAS --> Subnet
    VirtualNetwork -- MEMBER_OF_EC2_SECURITY_GROUP --> NetworkAccessControl
    VirtualNetwork -- RESOURCE --> LoadBalancer
    VirtualNetwork -- RESOURCE --> NetworkAccessControl
    VirtualNetwork -- TAGGED --> Tag
```

(ontology-aimodel)=
### AIModel

A cross-provider AIModel resource in Cartography's ontology.

> **Semantic Label**: This label is applied directly to provider-specific nodes; it does not create a separate node.

> **Implementations**: `AIBOMComponent`, `AWSBedrockCustomModel`, `AWSBedrockFoundationModel`, `AWSSageMakerModel`, `GCPVertexAIModel`.

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| *_ont_name* | Yes | Normalized name for nodes carrying `AIModel`. |
| *_ont_provider* | Yes | Normalized provider for nodes carrying `AIModel`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |
| *_ont_status* | Yes | Normalized status for nodes carrying `AIModel`. |
| *_ont_type* | Yes | Normalized type for nodes carrying `AIModel`. |

#### Relationships

- `(:AIModel)-[:BASED_ON]->(:AIModel)`

- `(:AIModel)-[:CUSTOM]->(:AIModel)`

- `(:AIModel)-[:DETECTED_IN]->(:CodeRepository)`

- `(:AIModel)-[:DETECTED_IN]->(:Image)`

- `(:AIModel)-[:EXPOSES_TOOL]->(:AIModel)`

- `(:AIModel)-[:HAS_EXECUTION_ROLE]->(:PermissionRole)`

- `(:AIModel)-[:REFERENCES_ARTIFACTS_IN]->(:ObjectStorage)`

- `(:AIModel)-[:STORED_IN]->(:ObjectStorage)`

- `(:AIModel)-[:TRAINED_FROM]->(:ObjectStorage)`

- `(:AIModel)-[:USES_MODEL]->(:AIModel)`

- `(:AIModel)-[:USES_TOOL]->(:AIModel)`

- `(:Tenant)-[:RESOURCE]->(:AIModel)`

(ontology-apikey)=
### APIKey

A cross-provider APIKey resource in Cartography's ontology.

> **Semantic Label**: This label is applied directly to provider-specific nodes; it does not create a separate node.

> **Implementations**: `AWSAccountAccessKey`, `AnthropicApiKey`, `GCPApiKey`, `GCPServiceAccountKey`, `GitHubPersonalAccessToken`, `ModalApiToken`, `ModalProxyToken`, `OpenAIAdminApiKey`, `OpenAIApiKey`, `RailwayApiToken`, `RailwayProjectToken`, `ScalewayApiKey`, `SnowflakeProgrammaticAccessToken`, `SubImageAPIKey`, `SupabaseApiKey`, `WorkOSAPIKey`, `WorkOSApplicationClientSecret`.

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| *_ont_created_at* | Yes | Normalized created at for nodes carrying `APIKey`. |
| *_ont_expires_at* | Yes | Normalized expires at for nodes carrying `APIKey`. |
| *_ont_last_used_at* | Yes | Normalized last used at for nodes carrying `APIKey`. |
| *_ont_name* | Yes | Normalized name for nodes carrying `APIKey`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |
| *_ont_type* | Yes | Normalized type for nodes carrying `APIKey`. |
| *_ont_updated_at* | Yes | Normalized updated at for nodes carrying `APIKey`. |

#### Relationships

- `(:APIKey)-[:CAN_ACCESS]->(:CodeRepository)`

- `(:APIKey)-[:OWNED_BY]->(:ServiceAccount)`: `OWNED_BY` is the canonical relationship name from `APIKey` to `ServiceAccount`. This constraint validates existing relationships and does not create them.

- `(:APIKey)-[:OWNED_BY]->(:UserAccount)`: `OWNED_BY` is the canonical relationship name from `APIKey` to `UserAccount`. This constraint validates existing relationships and does not create them.

- `(:APIKey)-[:RESTRICTED_TO]->(:PermissionRole)`

- `(:SecurityIssue)-[:AFFECTS]->(:APIKey)`

- `(:ServiceAccount)-[:HAS]->(:APIKey)`

- `(:ServiceAccount)-[:HAS_KEY]->(:APIKey)`

- `(:ServiceAccount)-[:OWNS]->(:APIKey)`

- `(:Tenant)-[:OWNS]->(:APIKey)`

- `(:Tenant)-[:RESOURCE]->(:APIKey)`

- `(:ThirdPartyApp)-[:HAS_SECRET]->(:APIKey)`

- `(:User)-[:OWNS]->(:APIKey)`: generated by analysis job `Ontology - User OWNS APIKey linking`.

- `(:UserAccount)-[:AWS_ACCESS_KEY]->(:APIKey)`

- `(:UserAccount)-[:HAS]->(:APIKey)`

- `(:UserAccount)-[:OWNS]->(:APIKey)`

(ontology-blockstorage)=
### BlockStorage

A cross-provider BlockStorage resource in Cartography's ontology.

> **Semantic Label**: This label is applied directly to provider-specific nodes; it does not create a separate node.

> **Implementations**: `AWSEBSVolume`, `AzureDisk`, `RailwayVolumeInstance`, `ScalewayVolume`.

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| *_ont_encrypted* | Yes | Normalized encrypted for nodes carrying `BlockStorage`. |
| *_ont_name* | Yes | Normalized name for nodes carrying `BlockStorage`. |
| *_ont_region* | Yes | Normalized region for nodes carrying `BlockStorage`. |
| *_ont_size_gb* | Yes | Normalized size gb for nodes carrying `BlockStorage`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |
| *_ont_state* | Yes | Normalized state for nodes carrying `BlockStorage`. |

#### Relationships

- `(:BlockStorage)-[:ATTACHED_TO]->(:ComputeInstance)`

- `(:BlockStorage)-[:HAS]->(:Snapshot)`

- `(:BlockStorage)-[:TAGGED]->(:Tag)`

- `(:ComputeInstance)-[:MOUNTS]->(:BlockStorage)`

- `(:ComputeService)-[:MOUNTS]->(:BlockStorage)`

- `(:Snapshot)-[:CREATED_FROM]->(:BlockStorage)`

- `(:Tenant)-[:RESOURCE]->(:BlockStorage)`

(ontology-certificate)=
### Certificate

A cross-provider Certificate resource in Cartography's ontology.

> **Semantic Label**: This label is applied directly to provider-specific nodes; it does not create a separate node.

> **Implementations**: `AWSACMCertificate`, `AWSServerCertificate`, `AzureKeyVaultCertificate`, `NetlifyCertificate`.

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| *_ont_domain* | Yes | Normalized domain for nodes carrying `Certificate`. |
| *_ont_expiry* | Yes | Normalized expiry for nodes carrying `Certificate`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |

#### Relationships

- `(:ComputeService)-[:HAS_CERTIFICATE]->(:Certificate)`

- `(:Tenant)-[:RESOURCE]->(:Certificate)`

(ontology-cicdpipeline)=
### CICDPipeline

A cross-provider CICDPipeline resource in Cartography's ontology.

> **Semantic Label**: This label is applied directly to provider-specific nodes; it does not create a separate node.

> **Implementations**: `AWSCodeBuildProject`, `CircleCIPipeline`, `GitHubWorkflow`, `GitLabCIConfig`, `SpaceliftStack`.

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| *_ont_name* | Yes | Normalized name for nodes carrying `CICDPipeline`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |
| *_ont_status* | Yes | Normalized status for nodes carrying `CICDPipeline`. |
| *_ont_type* | Yes | Normalized type for nodes carrying `CICDPipeline`. |

#### Relationships

- `(:CICDPipeline)-[:ASSUMES]->(:PermissionRole)`

- `(:CICDPipeline)-[:REFERENCES_SECRET]->(:Secret)`

- `(:CodeRepository)-[:HAS_WORKFLOW]->(:CICDPipeline)`

- `(:CodeRepository)-[:RESOURCE]->(:CICDPipeline)`

- `(:Image)-[:PACKAGED_BY]->(:CICDPipeline)`

- `(:SecurityIssue)-[:AFFECTS]->(:CICDPipeline)`

- `(:Tenant)-[:RESOURCE]->(:CICDPipeline)`

(ontology-coderepository)=
### CodeRepository

A cross-provider CodeRepository resource in Cartography's ontology.

> **Semantic Label**: This label is applied directly to provider-specific nodes; it does not create a separate node.

> **Implementations**: `GitHubRepository`, `GitLabProject`.

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| *_ont_archived* | Yes | Normalized archived for nodes carrying `CodeRepository`. |
| *_ont_default_branch* | Yes | Normalized default branch for nodes carrying `CodeRepository`. |
| *_ont_description* |  | Normalized description for nodes carrying `CodeRepository`. |
| *_ont_fork* | Yes | Normalized fork for nodes carrying `CodeRepository`. |
| *_ont_fullname* | Yes | Normalized fullname for nodes carrying `CodeRepository`. |
| *_ont_name* | Yes | Normalized name for nodes carrying `CodeRepository`. |
| *_ont_public* | Yes | Normalized public for nodes carrying `CodeRepository`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |
| *_ont_url* | Yes | Normalized url for nodes carrying `CodeRepository`. |

#### Relationships

- `(:AIModel)-[:DETECTED_IN]->(:CodeRepository)`

- `(:APIKey)-[:CAN_ACCESS]->(:CodeRepository)`

- `(:CVE)-[:FOUND_IN]->(:CodeRepository)`

- `(:CodeRepository)-[:ASSUMED_ROLE_WITH_WEB_IDENTITY]->(:PermissionRole)`
  - Properties:

    | Field | Description |
    |-------|-------------|
    | first_seen_in_time_window | Timestamp when this relationship was first observed in the current time window. |
    | last_used | Timestamp when this relationship was last observed in use. |
    | times_used | Number of times this relationship was observed in use. |

- `(:CodeRepository)-[:HAS_PACKAGE]->(:ContainerRegistry)`

- `(:CodeRepository)-[:HAS_SECRET]->(:Secret)`

- `(:CodeRepository)-[:HAS_WORKFLOW]->(:CICDPipeline)`

- `(:CodeRepository)-[:MEMBER_OF]->(:UserGroup)`

- `(:CodeRepository)-[:OWNER]->(:Tenant)`

- `(:CodeRepository)-[:OWNER]->(:UserAccount)`

- `(:CodeRepository)-[:RESOURCE]->(:CICDPipeline)`

- `(:ComputeService)-[:DEPLOYED_FROM]->(:CodeRepository)`

- `(:Image)-[:PACKAGED_FROM]->(:CodeRepository)`: `PACKAGED_FROM` is the canonical relationship name from `Image` to `CodeRepository`. This constraint validates existing relationships and does not create them.
  - Properties:

    | Field | Description |
    |-------|-------------|
    | command_similarity | Similarity score between image build commands and Dockerfile commands. |
    | confidence | Confidence score for the image-to-project match. |
    | dockerfile_path | Path of the Dockerfile associated with the image. |
    | match_method | Matching method: provenance, dockerfile_analysis, or dockerfile_singleton_fallback. |
    | matched_commands | Number of image build commands matched to Dockerfile commands. |
    | total_commands | Command count used to normalize the Dockerfile comparison. |

- `(:SecurityIssue)-[:FOUND_IN]->(:CodeRepository)`

- `(:UserAccount)-[:COMMITTED_TO]->(:CodeRepository)`
  - Properties:

    | Field | Description |
    |-------|-------------|
    | commit_count | Number of commits made by the user to the project. |
    | first_commit_date | Timestamp of the user's oldest commit to the project. |
    | last_commit_date | Timestamp of the user's most recent commit to the project. |

- `(:UserAccount)-[:DIRECT_COLLAB_ADMIN]->(:CodeRepository)`

- `(:UserAccount)-[:DIRECT_COLLAB_MAINTAIN]->(:CodeRepository)`

- `(:UserAccount)-[:DIRECT_COLLAB_READ]->(:CodeRepository)`

- `(:UserAccount)-[:DIRECT_COLLAB_TRIAGE]->(:CodeRepository)`

- `(:UserAccount)-[:DIRECT_COLLAB_WRITE]->(:CodeRepository)`

- `(:UserAccount)-[:OUTSIDE_COLLAB_ADMIN]->(:CodeRepository)`

- `(:UserAccount)-[:OUTSIDE_COLLAB_MAINTAIN]->(:CodeRepository)`

- `(:UserAccount)-[:OUTSIDE_COLLAB_READ]->(:CodeRepository)`

- `(:UserAccount)-[:OUTSIDE_COLLAB_TRIAGE]->(:CodeRepository)`

- `(:UserAccount)-[:OUTSIDE_COLLAB_WRITE]->(:CodeRepository)`

- `(:UserGroup)-[:ADMIN]->(:CodeRepository)`

- `(:UserGroup)-[:CAN_ACCESS]->(:CodeRepository)`
  - Properties:

    | Field | Description |
    |-------|-------------|
    | access_level | Numeric GitLab access level granted to the group. |

- `(:UserGroup)-[:MAINTAIN]->(:CodeRepository)`

- `(:UserGroup)-[:READ]->(:CodeRepository)`

- `(:UserGroup)-[:TRIAGE]->(:CodeRepository)`

- `(:UserGroup)-[:WRITE]->(:CodeRepository)`

(ontology-computecluster)=
### ComputeCluster

A cross-provider ComputeCluster resource in Cartography's ontology.

> **Semantic Label**: This label is applied directly to provider-specific nodes; it does not create a separate node.

> **Implementations**: `AWSECSCluster`, `AWSEKSCluster`, `AWSEMRCluster`, `AzureKubernetesCluster`, `GKECluster`, `KubernetesCluster`, `ScalewayKapsuleCluster`, `SnowflakeComputePool`, `SnowflakeWarehouse`.

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| *_ont_control_plane_public_access* | Yes | Normalized control plane public access for nodes carrying `ComputeCluster`. |
| *_ont_endpoint* | Yes | Normalized endpoint for nodes carrying `ComputeCluster`. |
| *_ont_name* | Yes | Normalized name for nodes carrying `ComputeCluster`. |
| *_ont_region* | Yes | Normalized region for nodes carrying `ComputeCluster`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |
| *_ont_status* | Yes | Normalized status for nodes carrying `ComputeCluster`. |
| *_ont_version* | Yes | Normalized version for nodes carrying `ComputeCluster`. |

#### Relationships

- `(:ComputeCluster)-[:HAS_SERVICE]->(:ComputeService)`

- `(:ComputeCluster)-[:HAS_TASK]->(:ComputePod)`

- `(:ComputeCluster)-[:LABELED]->(:Tag)`

- `(:ComputeCluster)-[:MAPS_TO]->(:ComputeCluster)`

- `(:ComputeCluster)-[:RESOURCE]->(:ComputeNamespace)`

- `(:ComputeCluster)-[:RESOURCE]->(:ComputePod)`

- `(:ComputeCluster)-[:RESOURCE]->(:ComputeService)`

- `(:ComputeCluster)-[:RESOURCE]->(:Container)`

- `(:ComputeCluster)-[:RESOURCE]->(:IdentityProvider)`

- `(:ComputeCluster)-[:RESOURCE]->(:PermissionRole)`

- `(:ComputeCluster)-[:RESOURCE]->(:Secret)`

- `(:ComputeCluster)-[:RESOURCE]->(:ServiceAccount)`

- `(:ComputeCluster)-[:RESOURCE]->(:UserAccount)`

- `(:ComputeCluster)-[:RESOURCE]->(:UserGroup)`

- `(:ComputeCluster)-[:TAGGED]->(:Tag)`

- `(:ComputeCluster)-[:TRUSTS]->(:IdentityProvider)`

- `(:ComputeInstance)-[:MEMBER_OF_EKS_CLUSTER]->(:ComputeCluster)`

- `(:ComputeNamespace)-[:WORKLOAD_PARENT]->(:ComputeCluster)`: `WORKLOAD_PARENT` is the canonical relationship name from `ComputeNamespace` to `ComputeCluster`. This constraint validates existing relationships and does not create them.

- `(:ComputePod)-[:WORKLOAD_PARENT]->(:ComputeCluster)`: `WORKLOAD_PARENT` is the canonical relationship name from `ComputePod` to `ComputeCluster`. This constraint validates existing relationships and does not create them.

- `(:ComputeService)-[:USES_WAREHOUSE]->(:ComputeCluster)`

- `(:ComputeService)-[:WORKLOAD_PARENT]->(:ComputeCluster)`: `WORKLOAD_PARENT` is the canonical relationship name from `ComputeService` to `ComputeCluster`. This constraint validates existing relationships and does not create them.

- `(:SecurityIssue)-[:AFFECTS]->(:ComputeCluster)`

- `(:Tenant)-[:RESOURCE]->(:ComputeCluster)`

(ontology-computeinstance)=
### ComputeInstance

A cross-provider ComputeInstance resource in Cartography's ontology.

> **Semantic Label**: This label is applied directly to provider-specific nodes; it does not create a separate node.

> **Implementations**: `AWSEC2Instance`, `AzureVirtualMachine`, `DODroplet`, `GCPInstance`, `NetlifyDevServer`, `ScalewayAppleSiliconServer`, `ScalewayDediboxServer`, `ScalewayElasticMetalServer`, `ScalewayInstance`.

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| *_ont_created_at* | Yes | Normalized created at for nodes carrying `ComputeInstance`. |
| *_ont_name* | Yes | Normalized name for nodes carrying `ComputeInstance`. |
| *_ont_private_ip_address* | Yes | Normalized private ip address for nodes carrying `ComputeInstance`. |
| *_ont_public_ip_address* | Yes | Normalized public ip address for nodes carrying `ComputeInstance`. |
| *_ont_region* | Yes | Normalized region for nodes carrying `ComputeInstance`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |
| *_ont_state* | Yes | Normalized state for nodes carrying `ComputeInstance`. |
| *_ont_type* | Yes | Normalized type for nodes carrying `ComputeInstance`. |

#### Relationships

- `(:BlockStorage)-[:ATTACHED_TO]->(:ComputeInstance)`

- `(:CVE)-[:AFFECTS]->(:ComputeInstance)`

- `(:ComputeInstance)-[:ASSUMES]->(:PermissionRole)`: `ASSUMES` is the canonical relationship name from `ComputeInstance` to `PermissionRole`. This constraint validates existing relationships and does not create them.

- `(:ComputeInstance)-[:LABELED]->(:Tag)`

- `(:ComputeInstance)-[:MEMBER_OF_EC2_SECURITY_GROUP]->(:NetworkAccessControl)`

- `(:ComputeInstance)-[:MEMBER_OF_EKS_CLUSTER]->(:ComputeCluster)`

- `(:ComputeInstance)-[:MEMBER_OF_GCP_VPC]->(:VirtualNetwork)`: generated by analysis job `GCP Instance to VPC derived relationship analysis`.

- `(:ComputeInstance)-[:MEMBER_OF_SCALEWAY_SECURITY_GROUP]->(:NetworkAccessControl)`

- `(:ComputeInstance)-[:MOUNTS]->(:BlockStorage)`

- `(:ComputeInstance)-[:PART_OF_SUBNET]->(:Subnet)`

- `(:ComputeInstance)-[:RESOURCE]->(:Tenant)`

- `(:ComputeInstance)-[:RUNS_AS]->(:ServiceAccount)`: `RUNS_AS` is the canonical relationship name from `ComputeInstance` to `ServiceAccount`. This constraint validates existing relationships and does not create them.

- `(:ComputeInstance)-[:STS_ASSUMEROLE_ALLOW]->(:PermissionRole)`: generated by analysis job `EC2 Instances assume IAM roles`.

- `(:ComputeInstance)-[:TAGGED]->(:Tag)`

- `(:ComputeInstance)-[:USES_SECRET]->(:Secret)`: `USES_SECRET` is the canonical relationship name from `ComputeInstance` to `Secret`. This constraint validates existing relationships and does not create them.

- `(:ComputeService)-[:HAS_DEV_SERVER]->(:ComputeInstance)`

- `(:DNSRecord)-[:DNS_POINTS_TO]->(:ComputeInstance)`: generated by analysis job `Ontology - DNSRecord to AWSEC2Instance linking`, `Ontology - DNSRecord to GCPInstance linking`.

- `(:LoadBalancer)-[:EXPOSE]->(:ComputeInstance)`: `EXPOSE` is the canonical relationship name from `LoadBalancer` to `ComputeInstance`. This constraint validates existing relationships and does not create them.
  - Properties:

    | Field | Description |
    |-------|-------------|
    | exposure_type | Property generated by analysis job: `Scaleway Load Balancer EXPOSE relationships`. |
    | port | Port on which the listener or target group receives traffic. |
    | protocol | Protocol used by the listener or target group. |
    | target_group_arn | ARN of the Elastic Load Balancing target group represented by this relationship. |

- `(:NetworkAccessControl)-[:FIREWALL_INGRESS]->(:ComputeInstance)`: generated by analysis job `GCP firewall ingress to instance analysis`.

- `(:PublicIP)-[:POINTS_TO]->(:ComputeInstance)`

- `(:SecurityIssue)-[:AFFECTS]->(:ComputeInstance)`

- `(:TailscaleDevice)-[:IS_INSTANCE]->(:ComputeInstance)`: generated by analysis job `Tailscale device to cloud instance linking`.

- `(:Tenant)-[:RESOURCE]->(:ComputeInstance)`

(ontology-computenamespace)=
### ComputeNamespace

A cross-provider ComputeNamespace resource in Cartography's ontology.

> **Semantic Label**: This label is applied directly to provider-specific nodes; it does not create a separate node.

> **Implementations**: `KubernetesNamespace`, `ScalewayServerlessContainerNamespace`, `ScalewayServerlessFunctionNamespace`.

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| *_ont_name* | Yes | Normalized name for nodes carrying `ComputeNamespace`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |
| *_ont_status* | Yes | Normalized status for nodes carrying `ComputeNamespace`. |

#### Relationships

- `(:ComputeCluster)-[:RESOURCE]->(:ComputeNamespace)`

- `(:ComputeNamespace)-[:CONTAINS]->(:ComputePod)`

- `(:ComputeNamespace)-[:CONTAINS]->(:Container)`

- `(:ComputeNamespace)-[:CONTAINS]->(:PermissionRole)`

- `(:ComputeNamespace)-[:CONTAINS]->(:Secret)`

- `(:ComputeNamespace)-[:CONTAINS]->(:ServiceAccount)`

- `(:ComputeNamespace)-[:HAS]->(:ComputeService)`

- `(:ComputeNamespace)-[:HAS]->(:Container)`

- `(:ComputeNamespace)-[:HAS]->(:Function)`

- `(:ComputeNamespace)-[:WORKLOAD_PARENT]->(:ComputeCluster)`: `WORKLOAD_PARENT` is the canonical relationship name from `ComputeNamespace` to `ComputeCluster`. This constraint validates existing relationships and does not create them.

- `(:ComputePod)-[:WORKLOAD_PARENT]->(:ComputeNamespace)`: `WORKLOAD_PARENT` is the canonical relationship name from `ComputePod` to `ComputeNamespace`. This constraint validates existing relationships and does not create them.

- `(:ComputeService)-[:WORKLOAD_PARENT]->(:ComputeNamespace)`

- `(:Tenant)-[:RESOURCE]->(:ComputeNamespace)`

(ontology-computepod)=
### ComputePod

A cross-provider ComputePod resource in Cartography's ontology.

> **Semantic Label**: This label is applied directly to provider-specific nodes; it does not create a separate node.

> **Implementations**: `AWSECSTask`, `AzureGroupContainer`, `KubernetesPod`, `ModalTask`.

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| *_ont_name* | Yes | Normalized name for nodes carrying `ComputePod`. |
| *_ont_namespace* | Yes | Normalized namespace for nodes carrying `ComputePod`. |
| *_ont_node* | Yes | Normalized node for nodes carrying `ComputePod`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |
| *_ont_status* | Yes | Normalized status for nodes carrying `ComputePod`. |

#### Relationships

- `(:ComputeCluster)-[:HAS_TASK]->(:ComputePod)`

- `(:ComputeCluster)-[:RESOURCE]->(:ComputePod)`

- `(:ComputeNamespace)-[:CONTAINS]->(:ComputePod)`

- `(:ComputePod)-[:ATTACHED_TO]->(:Subnet)`

- `(:ComputePod)-[:CONTAINS]->(:Container)`

- `(:ComputePod)-[:HAS_CONTAINER]->(:Container)`

- `(:ComputePod)-[:RUNS_AS]->(:ServiceAccount)`: `RUNS_AS` is the canonical relationship name from `ComputePod` to `ServiceAccount`. This constraint validates existing relationships and does not create them.

- `(:ComputePod)-[:TAGGED]->(:Tag)`

- `(:ComputePod)-[:USES_SECRET]->(:Secret)`: `USES_SECRET` is the canonical relationship name from `ComputePod` to `Secret`. This constraint validates existing relationships and does not create them.
  - Properties:

    | Field | Description |
    |-------|-------------|
    | mount_method | How the pod consumes the secret: volume, environment, or both. |

- `(:ComputePod)-[:USES_SECRET_ENV]->(:Secret)`

- `(:ComputePod)-[:USES_SECRET_VOLUME]->(:Secret)`

- `(:ComputePod)-[:USES_SERVICE_ACCOUNT]->(:ServiceAccount)`

- `(:ComputePod)-[:WORKLOAD_PARENT]->(:ComputeCluster)`: `WORKLOAD_PARENT` is the canonical relationship name from `ComputePod` to `ComputeCluster`. This constraint validates existing relationships and does not create them.

- `(:ComputePod)-[:WORKLOAD_PARENT]->(:ComputeNamespace)`: `WORKLOAD_PARENT` is the canonical relationship name from `ComputePod` to `ComputeNamespace`. This constraint validates existing relationships and does not create them.

- `(:ComputePod)-[:WORKLOAD_PARENT]->(:ComputeService)`: `WORKLOAD_PARENT` is the canonical relationship name from `ComputePod` to `ComputeService`. This constraint validates existing relationships and does not create them.

- `(:ComputeService)-[:HAS_TASK]->(:ComputePod)`

- `(:Container)-[:WORKLOAD_PARENT]->(:ComputePod)`: `WORKLOAD_PARENT` is the canonical relationship name from `Container` to `ComputePod`. This constraint validates existing relationships and does not create them.

- `(:LoadBalancer)-[:EXPOSE]->(:ComputePod)`: `EXPOSE` is the canonical relationship name from `LoadBalancer` to `ComputePod`. This constraint validates existing relationships and does not create them.
  - Properties:

    | Field | Description |
    |-------|-------------|
    | exposure_type | Property generated by analysis job: `Kubernetes LoadBalancer to pod EXPOSE relationships`. |

- `(:Tenant)-[:RESOURCE]->(:ComputePod)`

(ontology-computeservice)=
### ComputeService

A cross-provider ComputeService resource in Cartography's ontology.

> **Semantic Label**: This label is applied directly to provider-specific nodes; it does not create a separate node.

> **Implementations**: `AWSECSService`, `GCPCloudRunJob`, `GCPCloudRunService`, `KubernetesCronJob`, `KubernetesDaemonSet`, `KubernetesDeployment`, `KubernetesJob`, `KubernetesStatefulSet`, `ModalApp`, `NetlifySite`, `RailwayServiceInstance`, `ScalewayServerlessContainer`, `ScalewayWebHosting`, `SnowflakeService`.

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| *_ont_name* | Yes | Normalized name for nodes carrying `ComputeService`. |
| *_ont_region* | Yes | Normalized region for nodes carrying `ComputeService`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |
| *_ont_status* | Yes | Normalized status for nodes carrying `ComputeService`. |

#### Relationships

- `(:ComputeCluster)-[:HAS_SERVICE]->(:ComputeService)`

- `(:ComputeCluster)-[:RESOURCE]->(:ComputeService)`

- `(:ComputeNamespace)-[:HAS]->(:ComputeService)`

- `(:ComputePod)-[:WORKLOAD_PARENT]->(:ComputeService)`: `WORKLOAD_PARENT` is the canonical relationship name from `ComputePod` to `ComputeService`. This constraint validates existing relationships and does not create them.

- `(:ComputeService)-[:CONTAINS]->(:Container)`

- `(:ComputeService)-[:DEPLOYED_FROM]->(:CodeRepository)`

- `(:ComputeService)-[:EXPOSE]->(:DNSZone)`

- `(:ComputeService)-[:HAS_CERTIFICATE]->(:Certificate)`

- `(:ComputeService)-[:HAS_DATABASE_BRANCH]->(:Database)`

- `(:ComputeService)-[:HAS_DEV_SERVER]->(:ComputeInstance)`

- `(:ComputeService)-[:HAS_DNS_ZONE]->(:DNSZone)`

- `(:ComputeService)-[:HAS_ENV_VAR]->(:Secret)`

- `(:ComputeService)-[:HAS_FUNCTION]->(:Function)`

- `(:ComputeService)-[:HAS_IMAGE]->(:Image)`

- `(:ComputeService)-[:HAS_RUNTIME_IMAGE]->(:Image)`: generated by analysis job `Workload HAS_RUNTIME_IMAGE inventory analysis`.
  - Properties:

    | Field | Description |
    |-------|-------------|
    | exposed_internet | Property generated by analysis job: `Workload HAS_RUNTIME_IMAGE inventory analysis`. |

- `(:ComputeService)-[:HAS_SERVICE_INSTANCE]->(:ThirdPartyApp)`

- `(:ComputeService)-[:HAS_TASK]->(:ComputePod)`

- `(:ComputeService)-[:LABELED]->(:Tag)`

- `(:ComputeService)-[:MOUNTS]->(:BlockStorage)`

- `(:ComputeService)-[:RUNS_AS]->(:ServiceAccount)`: `RUNS_AS` is the canonical relationship name from `ComputeService` to `ServiceAccount`. This constraint validates existing relationships and does not create them.

- `(:ComputeService)-[:TAGGED]->(:Tag)`

- `(:ComputeService)-[:USES_SECRET]->(:Secret)`

- `(:ComputeService)-[:USES_SERVICE_ACCOUNT]->(:ServiceAccount)`

- `(:ComputeService)-[:USES_WAREHOUSE]->(:ComputeCluster)`

- `(:ComputeService)-[:WORKLOAD_PARENT]->(:ComputeCluster)`: `WORKLOAD_PARENT` is the canonical relationship name from `ComputeService` to `ComputeCluster`. This constraint validates existing relationships and does not create them.

- `(:ComputeService)-[:WORKLOAD_PARENT]->(:ComputeNamespace)`

- `(:ComputeService)-[:WORKLOAD_PARENT]->(:ComputeService)`

- `(:Container)-[:WORKLOAD_PARENT]->(:ComputeService)`: `WORKLOAD_PARENT` is the canonical relationship name from `Container` to `ComputeService`. This constraint validates existing relationships and does not create them.

- `(:Function)-[:WORKLOAD_PARENT]->(:ComputeService)`

- `(:Tenant)-[:RESOURCE]->(:ComputeService)`

(ontology-container)=
### Container

A cross-provider Container resource in Cartography's ontology.

> **Semantic Label**: This label is applied directly to provider-specific nodes; it does not create a separate node.

> **Implementations**: `AWSECSContainer`, `AzureContainerInstance`, `GCPCloudRunJobContainer`, `GCPCloudRunServiceContainer`, `KubernetesContainer`, `ModalSandbox`, `RailwayDeployment`, `ScalewayServerlessContainer`, `SnowflakeServiceContainer`.

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| *_ont_cpu* | Yes | Normalized cpu for nodes carrying `Container`. |
| *_ont_health_status* | Yes | Normalized health status for nodes carrying `Container`. |
| *_ont_image* | Yes | Normalized image for nodes carrying `Container`. |
| *_ont_image_digest* | Yes | Normalized image digest for nodes carrying `Container`. |
| *_ont_memory* | Yes | Normalized memory for nodes carrying `Container`. |
| *_ont_name* | Yes | Normalized name for nodes carrying `Container`. |
| *_ont_namespace* | Yes | Normalized namespace for nodes carrying `Container`. |
| *_ont_region* | Yes | Normalized region for nodes carrying `Container`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |
| *_ont_state* | Yes | Normalized state for nodes carrying `Container`. |

#### Relationships

- `(:ComputeCluster)-[:RESOURCE]->(:Container)`

- `(:ComputeNamespace)-[:CONTAINS]->(:Container)`

- `(:ComputeNamespace)-[:HAS]->(:Container)`

- `(:ComputePod)-[:CONTAINS]->(:Container)`

- `(:ComputePod)-[:HAS_CONTAINER]->(:Container)`

- `(:ComputeService)-[:CONTAINS]->(:Container)`

- `(:Container)-[:HAS_IMAGE]->(:Image)`

- `(:Container)-[:HAS_IMAGE]->(:ImageAttestation)`

- `(:Container)-[:HAS_IMAGE]->(:ImageManifestList)`

- `(:Container)-[:RESOLVED_IMAGE]->(:Image)`: `RESOLVED_IMAGE` is the canonical relationship name from `Container` to `Image`. This constraint validates existing relationships and does not create them.

- `(:Container)-[:TAGGED]->(:Tag)`

- `(:Container)-[:WORKLOAD_PARENT]->(:ComputePod)`: `WORKLOAD_PARENT` is the canonical relationship name from `Container` to `ComputePod`. This constraint validates existing relationships and does not create them.

- `(:Container)-[:WORKLOAD_PARENT]->(:ComputeService)`: `WORKLOAD_PARENT` is the canonical relationship name from `Container` to `ComputeService`. This constraint validates existing relationships and does not create them.

- `(:LoadBalancer)-[:EXPOSE]->(:Container)`: `EXPOSE` is the canonical relationship name from `LoadBalancer` to `Container`. This constraint validates existing relationships and does not create them.
  - Properties:

    | Field | Description |
    |-------|-------------|
    | exposure_type | Property generated by analysis job: `Kubernetes LoadBalancer to container EXPOSE relationships`. |

- `(:Tenant)-[:RESOURCE]->(:Container)`

(ontology-containerregistry)=
### ContainerRegistry

A cross-provider ContainerRegistry resource in Cartography's ontology.

> **Semantic Label**: This label is applied directly to provider-specific nodes; it does not create a separate node.

> **Implementations**: `AWSECRRepository`, `GCPArtifactRegistryRepository`, `GitHubPackage`, `GitLabContainerRepository`, `ScalewayContainerRegistryNamespace`, `SnowflakeImageRepository`.

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| *_ont_created_at* | Yes | Normalized created at for nodes carrying `ContainerRegistry`. |
| *_ont_location* | Yes | Normalized location for nodes carrying `ContainerRegistry`. |
| *_ont_name* | Yes | Normalized name for nodes carrying `ContainerRegistry`. |
| *_ont_size_bytes* | Yes | Normalized size bytes for nodes carrying `ContainerRegistry`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |
| *_ont_uri* | Yes | Normalized uri for nodes carrying `ContainerRegistry`. |

#### Relationships

- `(:CVE)-[:AFFECTS]->(:ContainerRegistry)`

- `(:CodeRepository)-[:HAS_PACKAGE]->(:ContainerRegistry)`

- `(:ContainerRegistry)-[:CONTAINS]->(:Image)`

- `(:ContainerRegistry)-[:CONTAINS]->(:ImageTag)`

- `(:ContainerRegistry)-[:HAS_IMAGE]->(:Image)`

- `(:ContainerRegistry)-[:HAS_IMAGE]->(:ImageManifestList)`

- `(:ContainerRegistry)-[:HAS_TAG]->(:ImageTag)`

- `(:ContainerRegistry)-[:REPO_IMAGE]->(:ImageTag)`

- `(:ContainerRegistry)-[:TAGGED]->(:Tag)`

- `(:SecurityIssue)-[:AFFECTS]->(:ContainerRegistry)`

- `(:Tenant)-[:RESOURCE]->(:ContainerRegistry)`

(ontology-cve)=
### CVE

A cross-provider CVE resource in Cartography's ontology.

> **Semantic Label**: This label is applied directly to provider-specific nodes; it does not create a separate node.

> **Implementations**: `AWSInspectorFinding`, `CVE`, `CrowdstrikeFinding`, `GitHubDependabotAlert`, `S1AppFinding`, `SemgrepSCAFinding`, `TenableFinding`, `TrivyImageFinding`, `UbuntuCVE`, `WizFinding`.

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| *_ont_assigner* | Yes | Normalized assigner for nodes carrying `CVE`. |
| *_ont_attack_complexity* | Yes | Normalized attack complexity for nodes carrying `CVE`. |
| *_ont_attack_vector* | Yes | Normalized attack vector for nodes carrying `CVE`. |
| *_ont_availability_impact* | Yes | Normalized availability impact for nodes carrying `CVE`. |
| *_ont_base_score* | Yes | Normalized base score for nodes carrying `CVE`. |
| *_ont_base_severity* | Yes | Normalized base severity for nodes carrying `CVE`. |
| *_ont_confidentiality_impact* | Yes | Normalized confidentiality impact for nodes carrying `CVE`. |
| *_ont_cve_id* | Yes | Normalized cve id for nodes carrying `CVE`. |
| *_ont_description* |  | Normalized description for nodes carrying `CVE`. |
| *_ont_exploitability_score* | Yes | Normalized exploitability score for nodes carrying `CVE`. |
| *_ont_first_seen* | Yes | Normalized first seen for nodes carrying `CVE`. |
| *_ont_impact_score* | Yes | Normalized impact score for nodes carrying `CVE`. |
| *_ont_integrity_impact* | Yes | Normalized integrity impact for nodes carrying `CVE`. |
| *_ont_last_modified_date* | Yes | Normalized last modified date for nodes carrying `CVE`. |
| *_ont_privileges_required* | Yes | Normalized privileges required for nodes carrying `CVE`. |
| *_ont_problem_types* |  | Normalized problem types for nodes carrying `CVE`. |
| *_ont_published_date* | Yes | Normalized published date for nodes carrying `CVE`. |
| *_ont_references* |  | Normalized references for nodes carrying `CVE`. |
| *_ont_scope* | Yes | Normalized scope for nodes carrying `CVE`. |
| *_ont_severity* | Yes | Normalized severity for nodes carrying `CVE`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |
| *_ont_status* | Yes | Normalized status for nodes carrying `CVE`. |
| *_ont_title* | Yes | Normalized title for nodes carrying `CVE`. |
| *_ont_user_interaction* | Yes | Normalized user interaction for nodes carrying `CVE`. |
| *_ont_vector_string* | Yes | Normalized vector string for nodes carrying `CVE`. |
| *_ont_vuln_status* | Yes | Normalized vuln status for nodes carrying `CVE`. |

#### Relationships

- `(:CVE)-[:AFFECTS]->(:ComputeInstance)`

- `(:CVE)-[:AFFECTS]->(:ContainerRegistry)`

- `(:CVE)-[:AFFECTS]->(:Device)`: generated by analysis job `Ontology - CrowdstrikeFinding AFFECTS Device linking`, `Ontology - S1AppFinding AFFECTS Device linking`.

- `(:CVE)-[:AFFECTS]->(:Image)`

- `(:CVE)-[:AFFECTS]->(:ImageAttestation)`

- `(:CVE)-[:AFFECTS]->(:ImageManifestList)`

- `(:CVE)-[:AFFECTS]->(:PackageVersion)`: `AFFECTS` is the canonical relationship name from `CVE` to `PackageVersion`. This constraint validates existing relationships and does not create them.

- `(:CVE)-[:ASSIGNED_TO]->(:UserAccount)`

- `(:CVE)-[:DISMISSED_BY]->(:UserAccount)`

- `(:CVE)-[:FOUND_IN]->(:CodeRepository)`

- `(:CVE)-[:LINKED_TO]->(:CVE)`

- `(:CVE)-[:LINKED_TO]->(:SecurityIssue)`

- `(:SecurityIssue)-[:LINKED_TO]->(:CVE)`

- `(:Tenant)-[:MEMBER]->(:CVE)`

- `(:Tenant)-[:RESOURCE]->(:CVE)`

(ontology-database)=
### Database

A cross-provider Database resource in Cartography's ontology.

> **Semantic Label**: This label is applied directly to provider-specific nodes; it does not create a separate node.

> **Implementations**: `AWSDynamoDBTable`, `AWSESDomain`, `AWSRDSInstance`, `AzureCosmosDBCassandraKeyspace`, `AzureCosmosDBMongoDBDatabase`, `AzureCosmosDBSqlDatabase`, `AzureSQLDatabase`, `DatabricksCatalog`, `DatabricksSchema`, `DatabricksTable`, `GCPBigQueryDataset`, `GCPBigtableInstance`, `GCPCloudSQLInstance`, `NetlifyDatabaseBranch`, `ScalewayDataWarehouseDeployment`, `ScalewayMongoDBInstance`, `ScalewayRdbInstance`, `ScalewayRedisCluster`, `ScalewaySearchDeployment`, `ScalewayServerlessSQLDatabase`, `SnowflakeDatabase`, `SupabaseDatabase`.

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| *_ont_encrypted* | Yes | Normalized encrypted for nodes carrying `Database`. |
| *_ont_endpoint* | Yes | Normalized endpoint for nodes carrying `Database`. |
| *_ont_location* | Yes | Normalized location for nodes carrying `Database`. |
| *_ont_name* | Yes | Normalized name for nodes carrying `Database`. |
| *_ont_port* | Yes | Normalized port for nodes carrying `Database`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |
| *_ont_type* | Yes | Normalized type for nodes carrying `Database`. |
| *_ont_version* | Yes | Normalized version for nodes carrying `Database`. |

#### Relationships

- `(:ComputeService)-[:HAS_DATABASE_BRANCH]->(:Database)`

- `(:DNSRecord)-[:DNS_POINTS_TO]->(:Database)`

- `(:Database)-[:ASSOCIATED_WITH]->(:VirtualNetwork)`

- `(:Database)-[:BACKED_BY]->(:ObjectStorage)`

- `(:Database)-[:CONTAINS]->(:Database)`

- `(:Database)-[:CONTAINS]->(:ObjectStorage)`

- `(:Database)-[:CONTAINS]->(:PermissionRole)`

- `(:Database)-[:ENCRYPTED_BY]->(:EncryptionKey)`: `ENCRYPTED_BY` is the canonical relationship name from `Database` to `EncryptionKey`. This constraint validates existing relationships and does not create them.

- `(:Database)-[:HAS_SNAPSHOT]->(:Snapshot)`

- `(:Database)-[:IS_READ_REPLICA_OF]->(:Database)`

- `(:Database)-[:LABELED]->(:Tag)`

- `(:Database)-[:MEMBER_OF_EC2_SECURITY_GROUP]->(:NetworkAccessControl)`

- `(:Database)-[:PART_OF_SUBNET]->(:Subnet)`

- `(:Database)-[:TAGGED]->(:Tag)`

- `(:Database)-[:USES_SERVICE_ACCOUNT]->(:ServiceAccount)`

- `(:SecurityIssue)-[:AFFECTS]->(:Database)`

- `(:Snapshot)-[:IS_SNAPSHOT_SOURCE]->(:Database)`

- `(:Tenant)-[:RESOURCE]->(:Database)`

(ontology-device)=
### Device

A canonical physical or virtual device aggregated across providers.

> **Abstract Ontology Node**: This is a dedicated canonical node created separately from provider-specific nodes.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Canonical device identifier. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| hostname | Yes | Device hostname. |
| instance_id |  | Provider-specific instance identifier when available. |
| manufacturer |  | Device manufacturer. |
| model |  | Device model. |
| os |  | Operating system name. |
| os_version |  | Operating system version. |
| platform |  | Platform or device family reported by the source. |
| serial_number | Yes | Device serial number. |

#### Relationships

- `(:CVE)-[:AFFECTS]->(:Device)`: generated by analysis job `Ontology - CrowdstrikeFinding AFFECTS Device linking`, `Ontology - S1AppFinding AFFECTS Device linking`.

- `(:Device)-[:OBSERVED_AS]->(:BigfixComputer)`

- `(:Device)-[:OBSERVED_AS]->(:CrowdstrikeHost)`

- `(:Device)-[:OBSERVED_AS]->(:DuoEndpoint)`

- `(:Device)-[:OBSERVED_AS]->(:DuoPhone)`

- `(:Device)-[:OBSERVED_AS]->(:GoogleWorkspaceDevice)`

- `(:Device)-[:OBSERVED_AS]->(:IntuneManagedDevice)`

- `(:Device)-[:OBSERVED_AS]->(:JamfComputer)`

- `(:Device)-[:OBSERVED_AS]->(:JamfMobileDevice)`

- `(:Device)-[:OBSERVED_AS]->(:JumpCloudSystem)`

- `(:Device)-[:OBSERVED_AS]->(:KandjiDevice)`

- `(:Device)-[:OBSERVED_AS]->(:MiradoreDevice)`

- `(:Device)-[:OBSERVED_AS]->(:S1Agent)`: Links a canonical device to its SentinelOne agent, matched on hostname when no serial number is available. Links a canonical device to its SentinelOne agent, matched on serial number.

- `(:Device)-[:OBSERVED_AS]->(:SnipeitAsset)`

- `(:Device)-[:OBSERVED_AS]->(:TailscaleDevice)`

- `(:PublicIP)-[:POINTS_TO]->(:Device)`: generated by analysis job `Ontology - PublicIP POINTS_TO Device linking`.

- `(:User)-[:OWNS]->(:Device)`: generated by analysis job `Ontology - Devices OWNS relationship linking`.

(ontology-dnsrecord)=
### DNSRecord

A cross-provider DNSRecord resource in Cartography's ontology.

> **Semantic Label**: This label is applied directly to provider-specific nodes; it does not create a separate node.

> **Implementations**: `AWSDNSRecord`, `BbotDNSName`, `CloudflareDNSRecord`, `GCPRecordSet`, `NetlifyDNSRecord`, `ScalewayDnsRecord`, `SupabaseCustomHostname`, `VercelDNSRecord`.

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| *_ont_name* | Yes | Normalized name for nodes carrying `DNSRecord`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |
| *_ont_type* | Yes | Normalized type for nodes carrying `DNSRecord`. |
| *_ont_value* | Yes | Normalized value for nodes carrying `DNSRecord`. |

#### Relationships

- `(:DNSRecord)-[:DISCOVERED_FROM]->(:DNSRecord)`

- `(:DNSRecord)-[:DISCOVERED_FROM]->(:SecurityIssue)`

- `(:DNSRecord)-[:DNS_POINTS_TO]->(:AWSCloudFrontDistribution)`: generated by analysis job `Ontology - DNSRecord to AWSCloudFrontDistribution linking`.

- `(:DNSRecord)-[:DNS_POINTS_TO]->(:AzureAppService)`: generated by analysis job `Ontology - DNSRecord to AzureAppService linking`.

- `(:DNSRecord)-[:DNS_POINTS_TO]->(:ComputeInstance)`: generated by analysis job `Ontology - DNSRecord to AWSEC2Instance linking`, `Ontology - DNSRecord to GCPInstance linking`.

- `(:DNSRecord)-[:DNS_POINTS_TO]->(:DNSRecord)`

- `(:DNSRecord)-[:DNS_POINTS_TO]->(:Database)`

- `(:DNSRecord)-[:DNS_POINTS_TO]->(:Function)`: generated by analysis job `Ontology - DNSRecord to AzureFunctionApp linking`.

- `(:DNSRecord)-[:DNS_POINTS_TO]->(:KubernetesIngress)`: generated by analysis job `Ontology - DNSRecord to KubernetesIngress linking`.

- `(:DNSRecord)-[:DNS_POINTS_TO]->(:LoadBalancer)`: generated by analysis job `Ontology - DNSRecord to AWSLoadBalancer linking`, `Ontology - DNSRecord to AWSLoadBalancerV2 linking`.

- `(:DNSRecord)-[:MATCHES_DNS_RECORD]->(:DNSRecord)`: generated by analysis job `Ontology - BbotDNSName to provider DNSRecord linking`.

- `(:DNSRecord)-[:MEMBER_OF_DNS_ZONE]->(:DNSZone)`

- `(:DNSRecord)-[:POINTS_TO]->(:Tenant)`

- `(:DNSRecord)-[:RESOLVES_TO]->(:DNSRecord)`

- `(:DNSZone)-[:HAS_DNS_RECORD]->(:DNSRecord)`

- `(:DNSZone)-[:HAS_RECORD]->(:DNSRecord)`

- `(:DNSZone)-[:RESOURCE]->(:DNSRecord)`

- `(:SecurityIssue)-[:AFFECTS]->(:DNSRecord)`

- `(:SecurityIssue)-[:DISCOVERED_FROM]->(:DNSRecord)`

- `(:Tenant)-[:RESOURCE]->(:DNSRecord)`

(ontology-dnszone)=
### DNSZone

A cross-provider DNSZone resource in Cartography's ontology.

> **Semantic Label**: This label is applied directly to provider-specific nodes; it does not create a separate node.

> **Implementations**: `AWSDNSZone`, `CloudflareZone`, `GCPDNSZone`, `NetlifyDNSZone`, `ScalewayDnsZone`.

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| *_ont_name* | Yes | Normalized name for nodes carrying `DNSZone`. |
| *_ont_public* | Yes | Normalized public for nodes carrying `DNSZone`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |

#### Relationships

- `(:ComputeService)-[:EXPOSE]->(:DNSZone)`

- `(:ComputeService)-[:HAS_DNS_ZONE]->(:DNSZone)`

- `(:DNSRecord)-[:MEMBER_OF_DNS_ZONE]->(:DNSZone)`

- `(:DNSZone)-[:HAS_DNS_RECORD]->(:DNSRecord)`

- `(:DNSZone)-[:HAS_R2_CUSTOM_DOMAIN]->(:ObjectStorage)`

- `(:DNSZone)-[:HAS_RECORD]->(:DNSRecord)`

- `(:DNSZone)-[:HAS_RULESET]->(:NetworkAccessControl)`

- `(:DNSZone)-[:LABELED]->(:Tag)`

- `(:DNSZone)-[:RESOURCE]->(:DNSRecord)`

- `(:DNSZone)-[:SUBZONE]->(:DNSZone)`

- `(:DNSZone)-[:TAGGED]->(:Tag)`

- `(:Tenant)-[:RESOURCE]->(:DNSZone)`

(ontology-encryptionkey)=
### EncryptionKey

A cross-provider EncryptionKey resource in Cartography's ontology.

> **Semantic Label**: This label is applied directly to provider-specific nodes; it does not create a separate node.

> **Implementations**: `AWSKMSKey`, `AzureKeyVaultKey`, `GCPCryptoKey`, `ScalewayKey`.

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| *_ont_enabled* | Yes | Normalized enabled for nodes carrying `EncryptionKey`. |
| *_ont_key_type* | Yes | Normalized key type for nodes carrying `EncryptionKey`. |
| *_ont_name* | Yes | Normalized name for nodes carrying `EncryptionKey`. |
| *_ont_rotation_enabled* | Yes | Normalized rotation enabled for nodes carrying `EncryptionKey`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |

#### Relationships

- `(:Database)-[:ENCRYPTED_BY]->(:EncryptionKey)`: `ENCRYPTED_BY` is the canonical relationship name from `Database` to `EncryptionKey`. This constraint validates existing relationships and does not create them.

- `(:EncryptionKey)-[:TAGGED]->(:Tag)`

- `(:FileStorage)-[:ENCRYPTED_BY]->(:EncryptionKey)`: `ENCRYPTED_BY` is the canonical relationship name from `FileStorage` to `EncryptionKey`. This constraint validates existing relationships and does not create them.

- `(:ObjectStorage)-[:ENCRYPTED_BY]->(:EncryptionKey)`: `ENCRYPTED_BY` is the canonical relationship name from `ObjectStorage` to `EncryptionKey`. This constraint validates existing relationships and does not create them.

- `(:Secret)-[:ENCRYPTED_BY]->(:EncryptionKey)`: `ENCRYPTED_BY` is the canonical relationship name from `Secret` to `EncryptionKey`. This constraint validates existing relationships and does not create them.

- `(:Tenant)-[:RESOURCE]->(:EncryptionKey)`

(ontology-filestorage)=
### FileStorage

A cross-provider FileStorage resource in Cartography's ontology.

> **Semantic Label**: This label is applied directly to provider-specific nodes; it does not create a separate node.

> **Implementations**: `AWSEfsFileSystem`, `AzureStorageFileShare`, `ModalNetworkFileSystem`, `ModalVolume`, `ScalewayFileSystem`, `SnowflakeStage`.

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| *_ont_encrypted* | Yes | Normalized encrypted for nodes carrying `FileStorage`. |
| *_ont_location* | Yes | Normalized location for nodes carrying `FileStorage`. |
| *_ont_name* | Yes | Normalized name for nodes carrying `FileStorage`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |

#### Relationships

- `(:FileStorage)-[:BACKED_BY]->(:ObjectStorage)`

- `(:FileStorage)-[:CREATED_BY]->(:UserAccount)`

- `(:FileStorage)-[:ENCRYPTED_BY]->(:EncryptionKey)`: `ENCRYPTED_BY` is the canonical relationship name from `FileStorage` to `EncryptionKey`. This constraint validates existing relationships and does not create them.

- `(:Tenant)-[:RESOURCE]->(:FileStorage)`

(ontology-function)=
### Function

A cross-provider Function resource in Cartography's ontology.

> **Semantic Label**: This label is applied directly to provider-specific nodes; it does not create a separate node.

> **Implementations**: `AWSLambda`, `AzureFunctionApp`, `CloudflareWorkerScript`, `GCPCloudFunction`, `ModalFunction`, `NetlifyFunction`, `ScalewayServerlessFunction`, `SnowflakeFunction`, `SnowflakeProcedure`, `SupabaseEdgeFunction`.

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| *_ont_deployment_type* | Yes | Normalized deployment type for nodes carrying `Function`. |
| *_ont_image* | Yes | Normalized image for nodes carrying `Function`. |
| *_ont_image_digest* | Yes | Normalized image digest for nodes carrying `Function`. |
| *_ont_memory* | Yes | Normalized memory for nodes carrying `Function`. |
| *_ont_name* | Yes | Normalized name for nodes carrying `Function`. |
| *_ont_runtime* | Yes | Normalized runtime for nodes carrying `Function`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |
| *_ont_timeout* | Yes | Normalized timeout for nodes carrying `Function`. |

#### Relationships

- `(:ComputeNamespace)-[:HAS]->(:Function)`

- `(:ComputeService)-[:HAS_FUNCTION]->(:Function)`

- `(:DNSRecord)-[:DNS_POINTS_TO]->(:Function)`: generated by analysis job `Ontology - DNSRecord to AzureFunctionApp linking`.

- `(:Function)-[:ASSUMES]->(:PermissionRole)`: `ASSUMES` is the canonical relationship name from `Function` to `PermissionRole`. This constraint validates existing relationships and does not create them.

- `(:Function)-[:HAS]->(:Image)`: generated by analysis job `Lambda functions with ECR images`.

- `(:Function)-[:HAS]->(:ImageAttestation)`: generated by analysis job `Lambda functions with ECR images`.

- `(:Function)-[:HAS]->(:ImageManifestList)`: generated by analysis job `Lambda functions with ECR images`.

- `(:Function)-[:HAS_IMAGE]->(:Image)`

- `(:Function)-[:HAS_IMAGE]->(:ImageAttestation)`

- `(:Function)-[:HAS_IMAGE]->(:ImageManifestList)`

- `(:Function)-[:LABELED]->(:Tag)`

- `(:Function)-[:RESOLVED_IMAGE]->(:Image)`: `RESOLVED_IMAGE` is the canonical relationship name from `Function` to `Image`. This constraint validates existing relationships and does not create them.

- `(:Function)-[:RUNS_AS]->(:ServiceAccount)`: `RUNS_AS` is the canonical relationship name from `Function` to `ServiceAccount`. This constraint validates existing relationships and does not create them.

- `(:Function)-[:TAGGED]->(:Tag)`

- `(:Function)-[:USES_SECRET]->(:Secret)`: `USES_SECRET` is the canonical relationship name from `Function` to `Secret`. This constraint validates existing relationships and does not create them.

- `(:Function)-[:WORKLOAD_PARENT]->(:ComputeService)`

- `(:LoadBalancer)-[:EXPOSE]->(:Function)`: `EXPOSE` is the canonical relationship name from `LoadBalancer` to `Function`. This constraint validates existing relationships and does not create them.
  - Properties:

    | Field | Description |
    |-------|-------------|
    | port | Port on which the listener or target group receives traffic. |
    | protocol | Protocol used by the listener or target group. |
    | target_group_arn | ARN of the Elastic Load Balancing target group represented by this relationship. |

- `(:Tenant)-[:RESOURCE]->(:Function)`

(ontology-identityprovider)=
### IdentityProvider

A cross-provider IdentityProvider resource in Cartography's ontology.

> **Semantic Label**: This label is applied directly to provider-specific nodes; it does not create a separate node.

> **Implementations**: `AWSSAMLProvider`, `GCPWorkloadIdentityProvider`, `KeycloakIdentityProvider`, `KubernetesOIDCProvider`, `SnowflakeSecurityIntegration`, `SupabaseSSOProvider`, `SupabaseThirdPartyAuthIntegration`.

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| *_ont_enabled* | Yes | Normalized enabled for nodes carrying `IdentityProvider`. |
| *_ont_issuer* | Yes | Normalized issuer for nodes carrying `IdentityProvider`. |
| *_ont_name* | Yes | Normalized name for nodes carrying `IdentityProvider`. |
| *_ont_protocol* | Yes | Normalized protocol for nodes carrying `IdentityProvider`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |

#### Relationships

- `(:ComputeCluster)-[:RESOURCE]->(:IdentityProvider)`

- `(:ComputeCluster)-[:TRUSTS]->(:IdentityProvider)`

- `(:IdentityProvider)-[:GOVERNED_BY]->(:NetworkAccessControl)`

- `(:IdentityProvider)-[:RUNS_AS_ROLE]->(:PermissionRole)`

- `(:Secret)-[:USES_INTEGRATION]->(:IdentityProvider)`

- `(:Tenant)-[:RESOURCE]->(:IdentityProvider)`

- `(:UserAccount)-[:HAS_IDENTITY]->(:IdentityProvider)`

(ontology-image)=
### Image

A concrete single-platform container image.

> **Semantic Label**: This label is applied directly to provider-specific nodes; it does not create a separate node.

> **Implementations**: `AWSECRImage`, `GCPArtifactRegistryImage`, `GitHubContainerImage`, `GitLabContainerImage`, `ScalewayContainerRegistryImage`, `SnowflakeImage`.

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| *_ont_architecture* | Yes | Normalized architecture for nodes carrying `Image`. |
| *_ont_digest* | Yes | Normalized digest for nodes carrying `Image`. |
| *_ont_os* | Yes | Normalized os for nodes carrying `Image`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |
| *_ont_uri* | Yes | Normalized uri for nodes carrying `Image`. |
| *_ont_variant* | Yes | Normalized variant for nodes carrying `Image`. |

#### Relationships

- `(:AIModel)-[:DETECTED_IN]->(:Image)`

- `(:CVE)-[:AFFECTS]->(:Image)`

- `(:ComputeService)-[:HAS_IMAGE]->(:Image)`

- `(:ComputeService)-[:HAS_RUNTIME_IMAGE]->(:Image)`: generated by analysis job `Workload HAS_RUNTIME_IMAGE inventory analysis`.
  - Properties:

    | Field | Description |
    |-------|-------------|
    | exposed_internet | Property generated by analysis job: `Workload HAS_RUNTIME_IMAGE inventory analysis`. |

- `(:Container)-[:HAS_IMAGE]->(:Image)`

- `(:Container)-[:RESOLVED_IMAGE]->(:Image)`: `RESOLVED_IMAGE` is the canonical relationship name from `Container` to `Image`. This constraint validates existing relationships and does not create them.

- `(:ContainerRegistry)-[:CONTAINS]->(:Image)`

- `(:ContainerRegistry)-[:HAS_IMAGE]->(:Image)`

- `(:Function)-[:HAS]->(:Image)`: generated by analysis job `Lambda functions with ECR images`.

- `(:Function)-[:HAS_IMAGE]->(:Image)`

- `(:Function)-[:RESOLVED_IMAGE]->(:Image)`: `RESOLVED_IMAGE` is the canonical relationship name from `Function` to `Image`. This constraint validates existing relationships and does not create them.

- `(:Image)-[:ATTESTS]->(:Image)`

- `(:Image)-[:ATTESTS]->(:ImageAttestation)`

- `(:Image)-[:ATTESTS]->(:ImageManifestList)`

- `(:Image)-[:BUILT_FROM]->(:Image)`
  - Properties:

    | Field | Description |
    |-------|-------------|
    | confidence | Confidence score for the parent image match. |
    | from_attestation | Whether the parent image was identified from an attestation. |
    | from_sbom | Match-method flag set when parent-image evidence comes from a digest-verified SPDX SBOM relationship. |
    | parent_image_uri | Parent image reference reported by provenance. |

- `(:Image)-[:BUILT_FROM]->(:ImageAttestation)`
  - Properties:

    | Field | Description |
    |-------|-------------|
    | confidence | Parent-image evidence strength; digest-verified SBOM matches use `explicit`. |
    | from_attestation | Whether the parent image relationship was derived from a provenance attestation. |
    | from_sbom | Match-method flag set when parent-image evidence comes from a digest-verified SPDX SBOM relationship. |
    | parent_image_uri | Parent image URI extracted from a digest-verified SPDX SBOM relationship. |

- `(:Image)-[:BUILT_FROM]->(:ImageManifestList)`
  - Properties:

    | Field | Description |
    |-------|-------------|
    | confidence | Confidence score for the parent image match. |
    | from_attestation | Whether the parent image was identified from an attestation. |
    | from_sbom | Match-method flag set when parent-image evidence comes from a digest-verified SPDX SBOM relationship. |
    | parent_image_uri | Parent image reference reported by provenance. |

- `(:Image)-[:CONTAINS_IMAGE]->(:Image)`

- `(:Image)-[:CONTAINS_IMAGE]->(:ImageAttestation)`

- `(:Image)-[:CONTAINS_IMAGE]->(:ImageManifestList)`

- `(:Image)-[:HAS_LAYER]->(:ImageLayer)`

- `(:Image)-[:HEAD]->(:ImageLayer)`

- `(:Image)-[:PACKAGED_BY]->(:CICDPipeline)`

- `(:Image)-[:PACKAGED_FROM]->(:CodeRepository)`: `PACKAGED_FROM` is the canonical relationship name from `Image` to `CodeRepository`. This constraint validates existing relationships and does not create them.
  - Properties:

    | Field | Description |
    |-------|-------------|
    | command_similarity | Similarity score between image build commands and Dockerfile commands. |
    | confidence | Confidence score for the image-to-project match. |
    | dockerfile_path | Path of the Dockerfile associated with the image. |
    | match_method | Matching method: provenance, dockerfile_analysis, or dockerfile_singleton_fallback. |
    | matched_commands | Number of image build commands matched to Dockerfile commands. |
    | total_commands | Command count used to normalize the Dockerfile comparison. |

- `(:Image)-[:TAIL]->(:ImageLayer)`

- `(:ImageAttestation)-[:ATTESTS]->(:Image)`

- `(:ImageAttestation)-[:BUILT_FROM]->(:Image)`
  - Properties:

    | Field | Description |
    |-------|-------------|
    | confidence | Parent-image evidence strength; digest-verified SBOM matches use `explicit`. |
    | from_attestation | Whether the parent image relationship was derived from a provenance attestation. |
    | from_sbom | Match-method flag set when parent-image evidence comes from a digest-verified SPDX SBOM relationship. |
    | parent_image_uri | Parent image URI extracted from a digest-verified SPDX SBOM relationship. |

- `(:ImageAttestation)-[:CONTAINS_IMAGE]->(:Image)`

- `(:ImageManifestList)-[:ATTESTS]->(:Image)`

- `(:ImageManifestList)-[:BUILT_FROM]->(:Image)`
  - Properties:

    | Field | Description |
    |-------|-------------|
    | confidence | Confidence score for the parent image match. |
    | from_attestation | Whether the parent image was identified from an attestation. |
    | from_sbom | Match-method flag set when parent-image evidence comes from a digest-verified SPDX SBOM relationship. |
    | parent_image_uri | Parent image reference reported by provenance. |

- `(:ImageManifestList)-[:CONTAINS_IMAGE]->(:Image)`

- `(:ImageTag)-[:IMAGE]->(:Image)`

- `(:ImageTag)-[:REFERENCES]->(:Image)`

- `(:PackageVersion)-[:DEPLOYED]->(:Image)`: `DEPLOYED` is the canonical relationship name from `PackageVersion` to `Image`. This constraint validates existing relationships and does not create them.

- `(:SecurityIssue)-[:AFFECTS]->(:Image)`

- `(:Tenant)-[:RESOURCE]->(:Image)`

(ontology-imageattestation)=
### ImageAttestation

A cross-provider ImageAttestation resource in Cartography's ontology.

> **Semantic Label**: This label is applied directly to provider-specific nodes; it does not create a separate node.

> **Implementations**: `AWSECRImage`, `GCPArtifactRegistryImage`.

#### Properties

No normalized properties are defined for this semantic label.


#### Relationships

- `(:CVE)-[:AFFECTS]->(:ImageAttestation)`

- `(:Container)-[:HAS_IMAGE]->(:ImageAttestation)`

- `(:Function)-[:HAS]->(:ImageAttestation)`: generated by analysis job `Lambda functions with ECR images`.

- `(:Function)-[:HAS_IMAGE]->(:ImageAttestation)`

- `(:Image)-[:ATTESTS]->(:ImageAttestation)`

- `(:Image)-[:BUILT_FROM]->(:ImageAttestation)`
  - Properties:

    | Field | Description |
    |-------|-------------|
    | confidence | Parent-image evidence strength; digest-verified SBOM matches use `explicit`. |
    | from_attestation | Whether the parent image relationship was derived from a provenance attestation. |
    | from_sbom | Match-method flag set when parent-image evidence comes from a digest-verified SPDX SBOM relationship. |
    | parent_image_uri | Parent image URI extracted from a digest-verified SPDX SBOM relationship. |

- `(:Image)-[:CONTAINS_IMAGE]->(:ImageAttestation)`

- `(:ImageAttestation)-[:ATTESTS]->(:Image)`

- `(:ImageAttestation)-[:ATTESTS]->(:ImageAttestation)`

- `(:ImageAttestation)-[:ATTESTS]->(:ImageManifestList)`

- `(:ImageAttestation)-[:BUILT_FROM]->(:Image)`
  - Properties:

    | Field | Description |
    |-------|-------------|
    | confidence | Parent-image evidence strength; digest-verified SBOM matches use `explicit`. |
    | from_attestation | Whether the parent image relationship was derived from a provenance attestation. |
    | from_sbom | Match-method flag set when parent-image evidence comes from a digest-verified SPDX SBOM relationship. |
    | parent_image_uri | Parent image URI extracted from a digest-verified SPDX SBOM relationship. |

- `(:ImageAttestation)-[:BUILT_FROM]->(:ImageAttestation)`
  - Properties:

    | Field | Description |
    |-------|-------------|
    | confidence | Parent-image evidence strength; digest-verified SBOM matches use `explicit`. |
    | from_attestation | Whether the parent image relationship was derived from a provenance attestation. |
    | from_sbom | Match-method flag set when parent-image evidence comes from a digest-verified SPDX SBOM relationship. |
    | parent_image_uri | Parent image URI extracted from a digest-verified SPDX SBOM relationship. |

- `(:ImageAttestation)-[:BUILT_FROM]->(:ImageManifestList)`
  - Properties:

    | Field | Description |
    |-------|-------------|
    | confidence | Parent-image evidence strength; digest-verified SBOM matches use `explicit`. |
    | from_attestation | Whether the parent image relationship was derived from a provenance attestation. |
    | from_sbom | Match-method flag set when parent-image evidence comes from a digest-verified SPDX SBOM relationship. |
    | parent_image_uri | Parent image URI extracted from a digest-verified SPDX SBOM relationship. |

- `(:ImageAttestation)-[:CONTAINS_IMAGE]->(:Image)`

- `(:ImageAttestation)-[:CONTAINS_IMAGE]->(:ImageAttestation)`

- `(:ImageAttestation)-[:CONTAINS_IMAGE]->(:ImageManifestList)`

- `(:ImageAttestation)-[:HAS_LAYER]->(:ImageLayer)`

- `(:ImageAttestation)-[:HEAD]->(:ImageLayer)`

- `(:ImageAttestation)-[:TAIL]->(:ImageLayer)`

- `(:ImageManifestList)-[:ATTESTS]->(:ImageAttestation)`

- `(:ImageManifestList)-[:BUILT_FROM]->(:ImageAttestation)`
  - Properties:

    | Field | Description |
    |-------|-------------|
    | confidence | Parent-image evidence strength; digest-verified SBOM matches use `explicit`. |
    | from_attestation | Whether the parent image relationship was derived from a provenance attestation. |
    | from_sbom | Match-method flag set when parent-image evidence comes from a digest-verified SPDX SBOM relationship. |
    | parent_image_uri | Parent image URI extracted from a digest-verified SPDX SBOM relationship. |

- `(:ImageManifestList)-[:CONTAINS_IMAGE]->(:ImageAttestation)`

- `(:ImageTag)-[:IMAGE]->(:ImageAttestation)`

- `(:SecurityIssue)-[:AFFECTS]->(:ImageAttestation)`

- `(:Tenant)-[:RESOURCE]->(:ImageAttestation)`

(ontology-imagelayer)=
### ImageLayer

A cross-provider ImageLayer resource in Cartography's ontology.

> **Semantic Label**: This label is applied directly to provider-specific nodes; it does not create a separate node.

> **Implementations**: `AWSECRImageLayer`, `GCPArtifactRegistryImageLayer`, `GitHubContainerImageLayer`, `GitLabContainerImageLayer`, `ScalewayContainerRegistryImageLayer`.

#### Properties

No normalized properties are defined for this semantic label.


#### Relationships

- `(:Image)-[:HAS_LAYER]->(:ImageLayer)`

- `(:Image)-[:HEAD]->(:ImageLayer)`

- `(:Image)-[:TAIL]->(:ImageLayer)`

- `(:ImageAttestation)-[:HAS_LAYER]->(:ImageLayer)`

- `(:ImageAttestation)-[:HEAD]->(:ImageLayer)`

- `(:ImageAttestation)-[:TAIL]->(:ImageLayer)`

- `(:ImageLayer)-[:NEXT]->(:ImageLayer)`

- `(:ImageManifestList)-[:HAS_LAYER]->(:ImageLayer)`

- `(:ImageManifestList)-[:HEAD]->(:ImageLayer)`

- `(:ImageManifestList)-[:TAIL]->(:ImageLayer)`

- `(:Tenant)-[:RESOURCE]->(:ImageLayer)`

(ontology-imagemanifestlist)=
### ImageManifestList

A cross-provider ImageManifestList resource in Cartography's ontology.

> **Semantic Label**: This label is applied directly to provider-specific nodes; it does not create a separate node.

> **Implementations**: `AWSECRImage`, `GCPArtifactRegistryImage`, `GitHubContainerImage`, `GitLabContainerImage`.

#### Properties

No normalized properties are defined for this semantic label.


#### Relationships

- `(:CVE)-[:AFFECTS]->(:ImageManifestList)`

- `(:Container)-[:HAS_IMAGE]->(:ImageManifestList)`

- `(:ContainerRegistry)-[:HAS_IMAGE]->(:ImageManifestList)`

- `(:Function)-[:HAS]->(:ImageManifestList)`: generated by analysis job `Lambda functions with ECR images`.

- `(:Function)-[:HAS_IMAGE]->(:ImageManifestList)`

- `(:Image)-[:ATTESTS]->(:ImageManifestList)`

- `(:Image)-[:BUILT_FROM]->(:ImageManifestList)`
  - Properties:

    | Field | Description |
    |-------|-------------|
    | confidence | Confidence score for the parent image match. |
    | from_attestation | Whether the parent image was identified from an attestation. |
    | from_sbom | Match-method flag set when parent-image evidence comes from a digest-verified SPDX SBOM relationship. |
    | parent_image_uri | Parent image reference reported by provenance. |

- `(:Image)-[:CONTAINS_IMAGE]->(:ImageManifestList)`

- `(:ImageAttestation)-[:ATTESTS]->(:ImageManifestList)`

- `(:ImageAttestation)-[:BUILT_FROM]->(:ImageManifestList)`
  - Properties:

    | Field | Description |
    |-------|-------------|
    | confidence | Parent-image evidence strength; digest-verified SBOM matches use `explicit`. |
    | from_attestation | Whether the parent image relationship was derived from a provenance attestation. |
    | from_sbom | Match-method flag set when parent-image evidence comes from a digest-verified SPDX SBOM relationship. |
    | parent_image_uri | Parent image URI extracted from a digest-verified SPDX SBOM relationship. |

- `(:ImageAttestation)-[:CONTAINS_IMAGE]->(:ImageManifestList)`

- `(:ImageManifestList)-[:ATTESTS]->(:Image)`

- `(:ImageManifestList)-[:ATTESTS]->(:ImageAttestation)`

- `(:ImageManifestList)-[:ATTESTS]->(:ImageManifestList)`

- `(:ImageManifestList)-[:BUILT_FROM]->(:Image)`
  - Properties:

    | Field | Description |
    |-------|-------------|
    | confidence | Confidence score for the parent image match. |
    | from_attestation | Whether the parent image was identified from an attestation. |
    | from_sbom | Match-method flag set when parent-image evidence comes from a digest-verified SPDX SBOM relationship. |
    | parent_image_uri | Parent image reference reported by provenance. |

- `(:ImageManifestList)-[:BUILT_FROM]->(:ImageAttestation)`
  - Properties:

    | Field | Description |
    |-------|-------------|
    | confidence | Parent-image evidence strength; digest-verified SBOM matches use `explicit`. |
    | from_attestation | Whether the parent image relationship was derived from a provenance attestation. |
    | from_sbom | Match-method flag set when parent-image evidence comes from a digest-verified SPDX SBOM relationship. |
    | parent_image_uri | Parent image URI extracted from a digest-verified SPDX SBOM relationship. |

- `(:ImageManifestList)-[:BUILT_FROM]->(:ImageManifestList)`
  - Properties:

    | Field | Description |
    |-------|-------------|
    | confidence | Confidence score for the parent image match. |
    | from_attestation | Whether the parent image was identified from an attestation. |
    | from_sbom | Match-method flag set when parent-image evidence comes from a digest-verified SPDX SBOM relationship. |
    | parent_image_uri | Parent image reference reported by provenance. |

- `(:ImageManifestList)-[:CONTAINS_IMAGE]->(:Image)`

- `(:ImageManifestList)-[:CONTAINS_IMAGE]->(:ImageAttestation)`

- `(:ImageManifestList)-[:CONTAINS_IMAGE]->(:ImageManifestList)`

- `(:ImageManifestList)-[:HAS_LAYER]->(:ImageLayer)`

- `(:ImageManifestList)-[:HEAD]->(:ImageLayer)`

- `(:ImageManifestList)-[:TAIL]->(:ImageLayer)`

- `(:ImageTag)-[:IMAGE]->(:ImageManifestList)`

- `(:ImageTag)-[:REFERENCES]->(:ImageManifestList)`

- `(:SecurityIssue)-[:AFFECTS]->(:ImageManifestList)`

- `(:Tenant)-[:RESOURCE]->(:ImageManifestList)`

(ontology-imagetag)=
### ImageTag

A cross-provider ImageTag resource in Cartography's ontology.

> **Semantic Label**: This label is applied directly to provider-specific nodes; it does not create a separate node.

> **Implementations**: `AWSECRRepositoryImage`, `GCPArtifactRegistryRepositoryImage`, `GitHubContainerImageTag`, `GitLabContainerRepositoryTag`, `ScalewayContainerRegistryImageTag`.

#### Properties

No normalized properties are defined for this semantic label.


#### Relationships

- `(:ContainerRegistry)-[:CONTAINS]->(:ImageTag)`

- `(:ContainerRegistry)-[:HAS_TAG]->(:ImageTag)`

- `(:ContainerRegistry)-[:REPO_IMAGE]->(:ImageTag)`

- `(:ImageTag)-[:IMAGE]->(:Image)`

- `(:ImageTag)-[:IMAGE]->(:ImageAttestation)`

- `(:ImageTag)-[:IMAGE]->(:ImageManifestList)`

- `(:ImageTag)-[:REFERENCES]->(:Image)`

- `(:ImageTag)-[:REFERENCES]->(:ImageManifestList)`

- `(:Tenant)-[:RESOURCE]->(:ImageTag)`

(ontology-loadbalancer)=
### LoadBalancer

A cross-provider LoadBalancer resource in Cartography's ontology.

> **Semantic Label**: This label is applied directly to provider-specific nodes; it does not create a separate node.

> **Implementations**: `AWSLoadBalancer`, `AWSLoadBalancerV2`, `AzureApplicationGateway`, `AzureLoadBalancer`, `GCPForwardingRule`, `ScalewayLoadBalancer`.

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| *_ont_dns_name* | Yes | Normalized dns name for nodes carrying `LoadBalancer`. |
| *_ont_ip_address* | Yes | Normalized ip address for nodes carrying `LoadBalancer`. |
| *_ont_lb_type* | Yes | Normalized lb type for nodes carrying `LoadBalancer`. |
| *_ont_name* | Yes | Normalized name for nodes carrying `LoadBalancer`. |
| *_ont_region* | Yes | Normalized region for nodes carrying `LoadBalancer`. |
| *_ont_scheme* | Yes | Normalized scheme for nodes carrying `LoadBalancer`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |

#### Relationships

- `(:DNSRecord)-[:DNS_POINTS_TO]->(:LoadBalancer)`: generated by analysis job `Ontology - DNSRecord to AWSLoadBalancer linking`, `Ontology - DNSRecord to AWSLoadBalancerV2 linking`.

- `(:LoadBalancer)-[:EXPOSE]->(:ComputeInstance)`: `EXPOSE` is the canonical relationship name from `LoadBalancer` to `ComputeInstance`. This constraint validates existing relationships and does not create them.
  - Properties:

    | Field | Description |
    |-------|-------------|
    | exposure_type | Property generated by analysis job: `Scaleway Load Balancer EXPOSE relationships`. |
    | port | Port on which the listener or target group receives traffic. |
    | protocol | Protocol used by the listener or target group. |
    | target_group_arn | ARN of the Elastic Load Balancing target group represented by this relationship. |

- `(:LoadBalancer)-[:EXPOSE]->(:ComputePod)`: `EXPOSE` is the canonical relationship name from `LoadBalancer` to `ComputePod`. This constraint validates existing relationships and does not create them.
  - Properties:

    | Field | Description |
    |-------|-------------|
    | exposure_type | Property generated by analysis job: `Kubernetes LoadBalancer to pod EXPOSE relationships`. |

- `(:LoadBalancer)-[:EXPOSE]->(:Container)`: `EXPOSE` is the canonical relationship name from `LoadBalancer` to `Container`. This constraint validates existing relationships and does not create them.
  - Properties:

    | Field | Description |
    |-------|-------------|
    | exposure_type | Property generated by analysis job: `Kubernetes LoadBalancer to container EXPOSE relationships`. |

- `(:LoadBalancer)-[:EXPOSE]->(:Function)`: `EXPOSE` is the canonical relationship name from `LoadBalancer` to `Function`. This constraint validates existing relationships and does not create them.
  - Properties:

    | Field | Description |
    |-------|-------------|
    | port | Port on which the listener or target group receives traffic. |
    | protocol | Protocol used by the listener or target group. |
    | target_group_arn | ARN of the Elastic Load Balancing target group represented by this relationship. |

- `(:LoadBalancer)-[:EXPOSE]->(:LoadBalancer)`: `EXPOSE` is the canonical relationship name from `LoadBalancer` to `LoadBalancer`. This constraint validates existing relationships and does not create them.
  - Properties:

    | Field | Description |
    |-------|-------------|
    | port | Port on which the listener or target group receives traffic. |
    | protocol | Protocol used by the listener or target group. |
    | target_group_arn | ARN of the Elastic Load Balancing target group represented by this relationship. |

- `(:LoadBalancer)-[:IN_SUBNET]->(:Subnet)`

- `(:LoadBalancer)-[:MEMBER_OF_EC2_SECURITY_GROUP]->(:NetworkAccessControl)`

- `(:LoadBalancer)-[:PART_OF_SUBNET]->(:Subnet)`

- `(:LoadBalancer)-[:SOURCE_SECURITY_GROUP]->(:NetworkAccessControl)`

- `(:LoadBalancer)-[:SUBNET]->(:Subnet)`

- `(:LoadBalancer)-[:TAGGED]->(:Tag)`

- `(:NetworkAccessControl)-[:PROTECTS]->(:LoadBalancer)`: generated by analysis job `Azure Firewall PROTECTS LB relationships`.

- `(:PublicIP)-[:POINTS_TO]->(:LoadBalancer)`

- `(:Subnet)-[:RESOURCE]->(:LoadBalancer)`

- `(:Tenant)-[:RESOURCE]->(:LoadBalancer)`

- `(:VirtualNetwork)-[:RESOURCE]->(:LoadBalancer)`

(ontology-networkaccesscontrol)=
### NetworkAccessControl

A cross-provider NetworkAccessControl resource in Cartography's ontology.

> **Semantic Label**: This label is applied directly to provider-specific nodes; it does not create a separate node.

> **Implementations**: `AWSEC2SecurityGroup`, `AzureFirewall`, `AzureNetworkSecurityGroup`, `CloudflareRuleset`, `DatabricksIpAccessList`, `GCPCloudArmorPolicy`, `GCPFirewall`, `GCPSslPolicy`, `ScalewaySecurityGroup`, `SnowflakeNetworkPolicy`, `SnowflakeNetworkRule`.

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| *_ont_direction* | Yes | Normalized direction for nodes carrying `NetworkAccessControl`. |
| *_ont_name* | Yes | Normalized name for nodes carrying `NetworkAccessControl`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |

#### Relationships

- `(:ComputeInstance)-[:MEMBER_OF_EC2_SECURITY_GROUP]->(:NetworkAccessControl)`

- `(:ComputeInstance)-[:MEMBER_OF_SCALEWAY_SECURITY_GROUP]->(:NetworkAccessControl)`

- `(:DNSZone)-[:HAS_RULESET]->(:NetworkAccessControl)`

- `(:Database)-[:MEMBER_OF_EC2_SECURITY_GROUP]->(:NetworkAccessControl)`

- `(:IdentityProvider)-[:GOVERNED_BY]->(:NetworkAccessControl)`

- `(:LoadBalancer)-[:MEMBER_OF_EC2_SECURITY_GROUP]->(:NetworkAccessControl)`

- `(:LoadBalancer)-[:SOURCE_SECURITY_GROUP]->(:NetworkAccessControl)`

- `(:NetworkAccessControl)-[:ALLOWS]->(:NetworkAccessControl)`

- `(:NetworkAccessControl)-[:ALLOWS_TRAFFIC_FROM]->(:NetworkAccessControl)`

- `(:NetworkAccessControl)-[:BLOCKS]->(:NetworkAccessControl)`

- `(:NetworkAccessControl)-[:FIREWALL_INGRESS]->(:ComputeInstance)`: generated by analysis job `GCP firewall ingress to instance analysis`.

- `(:NetworkAccessControl)-[:MEMBER_OF]->(:VirtualNetwork)`

- `(:NetworkAccessControl)-[:PROTECTS]->(:LoadBalancer)`: generated by analysis job `Azure Firewall PROTECTS LB relationships`.

- `(:NetworkAccessControl)-[:TAGGED]->(:Tag)`

- `(:ServiceAccount)-[:GOVERNED_BY]->(:NetworkAccessControl)`

- `(:Subnet)-[:ASSOCIATED_WITH]->(:NetworkAccessControl)`

- `(:Tenant)-[:GOVERNED_BY]->(:NetworkAccessControl)`

- `(:Tenant)-[:RESOURCE]->(:NetworkAccessControl)`

- `(:UserAccount)-[:GOVERNED_BY]->(:NetworkAccessControl)`

- `(:VirtualNetwork)-[:MEMBER_OF_EC2_SECURITY_GROUP]->(:NetworkAccessControl)`

- `(:VirtualNetwork)-[:RESOURCE]->(:NetworkAccessControl)`

(ontology-objectstorage)=
### ObjectStorage

A cross-provider ObjectStorage resource in Cartography's ontology.

> **Semantic Label**: This label is applied directly to provider-specific nodes; it does not create a separate node.

> **Implementations**: `AWSS3Bucket`, `AzureStorageBlobContainer`, `CloudflareR2Bucket`, `DatabricksExternalLocation`, `DatabricksVolume`, `GCPBucket`, `ScalewayObjectStorageBucket`, `SnowflakeExternalVolumeStorageLocation`, `SnowflakeStage`, `SupabaseStorageBucket`.

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| *_ont_encrypted* | Yes | Normalized encrypted for nodes carrying `ObjectStorage`. |
| *_ont_location* | Yes | Normalized location for nodes carrying `ObjectStorage`. |
| *_ont_name* | Yes | Normalized name for nodes carrying `ObjectStorage`. |
| *_ont_public* | Yes | Normalized public for nodes carrying `ObjectStorage`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |
| *_ont_versioning* | Yes | Normalized versioning for nodes carrying `ObjectStorage`. |

#### Relationships

- `(:AIModel)-[:REFERENCES_ARTIFACTS_IN]->(:ObjectStorage)`

- `(:AIModel)-[:STORED_IN]->(:ObjectStorage)`

- `(:AIModel)-[:TRAINED_FROM]->(:ObjectStorage)`

- `(:DNSZone)-[:HAS_R2_CUSTOM_DOMAIN]->(:ObjectStorage)`

- `(:Database)-[:BACKED_BY]->(:ObjectStorage)`

- `(:Database)-[:CONTAINS]->(:ObjectStorage)`

- `(:FileStorage)-[:BACKED_BY]->(:ObjectStorage)`

- `(:ObjectStorage)-[:BACKED_BY]->(:ObjectStorage)`

- `(:ObjectStorage)-[:ENCRYPTED_BY]->(:EncryptionKey)`: `ENCRYPTED_BY` is the canonical relationship name from `ObjectStorage` to `EncryptionKey`. This constraint validates existing relationships and does not create them.

- `(:ObjectStorage)-[:LABELED]->(:Tag)`

- `(:ObjectStorage)-[:TAGGED]->(:Tag)`

- `(:SecurityIssue)-[:AFFECTS]->(:ObjectStorage)`

- `(:Tenant)-[:RESOURCE]->(:ObjectStorage)`

(ontology-package)=
### Package

A canonical, version-independent software package aggregated across inventory sources.

> **Abstract Ontology Node**: This is a dedicated canonical node created separately from provider-specific nodes.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Version-independent normalized identifier in `{type}\|{namespace/}{name}` format. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| name |  | Normalized package name, including its namespace prefix when present. |
| namespace |  | Package URL namespace when present. |
| type |  | Package ecosystem or type. |

#### Relationships

- `(:Package)-[:HAS_VERSION]->(:PackageVersion)`: `HAS_VERSION` is the canonical relationship name from `Package` to `PackageVersion`. This constraint validates existing relationships and does not create them.

(ontology-packageversion)=
### PackageVersion

A canonical versioned software package aggregated across inventory sources.

> **Abstract Ontology Node**: This is a dedicated canonical node created separately from provider-specific nodes.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Normalized identifier for this specific package version. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| name |  | Package name. |
| purl |  | Package URL identifying this package version. |
| type |  | Package ecosystem or type. |
| version |  | Package version. |

#### Relationships

- `(:CVE)-[:AFFECTS]->(:PackageVersion)`: `AFFECTS` is the canonical relationship name from `CVE` to `PackageVersion`. This constraint validates existing relationships and does not create them.

- `(:Package)-[:HAS_VERSION]->(:PackageVersion)`: `HAS_VERSION` is the canonical relationship name from `Package` to `PackageVersion`. This constraint validates existing relationships and does not create them.

- `(:PackageVersion)-[:DEPENDS_ON]->(:PackageVersion)`: generated by analysis job `Ontology - PackageVersion DEPENDS_ON PackageVersion linking`.

- `(:PackageVersion)-[:DEPLOYED]->(:Image)`: `DEPLOYED` is the canonical relationship name from `PackageVersion` to `Image`. This constraint validates existing relationships and does not create them.

- `(:PackageVersion)-[:DETECTED_AS]->(:GitHubDependency)`: A canonical package version was detected as a GitHub dependency.

- `(:PackageVersion)-[:DETECTED_AS]->(:GitLabDependency)`: A canonical package version was detected as a GitLab dependency.

- `(:PackageVersion)-[:DETECTED_AS]->(:SemgrepDependency)`: A canonical package version was detected as a Semgrep dependency.

- `(:PackageVersion)-[:DETECTED_AS]->(:SocketDevDependency)`: A canonical package version was detected as a Socket.dev dependency.

- `(:PackageVersion)-[:DETECTED_AS]->(:SyftPackage)`: A canonical package version was detected as a Syft package.

- `(:PackageVersion)-[:DETECTED_AS]->(:TrivyPackage)`: A canonical package version was detected as a Trivy package.

- `(:PackageVersion)-[:SHOULD_UPDATE_TO]->(:TrivyFix)`: A canonical package version should be updated to an available Trivy fix.

- `(:SecurityIssue)-[:AFFECTS]->(:PackageVersion)`: `AFFECTS` is the canonical relationship name from `SecurityIssue` to `PackageVersion`. This constraint validates existing relationships and does not create them.

(ontology-permissionrole)=
### PermissionRole

A cross-provider PermissionRole resource in Cartography's ontology.

> **Semantic Label**: This label is applied directly to provider-specific nodes; it does not create a separate node.

> **Implementations**: `AWSPermissionSet`, `AWSRole`, `AzureRoleDefinition`, `CloudflareRole`, `GCPRole`, `KeycloakRole`, `KubernetesClusterRole`, `KubernetesRole`, `ModalEnvironmentRole`, `ModalWorkspaceRole`, `OCIPolicy`, `SalesforcePermissionSet`, `SalesforceProfile`, `ScalewayPermissionSet`, `SnowflakeDatabaseRole`, `SnowflakeRole`, `WorkOSRole`.

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| *_ont_name* | Yes | Normalized name for nodes carrying `PermissionRole`. |
| *_ont_scope* | Yes | Normalized scope for nodes carrying `PermissionRole`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |
| *_ont_type* | Yes | Normalized type for nodes carrying `PermissionRole`. |

#### Relationships

- `(:AIModel)-[:HAS_EXECUTION_ROLE]->(:PermissionRole)`

- `(:APIKey)-[:RESTRICTED_TO]->(:PermissionRole)`

- `(:CICDPipeline)-[:ASSUMES]->(:PermissionRole)`

- `(:CodeRepository)-[:ASSUMED_ROLE_WITH_WEB_IDENTITY]->(:PermissionRole)`
  - Properties:

    | Field | Description |
    |-------|-------------|
    | first_seen_in_time_window | Timestamp when this relationship was first observed in the current time window. |
    | last_used | Timestamp when this relationship was last observed in use. |
    | times_used | Number of times this relationship was observed in use. |

- `(:ComputeCluster)-[:RESOURCE]->(:PermissionRole)`

- `(:ComputeInstance)-[:ASSUMES]->(:PermissionRole)`: `ASSUMES` is the canonical relationship name from `ComputeInstance` to `PermissionRole`. This constraint validates existing relationships and does not create them.

- `(:ComputeInstance)-[:STS_ASSUMEROLE_ALLOW]->(:PermissionRole)`: generated by analysis job `EC2 Instances assume IAM roles`.

- `(:ComputeNamespace)-[:CONTAINS]->(:PermissionRole)`

- `(:Database)-[:CONTAINS]->(:PermissionRole)`

- `(:Function)-[:ASSUMES]->(:PermissionRole)`: `ASSUMES` is the canonical relationship name from `Function` to `PermissionRole`. This constraint validates existing relationships and does not create them.

- `(:IdentityProvider)-[:RUNS_AS_ROLE]->(:PermissionRole)`

- `(:PermissionRole)-[:ALLOWED_BY]->(:UserAccount)`
  - Properties:

    | Field | Description |
    |-------|-------------|
    | permission_set_arn | ARN of the IAM Identity Center permission set that grants this relationship. |

- `(:PermissionRole)-[:ALLOWED_BY]->(:UserGroup)`
  - Properties:

    | Field | Description |
    |-------|-------------|
    | permission_set_arn | ARN of the IAM Identity Center permission set that grants this relationship. |

- `(:PermissionRole)-[:ASSIGNED_TO_ROLE]->(:PermissionRole)`

- `(:PermissionRole)-[:INCLUDES]->(:PermissionRole)`: `INCLUDES` is the canonical relationship name from `PermissionRole` to `PermissionRole`. This constraint validates existing relationships and does not create them.
  - Properties:

    | Field | Description |
    |-------|-------------|
    | created_on | When the role was granted. |
    | granted_by | Name of the role that created the grant. |

- `(:PermissionRole)-[:MAPS_TO]->(:UserAccount)`

- `(:PermissionRole)-[:MAPS_TO]->(:UserGroup)`

- `(:PermissionRole)-[:OCI_POLICY_REFERENCE]->(:UserGroup)`

- `(:PermissionRole)-[:TAGGED]->(:Tag)`

- `(:SecurityIssue)-[:AFFECTS]->(:PermissionRole)`

- `(:ServiceAccount)-[:ASSUMES_ROLE]->(:PermissionRole)`

- `(:ServiceAccount)-[:HAS_ROLE]->(:PermissionRole)`: `HAS_ROLE` is the canonical relationship name from `ServiceAccount` to `PermissionRole`. This constraint validates existing relationships and does not create them.
  - Properties:

    | Field | Description |
    |-------|-------------|
    | created_on | When the role was granted. |
    | granted_by | Name of the role that created the grant. |

- `(:Tenant)-[:HAS]->(:PermissionRole)`

- `(:Tenant)-[:RESOURCE]->(:PermissionRole)`

- `(:ThirdPartyApp)-[:DEFINES]->(:PermissionRole)`

- `(:UserAccount)-[:ASSUMED_ROLE_WITH_SAML]->(:PermissionRole)`
  - Properties:

    | Field | Description |
    |-------|-------------|
    | first_seen_in_time_window | Timestamp when this relationship was first observed in the current time window. |
    | last_used | Timestamp when this relationship was last observed in use. |
    | times_used | Number of times this relationship was observed in use. |

- `(:UserAccount)-[:ASSUME_ROLE]->(:PermissionRole)`

- `(:UserAccount)-[:HAS_PERMISSION_SET]->(:PermissionRole)`

- `(:UserAccount)-[:HAS_ROLE]->(:PermissionRole)`: `HAS_ROLE` is the canonical relationship name from `UserAccount` to `PermissionRole`. This constraint validates existing relationships and does not create them.
  - Properties:

    | Field | Description |
    |-------|-------------|
    | created_on | When the role was granted. |
    | granted_by | Name of the role that created the grant. |

- `(:UserGroup)-[:GRANTS]->(:PermissionRole)`

- `(:UserGroup)-[:HAS_PERMISSION_SET]->(:PermissionRole)`

- `(:UserGroup)-[:HAS_ROLE]->(:PermissionRole)`: `HAS_ROLE` is the canonical relationship name from `UserGroup` to `PermissionRole`. This constraint validates existing relationships and does not create them.

(ontology-publicip)=
### PublicIP

A canonical public IP address linked to provider network resources.

> **Abstract Ontology Node**: This is a dedicated canonical node created separately from provider-specific nodes.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Canonical public IP address identifier. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| ip_address | Yes | Public IP address. |
| ip_version |  | IP protocol version. |

#### Relationships

- `(:BbotIPAddress)-[:MATCHES_PUBLIC_IP]->(:PublicIP)`: generated by analysis job `Ontology - BbotIPAddress to PublicIP linking`.

- `(:PublicIP)-[:POINTS_TO]->(:ComputeInstance)`

- `(:PublicIP)-[:POINTS_TO]->(:Device)`: generated by analysis job `Ontology - PublicIP POINTS_TO Device linking`.

- `(:PublicIP)-[:POINTS_TO]->(:LoadBalancer)`

- `(:PublicIP)-[:RESERVED_BY]->(:AWSElasticIPAddress)`

- `(:PublicIP)-[:RESERVED_BY]->(:AzurePublicIPAddress)`

- `(:PublicIP)-[:RESERVED_BY]->(:GCPNicAccessConfig)`

- `(:PublicIP)-[:RESERVED_BY]->(:ScalewayElasticMetalFlexibleIp)`

- `(:PublicIP)-[:RESERVED_BY]->(:ScalewayFlexibleIp)`

(ontology-secret)=
### Secret

A cross-provider Secret resource in Cartography's ontology.

> **Semantic Label**: This label is applied directly to provider-specific nodes; it does not create a separate node.

> **Implementations**: `AWSSSMParameter`, `AWSSecretsManagerSecret`, `AzureKeyVaultSecret`, `GCPSecretManagerSecret`, `GitHubActionsSecret`, `KubernetesSecret`, `ModalSecret`, `NetlifyEnvVar`, `RailwayVariable`, `ScalewaySecret`, `SnowflakeSecret`, `SupabaseSecret`.

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| *_ont_created_at* | Yes | Normalized created at for nodes carrying `Secret`. |
| *_ont_name* | Yes | Normalized name for nodes carrying `Secret`. |
| *_ont_rotation_enabled* | Yes | Normalized rotation enabled for nodes carrying `Secret`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |
| *_ont_updated_at* | Yes | Normalized updated at for nodes carrying `Secret`. |

#### Relationships

- `(:CICDPipeline)-[:REFERENCES_SECRET]->(:Secret)`

- `(:CodeRepository)-[:HAS_SECRET]->(:Secret)`

- `(:ComputeCluster)-[:RESOURCE]->(:Secret)`

- `(:ComputeInstance)-[:USES_SECRET]->(:Secret)`: `USES_SECRET` is the canonical relationship name from `ComputeInstance` to `Secret`. This constraint validates existing relationships and does not create them.

- `(:ComputeNamespace)-[:CONTAINS]->(:Secret)`

- `(:ComputePod)-[:USES_SECRET]->(:Secret)`: `USES_SECRET` is the canonical relationship name from `ComputePod` to `Secret`. This constraint validates existing relationships and does not create them.
  - Properties:

    | Field | Description |
    |-------|-------------|
    | mount_method | How the pod consumes the secret: volume, environment, or both. |

- `(:ComputePod)-[:USES_SECRET_ENV]->(:Secret)`

- `(:ComputePod)-[:USES_SECRET_VOLUME]->(:Secret)`

- `(:ComputeService)-[:HAS_ENV_VAR]->(:Secret)`

- `(:ComputeService)-[:USES_SECRET]->(:Secret)`

- `(:Function)-[:USES_SECRET]->(:Secret)`: `USES_SECRET` is the canonical relationship name from `Function` to `Secret`. This constraint validates existing relationships and does not create them.

- `(:Secret)-[:CREATED_BY]->(:UserAccount)`

- `(:Secret)-[:ENCRYPTED_BY]->(:EncryptionKey)`: `ENCRYPTED_BY` is the canonical relationship name from `Secret` to `EncryptionKey`. This constraint validates existing relationships and does not create them.

- `(:Secret)-[:LABELED]->(:Tag)`

- `(:Secret)-[:TAGGED]->(:Tag)`

- `(:Secret)-[:UPDATED_BY]->(:UserAccount)`

- `(:Secret)-[:USES_INTEGRATION]->(:IdentityProvider)`

- `(:Tenant)-[:RESOURCE]->(:Secret)`

(ontology-securityissue)=
### SecurityIssue

A cross-provider SecurityIssue resource in Cartography's ontology.

> **Semantic Label**: This label is applied directly to provider-specific nodes; it does not create a separate node.

> **Implementations**: `AWSGuardDutyFinding`, `AWSInspectorFinding`, `AzureSecurityAssessment`, `BbotFinding`, `GitHubDependabotAlert`, `SemgrepSASTFinding`, `SemgrepSCAFinding`, `SemgrepSecretsFinding`, `SocketDevAlert`, `SupabaseSecurityAdvisorFinding`, `WizFinding`, `WizIssue`, `ZizmorFinding`.

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| *_ont_base_score* | Yes | Normalized base score for nodes carrying `SecurityIssue`. |
| *_ont_base_severity* | Yes | Normalized base severity for nodes carrying `SecurityIssue`. |
| *_ont_cve_id* | Yes | Normalized cve id for nodes carrying `SecurityIssue`. |
| *_ont_description* |  | Normalized description for nodes carrying `SecurityIssue`. |
| *_ont_exploitability_score* | Yes | Normalized exploitability score for nodes carrying `SecurityIssue`. |
| *_ont_first_seen* | Yes | Normalized first seen for nodes carrying `SecurityIssue`. |
| *_ont_impact_score* | Yes | Normalized impact score for nodes carrying `SecurityIssue`. |
| *_ont_references* |  | Normalized references for nodes carrying `SecurityIssue`. |
| *_ont_severity* | Yes | Normalized severity for nodes carrying `SecurityIssue`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |
| *_ont_status* | Yes | Normalized status for nodes carrying `SecurityIssue`. |
| *_ont_title* | Yes | Normalized title for nodes carrying `SecurityIssue`. |
| *_ont_type* | Yes | Normalized type for nodes carrying `SecurityIssue`. |

#### Relationships

- `(:CVE)-[:LINKED_TO]->(:SecurityIssue)`

- `(:DNSRecord)-[:DISCOVERED_FROM]->(:SecurityIssue)`

- `(:SecurityIssue)-[:AFFECTS]->(:APIKey)`

- `(:SecurityIssue)-[:AFFECTS]->(:CICDPipeline)`

- `(:SecurityIssue)-[:AFFECTS]->(:ComputeCluster)`

- `(:SecurityIssue)-[:AFFECTS]->(:ComputeInstance)`

- `(:SecurityIssue)-[:AFFECTS]->(:ContainerRegistry)`

- `(:SecurityIssue)-[:AFFECTS]->(:DNSRecord)`

- `(:SecurityIssue)-[:AFFECTS]->(:Database)`

- `(:SecurityIssue)-[:AFFECTS]->(:Image)`

- `(:SecurityIssue)-[:AFFECTS]->(:ImageAttestation)`

- `(:SecurityIssue)-[:AFFECTS]->(:ImageManifestList)`

- `(:SecurityIssue)-[:AFFECTS]->(:ObjectStorage)`

- `(:SecurityIssue)-[:AFFECTS]->(:PackageVersion)`: `AFFECTS` is the canonical relationship name from `SecurityIssue` to `PackageVersion`. This constraint validates existing relationships and does not create them.

- `(:SecurityIssue)-[:AFFECTS]->(:PermissionRole)`

- `(:SecurityIssue)-[:AFFECTS]->(:UserAccount)`

- `(:SecurityIssue)-[:ASSIGNED_TO]->(:UserAccount)`

- `(:SecurityIssue)-[:DISCOVERED_FROM]->(:DNSRecord)`

- `(:SecurityIssue)-[:DISCOVERED_FROM]->(:SecurityIssue)`

- `(:SecurityIssue)-[:DISMISSED_BY]->(:UserAccount)`

- `(:SecurityIssue)-[:FOUND_IN]->(:CodeRepository)`

- `(:SecurityIssue)-[:LINKED_TO]->(:CVE)`

- `(:SecurityIssue)-[:REMOTE_ACCOUNT]->(:Tenant)`

- `(:SecurityIssue)-[:TAGGED]->(:Tag)`

- `(:Tenant)-[:HAS_ASSESSMENT]->(:SecurityIssue)`

- `(:Tenant)-[:MEMBER]->(:SecurityIssue)`

- `(:Tenant)-[:RESOURCE]->(:SecurityIssue)`

(ontology-serviceaccount)=
### ServiceAccount

A cross-provider ServiceAccount resource in Cartography's ontology.

> **Semantic Label**: This label is applied directly to provider-specific nodes; it does not create a separate node.

> **Implementations**: `AWSServicePrincipal`, `DatabricksAccountServicePrincipal`, `DatabricksServicePrincipal`, `EntraServicePrincipal`, `GCPServiceAccount`, `KubernetesServiceAccount`, `ModalServiceUser`, `OpenAIServiceAccount`, `ScalewayApplication`, `SnowflakeServiceUser`.

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| *_ont_active* | Yes | Normalized active for nodes carrying `ServiceAccount`. |
| *_ont_email* | Yes | Normalized email for nodes carrying `ServiceAccount`. |
| *_ont_name* | Yes | Normalized name for nodes carrying `ServiceAccount`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |

#### Relationships

- `(:APIKey)-[:OWNED_BY]->(:ServiceAccount)`: `OWNED_BY` is the canonical relationship name from `APIKey` to `ServiceAccount`. This constraint validates existing relationships and does not create them.

- `(:ComputeCluster)-[:RESOURCE]->(:ServiceAccount)`

- `(:ComputeInstance)-[:RUNS_AS]->(:ServiceAccount)`: `RUNS_AS` is the canonical relationship name from `ComputeInstance` to `ServiceAccount`. This constraint validates existing relationships and does not create them.

- `(:ComputeNamespace)-[:CONTAINS]->(:ServiceAccount)`

- `(:ComputePod)-[:RUNS_AS]->(:ServiceAccount)`: `RUNS_AS` is the canonical relationship name from `ComputePod` to `ServiceAccount`. This constraint validates existing relationships and does not create them.

- `(:ComputePod)-[:USES_SERVICE_ACCOUNT]->(:ServiceAccount)`

- `(:ComputeService)-[:RUNS_AS]->(:ServiceAccount)`: `RUNS_AS` is the canonical relationship name from `ComputeService` to `ServiceAccount`. This constraint validates existing relationships and does not create them.

- `(:ComputeService)-[:USES_SERVICE_ACCOUNT]->(:ServiceAccount)`

- `(:Database)-[:USES_SERVICE_ACCOUNT]->(:ServiceAccount)`

- `(:Function)-[:RUNS_AS]->(:ServiceAccount)`: `RUNS_AS` is the canonical relationship name from `Function` to `ServiceAccount`. This constraint validates existing relationships and does not create them.

- `(:ServiceAccount)-[:ASSIGNED_TO]->(:Tenant)`
  - Properties:

    | Field | Description |
    |-------|-------------|
    | permissions | Workspace permissions granted to the account principal. |

- `(:ServiceAccount)-[:ASSUMES_ROLE]->(:PermissionRole)`

- `(:ServiceAccount)-[:CAN_ACCESS]->(:Tenant)`
  - Properties:

    | Field | Description |
    |-------|-------------|
    | has_condition | Whether every grant path to the project is gated by an IAM rule condition. |

- `(:ServiceAccount)-[:CREATED_BY]->(:UserAccount)`

- `(:ServiceAccount)-[:GOVERNED_BY]->(:NetworkAccessControl)`

- `(:ServiceAccount)-[:HAS]->(:APIKey)`

- `(:ServiceAccount)-[:HAS_KEY]->(:APIKey)`

- `(:ServiceAccount)-[:HAS_ROLE]->(:PermissionRole)`: `HAS_ROLE` is the canonical relationship name from `ServiceAccount` to `PermissionRole`. This constraint validates existing relationships and does not create them.
  - Properties:

    | Field | Description |
    |-------|-------------|
    | created_on | When the role was granted. |
    | granted_by | Name of the role that created the grant. |

- `(:ServiceAccount)-[:MEMBER_OF]->(:UserGroup)`: `MEMBER_OF` is the canonical relationship name from `ServiceAccount` to `UserGroup`. This constraint validates existing relationships and does not create them.

- `(:ServiceAccount)-[:OWNS]->(:APIKey)`

- `(:ServiceAccount)-[:WORKLOAD_IDENTITY_BINDING]->(:ServiceAccount)`

- `(:Tenant)-[:RESOURCE]->(:ServiceAccount)`

- `(:ThirdPartyApp)-[:SERVICE_PRINCIPAL]->(:ServiceAccount)`

(ontology-snapshot)=
### Snapshot

A cross-provider Snapshot resource in Cartography's ontology.

> **Semantic Label**: This label is applied directly to provider-specific nodes; it does not create a separate node.

> **Implementations**: `AWSEBSSnapshot`, `AWSRDSSnapshot`, `AzureSnapshot`, `NetlifyDatabaseSnapshot`, `ScalewayVolumeSnapshot`.

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| *_ont_created_at* | Yes | Normalized created at for nodes carrying `Snapshot`. |
| *_ont_encrypted* | Yes | Normalized encrypted for nodes carrying `Snapshot`. |
| *_ont_name* | Yes | Normalized name for nodes carrying `Snapshot`. |
| *_ont_public* | Yes | Normalized public for nodes carrying `Snapshot`. |
| *_ont_region* | Yes | Normalized region for nodes carrying `Snapshot`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |
| *_ont_source_id* | Yes | Normalized source id for nodes carrying `Snapshot`. |

#### Relationships

- `(:BlockStorage)-[:HAS]->(:Snapshot)`

- `(:Database)-[:HAS_SNAPSHOT]->(:Snapshot)`

- `(:Snapshot)-[:CREATED_FROM]->(:BlockStorage)`

- `(:Snapshot)-[:IS_SNAPSHOT_SOURCE]->(:Database)`

- `(:Snapshot)-[:TAGGED]->(:Tag)`

- `(:Tenant)-[:RESOURCE]->(:Snapshot)`

(ontology-subnet)=
### Subnet

A cross-provider Subnet resource in Cartography's ontology.

> **Semantic Label**: This label is applied directly to provider-specific nodes; it does not create a separate node.

> **Implementations**: `AWSEC2Subnet`, `AzureSubnet`, `GCPSubnet`, `ScalewaySubnet`.

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| *_ont_availability_zone* | Yes | Normalized availability zone for nodes carrying `Subnet`. |
| *_ont_cidr_block* | Yes | Normalized cidr block for nodes carrying `Subnet`. |
| *_ont_name* | Yes | Normalized name for nodes carrying `Subnet`. |
| *_ont_region* | Yes | Normalized region for nodes carrying `Subnet`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |

#### Relationships

- `(:ComputeInstance)-[:PART_OF_SUBNET]->(:Subnet)`

- `(:ComputePod)-[:ATTACHED_TO]->(:Subnet)`

- `(:Database)-[:PART_OF_SUBNET]->(:Subnet)`

- `(:LoadBalancer)-[:IN_SUBNET]->(:Subnet)`

- `(:LoadBalancer)-[:PART_OF_SUBNET]->(:Subnet)`

- `(:LoadBalancer)-[:SUBNET]->(:Subnet)`

- `(:Subnet)-[:ASSOCIATED_WITH]->(:NetworkAccessControl)`

- `(:Subnet)-[:MEMBER_OF_AWS_VPC]->(:VirtualNetwork)`

- `(:Subnet)-[:RESOURCE]->(:LoadBalancer)`

- `(:Subnet)-[:TAGGED]->(:Tag)`

- `(:Tenant)-[:RESOURCE]->(:Subnet)`

- `(:VirtualNetwork)-[:CONTAINS]->(:Subnet)`

- `(:VirtualNetwork)-[:HAS]->(:Subnet)`

(ontology-tag)=
### Tag

A cross-provider Tag resource in Cartography's ontology.

> **Semantic Label**: This label is applied directly to provider-specific nodes; it does not create a separate node.

> **Implementations**: `AWSTag`, `AzureTag`, `GCPLabel`, `TenableAssetTag`.

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| *_ont_source* |  | Module that populated this node's ontology fields. |

#### Relationships

- `(:BlockStorage)-[:TAGGED]->(:Tag)`

- `(:ComputeCluster)-[:LABELED]->(:Tag)`

- `(:ComputeCluster)-[:TAGGED]->(:Tag)`

- `(:ComputeInstance)-[:LABELED]->(:Tag)`

- `(:ComputeInstance)-[:TAGGED]->(:Tag)`

- `(:ComputePod)-[:TAGGED]->(:Tag)`

- `(:ComputeService)-[:LABELED]->(:Tag)`

- `(:ComputeService)-[:TAGGED]->(:Tag)`

- `(:Container)-[:TAGGED]->(:Tag)`

- `(:ContainerRegistry)-[:TAGGED]->(:Tag)`

- `(:DNSZone)-[:LABELED]->(:Tag)`

- `(:DNSZone)-[:TAGGED]->(:Tag)`

- `(:Database)-[:LABELED]->(:Tag)`

- `(:Database)-[:TAGGED]->(:Tag)`

- `(:EncryptionKey)-[:TAGGED]->(:Tag)`

- `(:Function)-[:LABELED]->(:Tag)`

- `(:Function)-[:TAGGED]->(:Tag)`

- `(:LoadBalancer)-[:TAGGED]->(:Tag)`

- `(:NetworkAccessControl)-[:TAGGED]->(:Tag)`

- `(:ObjectStorage)-[:LABELED]->(:Tag)`

- `(:ObjectStorage)-[:TAGGED]->(:Tag)`

- `(:PermissionRole)-[:TAGGED]->(:Tag)`

- `(:Secret)-[:LABELED]->(:Tag)`

- `(:Secret)-[:TAGGED]->(:Tag)`

- `(:SecurityIssue)-[:TAGGED]->(:Tag)`

- `(:Snapshot)-[:TAGGED]->(:Tag)`

- `(:Subnet)-[:TAGGED]->(:Tag)`

- `(:Tenant)-[:RESOURCE]->(:Tag)`

- `(:UserAccount)-[:TAGGED]->(:Tag)`

- `(:VirtualNetwork)-[:TAGGED]->(:Tag)`

(ontology-tenant)=
### Tenant

A cross-provider Tenant resource in Cartography's ontology.

> **Semantic Label**: This label is applied directly to provider-specific nodes; it does not create a separate node.

> **Implementations**: `AWSAccount`, `AWSOrganization`, `AirbyteOrganization`, `AnthropicOrganization`, `AzureSubscription`, `AzureTenant`, `CircleCIOrganization`, `CloudflareAccount`, `CrowdstrikeTenant`, `DOAccount`, `DOProject`, `DatabricksAccount`, `DatabricksWorkspace`, `DuoApiHost`, `GCPOrganization`, `GCPProject`, `GSuiteTenant`, `GitHubOrganization`, `GoogleWorkspaceTenant`, `JamfTenant`, `JumpCloudTenant`, `KandjiTenant`, `KeycloakRealm`, `LastpassTenant`, `MiradoreTenant`, `ModalEnvironment`, `ModalWorkspace`, `NetlifyAccount`, `OpenAIOrganization`, `OpenAIProject`, `RailwayProject`, `RailwayWorkspace`, `S1Account`, `SalesforceOrganization`, `ScalewayOrganization`, `ScalewayProject`, `SentryOrganization`, `SlackTeam`, `SnipeitTenant`, `SnowflakeAccount`, `SnowflakeManagedAccount`, `SnowflakeOrganization`, `SocketDevOrganization`, `SpaceliftAccount`, `SubImageTenant`, `SupabaseOrganization`, `SupabaseProject`, `TailscaleTailnet`, `VercelTeam`, `WizTenant`, `WorkOSOrganization`.

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| *_ont_domain* | Yes | Normalized domain for nodes carrying `Tenant`. |
| *_ont_name* | Yes | Normalized name for nodes carrying `Tenant`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |
| *_ont_status* | Yes | Normalized status for nodes carrying `Tenant`. |

#### Relationships

- `(:CodeRepository)-[:OWNER]->(:Tenant)`

- `(:ComputeInstance)-[:RESOURCE]->(:Tenant)`

- `(:DNSRecord)-[:POINTS_TO]->(:Tenant)`

- `(:SecurityIssue)-[:REMOTE_ACCOUNT]->(:Tenant)`

- `(:ServiceAccount)-[:ASSIGNED_TO]->(:Tenant)`
  - Properties:

    | Field | Description |
    |-------|-------------|
    | permissions | Workspace permissions granted to the account principal. |

- `(:ServiceAccount)-[:CAN_ACCESS]->(:Tenant)`
  - Properties:

    | Field | Description |
    |-------|-------------|
    | has_condition | Whether every grant path to the project is gated by an IAM rule condition. |

- `(:Tenant)-[:ASSOCIATED_WITH]->(:Tenant)`

- `(:Tenant)-[:GOVERNED_BY]->(:NetworkAccessControl)`

- `(:Tenant)-[:HAS]->(:PermissionRole)`

- `(:Tenant)-[:HAS_ASSESSMENT]->(:SecurityIssue)`

- `(:Tenant)-[:HAS_USER]->(:UserAccount)`

- `(:Tenant)-[:MEMBER]->(:CVE)`

- `(:Tenant)-[:MEMBER]->(:SecurityIssue)`

- `(:Tenant)-[:OWNS]->(:APIKey)`

- `(:Tenant)-[:PARENT]->(:Tenant)`

- `(:Tenant)-[:RESOURCE]->(:AIModel)`

- `(:Tenant)-[:RESOURCE]->(:APIKey)`

- `(:Tenant)-[:RESOURCE]->(:BlockStorage)`

- `(:Tenant)-[:RESOURCE]->(:CICDPipeline)`

- `(:Tenant)-[:RESOURCE]->(:CVE)`

- `(:Tenant)-[:RESOURCE]->(:Certificate)`

- `(:Tenant)-[:RESOURCE]->(:ComputeCluster)`

- `(:Tenant)-[:RESOURCE]->(:ComputeInstance)`

- `(:Tenant)-[:RESOURCE]->(:ComputeNamespace)`

- `(:Tenant)-[:RESOURCE]->(:ComputePod)`

- `(:Tenant)-[:RESOURCE]->(:ComputeService)`

- `(:Tenant)-[:RESOURCE]->(:Container)`

- `(:Tenant)-[:RESOURCE]->(:ContainerRegistry)`

- `(:Tenant)-[:RESOURCE]->(:DNSRecord)`

- `(:Tenant)-[:RESOURCE]->(:DNSZone)`

- `(:Tenant)-[:RESOURCE]->(:Database)`

- `(:Tenant)-[:RESOURCE]->(:EncryptionKey)`

- `(:Tenant)-[:RESOURCE]->(:FileStorage)`

- `(:Tenant)-[:RESOURCE]->(:Function)`

- `(:Tenant)-[:RESOURCE]->(:IdentityProvider)`

- `(:Tenant)-[:RESOURCE]->(:Image)`

- `(:Tenant)-[:RESOURCE]->(:ImageAttestation)`

- `(:Tenant)-[:RESOURCE]->(:ImageLayer)`

- `(:Tenant)-[:RESOURCE]->(:ImageManifestList)`

- `(:Tenant)-[:RESOURCE]->(:ImageTag)`

- `(:Tenant)-[:RESOURCE]->(:LoadBalancer)`

- `(:Tenant)-[:RESOURCE]->(:NetworkAccessControl)`

- `(:Tenant)-[:RESOURCE]->(:ObjectStorage)`

- `(:Tenant)-[:RESOURCE]->(:PermissionRole)`

- `(:Tenant)-[:RESOURCE]->(:Secret)`

- `(:Tenant)-[:RESOURCE]->(:SecurityIssue)`

- `(:Tenant)-[:RESOURCE]->(:ServiceAccount)`

- `(:Tenant)-[:RESOURCE]->(:Snapshot)`

- `(:Tenant)-[:RESOURCE]->(:Subnet)`

- `(:Tenant)-[:RESOURCE]->(:Tag)`

- `(:Tenant)-[:RESOURCE]->(:Tenant)`

- `(:Tenant)-[:RESOURCE]->(:ThirdPartyApp)`

- `(:Tenant)-[:RESOURCE]->(:UserAccount)`

- `(:Tenant)-[:RESOURCE]->(:UserGroup)`

- `(:Tenant)-[:RESOURCE]->(:VirtualNetwork)`

- `(:ThirdPartyApp)-[:BELONGS_TO]->(:Tenant)`

- `(:UserAccount)-[:ADMIN_OF]->(:Tenant)`

- `(:UserAccount)-[:ASSIGNED_TO]->(:Tenant)`
  - Properties:

    | Field | Description |
    |-------|-------------|
    | permissions | Workspace permissions granted to the account principal. |

- `(:UserAccount)-[:BELONGS_TO]->(:Tenant)`

- `(:UserAccount)-[:CAN_ACCESS]->(:Tenant)`
  - Properties:

    | Field | Description |
    |-------|-------------|
    | has_condition | Whether every grant path to the project is gated by an IAM rule condition. |

- `(:UserAccount)-[:MEMBER_OF]->(:Tenant)`
  - Properties:

    | Field | Description |
    |-------|-------------|
    | confirmed | Value sourced from `confirmed`. |
    | created_at | When the membership was created. |
    | deleted_at | Value sourced from `deleted_at`. |
    | invite_id | Id of the outstanding invitation, when there is one. |
    | joined_at | Value sourced from `joined_at`. |
    | joined_from | Value sourced from `joinedFrom`. |
    | last_active_at | Value sourced from `last_active_at`. |
    | managed_by_directory_sync | Whether this membership is provisioned by directory sync. |
    | member_id | Value sourced from `member_id`. |
    | member_role | Value sourced from `member_role`. |
    | membership_id | Id of the membership row in this team. |
    | pending | Whether an invitation to this team is still outstanding. |
    | role | Value sourced from `role`. |
    | site_access | Which of the team's sites this member can reach (`all`, `none`, ...). |
    | updated_at | When the membership was last modified. |

- `(:UserAccount)-[:RESOURCE]->(:Tenant)`

- `(:UserAccount)-[:UNAFFILIATED]->(:Tenant)`

- `(:UserGroup)-[:ASSIGNED_TO]->(:Tenant)`
  - Properties:

    | Field | Description |
    |-------|-------------|
    | permissions | Workspace permissions granted to the account principal. |

- `(:UserGroup)-[:CAN_ACCESS]->(:Tenant)`
  - Properties:

    | Field | Description |
    |-------|-------------|
    | has_condition | Whether every grant path to the project is gated by an IAM rule condition. |

(ontology-thirdpartyapp)=
### ThirdPartyApp

A cross-provider ThirdPartyApp resource in Cartography's ontology.

> **Semantic Label**: This label is applied directly to provider-specific nodes; it does not create a separate node.

> **Implementations**: `EntraApplication`, `GoogleWorkspaceOAuthApp`, `JumpCloudSaaSApplication`, `KeycloakClient`, `NetlifyServiceInstance`, `SalesforceConnectedApp`, `SlackBot`, `WorkOSApplication`.

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| *_ont_client_id* | Yes | Normalized client id for nodes carrying `ThirdPartyApp`. |
| *_ont_enabled* | Yes | Normalized enabled for nodes carrying `ThirdPartyApp`. |
| *_ont_name* | Yes | Normalized name for nodes carrying `ThirdPartyApp`. |
| *_ont_native_app* | Yes | Normalized native app for nodes carrying `ThirdPartyApp`. |
| *_ont_protocol* | Yes | Normalized protocol for nodes carrying `ThirdPartyApp`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |

#### Relationships

- `(:ComputeService)-[:HAS_SERVICE_INSTANCE]->(:ThirdPartyApp)`

- `(:Tenant)-[:RESOURCE]->(:ThirdPartyApp)`

- `(:ThirdPartyApp)-[:BELONGS_TO]->(:Tenant)`

- `(:ThirdPartyApp)-[:CREATED]->(:UserGroup)`

- `(:ThirdPartyApp)-[:DEFINES]->(:PermissionRole)`

- `(:ThirdPartyApp)-[:HAS_SECRET]->(:APIKey)`

- `(:ThirdPartyApp)-[:HAS_SERVICE_ACCOUNT]->(:UserAccount)`

- `(:ThirdPartyApp)-[:MEMBER_OF]->(:UserGroup)`

- `(:ThirdPartyApp)-[:SERVICE_PRINCIPAL]->(:ServiceAccount)`

- `(:User)-[:AUTHORIZED]->(:ThirdPartyApp)`: generated by analysis job `Ontology - User AUTHORIZED ThirdPartyApp linking`.
  - Properties:

    | Field | Description |
    |-------|-------------|
    | scopes | Property generated by analysis job: `Ontology - User AUTHORIZED ThirdPartyApp linking`. |

- `(:UserAccount)-[:AUTHORIZED]->(:ThirdPartyApp)`
  - Properties:

    | Field | Description |
    |-------|-------------|
    | scopes | Value sourced from `scopes`. |

- `(:UserAccount)-[:USES]->(:ThirdPartyApp)`

(ontology-user)=
### User

A canonical person or agent aggregated across provider user accounts.

> **Abstract Ontology Node**: This is a dedicated canonical node created separately from provider-specific nodes.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Canonical user identifier. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| active |  | Whether the user is active, or null when unknown. |
| email | Yes | User's primary email address. |
| firstname |  | User's first name. |
| fullname |  | User's full name. |
| lastname |  | User's last name. |

#### Relationships

- `(:User)-[:AUTHORIZED]->(:ThirdPartyApp)`: generated by analysis job `Ontology - User AUTHORIZED ThirdPartyApp linking`.
  - Properties:

    | Field | Description |
    |-------|-------------|
    | scopes | Property generated by analysis job: `Ontology - User AUTHORIZED ThirdPartyApp linking`. |

- `(:User)-[:HAS_ACCOUNT]->(:UserAccount)`: `HAS_ACCOUNT` is the canonical relationship name from `User` to `UserAccount`. This constraint validates existing relationships and does not create them.

- `(:User)-[:OWNS]->(:APIKey)`: generated by analysis job `Ontology - User OWNS APIKey linking`.

- `(:User)-[:OWNS]->(:Device)`: generated by analysis job `Ontology - Devices OWNS relationship linking`.

(ontology-useraccount)=
### UserAccount

An identity on a specific system or service.

> **Semantic Label**: This label is applied directly to provider-specific nodes; it does not create a separate node.

> **Implementations**: `AWSSSOUser`, `AWSUser`, `AirbyteUser`, `AnthropicUser`, `CloudflareMember`, `DatabricksAccountUser`, `DatabricksUser`, `DuoUser`, `EntraUser`, `GSuiteUser`, `GitHubUser`, `GitLabUser`, `GoogleWorkspaceUser`, `JumpCloudUser`, `KeycloakUser`, `KubernetesUser`, `LastpassUser`, `MiradoreUser`, `ModalUser`, `NetlifyUser`, `OCIUser`, `OpenAIUser`, `PagerDutyUser`, `RailwayUser`, `SalesforceUser`, `ScalewayUser`, `SentryUser`, `SlackUser`, `SnipeitUser`, `SnowflakeUser`, `SpaceliftUser`, `SubImageTeamMember`, `SupabaseOrganizationMember`, `TailscaleUser`, `VercelUser`, `WorkOSDirectoryUser`, `WorkOSUser`.

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| *_ont_active* | Yes | Normalized active for nodes carrying `UserAccount`. |
| *_ont_email* | Yes | Normalized email for nodes carrying `UserAccount`. |
| *_ont_firstname* | Yes | Normalized firstname for nodes carrying `UserAccount`. |
| *_ont_fullname* | Yes | Normalized fullname for nodes carrying `UserAccount`. |
| *_ont_has_mfa* | Yes | Normalized has mfa for nodes carrying `UserAccount`. |
| *_ont_inactive* | Yes | Normalized inactive for nodes carrying `UserAccount`. |
| *_ont_lastactivity* | Yes | Normalized lastactivity for nodes carrying `UserAccount`. |
| *_ont_lastname* | Yes | Normalized lastname for nodes carrying `UserAccount`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |
| *_ont_username* | Yes | Normalized username for nodes carrying `UserAccount`. |

#### Relationships

- `(:APIKey)-[:OWNED_BY]->(:UserAccount)`: `OWNED_BY` is the canonical relationship name from `APIKey` to `UserAccount`. This constraint validates existing relationships and does not create them.

- `(:CVE)-[:ASSIGNED_TO]->(:UserAccount)`

- `(:CVE)-[:DISMISSED_BY]->(:UserAccount)`

- `(:CodeRepository)-[:OWNER]->(:UserAccount)`

- `(:ComputeCluster)-[:RESOURCE]->(:UserAccount)`

- `(:FileStorage)-[:CREATED_BY]->(:UserAccount)`

- `(:PermissionRole)-[:ALLOWED_BY]->(:UserAccount)`
  - Properties:

    | Field | Description |
    |-------|-------------|
    | permission_set_arn | ARN of the IAM Identity Center permission set that grants this relationship. |

- `(:PermissionRole)-[:MAPS_TO]->(:UserAccount)`

- `(:Secret)-[:CREATED_BY]->(:UserAccount)`

- `(:Secret)-[:UPDATED_BY]->(:UserAccount)`

- `(:SecurityIssue)-[:AFFECTS]->(:UserAccount)`

- `(:SecurityIssue)-[:ASSIGNED_TO]->(:UserAccount)`

- `(:SecurityIssue)-[:DISMISSED_BY]->(:UserAccount)`

- `(:ServiceAccount)-[:CREATED_BY]->(:UserAccount)`

- `(:Tenant)-[:HAS_USER]->(:UserAccount)`

- `(:Tenant)-[:RESOURCE]->(:UserAccount)`

- `(:ThirdPartyApp)-[:HAS_SERVICE_ACCOUNT]->(:UserAccount)`

- `(:User)-[:HAS_ACCOUNT]->(:UserAccount)`: `HAS_ACCOUNT` is the canonical relationship name from `User` to `UserAccount`. This constraint validates existing relationships and does not create them.

- `(:UserAccount)-[:ADMIN_OF]->(:Tenant)`

- `(:UserAccount)-[:ADMIN_OF]->(:UserGroup)`

- `(:UserAccount)-[:ASSIGNED_TO]->(:Tenant)`
  - Properties:

    | Field | Description |
    |-------|-------------|
    | permissions | Workspace permissions granted to the account principal. |

- `(:UserAccount)-[:ASSUMED_ROLE_WITH_SAML]->(:PermissionRole)`
  - Properties:

    | Field | Description |
    |-------|-------------|
    | first_seen_in_time_window | Timestamp when this relationship was first observed in the current time window. |
    | last_used | Timestamp when this relationship was last observed in use. |
    | times_used | Number of times this relationship was observed in use. |

- `(:UserAccount)-[:ASSUME_ROLE]->(:PermissionRole)`

- `(:UserAccount)-[:AUTHORIZED]->(:ThirdPartyApp)`
  - Properties:

    | Field | Description |
    |-------|-------------|
    | scopes | Value sourced from `scopes`. |

- `(:UserAccount)-[:AWS_ACCESS_KEY]->(:APIKey)`

- `(:UserAccount)-[:BELONGS_TO]->(:Tenant)`

- `(:UserAccount)-[:CAN_ACCESS]->(:Tenant)`
  - Properties:

    | Field | Description |
    |-------|-------------|
    | has_condition | Whether every grant path to the project is gated by an IAM rule condition. |

- `(:UserAccount)-[:CAN_ASSUME_IDENTITY]->(:UserAccount)`

- `(:UserAccount)-[:CAN_SIGN_ON_TO]->(:UserAccount)`

- `(:UserAccount)-[:COMMITTED_TO]->(:CodeRepository)`
  - Properties:

    | Field | Description |
    |-------|-------------|
    | commit_count | Number of commits made by the user to the project. |
    | first_commit_date | Timestamp of the user's oldest commit to the project. |
    | last_commit_date | Timestamp of the user's most recent commit to the project. |

- `(:UserAccount)-[:CREATED]->(:UserGroup)`

- `(:UserAccount)-[:DIRECT_COLLAB_ADMIN]->(:CodeRepository)`

- `(:UserAccount)-[:DIRECT_COLLAB_MAINTAIN]->(:CodeRepository)`

- `(:UserAccount)-[:DIRECT_COLLAB_READ]->(:CodeRepository)`

- `(:UserAccount)-[:DIRECT_COLLAB_TRIAGE]->(:CodeRepository)`

- `(:UserAccount)-[:DIRECT_COLLAB_WRITE]->(:CodeRepository)`

- `(:UserAccount)-[:GOVERNED_BY]->(:NetworkAccessControl)`

- `(:UserAccount)-[:HAS]->(:APIKey)`

- `(:UserAccount)-[:HAS_IDENTITY]->(:IdentityProvider)`

- `(:UserAccount)-[:HAS_PERMISSION_SET]->(:PermissionRole)`

- `(:UserAccount)-[:HAS_ROLE]->(:PermissionRole)`: `HAS_ROLE` is the canonical relationship name from `UserAccount` to `PermissionRole`. This constraint validates existing relationships and does not create them.
  - Properties:

    | Field | Description |
    |-------|-------------|
    | created_on | When the role was granted. |
    | granted_by | Name of the role that created the grant. |

- `(:UserAccount)-[:INHERITED_MEMBER_OF]->(:UserGroup)`

- `(:UserAccount)-[:INHERITED_OWNER_OF]->(:UserGroup)`

- `(:UserAccount)-[:MAINTAINER]->(:UserGroup)`

- `(:UserAccount)-[:MAPS_TO]->(:UserAccount)`

- `(:UserAccount)-[:MAPS_TO]->(:UserGroup)`

- `(:UserAccount)-[:MEMBER]->(:UserGroup)`

- `(:UserAccount)-[:MEMBER_AWS_GROUP]->(:UserGroup)`

- `(:UserAccount)-[:MEMBER_GSUITE_GROUP]->(:UserGroup)`

- `(:UserAccount)-[:MEMBER_OCID_GROUP]->(:UserGroup)`

- `(:UserAccount)-[:MEMBER_OF]->(:Tenant)`
  - Properties:

    | Field | Description |
    |-------|-------------|
    | confirmed | Value sourced from `confirmed`. |
    | created_at | When the membership was created. |
    | deleted_at | Value sourced from `deleted_at`. |
    | invite_id | Id of the outstanding invitation, when there is one. |
    | joined_at | Value sourced from `joined_at`. |
    | joined_from | Value sourced from `joinedFrom`. |
    | last_active_at | Value sourced from `last_active_at`. |
    | managed_by_directory_sync | Whether this membership is provisioned by directory sync. |
    | member_id | Value sourced from `member_id`. |
    | member_role | Value sourced from `member_role`. |
    | membership_id | Id of the membership row in this team. |
    | pending | Whether an invitation to this team is still outstanding. |
    | role | Value sourced from `role`. |
    | site_access | Which of the team's sites this member can reach (`all`, `none`, ...). |
    | updated_at | When the membership was last modified. |

- `(:UserAccount)-[:MEMBER_OF]->(:UserGroup)`: `MEMBER_OF` is the canonical relationship name from `UserAccount` to `UserGroup`. This constraint validates existing relationships and does not create them.
  - Properties:

    | Field | Description |
    |-------|-------------|
    | access_level | Numeric GitLab access level for the group membership. |
    | role | Value sourced from `role`. |

- `(:UserAccount)-[:MEMBER_OF_DUO_GROUP]->(:UserGroup)`

- `(:UserAccount)-[:MEMBER_OF_SSO_GROUP]->(:UserGroup)`

- `(:UserAccount)-[:OUTSIDE_COLLAB_ADMIN]->(:CodeRepository)`

- `(:UserAccount)-[:OUTSIDE_COLLAB_MAINTAIN]->(:CodeRepository)`

- `(:UserAccount)-[:OUTSIDE_COLLAB_READ]->(:CodeRepository)`

- `(:UserAccount)-[:OUTSIDE_COLLAB_TRIAGE]->(:CodeRepository)`

- `(:UserAccount)-[:OUTSIDE_COLLAB_WRITE]->(:CodeRepository)`

- `(:UserAccount)-[:OWNER_GSUITE_GROUP]->(:UserGroup)`

- `(:UserAccount)-[:OWNER_OF]->(:UserGroup)`

- `(:UserAccount)-[:OWNS]->(:APIKey)`

- `(:UserAccount)-[:REPORTS_TO]->(:UserAccount)`

- `(:UserAccount)-[:RESOURCE]->(:Tenant)`

- `(:UserAccount)-[:TAGGED]->(:Tag)`

- `(:UserAccount)-[:UNAFFILIATED]->(:Tenant)`

- `(:UserAccount)-[:USES]->(:ThirdPartyApp)`

- `(:UserGroup)-[:HAS_MEMBER]->(:UserAccount)`

(ontology-usergroup)=
### UserGroup

A cross-provider UserGroup resource in Cartography's ontology.

> **Semantic Label**: This label is applied directly to provider-specific nodes; it does not create a separate node.

> **Implementations**: `AWSGroup`, `AWSSSOGroup`, `CircleCIGroup`, `DatabricksAccountGroup`, `DatabricksGroup`, `DuoGroup`, `EntraGroup`, `GSuiteGroup`, `GitHubTeam`, `GitLabGroup`, `GoogleWorkspaceGroup`, `KeycloakGroup`, `KubernetesGroup`, `OCIGroup`, `PagerDutyTeam`, `SalesforceGroup`, `ScalewayGroup`, `SentryTeam`, `SlackGroup`, `TailscaleGroup`, `VercelAccessGroup`.

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| *_ont_description* |  | Normalized description for nodes carrying `UserGroup`. |
| *_ont_email* | Yes | Normalized email for nodes carrying `UserGroup`. |
| *_ont_name* | Yes | Normalized name for nodes carrying `UserGroup`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |

#### Relationships

- `(:CodeRepository)-[:MEMBER_OF]->(:UserGroup)`

- `(:ComputeCluster)-[:RESOURCE]->(:UserGroup)`

- `(:PermissionRole)-[:ALLOWED_BY]->(:UserGroup)`
  - Properties:

    | Field | Description |
    |-------|-------------|
    | permission_set_arn | ARN of the IAM Identity Center permission set that grants this relationship. |

- `(:PermissionRole)-[:MAPS_TO]->(:UserGroup)`

- `(:PermissionRole)-[:OCI_POLICY_REFERENCE]->(:UserGroup)`

- `(:ServiceAccount)-[:MEMBER_OF]->(:UserGroup)`: `MEMBER_OF` is the canonical relationship name from `ServiceAccount` to `UserGroup`. This constraint validates existing relationships and does not create them.

- `(:Tenant)-[:RESOURCE]->(:UserGroup)`

- `(:ThirdPartyApp)-[:CREATED]->(:UserGroup)`

- `(:ThirdPartyApp)-[:MEMBER_OF]->(:UserGroup)`

- `(:UserAccount)-[:ADMIN_OF]->(:UserGroup)`

- `(:UserAccount)-[:CREATED]->(:UserGroup)`

- `(:UserAccount)-[:INHERITED_MEMBER_OF]->(:UserGroup)`

- `(:UserAccount)-[:INHERITED_OWNER_OF]->(:UserGroup)`

- `(:UserAccount)-[:MAINTAINER]->(:UserGroup)`

- `(:UserAccount)-[:MAPS_TO]->(:UserGroup)`

- `(:UserAccount)-[:MEMBER]->(:UserGroup)`

- `(:UserAccount)-[:MEMBER_AWS_GROUP]->(:UserGroup)`

- `(:UserAccount)-[:MEMBER_GSUITE_GROUP]->(:UserGroup)`

- `(:UserAccount)-[:MEMBER_OCID_GROUP]->(:UserGroup)`

- `(:UserAccount)-[:MEMBER_OF]->(:UserGroup)`: `MEMBER_OF` is the canonical relationship name from `UserAccount` to `UserGroup`. This constraint validates existing relationships and does not create them.
  - Properties:

    | Field | Description |
    |-------|-------------|
    | access_level | Numeric GitLab access level for the group membership. |
    | role | Value sourced from `role`. |

- `(:UserAccount)-[:MEMBER_OF_DUO_GROUP]->(:UserGroup)`

- `(:UserAccount)-[:MEMBER_OF_SSO_GROUP]->(:UserGroup)`

- `(:UserAccount)-[:OWNER_GSUITE_GROUP]->(:UserGroup)`

- `(:UserAccount)-[:OWNER_OF]->(:UserGroup)`

- `(:UserGroup)-[:ADMIN]->(:CodeRepository)`

- `(:UserGroup)-[:ASSIGNED_TO]->(:Tenant)`
  - Properties:

    | Field | Description |
    |-------|-------------|
    | permissions | Workspace permissions granted to the account principal. |

- `(:UserGroup)-[:CAN_ACCESS]->(:CodeRepository)`
  - Properties:

    | Field | Description |
    |-------|-------------|
    | access_level | Numeric GitLab access level granted to the group. |

- `(:UserGroup)-[:CAN_ACCESS]->(:Tenant)`
  - Properties:

    | Field | Description |
    |-------|-------------|
    | has_condition | Whether every grant path to the project is gated by an IAM rule condition. |

- `(:UserGroup)-[:GRANTS]->(:PermissionRole)`

- `(:UserGroup)-[:HAS_MEMBER]->(:UserAccount)`

- `(:UserGroup)-[:HAS_PERMISSION_SET]->(:PermissionRole)`

- `(:UserGroup)-[:HAS_ROLE]->(:PermissionRole)`: `HAS_ROLE` is the canonical relationship name from `UserGroup` to `PermissionRole`. This constraint validates existing relationships and does not create them.

- `(:UserGroup)-[:INHERITED_MEMBER_OF]->(:UserGroup)`

- `(:UserGroup)-[:INHERITED_OWNER_OF]->(:UserGroup)`

- `(:UserGroup)-[:MAINTAIN]->(:CodeRepository)`

- `(:UserGroup)-[:MEMBER_GSUITE_GROUP]->(:UserGroup)`
  - Properties:

    | Field | Description |
    |-------|-------------|
    | role | Value sourced from `role`. |

- `(:UserGroup)-[:MEMBER_OF]->(:UserGroup)`: `MEMBER_OF` is the canonical relationship name from `UserGroup` to `UserGroup`. This constraint validates existing relationships and does not create them.
  - Properties:

    | Field | Description |
    |-------|-------------|
    | role | Value sourced from `role`. |

- `(:UserGroup)-[:MEMBER_OF_TEAM]->(:UserGroup)`

- `(:UserGroup)-[:OWNER_GSUITE_GROUP]->(:UserGroup)`
  - Properties:

    | Field | Description |
    |-------|-------------|
    | role | Value sourced from `role`. |

- `(:UserGroup)-[:OWNER_OF]->(:UserGroup)`
  - Properties:

    | Field | Description |
    |-------|-------------|
    | role | Value sourced from `role`. |

- `(:UserGroup)-[:READ]->(:CodeRepository)`

- `(:UserGroup)-[:SUBGROUP_OF]->(:UserGroup)`

- `(:UserGroup)-[:TRIAGE]->(:CodeRepository)`

- `(:UserGroup)-[:WRITE]->(:CodeRepository)`

(ontology-virtualnetwork)=
### VirtualNetwork

A cross-provider VirtualNetwork resource in Cartography's ontology.

> **Semantic Label**: This label is applied directly to provider-specific nodes; it does not create a separate node.

> **Implementations**: `AWSVpc`, `AzureVirtualNetwork`, `GCPVpc`, `ScalewayVpc`.

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| *_ont_cidr* | Yes | Normalized cidr for nodes carrying `VirtualNetwork`. |
| *_ont_name* | Yes | Normalized name for nodes carrying `VirtualNetwork`. |
| *_ont_region* | Yes | Normalized region for nodes carrying `VirtualNetwork`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |

#### Relationships

- `(:ComputeInstance)-[:MEMBER_OF_GCP_VPC]->(:VirtualNetwork)`: generated by analysis job `GCP Instance to VPC derived relationship analysis`.

- `(:Database)-[:ASSOCIATED_WITH]->(:VirtualNetwork)`

- `(:NetworkAccessControl)-[:MEMBER_OF]->(:VirtualNetwork)`

- `(:Subnet)-[:MEMBER_OF_AWS_VPC]->(:VirtualNetwork)`

- `(:Tenant)-[:RESOURCE]->(:VirtualNetwork)`

- `(:VirtualNetwork)-[:CONTAINS]->(:Subnet)`

- `(:VirtualNetwork)-[:HAS]->(:Subnet)`

- `(:VirtualNetwork)-[:MEMBER_OF_EC2_SECURITY_GROUP]->(:NetworkAccessControl)`

- `(:VirtualNetwork)-[:RESOURCE]->(:LoadBalancer)`

- `(:VirtualNetwork)-[:RESOURCE]->(:NetworkAccessControl)`

- `(:VirtualNetwork)-[:TAGGED]->(:Tag)`
