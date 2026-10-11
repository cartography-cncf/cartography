<!-- Generated from the data model. Do not edit manually. -->

## GCP Schema

```mermaid
graph LR
    GCPArtifactRegistryImage -- BUILT_FROM --> GCPArtifactRegistryImage
    GCPArtifactRegistryImage -- CONTAINS_IMAGE --> GCPArtifactRegistryImage
    GCPArtifactRegistryRepository -- CONTAINS --> GCPArtifactRegistryGenericArtifact
    GCPArtifactRegistryRepository -- CONTAINS --> GCPArtifactRegistryHelmChart
    GCPArtifactRegistryRepository -- CONTAINS --> GCPArtifactRegistryLanguagePackage
    GCPArtifactRegistryRepository -- CONTAINS --> GCPArtifactRegistryRepositoryImage
    GCPArtifactRegistryRepository -- REPO_IMAGE --> GCPArtifactRegistryRepositoryImage
    GCPArtifactRegistryRepositoryImage -- IMAGE --> GCPArtifactRegistryImage
    GCPBackendService -- EXPOSE --> GCPInstance
    GCPBackendService -- ROUTES_TO --> GCPInstanceGroup
    GCPBigQueryConnection -- CONNECTS_TO --> GCPCloudSQLInstance
    GCPBigQueryConnection -- CONNECTS_WITH --> GCPServiceAccount
    GCPBigQueryDataset -- HAS_ROUTINE --> GCPBigQueryRoutine
    GCPBigQueryDataset -- HAS_TABLE --> GCPBigQueryTable
    GCPBigQueryRoutine -- USES_CONNECTION --> GCPBigQueryConnection
    GCPBigQueryTable -- USES_CONNECTION --> GCPBigQueryConnection
    GCPBigtableAppProfile -- ROUTES_TO --> GCPBigtableCluster
    GCPBigtableCluster -- STORES_BACKUP --> GCPBigtableBackup
    GCPBigtableInstance -- HAS_APP_PROFILE --> GCPBigtableAppProfile
    GCPBigtableInstance -- HAS_CLUSTER --> GCPBigtableCluster
    GCPBigtableInstance -- HAS_TABLE --> GCPBigtableTable
    GCPBigtableInstance -- LABELED --> GCPLabel
    GCPBigtableInstance -- TAGGED --> GCPLabel
    GCPBigtableTable -- BACKED_UP_AS --> GCPBigtableBackup
    GCPBucket -- LABELED --> GCPBucketLabel
    GCPBucket -- LABELED --> GCPLabel
    GCPBucket -- TAGGED --> GCPLabel
    GCPCloudArmorPolicy -- PROTECTS --> GCPBackendService
    GCPCloudFunction -- LABELED --> GCPLabel
    GCPCloudFunction -- RUNS_AS --> GCPServiceAccount
    GCPCloudRunJob -- CONTAINS --> GCPCloudRunJobContainer
    GCPCloudRunJob -- HAS_EXECUTION --> GCPCloudRunExecution
    GCPCloudRunJob -- LABELED --> GCPLabel
    GCPCloudRunJob -- RUNS_AS --> GCPServiceAccount
    GCPCloudRunJob -- TAGGED --> GCPLabel
    GCPCloudRunJob -- USES_SERVICE_ACCOUNT --> GCPServiceAccount
    GCPCloudRunJobContainer -- HAS_IMAGE --> GCPArtifactRegistryImage
    GCPCloudRunJobContainer -- WORKLOAD_PARENT --> GCPCloudRunJob
    GCPCloudRunRevision -- USES_SERVICE_ACCOUNT --> GCPServiceAccount
    GCPCloudRunService -- CONTAINS --> GCPCloudRunServiceContainer
    GCPCloudRunService -- HAS_REVISION --> GCPCloudRunRevision
    GCPCloudRunService -- LABELED --> GCPLabel
    GCPCloudRunService -- RUNS_AS --> GCPServiceAccount
    GCPCloudRunService -- TAGGED --> GCPLabel
    GCPCloudRunService -- USES_SERVICE_ACCOUNT --> GCPServiceAccount
    GCPCloudRunServiceContainer -- HAS_IMAGE --> GCPArtifactRegistryImage
    GCPCloudRunServiceContainer -- WORKLOAD_PARENT --> GCPCloudRunService
    GCPCloudSQLInstance -- ASSOCIATED_WITH --> GCPVpc
    GCPCloudSQLInstance -- AUTHORIZED_NETWORK --> GCPCloudSQLAuthorizedNetwork
    GCPCloudSQLInstance -- CONTAINS --> GCPCloudSQLDatabase
    GCPCloudSQLInstance -- HAS_BACKUP_CONFIG --> GCPCloudSQLBackupConfiguration
    GCPCloudSQLInstance -- HAS_USER --> GCPCloudSQLUser
    GCPCloudSQLInstance -- LABELED --> GCPLabel
    GCPCloudSQLInstance -- TAGGED --> GCPLabel
    GCPCloudSQLInstance -- USES_SERVICE_ACCOUNT --> GCPServiceAccount
    GCPDNSZone -- HAS_RECORD --> GCPRecordSet
    GCPDNSZone -- LABELED --> GCPLabel
    GCPDNSZone -- TAGGED --> GCPLabel
    GCPFirewall -- FIREWALL_INGRESS --> GCPInstance
    GCPFirewall -- TARGET_TAG --> GCPNetworkTag
    GCPFolder -- PARENT --> GCPFolder
    GCPFolder -- PARENT --> GCPOrganization
    GCPFolder -- RESOURCE --> GCPPolicyBinding
    GCPForwardingRule -- ROUTES_TO --> GCPTargetHttpsProxy
    GCPForwardingRule -- ROUTES_TO --> GCPTargetSslProxy
    GCPInstance -- LABELED --> GCPLabel
    GCPInstance -- MEMBER_OF_GCP_VPC --> GCPVpc
    GCPInstance -- NETWORK_INTERFACE --> GCPNetworkInterface
    GCPInstance -- RUNS_AS --> GCPServiceAccount
    GCPInstance -- TAGGED --> GCPLabel
    GCPInstance -- TAGGED --> GCPNetworkTag
    GCPInstanceGroup -- HAS_MEMBER --> GCPInstance
    GCPIpRange -- MEMBER_OF_IP_RULE --> GCPIpRule
    GCPIpRule -- ALLOWED_BY --> GCPFirewall
    GCPIpRule -- DENIED_BY --> GCPFirewall
    GCPKeyRing -- CONTAINS --> GCPCryptoKey
    GCPNetworkInterface -- PART_OF_SUBNET --> GCPSubnet
    GCPNetworkInterface -- RESOURCE --> GCPNicAccessConfig
    GCPNetworkTag -- DEFINED_IN --> GCPVpc
    GCPOrganization -- RESOURCE --> GCPFolder
    GCPOrganization -- RESOURCE --> GCPPolicyBinding
    GCPOrganization -- RESOURCE --> GCPProject
    GCPOrganization -- RESOURCE --> GCPRole
    GCPPolicyBinding -- APPLIES_TO --> GCPArtifactRegistryRepository
    GCPPolicyBinding -- APPLIES_TO --> GCPBigQueryDataset
    GCPPolicyBinding -- APPLIES_TO --> GCPBigQueryTable
    GCPPolicyBinding -- APPLIES_TO --> GCPBucket
    GCPPolicyBinding -- APPLIES_TO --> GCPCloudFunction
    GCPPolicyBinding -- APPLIES_TO --> GCPCloudRunService
    GCPPolicyBinding -- APPLIES_TO --> GCPCryptoKey
    GCPPolicyBinding -- APPLIES_TO --> GCPFirewall
    GCPPolicyBinding -- APPLIES_TO --> GCPFolder
    GCPPolicyBinding -- APPLIES_TO --> GCPInstance
    GCPPolicyBinding -- APPLIES_TO --> GCPKeyRing
    GCPPolicyBinding -- APPLIES_TO --> GCPOrganization
    GCPPolicyBinding -- APPLIES_TO --> GCPProject
    GCPPolicyBinding -- APPLIES_TO --> GCPSecretManagerSecret
    GCPPolicyBinding -- APPLIES_TO --> GCPSecretManagerSecretVersion
    GCPPolicyBinding -- APPLIES_TO --> GCPServiceAccount
    GCPPolicyBinding -- APPLIES_TO --> GCPSubnet
    GCPPolicyBinding -- APPLIES_TO --> GCPVpc
    GCPPolicyBinding -- GRANTS_ROLE --> GCPRole
    GCPProject -- PARENT --> GCPFolder
    GCPProject -- PARENT --> GCPOrganization
    GCPProject -- RESOURCE --> GCPApiKey
    GCPProject -- RESOURCE --> GCPArtifactRegistryGenericArtifact
    GCPProject -- RESOURCE --> GCPArtifactRegistryHelmChart
    GCPProject -- RESOURCE --> GCPArtifactRegistryImageLayer
    GCPProject -- RESOURCE --> GCPArtifactRegistryLanguagePackage
    GCPProject -- RESOURCE --> GCPArtifactRegistryRepository
    GCPProject -- RESOURCE --> GCPArtifactRegistryRepositoryImage
    GCPProject -- RESOURCE --> GCPBackendService
    GCPProject -- RESOURCE --> GCPBigQueryConnection
    GCPProject -- RESOURCE --> GCPBigQueryDataset
    GCPProject -- RESOURCE --> GCPBigQueryRoutine
    GCPProject -- RESOURCE --> GCPBigQueryTable
    GCPProject -- RESOURCE --> GCPBigtableAppProfile
    GCPProject -- RESOURCE --> GCPBigtableBackup
    GCPProject -- RESOURCE --> GCPBigtableCluster
    GCPProject -- RESOURCE --> GCPBigtableInstance
    GCPProject -- RESOURCE --> GCPBigtableTable
    GCPProject -- RESOURCE --> GCPBucket
    GCPProject -- RESOURCE --> GCPBucketLabel
    GCPProject -- RESOURCE --> GCPCloudArmorPolicy
    GCPProject -- RESOURCE --> GCPCloudFunction
    GCPProject -- RESOURCE --> GCPCloudRunExecution
    GCPProject -- RESOURCE --> GCPCloudRunJob
    GCPProject -- RESOURCE --> GCPCloudRunJobContainer
    GCPProject -- RESOURCE --> GCPCloudRunRevision
    GCPProject -- RESOURCE --> GCPCloudRunService
    GCPProject -- RESOURCE --> GCPCloudRunServiceContainer
    GCPProject -- RESOURCE --> GCPCloudSQLAuthorizedNetwork
    GCPProject -- RESOURCE --> GCPCloudSQLBackupConfiguration
    GCPProject -- RESOURCE --> GCPCloudSQLDatabase
    GCPProject -- RESOURCE --> GCPCloudSQLInstance
    GCPProject -- RESOURCE --> GCPCloudSQLUser
    GCPProject -- RESOURCE --> GCPCryptoKey
    GCPProject -- RESOURCE --> GCPDNSZone
    GCPProject -- RESOURCE --> GCPFirewall
    GCPProject -- RESOURCE --> GCPForwardingRule
    GCPProject -- RESOURCE --> GCPInstance
    GCPProject -- RESOURCE --> GCPInstanceGroup
    GCPProject -- RESOURCE --> GCPIpRange
    GCPProject -- RESOURCE --> GCPIpRule
    GCPProject -- RESOURCE --> GCPKeyRing
    GCPProject -- RESOURCE --> GCPLabel
    GCPProject -- RESOURCE --> GCPNetworkInterface
    GCPProject -- RESOURCE --> GCPNetworkTag
    GCPProject -- RESOURCE --> GCPNicAccessConfig
    GCPProject -- RESOURCE --> GCPPolicyBinding
    GCPProject -- RESOURCE --> GCPRecordSet
    GCPProject -- RESOURCE --> GCPRole
    GCPProject -- RESOURCE --> GCPSecretManagerSecret
    GCPProject -- RESOURCE --> GCPSecretManagerSecretVersion
    GCPProject -- RESOURCE --> GCPServiceAccount
    GCPProject -- RESOURCE --> GCPServiceAccountKey
    GCPProject -- RESOURCE --> GCPSslPolicy
    GCPProject -- RESOURCE --> GCPSubnet
    GCPProject -- RESOURCE --> GCPTargetHttpsProxy
    GCPProject -- RESOURCE --> GCPTargetSslProxy
    GCPProject -- RESOURCE --> GCPVertexAIDataset
    GCPProject -- RESOURCE --> GCPVertexAIDeployedModel
    GCPProject -- RESOURCE --> GCPVertexAIEndpoint
    GCPProject -- RESOURCE --> GCPVertexAIFeatureGroup
    GCPProject -- RESOURCE --> GCPVertexAIModel
    GCPProject -- RESOURCE --> GCPVertexAITrainingPipeline
    GCPProject -- RESOURCE --> GCPVertexAIWorkbenchInstance
    GCPProject -- RESOURCE --> GCPVpc
    GCPProject -- RESOURCE --> GCPVpcPeering
    GCPProject -- RESOURCE --> GCPVpnGateway
    GCPProject -- RESOURCE --> GCPVpnTunnel
    GCPProject -- RESOURCE --> GCPWorkloadIdentityPool
    GCPProject -- RESOURCE --> GCPWorkloadIdentityProvider
    GCPProject -- RESOURCE --> GKECluster
    GCPSecretManagerSecret -- LABELED --> GCPLabel
    GCPSecretManagerSecret -- TAGGED --> GCPLabel
    GCPSecretManagerSecretVersion -- VERSION_OF --> GCPSecretManagerSecret
    GCPServiceAccount -- HAS_KEY --> GCPServiceAccountKey
    GCPServiceAccountKey -- OWNED_BY --> GCPServiceAccount
    GCPSubnet -- RESOURCE --> GCPForwardingRule
    GCPTargetHttpsProxy -- USES --> GCPSslPolicy
    GCPTargetSslProxy -- ROUTES_TO --> GCPBackendService
    GCPTargetSslProxy -- USES --> GCPSslPolicy
    GCPVertexAIDeployedModel -- INSTANCE_OF --> GCPVertexAIModel
    GCPVertexAIEndpoint -- SERVES --> GCPVertexAIDeployedModel
    GCPVertexAIModel -- STORED_IN --> GCPBucket
    GCPVertexAITrainingPipeline -- PRODUCES --> GCPVertexAIModel
    GCPVertexAITrainingPipeline -- READS_FROM --> GCPVertexAIDataset
    GCPVertexAIWorkbenchInstance -- USES_SERVICE_ACCOUNT --> GCPServiceAccount
    GCPVpc -- HAS --> GCPSubnet
    GCPVpc -- RESOURCE --> GCPFirewall
    GCPVpc -- RESOURCE --> GCPForwardingRule
    GCPVpcPeering -- LOCAL_NETWORK --> GCPVpc
    GCPVpcPeering -- PEER_NETWORK --> GCPVpc
    GCPVpnGateway -- PART_OF_VPC --> GCPVpc
    GCPVpnTunnel -- CONNECTS_TO_GATEWAY --> GCPVpnGateway
    GCPVpnTunnel -- USES_GATEWAY --> GCPVpnGateway
    GCPWorkloadIdentityPool -- HAS_ALLOW_POLICY --> GCPPolicyBinding
    GCPWorkloadIdentityProvider -- MEMBER_OF --> GCPWorkloadIdentityPool
    GKECluster -- LABELED --> GCPLabel
    GKECluster -- TAGGED --> GCPLabel
```

### GCPApiKey

A Google Cloud API Key resource.

> **Ontology Mapping**: This node uses the ontology label [`APIKey`](#ontology-apikey).

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Stable identifier for this resource. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| create_time |  | RFC 3339 timestamp when the key was created. |
| delete_time |  | RFC 3339 timestamp when the key was deleted, if applicable. |
| display_name |  | Human-readable display name of the key. |
| etag |  | The etag of the key. |
| name |  | Same as id. |
| restricted |  | Whether the key has any API or application restrictions. Unrestricted keys are higher risk. |
| restrictions |  | JSON-encoded restriction configuration (API targets, allowed referrers/IPs/apps), if any. |
| uid |  | The unique identifier of the key. |
| update_time |  | RFC 3339 timestamp when the key was last updated. |
| *_ont_created_at* | Yes | Normalized field sourced from `create_time`. |
| *_ont_name* | Yes | Normalized field sourced from `display_name`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |
| *_ont_updated_at* | Yes | Normalized field sourced from `update_time`. |

#### Relationships

- `(:User)-[:OWNS]->(:GCPApiKey)`: generated by analysis job `Ontology - User OWNS APIKey linking`.

- `(:GCPProject)-[:RESOURCE]->(:GCPApiKey)`

### GCPArtifactRegistryGenericArtifact

A Google Cloud Artifact Registry Generic Artifact resource.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Stable identifier for this resource. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| format |  | Artifact Registry package format, such as DOCKER, MAVEN, NPM, PYTHON, APT, or YUM. |
| name |  | Name assigned to this resource. |
| package_name |  | Package coordinate or name within the repository. |
| project_id |  | Google Cloud project that owns this resource. |
| repository_id |  | Full resource name of the containing Artifact Registry repository. |

#### Relationships

- `(:GCPArtifactRegistryRepository)-[:CONTAINS]->(:GCPArtifactRegistryGenericArtifact)`

- `(:GCPProject)-[:RESOURCE]->(:GCPArtifactRegistryGenericArtifact)`

### GCPArtifactRegistryHelmChart

A Google Cloud Artifact Registry Helm Chart resource.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Stable identifier for this resource. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| create_time |  | Timestamp when Google Cloud created this resource. |
| name |  | Name assigned to this resource. |
| project_id |  | Google Cloud project that owns this resource. |
| repository_id |  | Full resource name of the containing Artifact Registry repository. |
| update_time |  | Timestamp when Google Cloud last changed this resource. |
| uri |  | Artifact Registry URI used to retrieve this artifact or tagged image. |
| version |  | Artifact or chart version published in the repository. |

#### Relationships

- `(:GCPArtifactRegistryRepository)-[:CONTAINS]->(:GCPArtifactRegistryHelmChart)`

- `(:GCPProject)-[:RESOURCE]->(:GCPArtifactRegistryHelmChart)`

### GCPArtifactRegistryImage

This node label is loaded by more than one sync path:

- A Google Cloud Artifact Registry Image resource.
- A single-platform image referenced by an Artifact Registry manifest list.
- Build provenance and layer data attached to an Artifact Registry image.

> **Conditional Labels**:
>
> - [`Image`](#ontology-image) (ontology label) when `type` equals `image`. A concrete single-platform container image.
> - [`ImageAttestation`](#ontology-imageattestation) (ontology label) when `type` equals `attestation`. A cross-provider ImageAttestation resource in Cartography's ontology.
> - [`ImageManifestList`](#ontology-imagemanifestlist) (ontology label) when `type` equals `manifest_list`. A cross-provider ImageManifestList resource in Cartography's ontology.

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Immutable OCI content digest used as the node ID. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| architecture |  | CPU architecture declared by the OCI image configuration. |
| digest | Yes | Digest that identifies the immutable artifact or image content. |
| layer_diff_ids |  | Ordered uncompressed layer digests from the OCI image configuration. |
| media_type |  | OCI media type describing the manifest or artifact payload. |
| os |  | Operating system declared by the OCI image configuration. |
| os_features |  | Operating system feature list declared by the OCI platform metadata. |
| os_version |  | Operating system version declared by the OCI image configuration. |
| parent_image_digest |  | Immutable parent image digest extracted from a digest-verified SPDX SBOM relationship. |
| parent_image_uri |  | Parent image URI extracted from a digest-verified SPDX SBOM relationship. |
| source_file |  | Source file path extracted from verified build provenance or SPDX SBOM data. |
| source_revision |  | Source revision extracted from verified build provenance or SPDX SBOM data. |
| source_uri | Yes | Source repository URI extracted from verified build provenance or SPDX SBOM data. |
| type | Yes | OCI content classification derived from manifest and artifact metadata. |
| variant |  | CPU architecture variant declared by the OCI platform metadata. |
| *_ont_architecture* | Yes | Normalized field sourced from `architecture`. |
| *_ont_digest* | Yes | Normalized field sourced from `digest`. |
| *_ont_os* | Yes | Normalized field sourced from `os`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |
| *_ont_variant* | Yes | Normalized field sourced from `variant`. |

#### Relationships

- `(:GCPArtifactRegistryImage)-[:BUILT_FROM]->(:GCPArtifactRegistryImage)`
  - Properties:

    | Field | Description |
    |-------|-------------|
    | confidence | Parent-image evidence strength; digest-verified SBOM matches use `explicit`. |
    | from_sbom | Match-method flag set when parent-image evidence comes from a digest-verified SPDX SBOM relationship. |
    | parent_image_uri | Parent image URI extracted from a digest-verified SPDX SBOM relationship. |

- `(:GCPArtifactRegistryImage)-[:CONTAINS_IMAGE]->(:GCPArtifactRegistryImage)`

- `(:PackageVersion)-[:DEPLOYED]->(:GCPArtifactRegistryImage)`: A canonical package version is deployed on a container image.

- `(:AWSECSContainer)-[:HAS_IMAGE]->(:GCPArtifactRegistryImage)`: Matches containers to GAR image artifacts by runtime digest (imageDigest).

- `(:AWSLambda)-[:HAS_IMAGE]->(:GCPArtifactRegistryImage)`

- `(:AzureContainerInstance)-[:HAS_IMAGE]->(:GCPArtifactRegistryImage)`: An Azure container uses a Google Artifact Registry image with the same digest.

- `(:AzureFunctionApp)-[:HAS_IMAGE]->(:GCPArtifactRegistryImage)`: An Azure Function App uses a Google Artifact Registry image with the same digest.

- `(:GCPCloudRunJobContainer)-[:HAS_IMAGE]->(:GCPArtifactRegistryImage)`

- `(:GCPCloudRunServiceContainer)-[:HAS_IMAGE]->(:GCPArtifactRegistryImage)`

- `(:KubernetesContainer)-[:HAS_IMAGE]->(:GCPArtifactRegistryImage)`: Links a container to the image it runs, hosted in Artifact Registry.

- `(:ComputeService)-[:HAS_RUNTIME_IMAGE]->(:GCPArtifactRegistryImage)`: generated by analysis job `Workload HAS_RUNTIME_IMAGE inventory analysis`.
  - Properties:

    | Field | Description |
    |-------|-------------|
    | exposed_internet | Property generated by analysis job: `Workload HAS_RUNTIME_IMAGE inventory analysis`. |

- `(:GCPArtifactRegistryRepositoryImage)-[:IMAGE]->(:GCPArtifactRegistryImage)`

- `(:Container)-[:RESOLVED_IMAGE]->(:GCPArtifactRegistryImage)`: generated by analysis job `Container RESOLVED_IMAGE analysis`.

- `(:Function)-[:RESOLVED_IMAGE]->(:GCPArtifactRegistryImage)`: generated by analysis job `Function RESOLVED_IMAGE analysis`.

### GCPArtifactRegistryImageLayer

A Google Cloud Artifact Registry Image Layer resource.

> **Ontology Mapping**: This node uses the ontology label [`ImageLayer`](#ontology-imagelayer).

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Uncompressed OCI layer digest used as the node ID; compressed manifest digest and size are not stored. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| diff_id |  | Uncompressed OCI layer digest from rootfs.diff_ids; compressed manifest digest and size are not stored. |
| history |  | OCI created_by command aligned to this diff ID after empty-layer history entries are skipped. |

#### Relationships

- `(:GCPProject)-[:RESOURCE]->(:GCPArtifactRegistryImageLayer)`

### GCPArtifactRegistryLanguagePackage

A Google Cloud Artifact Registry Language Package resource.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Stable identifier for this resource. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| artifact_id |  | Maven artifact identifier when the artifact is a Maven package. |
| create_time |  | Timestamp when Google Cloud created this resource. |
| format |  | Artifact Registry package format, such as DOCKER, MAVEN, NPM, PYTHON, APT, or YUM. |
| group_id |  | Maven group identifier when the artifact is a Maven package. |
| name |  | Name assigned to this resource. |
| package_name |  | Package coordinate or name within the repository. |
| project_id |  | Google Cloud project that owns this resource. |
| repository_id |  | Full resource name of the containing Artifact Registry repository. |
| tags |  | Tag names associated with this artifact or image API record. |
| update_time |  | Timestamp when Google Cloud last changed this resource. |
| uri |  | Artifact Registry URI used to retrieve this artifact or tagged image. |
| version |  | Artifact or chart version published in the repository. |

#### Relationships

- `(:GCPArtifactRegistryRepository)-[:CONTAINS]->(:GCPArtifactRegistryLanguagePackage)`

- `(:GCPProject)-[:RESOURCE]->(:GCPArtifactRegistryLanguagePackage)`

### GCPArtifactRegistryRepository

A Google Cloud Artifact Registry Repository resource.

> **Ontology Mapping**: This node uses the ontology label [`ContainerRegistry`](#ontology-containerregistry).

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Stable identifier for this resource. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| cleanup_policy_dry_run |  | Whether cleanup policies are evaluated without deleting artifacts. |
| create_time |  | Timestamp when Google Cloud created this resource. |
| description |  | Description configured for this resource. |
| format |  | Artifact Registry package format, such as DOCKER, MAVEN, NPM, PYTHON, APT, or YUM. |
| kms_key_name |  | Cloud KMS key resource name used for repository encryption. |
| location |  | Google Cloud location where this resource is deployed. |
| mode |  | Repository mode, such as standard, remote, or virtual. |
| name |  | Name assigned to this resource. |
| project_id |  | Google Cloud project that owns this resource. |
| registry_uri |  | Registry hostname and repository path used to address repository content. |
| size_bytes |  | Stored content size in bytes. |
| update_time |  | Timestamp when Google Cloud last changed this resource. |
| vulnerability_scanning_enabled |  | Whether Artifact Analysis vulnerability scanning is enabled for the repository. |
| *_ont_created_at* | Yes | Normalized field sourced from `create_time`. |
| *_ont_location* | Yes | Normalized field sourced from `location`. |
| *_ont_name* | Yes | Normalized field sourced from `name`. |
| *_ont_size_bytes* | Yes | Normalized field sourced from `size_bytes`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |
| *_ont_uri* | Yes | Normalized field sourced from `registry_uri`. |

#### Relationships

- `(:GCPPolicyBinding)-[:APPLIES_TO]->(:GCPArtifactRegistryRepository)`: Connects a GCP IAM policy binding to the concrete resource where the policy applies.

- `(:GCPPrincipal)-[:CAN_READ]->(:GCPArtifactRegistryRepository)`: `GCPPrincipal` receives evaluated `CAN_READ` access to `GCPArtifactRegistryRepository` from GCP IAM policies.
  - Evaluated permissions: `artifactregistry.repositories.downloadArtifacts`
  - Properties:

    | Field | Description |
    |-------|-------------|
    | condition_expression | CEL expression that must be satisfied for this permission. |
    | condition_title | Title of the IAM condition that restricts this permission. |
    | has_condition | Whether an IAM condition restricts this permission. |

- `(:GCPPrincipal)-[:CAN_WRITE]->(:GCPArtifactRegistryRepository)`: `GCPPrincipal` receives evaluated `CAN_WRITE` access to `GCPArtifactRegistryRepository` from GCP IAM policies.
  - Evaluated permissions: `artifactregistry.repositories.uploadArtifacts`
  - Properties:

    | Field | Description |
    |-------|-------------|
    | condition_expression | CEL expression that must be satisfied for this permission. |
    | condition_title | Title of the IAM condition that restricts this permission. |
    | has_condition | Whether an IAM condition restricts this permission. |

- `(:GCPArtifactRegistryRepository)-[:CONTAINS]->(:GCPArtifactRegistryGenericArtifact)`

- `(:GCPArtifactRegistryRepository)-[:CONTAINS]->(:GCPArtifactRegistryHelmChart)`

- `(:GCPArtifactRegistryRepository)-[:CONTAINS]->(:GCPArtifactRegistryLanguagePackage)`

- `(:GCPArtifactRegistryRepository)-[:CONTAINS]->(:GCPArtifactRegistryRepositoryImage)`

- `(:GCPArtifactRegistryRepository)-[:REPO_IMAGE]->(:GCPArtifactRegistryRepositoryImage)`

- `(:GCPProject)-[:RESOURCE]->(:GCPArtifactRegistryRepository)`

### GCPArtifactRegistryRepositoryImage

A Google Cloud Artifact Registry Repository Image resource.

> **Ontology Mapping**: This node uses the ontology label [`ImageTag`](#ontology-imagetag).

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Tag-scoped pull URI used as the node ID; untagged API records use their digest-pinned URI. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| _ont_tag |  | Normalized tag used by the ImageTag ontology. |
| _ont_uri |  | Normalized pull URI used by the ImageTag ontology. |
| artifact_type |  | Artifact media type reported for the repository image. |
| build_time |  | Timestamp when the image was built, when reported. |
| digest | Yes | Digest that identifies the immutable artifact or image content. |
| digest_uri |  | Pullable repository URI pinned to the immutable image digest. |
| image_size_bytes |  | Compressed image size reported by Artifact Registry, in bytes. |
| media_type |  | OCI media type describing the manifest or artifact payload. |
| name |  | Final segment of the DockerImage API resource name. |
| project_id |  | Google Cloud project that owns this resource. |
| repository_id |  | Full resource name of the containing Artifact Registry repository. |
| resource_name | Yes | Artifact Registry DockerImage API resource name. |
| tag |  | Tag represented by this repository-scoped image node. |
| tags |  | Tag names associated with this artifact or image API record. |
| update_time |  | Timestamp when Google Cloud last changed this resource. |
| upload_time |  | Timestamp when the image was uploaded to Artifact Registry. |
| uri | Yes | Artifact Registry URI used to retrieve this artifact or tagged image. |

#### Relationships

- `(:GCPArtifactRegistryRepository)-[:CONTAINS]->(:GCPArtifactRegistryRepositoryImage)`

- `(:GCPArtifactRegistryRepositoryImage)-[:IMAGE]->(:GCPArtifactRegistryImage)`

- `(:GCPArtifactRegistryRepository)-[:REPO_IMAGE]->(:GCPArtifactRegistryRepositoryImage)`

- `(:GCPProject)-[:RESOURCE]->(:GCPArtifactRegistryRepositoryImage)`

### GCPBackendService

A Google Cloud Backend Service resource.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Stable identifier for this resource. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| creation_timestamp |  | Creation timestamp of the resource. |
| description |  | An optional description of this backend service. |
| load_balancing_scheme |  | The load balancing scheme (e.g., `EXTERNAL`, `EXTERNAL_MANAGED`, `INTERNAL`, `INTERNAL_MANAGED`). |
| name | Yes | The name of the backend service. |
| partial_uri |  | Same as `id`. |
| port |  | The port for the backend service. |
| port_name |  | A named port on a backend instance group. |
| project_id |  | The project ID that this backend service belongs to. |
| protocol |  | The protocol this backend service uses (e.g., `HTTP`, `HTTPS`, `TCP`, `SSL`). |
| region |  | The region of this backend service, or `null` for global backend services. |
| security_policy |  | The full URL of the Cloud Armor security policy attached to this backend service. |
| self_link |  | Server-defined URL for the resource. |
| timeout_sec |  | Backend service timeout in seconds. |

#### Relationships

- `(:GCPBackendService)-[:EXPOSE]->(:GCPInstance)`: generated by analysis job `GCP BackendService to Instance EXPOSE relationship (scoped per project)`.
  - Properties:

    | Field | Description |
    |-------|-------------|
    | exposure_type | Property generated by analysis job: `GCP BackendService to Instance EXPOSE relationship (scoped per project)`. |

- `(:GCPCloudArmorPolicy)-[:PROTECTS]->(:GCPBackendService)`

- `(:GCPProject)-[:RESOURCE]->(:GCPBackendService)`

- `(:GCPBackendService)-[:ROUTES_TO]->(:GCPInstanceGroup)`

- `(:GCPTargetSslProxy)-[:ROUTES_TO]->(:GCPBackendService)`

### GCPBigQueryConnection

Represents a GCP BigQuery Connection (external data source connection).

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Stable identifier for this resource. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| aws_role_arn |  | The IAM role ARN for aws connections. |
| azure_app_client_id |  | The federated application client ID for azure connections. |
| cloud_sql_instance_id |  | The Cloud SQL instance ID for cloudSql connections (format: `project:region:instance`). |
| connection_type |  | Type of connection (e.g., cloudSql, spark, aws, azure). |
| creation_time |  | Creation time of the connection. |
| description |  | Description of the connection. |
| friendly_name |  | User-friendly name for the connection. |
| has_credential |  | Whether the connection has a credential configured. |
| last_modified_time |  | Last modification time of the connection. |
| name |  | The full resource name of the connection. |
| service_account_id |  | The service account email for cloudResource connections. |

#### Relationships

- `(:GCPBigQueryConnection)-[:CONNECTS_TO]->(:GCPCloudSQLInstance)`

- `(:GCPBigQueryConnection)-[:CONNECTS_WITH]->(:AWSRole)`

- `(:GCPBigQueryConnection)-[:CONNECTS_WITH]->(:EntraServicePrincipal)`

- `(:GCPBigQueryConnection)-[:CONNECTS_WITH]->(:GCPServiceAccount)`

- `(:GCPProject)-[:RESOURCE]->(:GCPBigQueryConnection)`

- `(:GCPBigQueryRoutine)-[:USES_CONNECTION]->(:GCPBigQueryConnection)`

- `(:GCPBigQueryTable)-[:USES_CONNECTION]->(:GCPBigQueryConnection)`

### GCPBigQueryDataset

Represents a GCP BigQuery Dataset.

> **Ontology Mapping**: This node uses the ontology label [`Database`](#ontology-database).

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Stable identifier for this resource. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| access_entries |  | JSON string containing the dataset access entries returned by the BigQuery API. |
| creation_time |  | Creation time of the dataset. |
| dataset_id |  | The short dataset ID. |
| default_kms_key_name |  | Default customer-managed encryption key configured for new tables in the dataset, when present. |
| default_partition_expiration_ms |  | Default expiration time for partitions in milliseconds. |
| default_table_expiration_ms |  | Default expiration time for tables in milliseconds. |
| description |  | Description of the dataset. |
| friendly_name |  | User-friendly name for the dataset. |
| last_modified_time |  | Last modification time of the dataset. |
| location |  | Geographic location of the dataset (e.g., US, EU). |
| *_ont_location* | Yes | Normalized field sourced from `location`. |
| *_ont_name* | Yes | Normalized field sourced from `dataset_id`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |
| *_ont_type* | Yes | Property generated by the ontology mapping. |

#### Relationships

- `(:GCPPolicyBinding)-[:APPLIES_TO]->(:GCPBigQueryDataset)`: Connects a GCP IAM policy binding to the concrete resource where the policy applies.

- `(:GCPPrincipal)-[:CAN_DELETE]->(:GCPBigQueryDataset)`: `GCPPrincipal` receives evaluated `CAN_DELETE` access to `GCPBigQueryDataset` from GCP IAM policies.
  - Evaluated permissions: `bigquery.datasets.delete`, `bigquery.tables.delete`
  - Properties:

    | Field | Description |
    |-------|-------------|
    | condition_expression | CEL expression that must be satisfied for this permission. |
    | condition_title | Title of the IAM condition that restricts this permission. |
    | has_condition | Whether an IAM condition restricts this permission. |

- `(:GCPPrincipal)-[:CAN_READ]->(:GCPBigQueryDataset)`: `GCPPrincipal` receives evaluated `CAN_READ` access to `GCPBigQueryDataset` from GCP IAM policies.
  - Evaluated permissions: `bigquery.tables.getData`
  - Properties:

    | Field | Description |
    |-------|-------------|
    | condition_expression | CEL expression that must be satisfied for this permission. |
    | condition_title | Title of the IAM condition that restricts this permission. |
    | has_condition | Whether an IAM condition restricts this permission. |

- `(:GCPPrincipal)-[:CAN_WRITE]->(:GCPBigQueryDataset)`: `GCPPrincipal` receives evaluated `CAN_WRITE` access to `GCPBigQueryDataset` from GCP IAM policies.
  - Evaluated permissions: `bigquery.tables.updateData`
  - Properties:

    | Field | Description |
    |-------|-------------|
    | condition_expression | CEL expression that must be satisfied for this permission. |
    | condition_title | Title of the IAM condition that restricts this permission. |
    | has_condition | Whether an IAM condition restricts this permission. |

- `(:GCPBigQueryDataset)-[:HAS_ROUTINE]->(:GCPBigQueryRoutine)`

- `(:GCPBigQueryDataset)-[:HAS_TABLE]->(:GCPBigQueryTable)`

- `(:GCPProject)-[:RESOURCE]->(:GCPBigQueryDataset)`

### GCPBigQueryRoutine

Represents a GCP BigQuery Routine (stored procedure, UDF, or table-valued function).

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Stable identifier for this resource. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| connection_id |  | The BigQuery connection resource name used by remote functions. |
| creation_time |  | Creation time of the routine. |
| dataset_id |  | The parent dataset identifier in `project_id:dataset_id` format. |
| language |  | Language of the routine (e.g., SQL, JAVASCRIPT). |
| last_modified_time |  | Last modification time of the routine. |
| routine_id |  | The short routine ID. |
| routine_type |  | Type: SCALAR_FUNCTION, PROCEDURE, or TABLE_VALUED_FUNCTION. |

#### Relationships

- `(:GCPBigQueryDataset)-[:HAS_ROUTINE]->(:GCPBigQueryRoutine)`

- `(:GCPProject)-[:RESOURCE]->(:GCPBigQueryRoutine)`

- `(:GCPBigQueryRoutine)-[:USES_CONNECTION]->(:GCPBigQueryConnection)`

### GCPBigQueryTable

Represents a GCP BigQuery Table, View, or Materialized View.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Stable identifier for this resource. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| connection_id |  | The BigQuery connection resource name used by external tables. |
| creation_time |  | Creation time of the table. |
| dataset_id |  | The parent dataset identifier in `project_id:dataset_id` format. |
| description |  | Description of the table. |
| expiration_time |  | Expiration time of the table, if set. |
| friendly_name |  | User-friendly name for the table. |
| kms_key_name |  | Customer-managed encryption key configured on the table, when present. |
| num_bytes |  | Size of the table in bytes. |
| num_long_term_bytes |  | Size of long-term storage in bytes. |
| num_rows |  | Number of rows in the table. |
| table_id |  | The short table ID. |
| type |  | Table type: TABLE, VIEW, MATERIALIZED_VIEW, or EXTERNAL. |

#### Relationships

- `(:GCPPolicyBinding)-[:APPLIES_TO]->(:GCPBigQueryTable)`: Connects a GCP IAM policy binding to the concrete resource where the policy applies.

- `(:GCPPrincipal)-[:CAN_DELETE]->(:GCPBigQueryTable)`: `GCPPrincipal` receives evaluated `CAN_DELETE` access to `GCPBigQueryTable` from GCP IAM policies.
  - Evaluated permissions: `bigquery.tables.delete`
  - Properties:

    | Field | Description |
    |-------|-------------|
    | condition_expression | CEL expression that must be satisfied for this permission. |
    | condition_title | Title of the IAM condition that restricts this permission. |
    | has_condition | Whether an IAM condition restricts this permission. |

- `(:GCPPrincipal)-[:CAN_READ]->(:GCPBigQueryTable)`: `GCPPrincipal` receives evaluated `CAN_READ` access to `GCPBigQueryTable` from GCP IAM policies.
  - Evaluated permissions: `bigquery.tables.getData`
  - Properties:

    | Field | Description |
    |-------|-------------|
    | condition_expression | CEL expression that must be satisfied for this permission. |
    | condition_title | Title of the IAM condition that restricts this permission. |
    | has_condition | Whether an IAM condition restricts this permission. |

- `(:GCPPrincipal)-[:CAN_WRITE]->(:GCPBigQueryTable)`: `GCPPrincipal` receives evaluated `CAN_WRITE` access to `GCPBigQueryTable` from GCP IAM policies.
  - Evaluated permissions: `bigquery.tables.updateData`
  - Properties:

    | Field | Description |
    |-------|-------------|
    | condition_expression | CEL expression that must be satisfied for this permission. |
    | condition_title | Title of the IAM condition that restricts this permission. |
    | has_condition | Whether an IAM condition restricts this permission. |

- `(:GCPBigQueryDataset)-[:HAS_TABLE]->(:GCPBigQueryTable)`

- `(:GCPProject)-[:RESOURCE]->(:GCPBigQueryTable)`

- `(:GCPBigQueryTable)-[:USES_CONNECTION]->(:GCPBigQueryConnection)`

### GCPBigtableAppProfile

Representation of a GCP [Bigtable App Profile](https://cloud.google.com/bigtable/docs/reference/admin/rest/v2/projects.instances.appProfiles).

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Stable identifier for this resource. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| description |  | The user-provided description of the app profile. |
| instance_id |  | Identifier of the parent service instance. |
| multi_cluster_routing_use_any |  | Whether the Bigtable app profile may route to any available cluster. |
| name |  | The full resource name of the App Profile. |
| single_cluster_routing_cluster_id |  | Cluster selected by the app profile's single-cluster routing policy. |

#### Relationships

- `(:GCPBigtableInstance)-[:HAS_APP_PROFILE]->(:GCPBigtableAppProfile)`

- `(:GCPProject)-[:RESOURCE]->(:GCPBigtableAppProfile)`

- `(:GCPBigtableAppProfile)-[:ROUTES_TO]->(:GCPBigtableCluster)`

### GCPBigtableBackup

Representation of a GCP [Bigtable Backup](https://cloud.google.com/bigtable/docs/reference/admin/rest/v2/projects.instances.clusters.backups).

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Stable identifier for this resource. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| cluster_id |  | Identifier of the parent Bigtable cluster. |
| end_time |  | Timestamp when the Bigtable backup operation completed. |
| expire_time |  | Timestamp when Bigtable will delete this backup. |
| name |  | The full resource name of the Backup. |
| size_bytes |  | Stored content size in bytes. |
| source_table |  | Full resource name of the Bigtable table captured by this backup. |
| start_time |  | Configured backup window start time or operation start timestamp. |
| state |  | The current state of the backup (e.g., `READY`). |

#### Relationships

- `(:GCPBigtableTable)-[:BACKED_UP_AS]->(:GCPBigtableBackup)`

- `(:GCPProject)-[:RESOURCE]->(:GCPBigtableBackup)`

- `(:GCPBigtableCluster)-[:STORES_BACKUP]->(:GCPBigtableBackup)`

### GCPBigtableCluster

Representation of a GCP [Bigtable Cluster](https://cloud.google.com/bigtable/docs/reference/admin/rest/v2/projects.instances.clusters).

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Stable identifier for this resource. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| default_storage_type |  | Default Bigtable storage medium, such as SSD or HDD. |
| instance_id |  | Identifier of the parent service instance. |
| location |  | The GCP location where this cluster resides (e.g., `projects/.../locations/us-central1-b`). |
| name |  | The full resource name of the Bigtable Cluster. |
| state |  | The current state of the cluster (e.g., `READY`). |

#### Relationships

- `(:GCPBigtableInstance)-[:HAS_CLUSTER]->(:GCPBigtableCluster)`

- `(:GCPProject)-[:RESOURCE]->(:GCPBigtableCluster)`

- `(:GCPBigtableAppProfile)-[:ROUTES_TO]->(:GCPBigtableCluster)`

- `(:GCPBigtableCluster)-[:STORES_BACKUP]->(:GCPBigtableBackup)`

### GCPBigtableInstance

Representation of a GCP [Bigtable Instance](https://cloud.google.com/bigtable/docs/reference/admin/rest/v2/projects.instances).

> **Ontology Mapping**: This node uses the ontology label [`Database`](#ontology-database).

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Stable identifier for this resource. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| display_name |  | Human-readable name shown for this resource. |
| name |  | The full resource name of the Bigtable Instance. |
| state |  | The current state of the instance (e.g., `READY`). |
| type |  | The type of instance (e.g., `PRODUCTION`). |
| *_ont_name* | Yes | Normalized field sourced from `display_name`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |
| *_ont_type* | Yes | Property generated by the ontology mapping. |

#### Relationships

- `(:GCPBigtableInstance)-[:HAS_APP_PROFILE]->(:GCPBigtableAppProfile)`

- `(:GCPBigtableInstance)-[:HAS_CLUSTER]->(:GCPBigtableCluster)`

- `(:GCPBigtableInstance)-[:HAS_TABLE]->(:GCPBigtableTable)`

- `(:GCPBigtableInstance)-[:LABELED]->(:GCPLabel)`: Indicates that a GCP Bigtable instance has this legacy label.

- `(:GCPProject)-[:RESOURCE]->(:GCPBigtableInstance)`

- `(:GCPBigtableInstance)-[:TAGGED]->(:GCPLabel)`: Indicates that a GCP Bigtable instance is tagged with this label.

### GCPBigtableTable

Representation of a GCP [Bigtable Table](https://cloud.google.com/bigtable/docs/reference/admin/rest/v2/projects.instances.tables).

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Stable identifier for this resource. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| granularity |  | The granularity at which timestamps are stored (e.g., `MILLIS`). |
| instance_id |  | Identifier of the parent service instance. |
| name |  | The full resource name of the Bigtable Table. |

#### Relationships

- `(:GCPBigtableTable)-[:BACKED_UP_AS]->(:GCPBigtableBackup)`

- `(:GCPBigtableInstance)-[:HAS_TABLE]->(:GCPBigtableTable)`

- `(:GCPProject)-[:RESOURCE]->(:GCPBigtableTable)`

### GCPBucket

Representation of a GCP [Storage Bucket](https://cloud.google.com/storage/docs/json_api/v1/buckets).

> **Ontology Mapping**: This node uses the ontology label [`ObjectStorage`](#ontology-objectstorage).

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The ID of the storage bucket, e.g. "bucket-12345". |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| _ont_public |  | Property generated by analysis job: `Ontology - GCP bucket public projection`. |
| acl_public |  | `true` if the bucket's legacy ACL or default object ACL grants access to `allUsers` or `allAuthenticatedUsers`. Consumed by the `_ont_public` projection job. |
| bucket_id |  | Cloud Storage bucket name. |
| default_kms_key_name |  | A Cloud KMS key that will be used to encrypt objects inserted into this bucket, if no encryption method is specified. |
| iam_config_bucket_policy_only |  | The bucket's [Bucket Policy Only](https://cloud.google.com/storage/docs/bucket-policy-only) configuration. |
| iam_config_public_access_prevention |  | The bucket's [Public Access Prevention](https://cloud.google.com/storage/docs/public-access-prevention) setting (`enforced` blocks all public access regardless of bindings; `inherited` defers to the project / org default). |
| kind |  | The kind of item this is. For storage buckets, this is always storage#bucket. |
| location |  | The location of the bucket. Object data for objects in the bucket resides in physical storage within this region. Defaults to US. See [Cloud Storage bucket locations](https://cloud.google.com/storage/docs/locations) for the authoritative list. |
| location_type |  | The type of location that the bucket resides in, as determined by the `location` property. |
| log_bucket |  | The destination bucket where the current bucket's logs should be placed. |
| meta_generation |  | The metadata generation of this bucket. |
| owner_entity |  | The entity, in the form `project-owner-projectId`. |
| owner_entity_id |  | The ID for the entity. |
| project_number |  | Numeric identifier of the owning Google Cloud project. |
| requester_pays |  | The bucket's billing configuration (if set to true, Requester Pays is enabled for this bucket). |
| retention_period |  | The period of time, in seconds, that objects in the bucket must be retained and cannot be deleted, overwritten, or archived. |
| self_link |  | The URI of the storage bucket. |
| storage_class |  | The bucket's default storage class, used whenever no `storageClass` is specified for a newly-created object. For more information, see [storage classes](https://cloud.google.com/storage/docs/storage-classes). |
| time_created |  | The creation time of the bucket in RFC 3339 format. |
| versioning_enabled |  | The bucket's versioning configuration (if set to `True`, versioning is fully enabled for this bucket). |
| *_ont_encrypted* | Yes | Property generated by the ontology mapping. |
| *_ont_location* | Yes | Normalized field sourced from `location`. |
| *_ont_name* | Yes | Normalized field sourced from `id`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |
| *_ont_versioning* | Yes | Normalized field sourced from `versioning_enabled`. |

#### Relationships

- `(:GCPPolicyBinding)-[:APPLIES_TO]->(:GCPBucket)`: Connects a GCP IAM policy binding to the concrete resource where the policy applies.

- `(:DatabricksExternalLocation)-[:BACKED_BY]->(:GCPBucket)`: A Databricks external location is backed by a Google Cloud Storage bucket.

- `(:DatabricksTable)-[:BACKED_BY]->(:GCPBucket)`: A Databricks table is backed by a Google Cloud Storage bucket.

- `(:DatabricksVolume)-[:BACKED_BY]->(:GCPBucket)`: A Databricks volume is backed by a Google Cloud Storage bucket.

- `(:SnowflakeExternalVolumeStorageLocation)-[:BACKED_BY]->(:GCPBucket)`: A Snowflake external volume storage location is backed by a Google Cloud Storage bucket.

- `(:SnowflakeStage)-[:BACKED_BY]->(:GCPBucket)`: A Snowflake external stage is backed by a Google Cloud Storage bucket.

- `(:GCPPrincipal)-[:CAN_DELETE]->(:GCPBucket)`: `GCPPrincipal` receives evaluated `CAN_DELETE` access to `GCPBucket` from GCP IAM policies.
  - Evaluated permissions: `storage.objects.delete`
  - Properties:

    | Field | Description |
    |-------|-------------|
    | condition_expression | CEL expression that must be satisfied for this permission. |
    | condition_title | Title of the IAM condition that restricts this permission. |
    | has_condition | Whether an IAM condition restricts this permission. |

- `(:GCPPrincipal)-[:CAN_READ]->(:GCPBucket)`: `GCPPrincipal` receives evaluated `CAN_READ` access to `GCPBucket` from GCP IAM policies.
  - Evaluated permissions: `storage.objects.get`
  - Properties:

    | Field | Description |
    |-------|-------------|
    | condition_expression | CEL expression that must be satisfied for this permission. |
    | condition_title | Title of the IAM condition that restricts this permission. |
    | has_condition | Whether an IAM condition restricts this permission. |

- `(:GCPPrincipal)-[:CAN_WRITE]->(:GCPBucket)`: `GCPPrincipal` receives evaluated `CAN_WRITE` access to `GCPBucket` from GCP IAM policies.
  - Evaluated permissions: `storage.objects.create`, `storage.objects.update`
  - Properties:

    | Field | Description |
    |-------|-------------|
    | condition_expression | CEL expression that must be satisfied for this permission. |
    | condition_title | Title of the IAM condition that restricts this permission. |
    | has_condition | Whether an IAM condition restricts this permission. |

- `(:GCPBucket)-[:LABELED]->(:GCPBucketLabel)`

- `(:GCPBucket)-[:LABELED]->(:GCPLabel)`: Indicates that a GCP bucket has this legacy label.

- `(:GCPProject)-[:RESOURCE]->(:GCPBucket)`

- `(:GCPVertexAIModel)-[:STORED_IN]->(:GCPBucket)`

- `(:GCPBucket)-[:TAGGED]->(:GCPLabel)`: Indicates that a GCP bucket is tagged with this label.

### GCPBucketLabel

Representation of a GCP [Storage Bucket Label](https://cloud.google.com/storage/docs/key-terms#bucket-labels).  This node contains a key-value pair.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Identifier derived from the label key. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| key | Yes | Label key. |
| value |  | Label value. |

#### Relationships

- `(:GCPBucket)-[:LABELED]->(:GCPBucketLabel)`

- `(:GCPProject)-[:RESOURCE]->(:GCPBucketLabel)`

### GCPCloudArmorPolicy

Representation of a GCP [Cloud Armor Security Policy](https://cloud.google.com/compute/docs/reference/rest/v1/securityPolicies). Cloud Armor policies provide DDoS protection and WAF capabilities for backend services.

> **Ontology Mapping**: This node uses the ontology label [`NetworkAccessControl`](#ontology-networkaccesscontrol).

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Stable identifier for this resource. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| creation_timestamp |  | Creation timestamp of the resource. |
| description |  | An optional description of this security policy. |
| name | Yes | The name of the security policy. |
| partial_uri |  | Same as `id`. |
| policy_type |  | The type of the security policy (e.g., `CLOUD_ARMOR`). |
| project_id |  | The project ID that this policy belongs to. |
| self_link |  | Server-defined URL for the resource. |
| *_ont_name* | Yes | Normalized field sourced from `name`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |

#### Relationships

- `(:GCPCloudArmorPolicy)-[:PROTECTS]->(:GCPBackendService)`

- `(:GCPProject)-[:RESOURCE]->(:GCPCloudArmorPolicy)`

### GCPCloudFunction

Representation of a Google [Cloud Function](https://cloud.google.com/functions/docs/reference/rest/v1/projects.locations.functions) (v1 API).

> **Ontology Mapping**: This node uses the ontology label [`Function`](#ontology-function).

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The full, unique resource name of the function. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| available_memory_mb |  | Memory allocated to the function, in MB (from `availableMemoryMb`). |
| description |  | User-provided description of the function. |
| entry_point |  | The name of the function within the source code to be executed. |
| event_trigger_resource |  | The specific resource the event trigger monitors. |
| event_trigger_type |  | The type of event that triggers the function (e.g., a Pub/Sub message). |
| https_trigger_url |  | The public URL if the function is triggered by an HTTP request. |
| name |  | The full, unique resource name of the function (same as id). |
| project_id |  | The ID of the GCP project to which the function belongs. |
| region |  | The GCP region where the function is deployed. |
| runtime |  | The language runtime environment for the function (e.g., python310). |
| service_account_email |  | The email of the service account the function runs as. |
| status |  | The current state of the function (e.g., ACTIVE, OFFLINE, DEPLOY_IN_PROGRESS). |
| timeout |  | Maximum execution time, in seconds (parsed from the API's Duration string; whole-second values are stored as int, fractional values as float). |
| update_time |  | The timestamp when the function was last modified. |
| *_ont_deployment_type* | Yes | Property generated by the ontology mapping. |
| *_ont_memory* | Yes | Normalized field sourced from `available_memory_mb`. |
| *_ont_name* | Yes | Normalized field sourced from `name`. |
| *_ont_runtime* | Yes | Normalized field sourced from `runtime`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |
| *_ont_timeout* | Yes | Normalized field sourced from `timeout`. |

#### Relationships

- `(:GCPPolicyBinding)-[:APPLIES_TO]->(:GCPCloudFunction)`: Connects a GCP IAM policy binding to the concrete resource where the policy applies.

- `(:GCPCloudFunction)-[:LABELED]->(:GCPLabel)`: Indicates that a GCP Cloud Function has this legacy label.

- `(:GCPCloudFunction)-[:RESOLVED_IMAGE]->(:Image)`: generated by analysis job `Function RESOLVED_IMAGE analysis`.

- `(:GCPProject)-[:RESOURCE]->(:GCPCloudFunction)`

- `(:GCPCloudFunction)-[:RUNS_AS]->(:GCPServiceAccount)`

### GCPCloudRunExecution

Representation of a GCP [Cloud Run Execution](https://cloud.google.com/run/docs/reference/rest/v2/projects.locations.jobs.executions).

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Stable identifier for this resource. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| cancelled_count |  | Number of tasks that were cancelled. |
| failed_count |  | Number of tasks that failed. |
| job |  | Full resource name of the parent job. |
| name |  | Short name of the execution. |
| project_id |  | Google Cloud project that owns this resource. |
| succeeded_count |  | Number of tasks that succeeded. |

#### Relationships

- `(:GCPCloudRunJob)-[:HAS_EXECUTION]->(:GCPCloudRunExecution)`

- `(:GCPProject)-[:RESOURCE]->(:GCPCloudRunExecution)`

### GCPCloudRunJob

A Google Cloud Cloud Run Job resource.

> **Ontology Mapping**: This node uses the ontology label [`ComputeService`](#ontology-computeservice).

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Stable identifier for this resource. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| location |  | The GCP location where the job is deployed. |
| name |  | Short name of the job. |
| project_id |  | The GCP project ID this job belongs to. |
| service_account_email |  | The email of the service account used by this job. |
| *_ont_name* | Yes | Normalized field sourced from `name`. |
| *_ont_region* | Yes | Normalized field sourced from `location`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |

#### Relationships

- `(:GCPCloudRunJob)-[:CONTAINS]->(:GCPCloudRunJobContainer)`

- `(:GCPCloudRunJob)-[:HAS_EXECUTION]->(:GCPCloudRunExecution)`

- `(:GCPCloudRunJob)-[:HAS_RUNTIME_IMAGE]->(:Image)`: generated by analysis job `Workload HAS_RUNTIME_IMAGE inventory analysis`.
  - Properties:

    | Field | Description |
    |-------|-------------|
    | exposed_internet | Property generated by analysis job: `Workload HAS_RUNTIME_IMAGE inventory analysis`. |

- `(:GCPCloudRunJob)-[:LABELED]->(:GCPLabel)`: Indicates that a GCP Cloud Run job has this legacy label.

- `(:GCPProject)-[:RESOURCE]->(:GCPCloudRunJob)`

- `(:GCPCloudRunJob)-[:RUNS_AS]->(:GCPServiceAccount)`

- `(:GCPCloudRunJob)-[:TAGGED]->(:GCPLabel)`: Indicates that a GCP Cloud Run job is tagged with this label.

- `(:GCPCloudRunJob)-[:USES_SERVICE_ACCOUNT]->(:GCPServiceAccount)`

- `(:GCPCloudRunJobContainer)-[:WORKLOAD_PARENT]->(:GCPCloudRunJob)`

### GCPCloudRunJobContainer

A Google Cloud Cloud Run Job Container resource.

> **Ontology Mapping**: This node uses the ontology label [`Container`](#ontology-container).

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Stable identifier for this resource. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| architecture |  | CPU architecture (always `amd64`; Cloud Run does not support ARM). |
| architecture_normalized |  | Normalized architecture value (always `amd64`). |
| architecture_source |  | How the architecture was determined (always `platform_requirement`). |
| image |  | The container image reference as declared in the task template. |
| image_digest |  | The digest portion of the image reference (e.g., `sha256:abc...`) when the image is pinned by digest; `None` for tag-based references. |
| job_id |  | Full resource name of the parent GCPCloudRunJob. |
| name |  | Name of the container as declared in the task template. Falls back to the container index when the Cloud Run API omits the field (single-container jobs). |
| project_id |  | The GCP project ID this container belongs to. |
| *_ont_image* | Yes | Normalized field sourced from `image`. |
| *_ont_image_digest* | Yes | Normalized field sourced from `image_digest`. |
| *_ont_name* | Yes | Normalized field sourced from `name`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |
| *_ont_state* | Yes | Property generated by the ontology mapping. |

#### Relationships

- `(:GCPCloudRunJob)-[:CONTAINS]->(:GCPCloudRunJobContainer)`

- `(:GCPCloudRunJobContainer)-[:HAS_IMAGE]->(:AWSECRImage)`

- `(:GCPCloudRunJobContainer)-[:HAS_IMAGE]->(:GCPArtifactRegistryImage)`

- `(:GCPCloudRunJobContainer)-[:HAS_IMAGE]->(:GitHubContainerImage)`

- `(:GCPCloudRunJobContainer)-[:HAS_IMAGE]->(:GitLabContainerImage)`

- `(:GCPCloudRunJobContainer)-[:RESOLVED_IMAGE]->(:Image)`: generated by analysis job `Container RESOLVED_IMAGE analysis`.

- `(:GCPProject)-[:RESOURCE]->(:GCPCloudRunJobContainer)`

- `(:GCPCloudRunJobContainer)-[:WORKLOAD_PARENT]->(:GCPCloudRunJob)`

### GCPCloudRunRevision

A Google Cloud Cloud Run Revision resource.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Stable identifier for this resource. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| log_uri |  | URI to Cloud Logging for this revision. |
| name |  | Short name of the revision. |
| project_id |  | The GCP project ID this revision belongs to. |
| service |  | Full resource name of the parent service. |
| service_account_email |  | The email of the service account used by this revision. |

#### Relationships

- `(:GCPCloudRunService)-[:HAS_REVISION]->(:GCPCloudRunRevision)`

- `(:GCPProject)-[:RESOURCE]->(:GCPCloudRunRevision)`

- `(:GCPCloudRunRevision)-[:USES_SERVICE_ACCOUNT]->(:GCPServiceAccount)`

### GCPCloudRunService

Representation of a GCP [Cloud Run Service](https://cloud.google.com/run/docs/reference/rest/v2/projects.locations.services).

> **Ontology Mapping**: This node uses the ontology label [`ComputeService`](#ontology-computeservice).

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Stable identifier for this resource. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| description |  | User-provided description of the service. |
| exposed_internet | Yes | `True` when `ingress` is `INGRESS_TRAFFIC_ALL`. `False` when ingress is internal-only or none. |
| exposed_internet_type | Yes | How it is exposed. Always `direct`. |
| ingress |  | The ingress setting for the service. Values: `INGRESS_TRAFFIC_ALL`, `INGRESS_TRAFFIC_INTERNAL_ONLY`, `INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER`, `INGRESS_TRAFFIC_NONE`. |
| latest_ready_revision |  | Full resource name of the latest ready revision for this service. |
| location |  | The GCP location where the service is deployed. |
| name |  | Short name of the service. |
| project_id |  | Google Cloud project that owns this resource. |
| service_account_email |  | The email of the service account configured on the service template (used by new revisions created from this service). |
| uri |  | Default URL serving the service. |
| *_ont_name* | Yes | Normalized field sourced from `name`. |
| *_ont_region* | Yes | Normalized field sourced from `location`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |

#### Relationships

- `(:GCPPolicyBinding)-[:APPLIES_TO]->(:GCPCloudRunService)`: Connects a GCP IAM policy binding to the concrete resource where the policy applies.

- `(:GCPCloudRunService)-[:CONTAINS]->(:GCPCloudRunServiceContainer)`

- `(:GCPCloudRunService)-[:HAS_REVISION]->(:GCPCloudRunRevision)`

- `(:GCPCloudRunService)-[:HAS_RUNTIME_IMAGE]->(:Image)`: generated by analysis job `Workload HAS_RUNTIME_IMAGE inventory analysis`.
  - Properties:

    | Field | Description |
    |-------|-------------|
    | exposed_internet | Property generated by analysis job: `Workload HAS_RUNTIME_IMAGE inventory analysis`. |

- `(:GCPCloudRunService)-[:LABELED]->(:GCPLabel)`: Indicates that a GCP Cloud Run service has this legacy label.

- `(:GCPProject)-[:RESOURCE]->(:GCPCloudRunService)`

- `(:GCPCloudRunService)-[:RUNS_AS]->(:GCPServiceAccount)`

- `(:GCPCloudRunService)-[:TAGGED]->(:GCPLabel)`: Indicates that a GCP Cloud Run service is tagged with this label.

- `(:GCPCloudRunService)-[:USES_SERVICE_ACCOUNT]->(:GCPServiceAccount)`

- `(:GCPCloudRunServiceContainer)-[:WORKLOAD_PARENT]->(:GCPCloudRunService)`

### GCPCloudRunServiceContainer

A Google Cloud Cloud Run Service Container resource.

> **Ontology Mapping**: This node uses the ontology label [`Container`](#ontology-container).

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Stable identifier for this resource. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| architecture |  | CPU architecture (always `amd64`; Cloud Run does not support ARM). |
| architecture_normalized |  | Normalized architecture value (always `amd64`). |
| architecture_source |  | How the architecture was determined (always `platform_requirement`). |
| image |  | The container image reference as declared in the spec. |
| image_digest |  | The digest portion of the image reference (e.g., `sha256:abc...`) when the image is pinned by digest; `None` for tag-based references. |
| name |  | Name of the container as declared in the spec. Falls back to the container index when the Cloud Run API omits the field (single-container deployments). |
| project_id |  | The GCP project ID this container belongs to. |
| service_id |  | Full resource name of the parent GCPCloudRunService. |
| *_ont_image* | Yes | Normalized field sourced from `image`. |
| *_ont_image_digest* | Yes | Normalized field sourced from `image_digest`. |
| *_ont_name* | Yes | Normalized field sourced from `name`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |
| *_ont_state* | Yes | Property generated by the ontology mapping. |

#### Relationships

- `(:GCPCloudRunService)-[:CONTAINS]->(:GCPCloudRunServiceContainer)`

- `(:GCPCloudRunServiceContainer)-[:HAS_IMAGE]->(:AWSECRImage)`

- `(:GCPCloudRunServiceContainer)-[:HAS_IMAGE]->(:GCPArtifactRegistryImage)`

- `(:GCPCloudRunServiceContainer)-[:HAS_IMAGE]->(:GitHubContainerImage)`

- `(:GCPCloudRunServiceContainer)-[:HAS_IMAGE]->(:GitLabContainerImage)`

- `(:GCPCloudRunServiceContainer)-[:RESOLVED_IMAGE]->(:Image)`: generated by analysis job `Container RESOLVED_IMAGE analysis`.

- `(:GCPProject)-[:RESOURCE]->(:GCPCloudRunServiceContainer)`

- `(:GCPCloudRunServiceContainer)-[:WORKLOAD_PARENT]->(:GCPCloudRunService)`

### GCPCloudSQLAuthorizedNetwork

A CIDR entry authorized to connect to a Cloud SQL instance.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | `{instance_self_link}/authorizedNetworks/{value}`. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| expiration_time |  | RFC 3339 timestamp at which the entry expires, if set. |
| instance_id |  | The selfLink of the parent GCPCloudSQLInstance. |
| name |  | Human-readable label assigned to the authorized network entry. |
| value |  | The CIDR allowed inbound, e.g. `203.0.113.0/24` or `0.0.0.0/0`. |

#### Relationships

- `(:GCPCloudSQLInstance)-[:AUTHORIZED_NETWORK]->(:GCPCloudSQLAuthorizedNetwork)`

- `(:GCPProject)-[:RESOURCE]->(:GCPCloudSQLAuthorizedNetwork)`

### GCPCloudSQLBackupConfiguration

Representation of a GCP [Cloud SQL Backup Configuration](https://cloud.google.com/sql/docs/mysql/admin-api/rest/v1beta4/instances#backupconfiguration). This node captures the backup settings for a Cloud SQL instance.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Synthetic `{instance_self_link}/backupConfig` identifier. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| backup_retention_settings |  | Cloud SQL retained-backup configuration encoded as JSON. |
| binary_log_enabled |  | Whether MySQL binary logging is enabled for recovery and replication. |
| enabled |  | Boolean indicating whether automated backups are enabled. |
| instance_id |  | Identifier of the parent service instance. |
| location |  | The location where backups are stored. |
| point_in_time_recovery_enabled |  | Whether Cloud SQL point-in-time recovery is enabled. |
| start_time |  | Configured backup window start time or operation start timestamp. |
| transaction_log_retention_days |  | Number of days Cloud SQL retains transaction logs for point-in-time recovery. |

#### Relationships

- `(:GCPCloudSQLInstance)-[:HAS_BACKUP_CONFIG]->(:GCPCloudSQLBackupConfiguration)`

- `(:GCPProject)-[:RESOURCE]->(:GCPCloudSQLBackupConfiguration)`

### GCPCloudSQLDatabase

Representation of a GCP [Cloud SQL Database](https://cloud.google.com/sql/docs/mysql/admin-api/rest/v1beta4/databases).

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Synthetic `{instance_self_link}/databases/{database_name}` identifier. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| charset |  | The character set for the database. |
| collation |  | The collation for the database. |
| instance_id |  | Identifier of the parent service instance. |
| name |  | The name of the database. |

#### Relationships

- `(:GCPCloudSQLInstance)-[:CONTAINS]->(:GCPCloudSQLDatabase)`

- `(:GCPProject)-[:RESOURCE]->(:GCPCloudSQLDatabase)`

### GCPCloudSQLInstance

Representation of a GCP [Cloud SQL Instance](https://cloud.google.com/sql/docs/mysql/admin-api/rest/v1beta4/instances).

> **Ontology Mapping**: This node uses the ontology label [`Database`](#ontology-database).

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Canonical Cloud SQL instance selfLink used as the node ID. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| authorized_networks |  | Authorized client network entries encoded as JSON from ipConfiguration.authorizedNetworks. |
| availability_type |  | Instance availability topology, such as ZONAL or REGIONAL. |
| backend_type |  | Cloud SQL backend type reported for the instance. |
| backup_configuration |  | Cloud SQL backup configuration encoded as JSON. |
| backup_enabled |  | Whether automated backups are enabled in the instance settings. |
| connection_name |  | Cloud SQL connection name in project:region:instance form. |
| database_engine |  | Database engine family derived from database_version, such as MYSQL, POSTGRES, or SQLSERVER. |
| database_flags |  | Configured database flags encoded as JSON name-value entries. |
| database_version |  | Cloud SQL database engine and major version reported by the API. |
| disk_size_gb |  | Provisioned data disk capacity in gigabytes, derived from settings.dataDiskSizeGb. |
| disk_type |  | Cloud SQL data disk type, such as PD_SSD or PD_HDD. |
| gce_zone |  | Compute Engine zone hosting the primary Cloud SQL instance, when zonal. |
| ip_addresses |  | Instance IP assignments encoded as JSON, including address and assignment type. |
| name |  | The user-assigned name of the instance. |
| network_id |  | Project-relative URI of the private VPC network attached to the instance. |
| region |  | The GCP region the instance lives in. |
| require_ssl |  | Whether the instance rejects unencrypted client connections. |
| service_account_email |  | Google-managed service account used by the Cloud SQL instance. |
| ssl_mode |  | Configured Cloud SQL transport-encryption policy. |
| state |  | The current state of the instance (e.g., `RUNNABLE`). |
| tier |  | The machine type tier (e.g., `db-custom-1-3840`). |
| *_ont_location* | Yes | Normalized field sourced from `region`. |
| *_ont_name* | Yes | Normalized field sourced from `name`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |
| *_ont_type* | Yes | Normalized field sourced from `database_engine`. |
| *_ont_version* | Yes | Normalized field sourced from `database_version`. |

#### Relationships

- `(:GCPCloudSQLInstance)-[:ASSOCIATED_WITH]->(:GCPVpc)`

- `(:GCPCloudSQLInstance)-[:AUTHORIZED_NETWORK]->(:GCPCloudSQLAuthorizedNetwork)`

- `(:GCPBigQueryConnection)-[:CONNECTS_TO]->(:GCPCloudSQLInstance)`

- `(:GCPCloudSQLInstance)-[:CONTAINS]->(:GCPCloudSQLDatabase)`

- `(:GCPCloudSQLInstance)-[:HAS_BACKUP_CONFIG]->(:GCPCloudSQLBackupConfiguration)`

- `(:GCPCloudSQLInstance)-[:HAS_USER]->(:GCPCloudSQLUser)`

- `(:GCPCloudSQLInstance)-[:LABELED]->(:GCPLabel)`: Indicates that a GCP Cloud SQL instance has this legacy label.

- `(:GCPProject)-[:RESOURCE]->(:GCPCloudSQLInstance)`

- `(:GCPCloudSQLInstance)-[:TAGGED]->(:GCPLabel)`: Indicates that a GCP Cloud SQL instance is tagged with this label.

- `(:GCPCloudSQLInstance)-[:USES_SERVICE_ACCOUNT]->(:GCPServiceAccount)`

### GCPCloudSQLUser

Representation of a GCP [Cloud SQL User](https://cloud.google.com/sql/docs/mysql/admin-api/rest/v1beta4/users).

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Synthetic `{instance_self_link}/users/{user_name}@{host}` identifier. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| host |  | The host from which the user is allowed to connect. |
| instance_id |  | Identifier of the parent service instance. |
| name |  | The name of the user. |

#### Relationships

- `(:GCPCloudSQLInstance)-[:HAS_USER]->(:GCPCloudSQLUser)`

- `(:GCPProject)-[:RESOURCE]->(:GCPCloudSQLUser)`

### GCPCryptoKey

Representation of a GCP [Crypto Key](https://cloud.google.com/kms/docs/reference/rest/v1/projects.locations.keyRings.cryptoKeys).

> **Ontology Mapping**: This node uses the ontology label [`EncryptionKey`](#ontology-encryptionkey).

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The full resource name of the Crypto Key. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| key_ring_id |  | Full resource name of the containing Cloud KMS key ring. |
| name |  | The short name of the Crypto Key. |
| purpose |  | The key purpose (e.g., `ENCRYPT_DECRYPT`). |
| rotation_period |  | Configured automatic Cloud KMS key rotation interval. |
| state |  | The state of the primary key version (e.g., `ENABLED`). |
| *_ont_enabled* | Yes | Normalized field sourced from `state`. |
| *_ont_key_type* | Yes | Normalized field sourced from `purpose`. |
| *_ont_name* | Yes | Normalized field sourced from `name`. |
| *_ont_rotation_enabled* | Yes | Normalized field sourced from `rotation_period`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |

#### Relationships

- `(:GCPPolicyBinding)-[:APPLIES_TO]->(:GCPCryptoKey)`: Connects a GCP IAM policy binding to the concrete resource where the policy applies.

- `(:GCPPrincipal)-[:CAN_DECRYPT]->(:GCPCryptoKey)`: `GCPPrincipal` receives evaluated `CAN_DECRYPT` access to `GCPCryptoKey` from GCP IAM policies.
  - Evaluated permissions: `cloudkms.cryptoKeyVersions.useToDecrypt`
  - Properties:

    | Field | Description |
    |-------|-------------|
    | condition_expression | CEL expression that must be satisfied for this permission. |
    | condition_title | Title of the IAM condition that restricts this permission. |
    | has_condition | Whether an IAM condition restricts this permission. |

- `(:GCPPrincipal)-[:CAN_ENCRYPT]->(:GCPCryptoKey)`: `GCPPrincipal` receives evaluated `CAN_ENCRYPT` access to `GCPCryptoKey` from GCP IAM policies.
  - Evaluated permissions: `cloudkms.cryptoKeyVersions.useToEncrypt`
  - Properties:

    | Field | Description |
    |-------|-------------|
    | condition_expression | CEL expression that must be satisfied for this permission. |
    | condition_title | Title of the IAM condition that restricts this permission. |
    | has_condition | Whether an IAM condition restricts this permission. |

- `(:GCPKeyRing)-[:CONTAINS]->(:GCPCryptoKey)`

- `(:DatabricksEncryptionKey)-[:REFERENCES_KEY]->(:GCPCryptoKey)`: A Databricks encryption key references a Google Cloud KMS key.

- `(:GCPProject)-[:RESOURCE]->(:GCPCryptoKey)`

### GCPDNSZone

Representation of a GCP [DNS Zone](https://cloud.google.com/dns/docs/reference/v1/).

> **Ontology Mapping**: This node uses the ontology label [`DNSZone`](#ontology-dnszone).

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Stable identifier for this resource. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| created_at |  | The date and time the zone was created. |
| description |  | An optional description of the zone. |
| dns_name |  | The DNS name of this managed zone, for instance "example.com.". |
| dnssec_key_signing_algorithm |  | Algorithm configured for the DNSSEC key-signing key, when present. |
| dnssec_state |  | DNSSEC state for the managed zone, e.g. `on` or `off`. |
| dnssec_zone_signing_algorithm |  | Algorithm configured for the DNSSEC zone-signing key, when present. |
| kind |  | Google DNS API resource kind identifier. |
| name | Yes | The name of the zone. |
| nameservers |  | Virtual name servers the zone is delegated to. |
| visibility |  | The zone's visibility: `public` zones are exposed to the Internet, while `private` zones are visible only to Virtual Private Cloud resources. |
| *_ont_name* | Yes | Normalized field sourced from `dns_name`. |
| *_ont_public* | Yes | Normalized field sourced from `visibility`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |

#### Relationships

- `(:GCPDNSZone)-[:HAS_RECORD]->(:GCPRecordSet)`

- `(:GCPDNSZone)-[:LABELED]->(:GCPLabel)`: Indicates that a GCP DNS zone has this legacy label.

- `(:GCPProject)-[:RESOURCE]->(:GCPDNSZone)`

- `(:GCPDNSZone)-[:TAGGED]->(:GCPLabel)`: Indicates that a GCP DNS zone is tagged with this label.

### GCPFirewall

Representation of a GCP [Firewall](https://cloud.google.com/compute/docs/reference/rest/v1/firewalls/list).

> **Ontology Mapping**: This node uses the ontology label [`NetworkAccessControl`](#ontology-networkaccesscontrol).

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | A partial resource URI representing this Firewall. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| direction |  | Either 'INGRESS' for inbound or 'EGRESS' for outbound. |
| disabled |  | Whether this firewall object is disabled. |
| has_target_service_accounts |  | Set to True if this Firewall has target service accounts defined. This field is currently a placeholder for future functionality to add GCP IAM objects to Cartography. If True, this firewall rule will only apply to GCP instances that use the specified target service account. |
| name | Yes | Name assigned to this resource. |
| priority |  | The priority of this firewall rule from 0 to 65535; lower values have higher precedence. |
| self_link |  | The full resource URI to this firewall. |
| *_ont_direction* | Yes | Normalized field sourced from `direction`. |
| *_ont_name* | Yes | Normalized field sourced from `name`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |

#### Relationships

- `(:GCPIpRule)-[:ALLOWED_BY]->(:GCPFirewall)`

- `(:GCPPolicyBinding)-[:APPLIES_TO]->(:GCPFirewall)`: Connects a GCP IAM policy binding to the concrete resource where the policy applies.

- `(:GCPIpRule)-[:DENIED_BY]->(:GCPFirewall)`

- `(:GCPFirewall)-[:FIREWALL_INGRESS]->(:GCPInstance)`: generated by analysis job `GCP firewall ingress to instance analysis`.

- `(:GCPProject)-[:RESOURCE]->(:GCPFirewall)`

- `(:GCPVpc)-[:RESOURCE]->(:GCPFirewall)`

- `(:GCPFirewall)-[:TARGET_TAG]->(:GCPNetworkTag)`

### GCPFolder

A Google Cloud Folder resource.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The name of the folder, e.g. "folders/1234". |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| displayname |  | A friendly name of the folder, e.g. "My Folder". |
| foldername |  | The name of the folder, e.g. "folders/1234". |
| lifecyclestate |  | The folder's current lifecycle state. Assigned by the server.  See the [official docs](https://cloud.google.com/resource-manager/reference/rest/v2/folders#LifecycleState). |
| parent_folder |  | If the folder's parent is another folder, this field contains the folder ID, e.g. "folders/5678". |
| parent_org |  | If the folder's parent is an organization, this field contains the organization ID, e.g. "organizations/1234". |

#### Relationships

- `(:GCPPolicyBinding)-[:APPLIES_TO]->(:GCPFolder)`: Connects a GCP IAM policy binding to the concrete resource where the policy applies.

- `(:GCPFolder)-[:PARENT]->(:GCPFolder)`: Relationship when folder's parent is another folder

- `(:GCPFolder)-[:PARENT]->(:GCPOrganization)`: Relationship when folder's parent is an organization

- `(:GCPProject)-[:PARENT]->(:GCPFolder)`: Relationship when project's parent is a folder

- `(:GCPOrganization)-[:RESOURCE]->(:GCPFolder)`

- `(:GCPFolder)-[:RESOURCE]->(:GCPPolicyBinding)`

### GCPForwardingRule

A Google Cloud forwarding rule that directs traffic to a load balancer target.

> **Ontology Mapping**: This node uses the ontology label [`LoadBalancer`](#ontology-loadbalancer).

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | A partial resource URI representing this Forwarding Rule. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| exposed_internet | Yes | `True` when the load balancing scheme is external. `False` otherwise. |
| exposed_internet_type | Yes | How it is exposed. Always `direct`. |
| ip_address |  | IP address that this Forwarding Rule serves. |
| ip_protocol |  | IP protocol to which this rule applies. |
| lb_type |  | Normalised load-balancer family derived from the target proxy collection (`http`, `https`, `tcp`, `ssl`, `grpc`, `network`, `vpn`). |
| load_balancing_scheme |  | Specifies the Forwarding Rule type. |
| name | Yes | Name of the Forwarding Rule. |
| network |  | A partial resource URI of the network this Forwarding Rule belongs to. |
| partial_uri |  | Same as `id`. |
| port_range |  | Port range used in conjunction with a target resource. Only packets addressed to ports in the specified range will be forwarded to target configured. |
| ports |  | Ports to forward to a backend service. Only packets addressed to these ports are forwarded to the backend services configured. |
| project_id |  | The project ID that this Forwarding Rule belongs to. |
| region |  | The region of this Forwarding Rule. |
| self_link |  | Server-defined URL for the resource. |
| subnetwork |  | A partial resource URI of the subnetwork this Forwarding Rule belongs to. |
| target |  | A partial resource URI of the target resource to receive the traffic. |
| *_ont_ip_address* | Yes | Normalized field sourced from `ip_address`. |
| *_ont_lb_type* | Yes | Normalized field sourced from `lb_type`. |
| *_ont_name* | Yes | Normalized field sourced from `name`. |
| *_ont_region* | Yes | Normalized field sourced from `region`. |
| *_ont_scheme* | Yes | Normalized field sourced from `load_balancing_scheme`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |

#### Relationships

- `(:PublicIP)-[:POINTS_TO]->(:GCPForwardingRule)`

- `(:GCPProject)-[:RESOURCE]->(:GCPForwardingRule)`

- `(:GCPSubnet)-[:RESOURCE]->(:GCPForwardingRule)`

- `(:GCPVpc)-[:RESOURCE]->(:GCPForwardingRule)`

- `(:GCPForwardingRule)-[:ROUTES_TO]->(:GCPTargetHttpsProxy)`: Matches on the existing `target` property, which transform_gcp_forwarding_rules()
already parses to a partial URI. A rule whose target isn't a targetHttpsProxies
resource simply won't match anything here.

- `(:GCPForwardingRule)-[:ROUTES_TO]->(:GCPTargetSslProxy)`: Same matching approach as GCPForwardingRuleToTargetHttpsProxyRel, for targetSslProxies.

### GCPInstance

Representation of a GCP [Instance](https://cloud.google.com/compute/docs/reference/rest/v1/instances).  Additional references can be found in the [official documentation]( https://cloud.google.com/compute/docs/concepts).

> **Ontology Mapping**: This node uses the ontology label [`ComputeInstance`](#ontology-computeinstance).

> **Additional Labels**: This node also uses `Instance`.

> **Additional Label Definitions**:
>
> - `Instance`: A gcp node participating in the shared Instance graph interface.

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The partial resource URI representing this instance. Has the form `projects/{project_name}/zones/{zone_name}/instances/{instance_name}`. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| block_project_ssh_keys |  | Instance metadata value for `block-project-ssh-keys` when explicitly set. |
| can_ip_forward |  | Whether the instance is configured with IP forwarding enabled. |
| creation_timestamp |  | RFC 3339 timestamp of when the instance was created. |
| enable_confidential_compute |  | Confidential Computing state from `confidentialInstanceConfig.enableConfidentialCompute`. |
| enable_integrity_monitoring |  | Shielded VM Integrity Monitoring state from `shieldedInstanceConfig.enableIntegrityMonitoring`. |
| enable_oslogin_metadata |  | Instance metadata value for `enable-oslogin` when explicitly set. |
| enable_vtpm |  | Shielded VM vTPM state from `shieldedInstanceConfig.enableVtpm`. |
| exposed_internet | Yes | `True` when the instance has a public access config reachable through an allowing firewall rule, or sits behind an exposed load balancer. `False` otherwise. |
| exposed_internet_type | Yes | How the instance is exposed: `direct` and/or `gcp_lb`. |
| hostname |  | If present, the hostname of the instance. |
| instancename | Yes | The name of the instance, e.g. "my-instance". |
| machine_type |  | The instance machine type short name, e.g. `n2d-standard-4`. |
| private_ip |  | Primary internal IP address (first NIC's `networkIP`). |
| project_id |  | Google Cloud project that owns this resource. |
| public_ip |  | Primary external IP address (first access config's `natIP`), if any. |
| self_link |  | The full resource URI representing this instance. Has the form `https://www.googleapis.com/compute/v1/{partial_uri}`. |
| serial_port_enable |  | Instance metadata value for `serial-port-enable` when explicitly set. |
| service_account_email |  | Primary attached service account email when the instance has one. |
| service_account_scopes |  | OAuth scopes configured on the primary attached service account. |
| status |  | The [GCP Instance Lifecycle](https://cloud.google.com/compute/docs/instances/instance-life-cycle) state of the instance. |
| zone_name |  | The zone that the instance is installed on. |
| *_ont_created_at* | Yes | Normalized field sourced from `creation_timestamp`. |
| *_ont_name* | Yes | Normalized field sourced from `instancename`. |
| *_ont_private_ip_address* | Yes | Normalized field sourced from `private_ip`. |
| *_ont_public_ip_address* | Yes | Normalized field sourced from `public_ip`. |
| *_ont_region* | Yes | Normalized field sourced from `zone_name`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |
| *_ont_state* | Yes | Normalized field sourced from `status`. |
| *_ont_type* | Yes | Normalized field sourced from `machine_type`. |

#### Relationships

- `(:GCPPolicyBinding)-[:APPLIES_TO]->(:GCPInstance)`: Connects a GCP IAM policy binding to the concrete resource where the policy applies.

- `(:DNSRecord)-[:DNS_POINTS_TO]->(:GCPInstance)`: generated by analysis job `Ontology - DNSRecord to GCPInstance linking`.

- `(:GCPBackendService)-[:EXPOSE]->(:GCPInstance)`: generated by analysis job `GCP BackendService to Instance EXPOSE relationship (scoped per project)`.
  - Properties:

    | Field | Description |
    |-------|-------------|
    | exposure_type | Property generated by analysis job: `GCP BackendService to Instance EXPOSE relationship (scoped per project)`. |

- `(:GCPFirewall)-[:FIREWALL_INGRESS]->(:GCPInstance)`: generated by analysis job `GCP firewall ingress to instance analysis`.

- `(:GCPInstanceGroup)-[:HAS_MEMBER]->(:GCPInstance)`

- `(:GCPInstance)-[:LABELED]->(:GCPLabel)`: Indicates that a GCP instance has this legacy label.

- `(:GCPInstance)-[:MEMBER_OF_GCP_VPC]->(:GCPVpc)`: generated by analysis job `GCP Instance to VPC derived relationship analysis`.

- `(:GCPInstance)-[:NETWORK_INTERFACE]->(:GCPNetworkInterface)`

- `(:PublicIP)-[:POINTS_TO]->(:GCPInstance)`

- `(:GCPProject)-[:RESOURCE]->(:GCPInstance)`

- `(:GCPInstance)-[:RUNS_AS]->(:GCPServiceAccount)`

- `(:GCPInstance)-[:TAGGED]->(:GCPLabel)`: Indicates that a GCP instance is tagged with this label.

- `(:GCPInstance)-[:TAGGED]->(:GCPNetworkTag)`

### GCPInstanceGroup

Representation of a GCP [Instance Group](https://cloud.google.com/compute/docs/reference/rest/v1/instanceGroups). Instance groups are collections of VM instances that can be managed together and serve as backends for load balancing.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Stable identifier for this resource. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| creation_timestamp |  | Creation timestamp of the resource. |
| description |  | An optional description of this instance group. |
| name | Yes | Name assigned to this resource. |
| network |  | The partial URI of the VPC network this instance group belongs to. |
| partial_uri |  | Same as `id`. |
| project_id |  | The project ID that this instance group belongs to. |
| region |  | The region of this instance group (for regional instance groups). |
| self_link |  | Server-defined URL for the resource. |
| size |  | The number of instances in this instance group. |
| subnetwork |  | The partial URI of the subnet this instance group belongs to. |
| zone |  | The zone of this instance group. |

#### Relationships

- `(:GCPInstanceGroup)-[:HAS_MEMBER]->(:GCPInstance)`

- `(:GCPProject)-[:RESOURCE]->(:GCPInstanceGroup)`

- `(:GCPBackendService)-[:ROUTES_TO]->(:GCPInstanceGroup)`

### GCPIpRange

Representation of an IP range or subnet.

> **Additional Labels**: This node also uses `IpRange`.

> **Additional Label Definitions**:
>
> - `IpRange`: A node participating in the shared IpRange graph interface.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | CIDR notation for the IP range. E.g. "0.0.0.0/0" for the whole internet. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| range | Yes | CIDR range governed by this firewall rule. |

#### Relationships

- `(:GCPIpRange)-[:MEMBER_OF_IP_RULE]->(:GCPIpRule)`

- `(:GCPProject)-[:RESOURCE]->(:GCPIpRange)`

### GCPIpRule

An allowed or denied protocol and port rule attached to a Google Cloud firewall.

> **Additional Labels**: This node also uses `IpPermissionInbound`, `IpRule`.

> **Additional Label Definitions**:
>
> - `IpPermissionInbound`: A node participating in the shared IpPermissionInbound graph interface.
> - `IpRule`: A node participating in the shared IpRule graph interface.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Stable identifier for this resource. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| fromport |  | Lowest port in the range defined by this rule. |
| protocol |  | The protocol this rule applies to. |
| toport |  | Highest port in the range defined by this rule. |

#### Relationships

- `(:GCPIpRule)-[:ALLOWED_BY]->(:GCPFirewall)`

- `(:GCPIpRule)-[:DENIED_BY]->(:GCPFirewall)`

- `(:GCPIpRange)-[:MEMBER_OF_IP_RULE]->(:GCPIpRule)`

- `(:GCPProject)-[:RESOURCE]->(:GCPIpRule)`

### GCPKeyRing

Representation of a GCP [Key Ring](https://cloud.google.com/kms/docs/reference/rest/v1/projects.locations.keyRings).

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The full resource name of the Key Ring. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| location |  | The GCP location of the Key Ring. |
| name |  | The short name of the Key Ring. |
| project_id |  | Google Cloud project that owns this resource. |

#### Relationships

- `(:GCPPolicyBinding)-[:APPLIES_TO]->(:GCPKeyRing)`: Connects a GCP IAM policy binding to the concrete resource where the policy applies.

- `(:GCPKeyRing)-[:CONTAINS]->(:GCPCryptoKey)`

- `(:GCPProject)-[:RESOURCE]->(:GCPKeyRing)`

### GCPLabel

A key-value label attached to a supported Google Cloud resource.

> **Ontology Mapping**: Some schema variants may also use the ontology label [`Tag`](#ontology-tag).

> **Additional Labels**: This node also uses `Label`.

> **Additional Labels**: Some schema variants may also use `GCPBucketLabel`.

> **Additional Label Definitions**:
>
> - `GCPBucketLabel`: A gcp node participating in the shared GCPBucketLabel graph interface.
> - `Label`: A gcp node participating in the shared Label graph interface.

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The ID of the label. Takes the form `{resource_id}:{key}:{value}`. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| key | Yes | The key of the label. |
| resource_type |  | The Cartography node label of the resource this label is attached to (e.g. `GCPBucket`, `GCPInstance`). |
| value |  | The value of the label. |
| *_ont_source* |  | Module that populated this node's ontology fields. |

#### Relationships

- `(:GCPBigtableInstance)-[:LABELED]->(:GCPLabel)`: Indicates that a GCP Bigtable instance has this legacy label.

- `(:GCPBucket)-[:LABELED]->(:GCPLabel)`: Indicates that a GCP bucket has this legacy label.

- `(:GCPCloudFunction)-[:LABELED]->(:GCPLabel)`: Indicates that a GCP Cloud Function has this legacy label.

- `(:GCPCloudRunJob)-[:LABELED]->(:GCPLabel)`: Indicates that a GCP Cloud Run job has this legacy label.

- `(:GCPCloudRunService)-[:LABELED]->(:GCPLabel)`: Indicates that a GCP Cloud Run service has this legacy label.

- `(:GCPCloudSQLInstance)-[:LABELED]->(:GCPLabel)`: Indicates that a GCP Cloud SQL instance has this legacy label.

- `(:GCPDNSZone)-[:LABELED]->(:GCPLabel)`: Indicates that a GCP DNS zone has this legacy label.

- `(:GCPInstance)-[:LABELED]->(:GCPLabel)`: Indicates that a GCP instance has this legacy label.

- `(:GCPSecretManagerSecret)-[:LABELED]->(:GCPLabel)`: Indicates that a GCP Secret Manager secret has this legacy label.

- `(:GKECluster)-[:LABELED]->(:GCPLabel)`: Indicates that a GKE cluster has this legacy label.

- `(:GCPProject)-[:RESOURCE]->(:GCPLabel)`: Indicates that a GCP project contains this label as a resource.

- `(:GCPBigtableInstance)-[:TAGGED]->(:GCPLabel)`: Indicates that a GCP Bigtable instance is tagged with this label.

- `(:GCPBucket)-[:TAGGED]->(:GCPLabel)`: Indicates that a GCP bucket is tagged with this label.

- `(:GCPCloudRunJob)-[:TAGGED]->(:GCPLabel)`: Indicates that a GCP Cloud Run job is tagged with this label.

- `(:GCPCloudRunService)-[:TAGGED]->(:GCPLabel)`: Indicates that a GCP Cloud Run service is tagged with this label.

- `(:GCPCloudSQLInstance)-[:TAGGED]->(:GCPLabel)`: Indicates that a GCP Cloud SQL instance is tagged with this label.

- `(:GCPDNSZone)-[:TAGGED]->(:GCPLabel)`: Indicates that a GCP DNS zone is tagged with this label.

- `(:GCPInstance)-[:TAGGED]->(:GCPLabel)`: Indicates that a GCP instance is tagged with this label.

- `(:GCPSecretManagerSecret)-[:TAGGED]->(:GCPLabel)`: Indicates that a GCP Secret Manager secret is tagged with this label.

- `(:GKECluster)-[:TAGGED]->(:GCPLabel)`: Indicates that a GKE cluster is tagged with this label.

### GCPNetworkInterface

Representation of a GCP Instance's [network interface](https://cloud.google.com/compute/docs/reference/rest/v1/instances/list) (scroll down to the fields on "networkInterface").

> **Additional Labels**: This node also uses `NetworkInterface`.

> **Additional Label Definitions**:
>
> - `NetworkInterface`: A node participating in the shared NetworkInterface graph interface.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | A partial resource URI representing this network interface.  Note: GCP does not define a partial resource URI for network interfaces, so we create one so we can uniquely identify GCP network interfaces.  Has the form `projects/{project_name}/zones/{zone_name}/instances/{instance_name}/networkinterfaces/{network interface name}`. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| name |  | The name of the network interface. |
| private_ip |  | The private IP address of this network interface.  This IP is valid on the network interface's VPC. |

#### Relationships

- `(:GCPInstance)-[:NETWORK_INTERFACE]->(:GCPNetworkInterface)`

- `(:GCPNetworkInterface)-[:PART_OF_SUBNET]->(:GCPSubnet)`

- `(:GCPNetworkInterface)-[:RESOURCE]->(:GCPNicAccessConfig)`

- `(:GCPProject)-[:RESOURCE]->(:GCPNetworkInterface)`

### GCPNetworkTag

A Google Cloud Network Tag resource.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | GCP doesn't define a resource URI for Tags so we define this as `{instance resource URI}/tags/{tag value}`. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| tag_id | Yes | same as `id`. |
| value |  | The actual value of the tag. |

#### Relationships

- `(:GCPNetworkTag)-[:DEFINED_IN]->(:GCPVpc)`

- `(:GCPProject)-[:RESOURCE]->(:GCPNetworkTag)`

- `(:GCPInstance)-[:TAGGED]->(:GCPNetworkTag)`

- `(:GCPFirewall)-[:TARGET_TAG]->(:GCPNetworkTag)`

### GCPNicAccessConfig

Representation of the AccessConfig object on a GCP Instance's [network interface](https://cloud.google.com/compute/docs/reference/rest/v1/instances/list) (scroll down to the fields on "networkInterface").

> **Ontology Projection**: `GCPNicAccessConfig` contributes data to canonical [`PublicIP`](#ontology-publicip) nodes.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | A partial resource URI representing this AccessConfig.  Note: GCP does not define a partial resource URI for AccessConfigs, so we create one so we can uniquely identify GCP network interface access configs.  Has the form `projects/{project_name}/zones/{zone_name}/instances/{instance_name}/networkinterfaces/{network interface name}/accessconfigs/{access config type}`. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| name |  | The name of this access configuration. The default and recommended name is External NAT, but you can use any arbitrary string, such as My external IP or Network Access. |
| network_tier |  | This signifies the networking tier used for configuring this access configuration and can only take the following values: PREMIUM, STANDARD. |
| public_ip |  | The external IP associated with this instance. |
| public_ptr_domain_name |  | The DNS domain name for the public PTR record. You can set this field only if the setPublicPtr field is enabled. |
| set_public_ptr |  | Specifies whether a public DNS 'PTR' record should be created to map the external IP address of the instance to a DNS domain name. |
| type |  | The type of configuration. GCP docs say: "The default and only option is ONE_TO_ONE_NAT.". |

#### Relationships

- `(:PublicIP)-[:RESERVED_BY]->(:GCPNicAccessConfig)`

- `(:GCPNetworkInterface)-[:RESOURCE]->(:GCPNicAccessConfig)`

- `(:GCPProject)-[:RESOURCE]->(:GCPNicAccessConfig)`

### GCPOrganization

Representation of a GCP [Organization](https://cloud.google.com/resource-manager/reference/rest/v1/organizations) object.

> **Ontology Mapping**: This node uses the ontology label [`Tenant`](#ontology-tenant).

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The name of the GCP Organization, e.g. "organizations/1234". |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| displayname |  | The "friendly name", e.g. "My Company". |
| lifecyclestate |  | The organization's current lifecycle state. Assigned by the server.  See the [official docs](https://cloud.google.com/resource-manager/reference/rest/v1/organizations#LifecycleState). |
| orgname |  | Name assigned to this resource. |
| *_ont_name* | Yes | Normalized field sourced from `displayname`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |
| *_ont_status* | Yes | Normalized field sourced from `lifecyclestate`. |

#### Relationships

- `(:GCPPolicyBinding)-[:APPLIES_TO]->(:GCPOrganization)`: Connects a GCP IAM policy binding to the concrete resource where the policy applies.

- `(:GCPFolder)-[:PARENT]->(:GCPOrganization)`: Relationship when folder's parent is an organization

- `(:GCPProject)-[:PARENT]->(:GCPOrganization)`: Relationship when project's parent is an organization

- `(:GCPOrganization)-[:RESOURCE]->(:GCPFolder)`

- `(:GCPOrganization)-[:RESOURCE]->(:GCPPolicyBinding)`

- `(:GCPOrganization)-[:RESOURCE]->(:GCPProject)`

- `(:GCPOrganization)-[:RESOURCE]->(:GCPRole)`: Relationship connecting organization-level GCPRole to GCPOrganization.

### GCPPolicyBinding

A Google Cloud IAM policy binding that grants a role on a resource.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Binding identifier in `{resource}_{role}` form. Conditional bindings append `_{hash}`, where `hash` is the first eight hexadecimal characters of the SHA-256 condition-expression digest. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| condition_expression |  | The expression of the condition. |
| condition_title |  | The title of the condition. |
| domains |  | A list of domains (`domain:{domain}`) granted the role. These do not resolve to a single `GCPPrincipal` node, but are retained for visibility (e.g. broad-access audits). |
| has_condition | Yes | A boolean indicating if the policy binding has a condition attached. |
| is_public | Yes | True if the binding includes the `allUsers` or `allAuthenticatedUsers` principal. Combine with `has_condition = false` to reason about unconditional public exposure. |
| members |  | A list of principal email addresses that are granted the role. The synthetic GCP principals `allUsers` and `allAuthenticatedUsers` are NOT included here; presence of either is reflected in `is_public` instead. |
| resource |  | The full resource name where the policy binding is attached. |
| resource_type |  | The type of resource. |
| role |  | The name of the GCP role being granted. |
| wif_pools |  | A list of Workload Identity Federation pool resource names (`projects/{N}/locations/global/workloadIdentityPools/{POOL}`) referenced by `principal://` or `principalSet://` members of this binding. |

#### Relationships

- `(:GCPPolicyBinding)-[:APPLIES_TO]->(:GCPArtifactRegistryRepository)`: Connects a GCP IAM policy binding to the concrete resource where the policy applies.

- `(:GCPPolicyBinding)-[:APPLIES_TO]->(:GCPBigQueryDataset)`: Connects a GCP IAM policy binding to the concrete resource where the policy applies.

- `(:GCPPolicyBinding)-[:APPLIES_TO]->(:GCPBigQueryTable)`: Connects a GCP IAM policy binding to the concrete resource where the policy applies.

- `(:GCPPolicyBinding)-[:APPLIES_TO]->(:GCPBucket)`: Connects a GCP IAM policy binding to the concrete resource where the policy applies.

- `(:GCPPolicyBinding)-[:APPLIES_TO]->(:GCPCloudFunction)`: Connects a GCP IAM policy binding to the concrete resource where the policy applies.

- `(:GCPPolicyBinding)-[:APPLIES_TO]->(:GCPCloudRunService)`: Connects a GCP IAM policy binding to the concrete resource where the policy applies.

- `(:GCPPolicyBinding)-[:APPLIES_TO]->(:GCPCryptoKey)`: Connects a GCP IAM policy binding to the concrete resource where the policy applies.

- `(:GCPPolicyBinding)-[:APPLIES_TO]->(:GCPFirewall)`: Connects a GCP IAM policy binding to the concrete resource where the policy applies.

- `(:GCPPolicyBinding)-[:APPLIES_TO]->(:GCPFolder)`: Connects a GCP IAM policy binding to the concrete resource where the policy applies.

- `(:GCPPolicyBinding)-[:APPLIES_TO]->(:GCPInstance)`: Connects a GCP IAM policy binding to the concrete resource where the policy applies.

- `(:GCPPolicyBinding)-[:APPLIES_TO]->(:GCPKeyRing)`: Connects a GCP IAM policy binding to the concrete resource where the policy applies.

- `(:GCPPolicyBinding)-[:APPLIES_TO]->(:GCPOrganization)`: Connects a GCP IAM policy binding to the concrete resource where the policy applies.

- `(:GCPPolicyBinding)-[:APPLIES_TO]->(:GCPProject)`: Connects a GCP IAM policy binding to the concrete resource where the policy applies.

- `(:GCPPolicyBinding)-[:APPLIES_TO]->(:GCPSecretManagerSecret)`: Connects a GCP IAM policy binding to the concrete resource where the policy applies.

- `(:GCPPolicyBinding)-[:APPLIES_TO]->(:GCPSecretManagerSecretVersion)`: Connects a GCP IAM policy binding to the concrete resource where the policy applies.

- `(:GCPPolicyBinding)-[:APPLIES_TO]->(:GCPServiceAccount)`: Connects a GCP IAM policy binding to the concrete resource where the policy applies.

- `(:GCPPolicyBinding)-[:APPLIES_TO]->(:GCPSubnet)`: Connects a GCP IAM policy binding to the concrete resource where the policy applies.

- `(:GCPPolicyBinding)-[:APPLIES_TO]->(:GCPVpc)`: Connects a GCP IAM policy binding to the concrete resource where the policy applies.

- `(:GCPPolicyBinding)-[:GRANTS_ROLE]->(:GCPRole)`

- `(:GCPPrincipal)-[:HAS_ALLOW_POLICY]->(:GCPPolicyBinding)`

- `(:GCPWorkloadIdentityPool)-[:HAS_ALLOW_POLICY]->(:GCPPolicyBinding)`

- `(:GCPFolder)-[:RESOURCE]->(:GCPPolicyBinding)`

- `(:GCPOrganization)-[:RESOURCE]->(:GCPPolicyBinding)`

- `(:GCPProject)-[:RESOURCE]->(:GCPPolicyBinding)`

### GCPProject

A Google Cloud Project resource.

> **Ontology Mapping**: This node uses the ontology label [`Tenant`](#ontology-tenant).

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Stable identifier for this resource. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| compute_project_enable_oslogin |  | Project metadata setting that enables OS Login for Compute Engine instances. |
| displayname |  | Human-readable name shown for this resource. |
| lifecyclestate |  | Current Resource Manager project lifecycle state. |
| parent_folder |  | Parent folder resource name when the project belongs to a folder. |
| parent_org |  | Parent organization resource name when the project belongs directly to an organization. |
| projectnumber | Yes | Numeric identifier of the owning Google Cloud project. |
| *_ont_name* | Yes | Normalized field sourced from `displayname`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |
| *_ont_status* | Yes | Normalized field sourced from `lifecyclestate`. |

#### Relationships

- `(:GCPPolicyBinding)-[:APPLIES_TO]->(:GCPProject)`: Connects a GCP IAM policy binding to the concrete resource where the policy applies.

- `(:GCPProject)-[:PARENT]->(:GCPFolder)`: Relationship when project's parent is a folder

- `(:GCPProject)-[:PARENT]->(:GCPOrganization)`: Relationship when project's parent is an organization

- `(:GCPProject)-[:RESOURCE]->(:GCPApiKey)`

- `(:GCPProject)-[:RESOURCE]->(:GCPArtifactRegistryGenericArtifact)`

- `(:GCPProject)-[:RESOURCE]->(:GCPArtifactRegistryHelmChart)`

- `(:GCPProject)-[:RESOURCE]->(:GCPArtifactRegistryImageLayer)`

- `(:GCPProject)-[:RESOURCE]->(:GCPArtifactRegistryLanguagePackage)`

- `(:GCPProject)-[:RESOURCE]->(:GCPArtifactRegistryRepository)`

- `(:GCPProject)-[:RESOURCE]->(:GCPArtifactRegistryRepositoryImage)`

- `(:GCPProject)-[:RESOURCE]->(:GCPBackendService)`

- `(:GCPProject)-[:RESOURCE]->(:GCPBigQueryConnection)`

- `(:GCPProject)-[:RESOURCE]->(:GCPBigQueryDataset)`

- `(:GCPProject)-[:RESOURCE]->(:GCPBigQueryRoutine)`

- `(:GCPProject)-[:RESOURCE]->(:GCPBigQueryTable)`

- `(:GCPProject)-[:RESOURCE]->(:GCPBigtableAppProfile)`

- `(:GCPProject)-[:RESOURCE]->(:GCPBigtableBackup)`

- `(:GCPProject)-[:RESOURCE]->(:GCPBigtableCluster)`

- `(:GCPProject)-[:RESOURCE]->(:GCPBigtableInstance)`

- `(:GCPProject)-[:RESOURCE]->(:GCPBigtableTable)`

- `(:GCPProject)-[:RESOURCE]->(:GCPBucket)`

- `(:GCPProject)-[:RESOURCE]->(:GCPBucketLabel)`

- `(:GCPProject)-[:RESOURCE]->(:GCPCloudArmorPolicy)`

- `(:GCPProject)-[:RESOURCE]->(:GCPCloudFunction)`

- `(:GCPProject)-[:RESOURCE]->(:GCPCloudRunExecution)`

- `(:GCPProject)-[:RESOURCE]->(:GCPCloudRunJob)`

- `(:GCPProject)-[:RESOURCE]->(:GCPCloudRunJobContainer)`

- `(:GCPProject)-[:RESOURCE]->(:GCPCloudRunRevision)`

- `(:GCPProject)-[:RESOURCE]->(:GCPCloudRunService)`

- `(:GCPProject)-[:RESOURCE]->(:GCPCloudRunServiceContainer)`

- `(:GCPProject)-[:RESOURCE]->(:GCPCloudSQLAuthorizedNetwork)`

- `(:GCPProject)-[:RESOURCE]->(:GCPCloudSQLBackupConfiguration)`

- `(:GCPProject)-[:RESOURCE]->(:GCPCloudSQLDatabase)`

- `(:GCPProject)-[:RESOURCE]->(:GCPCloudSQLInstance)`

- `(:GCPProject)-[:RESOURCE]->(:GCPCloudSQLUser)`

- `(:GCPProject)-[:RESOURCE]->(:GCPCryptoKey)`

- `(:GCPProject)-[:RESOURCE]->(:GCPDNSZone)`

- `(:GCPProject)-[:RESOURCE]->(:GCPFirewall)`

- `(:GCPProject)-[:RESOURCE]->(:GCPForwardingRule)`

- `(:GCPProject)-[:RESOURCE]->(:GCPInstance)`

- `(:GCPProject)-[:RESOURCE]->(:GCPInstanceGroup)`

- `(:GCPProject)-[:RESOURCE]->(:GCPIpRange)`

- `(:GCPProject)-[:RESOURCE]->(:GCPIpRule)`

- `(:GCPProject)-[:RESOURCE]->(:GCPKeyRing)`

- `(:GCPProject)-[:RESOURCE]->(:GCPLabel)`: Indicates that a GCP project contains this label as a resource.

- `(:GCPProject)-[:RESOURCE]->(:GCPNetworkInterface)`

- `(:GCPProject)-[:RESOURCE]->(:GCPNetworkTag)`

- `(:GCPProject)-[:RESOURCE]->(:GCPNicAccessConfig)`

- `(:GCPOrganization)-[:RESOURCE]->(:GCPProject)`

- `(:GCPProject)-[:RESOURCE]->(:GCPPolicyBinding)`

- `(:GCPProject)-[:RESOURCE]->(:GCPRecordSet)`

- `(:GCPProject)-[:RESOURCE]->(:GCPRole)`: Relationship connecting project-level GCPRole to GCPProject.

- `(:GCPProject)-[:RESOURCE]->(:GCPSecretManagerSecret)`: Indicates that a GCP project contains this Secret Manager secret as a resource.

- `(:GCPProject)-[:RESOURCE]->(:GCPSecretManagerSecretVersion)`: Indicates that a GCP project contains this Secret Manager secret version as a resource.

- `(:GCPProject)-[:RESOURCE]->(:GCPServiceAccount)`

- `(:GCPProject)-[:RESOURCE]->(:GCPServiceAccountKey)`

- `(:GCPProject)-[:RESOURCE]->(:GCPSslPolicy)`

- `(:GCPProject)-[:RESOURCE]->(:GCPSubnet)`

- `(:GCPProject)-[:RESOURCE]->(:GCPTargetHttpsProxy)`

- `(:GCPProject)-[:RESOURCE]->(:GCPTargetSslProxy)`

- `(:GCPProject)-[:RESOURCE]->(:GCPVertexAIDataset)`

- `(:GCPProject)-[:RESOURCE]->(:GCPVertexAIDeployedModel)`

- `(:GCPProject)-[:RESOURCE]->(:GCPVertexAIEndpoint)`

- `(:GCPProject)-[:RESOURCE]->(:GCPVertexAIFeatureGroup)`

- `(:GCPProject)-[:RESOURCE]->(:GCPVertexAIModel)`

- `(:GCPProject)-[:RESOURCE]->(:GCPVertexAITrainingPipeline)`

- `(:GCPProject)-[:RESOURCE]->(:GCPVertexAIWorkbenchInstance)`

- `(:GCPProject)-[:RESOURCE]->(:GCPVpc)`

- `(:GCPProject)-[:RESOURCE]->(:GCPVpcPeering)`

- `(:GCPProject)-[:RESOURCE]->(:GCPVpnGateway)`

- `(:GCPProject)-[:RESOURCE]->(:GCPVpnTunnel)`

- `(:GCPProject)-[:RESOURCE]->(:GCPWorkloadIdentityPool)`

- `(:GCPProject)-[:RESOURCE]->(:GCPWorkloadIdentityProvider)`

- `(:GCPProject)-[:RESOURCE]->(:GKECluster)`

### GCPRecordSet

Representation of a GCP [Resource Record Set](https://cloud.google.com/dns/docs/reference/v1/).

> **Ontology Mapping**: This node uses the ontology label [`DNSRecord`](#ontology-dnsrecord).

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Stable identifier for this resource. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| data |  | Data contained in the record. |
| name | Yes | The name of the Resource Record Set. |
| ttl |  | Number of seconds that this ResourceRecordSet can be cached by resolvers. |
| type |  | The identifier of a supported record type. See the list of [Supported DNS record types](https://cloud.google.com/dns/docs/overview#supported_dns_record_types). |
| *_ont_name* | Yes | Normalized field sourced from `name`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |
| *_ont_type* | Yes | Normalized field sourced from `type`. |

#### Relationships

- `(:GCPRecordSet)-[:DNS_POINTS_TO]->(:GCPInstance)`: generated by analysis job `Ontology - DNSRecord to GCPInstance linking`.

- `(:GCPDNSZone)-[:HAS_RECORD]->(:GCPRecordSet)`

- `(:GCPProject)-[:RESOURCE]->(:GCPRecordSet)`

### GCPRole

This node label is loaded by more than one sync path:

- A custom Google Cloud IAM role defined in a single project.
- A predefined or organization-level Google Cloud IAM role.

> **Ontology Mapping**: This node uses the ontology label [`PermissionRole`](#ontology-permissionrole).

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The unique identifier for the role (same as name). |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| deleted |  | A boolean indicating if the role is deleted. |
| description |  | A description of the role. |
| etag |  | The ETag of the role for optimistic concurrency control. |
| name | Yes | The name of the role (e.g., `roles/editor`, `organizations/123/roles/custom`, `projects/abc/roles/custom`). |
| organization_id |  | Google Cloud organization that owns this resource. |
| permissions |  | A list of permissions included in the role. |
| project_id |  | Google Cloud project that owns this resource. |
| role_type |  | IAM role category, such as predefined or custom. |
| scope |  | The scope of the role: `GLOBAL` (predefined/basic), `ORGANIZATION` (custom org), or `PROJECT` (custom project). |
| title |  | The human-readable title of the role. |
| *_ont_name* | Yes | Normalized field sourced from `title`. |
| *_ont_scope* | Yes | Normalized field sourced from `scope`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |
| *_ont_type* | Yes | Normalized field sourced from `role_type`. |

#### Relationships

- `(:GCPPolicyBinding)-[:GRANTS_ROLE]->(:GCPRole)`

- `(:GCPOrganization)-[:RESOURCE]->(:GCPRole)`: Relationship connecting organization-level GCPRole to GCPOrganization.

- `(:GCPProject)-[:RESOURCE]->(:GCPRole)`: Relationship connecting project-level GCPRole to GCPProject.

### GCPSecretManagerSecret

Representation of a GCP [Secret Manager Secret](https://cloud.google.com/secret-manager/docs/reference/rest/v1/projects.secrets). A Secret is a logical container for secret data that can have multiple versions.

> **Ontology Mapping**: This node uses the ontology label [`Secret`](#ontology-secret).

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Stable identifier for this resource. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| created_date |  | Epoch timestamp when the secret was created. |
| etag |  | Used to perform consistent read-modify-write updates. |
| expire_time |  | Epoch timestamp when the secret will automatically expire and be deleted. |
| labels |  | JSON string of user-defined labels. |
| name | Yes | The short name of the secret. |
| project_id |  | The GCP project ID that owns this secret. |
| replication_type |  | The replication policy type: `automatic` or `user_managed`. |
| rotation_enabled |  | Boolean indicating if automatic rotation is configured. |
| rotation_next_time |  | Epoch timestamp of the next scheduled rotation. |
| rotation_period |  | The rotation period in seconds (if rotation is enabled). |
| topics |  | JSON string of Pub/Sub topics for rotation notifications. |
| version_aliases |  | JSON string mapping alias names to version numbers. |
| *_ont_created_at* | Yes | Normalized field sourced from `created_date`. |
| *_ont_name* | Yes | Normalized field sourced from `name`. |
| *_ont_rotation_enabled* | Yes | Normalized field sourced from `rotation_enabled`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |

#### Relationships

- `(:GCPPolicyBinding)-[:APPLIES_TO]->(:GCPSecretManagerSecret)`: Connects a GCP IAM policy binding to the concrete resource where the policy applies.

- `(:GCPPrincipal)-[:CAN_READ]->(:GCPSecretManagerSecret)`: `GCPPrincipal` receives evaluated `CAN_READ` access to `GCPSecretManagerSecret` from GCP IAM policies.
  - Evaluated permissions: `secretmanager.versions.access`
  - Properties:

    | Field | Description |
    |-------|-------------|
    | condition_expression | CEL expression that must be satisfied for this permission. |
    | condition_title | Title of the IAM condition that restricts this permission. |
    | has_condition | Whether an IAM condition restricts this permission. |

- `(:GCPSecretManagerSecret)-[:LABELED]->(:GCPLabel)`: Indicates that a GCP Secret Manager secret has this legacy label.

- `(:GCPProject)-[:RESOURCE]->(:GCPSecretManagerSecret)`: Indicates that a GCP project contains this Secret Manager secret as a resource.

- `(:GCPSecretManagerSecret)-[:TAGGED]->(:GCPLabel)`: Indicates that a GCP Secret Manager secret is tagged with this label.

- `(:GCPSecretManagerSecretVersion)-[:VERSION_OF]->(:GCPSecretManagerSecret)`: Indicates that this Secret Manager secret version is a version of its parent secret.

### GCPSecretManagerSecretVersion

Representation of a GCP [Secret Manager Secret Version](https://cloud.google.com/secret-manager/docs/reference/rest/v1/projects.secrets.versions). A SecretVersion stores a specific version of secret data within a Secret.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Stable identifier for this resource. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| created_date |  | Epoch timestamp when the version was created. |
| destroy_time |  | Epoch timestamp when the version was destroyed (only present if state is `DESTROYED`). |
| etag |  | Used to perform consistent read-modify-write updates. |
| secret_id |  | Full resource name of the parent secret. |
| state |  | The current state of the version: `ENABLED`, `DISABLED`, or `DESTROYED`. |
| version |  | The version number (e.g., "1", "2"). |

#### Relationships

- `(:GCPPolicyBinding)-[:APPLIES_TO]->(:GCPSecretManagerSecretVersion)`: Connects a GCP IAM policy binding to the concrete resource where the policy applies.

- `(:GCPProject)-[:RESOURCE]->(:GCPSecretManagerSecretVersion)`: Indicates that a GCP project contains this Secret Manager secret version as a resource.

- `(:GCPSecretManagerSecretVersion)-[:VERSION_OF]->(:GCPSecretManagerSecret)`: Indicates that this Secret Manager secret version is a version of its parent secret.

### GCPServiceAccount

Representation of a GCP [Service Account](https://cloud.google.com/iam/docs/reference/rest/v1/projects.serviceAccounts).

> **Ontology Mapping**: This node uses the ontology label [`ServiceAccount`](#ontology-serviceaccount).

> **Additional Labels**: This node also uses `GCPPrincipal`.

> **Additional Label Definitions**:
>
> - `GCPPrincipal`: A node participating in the shared GCPPrincipal graph interface.

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Stable numeric uniqueId used as the service account graph ID. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| disabled |  | A boolean indicating if the service account is disabled. |
| display_name |  | Human-readable name shown for this resource. |
| email | Yes | The email address associated with the service account. |
| oauth2_client_id |  | OAuth 2.0 client ID assigned to the service account. |
| project_id |  | Google Cloud project that owns this resource. |
| unique_id |  | Stable numeric Google-generated service account ID used as the graph identifier. |
| *_ont_active* | Yes | Normalized field sourced from `disabled`. |
| *_ont_email* | Yes | Normalized field sourced from `email`. |
| *_ont_name* | Yes | Normalized field sourced from `display_name`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |

#### Relationships

- `(:GCPPolicyBinding)-[:APPLIES_TO]->(:GCPServiceAccount)`: Connects a GCP IAM policy binding to the concrete resource where the policy applies.

- `(:GCPPrincipal)-[:CAN_IMPERSONATE]->(:GCPServiceAccount)`: `GCPPrincipal` receives evaluated `CAN_IMPERSONATE` access to `GCPServiceAccount` from GCP IAM policies.
  - Evaluated permissions: `iam.serviceAccounts.actAs`, `iam.serviceAccounts.getAccessToken`, `iam.serviceAccounts.getOpenIdToken`, `iam.serviceAccounts.implicitDelegation`, `iam.serviceAccounts.signBlob`, `iam.serviceAccounts.signJwt`
  - Properties:

    | Field | Description |
    |-------|-------------|
    | condition_expression | CEL expression that must be satisfied for this permission. |
    | condition_title | Title of the IAM condition that restricts this permission. |
    | has_condition | Whether an IAM condition restricts this permission. |

- `(:GCPBigQueryConnection)-[:CONNECTS_WITH]->(:GCPServiceAccount)`

- `(:GCPServiceAccount)-[:HAS_KEY]->(:GCPServiceAccountKey)`

- `(:DatabricksStorageCredential)-[:IMPERSONATES]->(:GCPServiceAccount)`: A Databricks storage credential impersonates a Google Cloud service account.

- `(:GCPServiceAccountKey)-[:OWNED_BY]->(:GCPServiceAccount)`

- `(:GCPProject)-[:RESOURCE]->(:GCPServiceAccount)`

- `(:GCPCloudFunction)-[:RUNS_AS]->(:GCPServiceAccount)`

- `(:GCPCloudRunJob)-[:RUNS_AS]->(:GCPServiceAccount)`

- `(:GCPCloudRunService)-[:RUNS_AS]->(:GCPServiceAccount)`

- `(:GCPInstance)-[:RUNS_AS]->(:GCPServiceAccount)`

- `(:GCPCloudRunJob)-[:USES_SERVICE_ACCOUNT]->(:GCPServiceAccount)`

- `(:GCPCloudRunRevision)-[:USES_SERVICE_ACCOUNT]->(:GCPServiceAccount)`

- `(:GCPCloudRunService)-[:USES_SERVICE_ACCOUNT]->(:GCPServiceAccount)`

- `(:GCPCloudSQLInstance)-[:USES_SERVICE_ACCOUNT]->(:GCPServiceAccount)`

- `(:GCPVertexAIWorkbenchInstance)-[:USES_SERVICE_ACCOUNT]->(:GCPServiceAccount)`

- `(:KubernetesServiceAccount)-[:WORKLOAD_IDENTITY_BINDING]->(:GCPServiceAccount)`: Links a service account to the Google Cloud service account it impersonates through Workload Identity.

### GCPServiceAccountKey

Representation of a user-managed GCP [Service Account Key](https://cloud.google.com/iam/docs/reference/rest/v1/projects.serviceAccounts.keys). System-managed keys (rotated automatically by Google) are not ingested.

> **Ontology Mapping**: This node uses the ontology label [`APIKey`](#ontology-apikey).

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The full resource name of the key, e.g. `projects/{p}/serviceAccounts/{email}/keys/{key_id}`. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| disabled |  | Whether the key is disabled. |
| key_algorithm |  | The cryptographic algorithm of the key (e.g. `KEY_ALG_RSA_2048`). |
| key_origin |  | Whether the key was generated by Google (`GOOGLE_PROVIDED`) or imported (`USER_PROVIDED`). |
| key_type |  | The provenance of the key. Always `USER_MANAGED` for ingested keys. |
| name |  | Same as id. |
| service_account_email |  | Email of the parent GCPServiceAccount. |
| valid_after_time |  | RFC 3339 timestamp from which the key is valid (effectively the key creation time). |
| valid_before_time |  | RFC 3339 timestamp until which the key is valid. |
| *_ont_created_at* | Yes | Normalized field sourced from `valid_after_time`. |
| *_ont_expires_at* | Yes | Normalized field sourced from `valid_before_time`. |
| *_ont_name* | Yes | Normalized field sourced from `name`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |

#### Relationships

- `(:GCPServiceAccount)-[:HAS_KEY]->(:GCPServiceAccountKey)`

- `(:GCPServiceAccountKey)-[:OWNED_BY]->(:GCPServiceAccount)`

- `(:User)-[:OWNS]->(:GCPServiceAccountKey)`: generated by analysis job `Ontology - User OWNS APIKey linking`.

- `(:GCPProject)-[:RESOURCE]->(:GCPServiceAccountKey)`

### GCPSslPolicy

Representation of a GCP [SSL Policy](https://cloud.google.com/compute/docs/reference/rest/v1/sslPolicies). SSL policies control the TLS versions and cipher suites that HTTPS/SSL proxy load balancers negotiate with clients.

> **Ontology Mapping**: This node uses the ontology label [`NetworkAccessControl`](#ontology-networkaccesscontrol).

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Stable identifier for this resource. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| creation_timestamp |  | Creation timestamp of the resource. |
| custom_features |  | The list of features explicitly enabled when `profile` is `CUSTOM`. |
| description |  | An optional description of this SSL policy. |
| enabled_features |  | The list of features enabled in this SSL policy, given its profile and custom features. |
| min_tls_version |  | The minimum TLS version this SSL policy accepts (e.g. `TLS_1_2`). |
| name | Yes | The name of the SSL policy. |
| partial_uri |  | Same as `id`. |
| profile |  | The compatibility profile (`COMPATIBLE`, `MODERN`, `RESTRICTED`, or `CUSTOM`). |
| project_id |  | The project ID that this SSL policy belongs to. |
| region |  | The region of this SSL policy, or `null` for global SSL policies. |
| self_link |  | Server-defined URL for the resource. |

#### Relationships

- `(:GCPProject)-[:RESOURCE]->(:GCPSslPolicy)`

- `(:GCPTargetHttpsProxy)-[:USES]->(:GCPSslPolicy)`

- `(:GCPTargetSslProxy)-[:USES]->(:GCPSslPolicy)`

### GCPSubnet

Representation of a GCP [Subnetwork](https://cloud.google.com/compute/docs/reference/rest/v1/subnetworks).

> **Ontology Mapping**: Some schema variants may also use the ontology label [`Subnet`](#ontology-subnet).

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | A partial resource URI representing this Subnet.  Has the form `projects/{project}/regions/{region}/subnetworks/{subnet name}`. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| flow_logs_aggregation_interval |  | Flow Logs aggregation interval, e.g. `INTERVAL_5_SEC`. |
| flow_logs_enabled |  | Whether VPC Flow Logs are enabled for the subnet. |
| flow_logs_filter_expr |  | Optional Flow Logs filter expression when subnet logging is filtered. |
| flow_logs_metadata |  | Flow Logs metadata mode, e.g. `INCLUDE_ALL_METADATA`. |
| flow_logs_sampling |  | Flow Logs sampling rate, e.g. `1.0` for 100%. |
| gateway_address |  | Gateway IP address of this Subnet. |
| ip_cidr_range |  | The CIDR range covered by this Subnet. |
| name | Yes | The name of this Subnet. |
| partial_uri | Yes | Same as `id`. |
| private_ip_google_access |  | Whether the VMs in this subnet can access Google services without assigned external IP addresses. This field can be both set at resource creation time and updated using setPrivateIpGoogleAccess. |
| project_id |  | The project ID that this Subnet belongs to. |
| purpose |  | Purpose of the subnet, e.g. `PRIVATE` or service-specific values such as internal load-balancer reservations. |
| region |  | The region of this Subnet. |
| self_link |  | The full resource URI representing this subnet. Has the form `https://www.googleapis.com/compute/v1/{partial_uri}`. |
| vpc_partial_uri |  | The partial URI of the VPC that this Subnet is a part of. |
| *_ont_cidr_block* | Yes | Normalized field sourced from `ip_cidr_range`. |
| *_ont_name* | Yes | Normalized field sourced from `name`. |
| *_ont_region* | Yes | Normalized field sourced from `region`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |

#### Relationships

- `(:GCPPolicyBinding)-[:APPLIES_TO]->(:GCPSubnet)`: Connects a GCP IAM policy binding to the concrete resource where the policy applies.

- `(:GCPVpc)-[:HAS]->(:GCPSubnet)`

- `(:GCPNetworkInterface)-[:PART_OF_SUBNET]->(:GCPSubnet)`

- `(:GCPSubnet)-[:RESOURCE]->(:GCPForwardingRule)`

- `(:GCPProject)-[:RESOURCE]->(:GCPSubnet)`

### GCPTargetHttpsProxy

Representation of a GCP [Target HTTPS Proxy](https://cloud.google.com/compute/docs/reference/rest/v1/targetHttpsProxies), used by external and internal HTTPS load balancers to terminate TLS.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Stable identifier for this resource. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| creation_timestamp |  | Creation timestamp of the resource. |
| description |  | An optional description of this target proxy. |
| name | Yes | The name of the target HTTPS proxy. |
| partial_uri |  | Same as `id`. |
| project_id |  | The project ID that this target HTTPS proxy belongs to. |
| region |  | The region of this proxy, or `null` for global target HTTPS proxies. |
| self_link |  | Server-defined URL for the resource. |
| ssl_policy |  | A partial resource URI of the SSL policy attached to this target proxy. Absent means no SSL policy is configured on the proxy. |
| url_map |  | A partial resource URI of the URL map this target proxy uses. |

#### Relationships

- `(:GCPProject)-[:RESOURCE]->(:GCPTargetHttpsProxy)`

- `(:GCPForwardingRule)-[:ROUTES_TO]->(:GCPTargetHttpsProxy)`: Matches on the existing `target` property, which transform_gcp_forwarding_rules()
already parses to a partial URI. A rule whose target isn't a targetHttpsProxies
resource simply won't match anything here.

- `(:GCPTargetHttpsProxy)-[:USES]->(:GCPSslPolicy)`

### GCPTargetSslProxy

Representation of a GCP [Target SSL Proxy](https://cloud.google.com/compute/docs/reference/rest/v1/targetSslProxies), used by SSL proxy load balancers to terminate TLS for non-HTTP TCP traffic.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Stable identifier for this resource. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| creation_timestamp |  | Creation timestamp of the resource. |
| description |  | An optional description of this target proxy. |
| name | Yes | The name of the target SSL proxy. |
| partial_uri |  | Same as `id`. |
| project_id |  | The project ID that this target SSL proxy belongs to. |
| self_link |  | Server-defined URL for the resource. |
| service |  | A partial resource URI of the backend service this target proxy forwards to. |
| ssl_policy |  | A partial resource URI of the SSL policy attached to this target proxy. Absent means no SSL policy is configured on the proxy. |

#### Relationships

- `(:GCPProject)-[:RESOURCE]->(:GCPTargetSslProxy)`

- `(:GCPTargetSslProxy)-[:ROUTES_TO]->(:GCPBackendService)`

- `(:GCPForwardingRule)-[:ROUTES_TO]->(:GCPTargetSslProxy)`: Same matching approach as GCPForwardingRuleToTargetHttpsProxyRel, for targetSslProxies.

- `(:GCPTargetSslProxy)-[:USES]->(:GCPSslPolicy)`

### GCPVertexAIDataset

Representation of a GCP [Vertex AI Dataset](https://cloud.google.com/vertex-ai/docs/reference/rest/v1/projects.locations.datasets).

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Stable identifier for this resource. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| create_time |  | Timestamp when the dataset was created. |
| data_item_count |  | The number of data items in the dataset. |
| description |  | Description configured for this resource. |
| display_name |  | User-provided display name of the dataset. |
| encryption_spec |  | JSON string with encryption configuration. |
| etag |  | Used to perform consistent read-modify-write updates. |
| labels |  | JSON string of key-value labels attached to this resource. |
| metadata |  | JSON string with dataset metadata. |
| metadata_schema_uri |  | The metadata schema URI for the dataset. |
| name |  | Same as `id`. |
| update_time |  | Timestamp when the dataset was last updated. |

#### Relationships

- `(:GCPVertexAITrainingPipeline)-[:READS_FROM]->(:GCPVertexAIDataset)`

- `(:GCPProject)-[:RESOURCE]->(:GCPVertexAIDataset)`

### GCPVertexAIDeployedModel

Representation of a deployed model on a Vertex AI Endpoint. This is derived from the [deployedModels field](https://cloud.google.com/vertex-ai/docs/reference/rest/v1/projects.locations.endpoints#DeployedModel) on an Endpoint.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Stable identifier for this resource. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| create_time |  | Timestamp when the deployed model was created. |
| deployed_model_id |  | The ID of the DeployedModel (unique within the endpoint). |
| display_name |  | User-provided display name of the deployed model. |
| enable_access_logging |  | Whether access logging is enabled for this deployed model. |
| endpoint_id |  | Identifier of the Vertex AI endpoint hosting this deployment. |
| model |  | Full resource name of the Model that this DeployedModel is serving. |
| service_account |  | Service account identity configured for this Vertex AI resource. |

#### Relationships

- `(:GCPVertexAIDeployedModel)-[:INSTANCE_OF]->(:GCPVertexAIModel)`

- `(:GCPProject)-[:RESOURCE]->(:GCPVertexAIDeployedModel)`

- `(:GCPVertexAIEndpoint)-[:SERVES]->(:GCPVertexAIDeployedModel)`

### GCPVertexAIEndpoint

Representation of a GCP [Vertex AI Endpoint](https://cloud.google.com/vertex-ai/docs/reference/rest/v1/projects.locations.endpoints).

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Stable identifier for this resource. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| create_time |  | Timestamp when the endpoint was created. |
| description |  | Description of the endpoint. |
| display_name |  | User-provided display name of the endpoint. |
| etag |  | Used to perform consistent read-modify-write updates. |
| labels |  | Key-value labels attached to this resource. |
| name |  | Same as `id`. |
| network |  | The full name of the Google Compute Engine network to which the endpoint should be peered. |
| update_time |  | Timestamp when the endpoint was last updated. |

#### Relationships

- `(:GCPProject)-[:RESOURCE]->(:GCPVertexAIEndpoint)`

- `(:GCPVertexAIEndpoint)-[:SERVES]->(:GCPVertexAIDeployedModel)`

### GCPVertexAIFeatureGroup

Representation of a GCP [Vertex AI Feature Group](https://cloud.google.com/vertex-ai/docs/reference/rest/v1/projects.locations.featureGroups). Feature Groups are the new architecture for Vertex AI Feature Store.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Stable identifier for this resource. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| bigquery_source_uri |  | The BigQuery source URI for the feature group. |
| create_time |  | Timestamp when the feature group was created. |
| description |  | Description configured for this resource. |
| entity_id_columns |  | JSON array of entity ID column names. |
| etag |  | Used to perform consistent read-modify-write updates. |
| labels |  | Key-value labels attached to this resource. |
| name |  | Same as `id`. |
| timestamp_column |  | The timestamp column name (for time series features). |
| update_time |  | Timestamp when the feature group was last updated. |

#### Relationships

- `(:GCPProject)-[:RESOURCE]->(:GCPVertexAIFeatureGroup)`

### GCPVertexAIModel

Representation of a GCP [Vertex AI Model](https://cloud.google.com/vertex-ai/docs/reference/rest/v1/projects.locations.models).

> **Ontology Mapping**: This node uses the ontology label [`AIModel`](#ontology-aimodel).

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Stable identifier for this resource. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| artifact_uri |  | The path to the directory containing the Model artifact and supporting files (GCS URI). |
| create_time |  | Timestamp when the model was originally created. |
| description |  | Description of the model. |
| display_name |  | User-provided display name of the model. |
| etag |  | Used to perform consistent read-modify-write updates. |
| labels |  | JSON string of user-defined labels. |
| name |  | Same as `id`. |
| training_pipeline |  | Resource name of the Training Pipeline that created this model. |
| update_time |  | Timestamp when the model was last updated. |
| version_create_time |  | Timestamp when this model version was created. |
| version_id |  | The version ID of the model. |
| version_update_time |  | Timestamp when this model version was last updated. |
| *_ont_name* | Yes | Normalized field sourced from `display_name`. |
| *_ont_provider* | Yes | Property generated by the ontology mapping. |
| *_ont_source* |  | Module that populated this node's ontology fields. |
| *_ont_type* | Yes | Property generated by the ontology mapping. |

#### Relationships

- `(:GCPVertexAIDeployedModel)-[:INSTANCE_OF]->(:GCPVertexAIModel)`

- `(:GCPVertexAITrainingPipeline)-[:PRODUCES]->(:GCPVertexAIModel)`

- `(:GCPProject)-[:RESOURCE]->(:GCPVertexAIModel)`

- `(:GCPVertexAIModel)-[:STORED_IN]->(:GCPBucket)`

### GCPVertexAITrainingPipeline

Representation of a GCP [Vertex AI Training Pipeline](https://cloud.google.com/vertex-ai/docs/reference/rest/v1/projects.locations.trainingPipelines).

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Stable identifier for this resource. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| create_time |  | Timestamp when the pipeline was created. |
| dataset_id |  | Full resource name of the Dataset used for training (used for relationships). |
| display_name |  | User-provided display name of the training pipeline. |
| end_time |  | Timestamp when the pipeline finished. |
| error |  | JSON string with error information if the pipeline failed. |
| model_id |  | Full resource name of the Model produced by training (used for relationships). |
| model_to_upload |  | JSON string describing the model that was uploaded. |
| name |  | Same as `id`. |
| start_time |  | Timestamp when the pipeline started running. |
| state |  | The state of the pipeline (e.g., `PIPELINE_STATE_SUCCEEDED`). |
| training_task_definition |  | The training task definition schema URI. |
| update_time |  | Timestamp when the pipeline was last updated. |

#### Relationships

- `(:GCPVertexAITrainingPipeline)-[:PRODUCES]->(:GCPVertexAIModel)`

- `(:GCPVertexAITrainingPipeline)-[:READS_FROM]->(:GCPVertexAIDataset)`

- `(:GCPProject)-[:RESOURCE]->(:GCPVertexAITrainingPipeline)`

### GCPVertexAIWorkbenchInstance

Representation of a GCP [Vertex AI Workbench Instance](https://cloud.google.com/vertex-ai/docs/workbench/reference/rest/v2/projects.locations.instances) (v2 API).

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Stable identifier for this resource. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| create_time |  | Timestamp when the instance was created. |
| description |  | Description configured for this resource. |
| display_name |  | Human-readable name shown for this resource. |
| health_state |  | The health state of the instance (e.g., `HEALTHY`). |
| name |  | Same as `id`. |
| notebook_runtime_type |  | Workbench runtime type reported by the Notebooks API. |
| runtime_user |  | User identity configured to run the Vertex AI Workbench instance. |
| service_account |  | Service account identity configured for this Vertex AI resource. |
| state |  | The state of the instance (e.g., `ACTIVE`, `STOPPED`). |
| update_time |  | Timestamp when the instance was last updated. |

#### Relationships

- `(:GCPProject)-[:RESOURCE]->(:GCPVertexAIWorkbenchInstance)`

- `(:GCPVertexAIWorkbenchInstance)-[:USES_SERVICE_ACCOUNT]->(:GCPServiceAccount)`

### GCPVpc

This node label is loaded by more than one sync path:

- Representation of a GCP [VPC](https://cloud.google.com/compute/docs/reference/rest/v1/networks/) placeholder.
- Representation of a GCP [VPC](https://cloud.google.com/compute/docs/reference/rest/v1/networks/).  In GCP documentation this is also known simply as a "Network" object.

> **Ontology Mapping**: Some schema variants may also use the ontology label [`VirtualNetwork`](#ontology-virtualnetwork).

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The partial resource URI representing this VPC.  Has the form `projects/{project_name}/global/networks/{vpc name}`. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| auto_create_subnetworks |  | When set to true, the VPC network is created in "auto" mode. When set to false, the VPC network is created in "custom" mode.  An auto mode VPC network starts with one subnet per region. Each subnet has a predetermined range as described in [Auto mode VPC network IP ranges](https://cloud.google.com/vpc/docs/vpc#ip-ranges). |
| description |  | A description for the VPC. |
| name | Yes | The name of the VPC. |
| partial_uri | Yes | Same as `id`. |
| project_id |  | The project ID that this VPC belongs to. |
| routing_config_routing_mode |  | VPC dynamic routing mode, either REGIONAL or GLOBAL. |
| self_link |  | The full resource URI representing this VPC. Has the form `https://www.googleapis.com/compute/v1/{partial_uri}`. |
| *_ont_name* | Yes | Normalized field sourced from `name`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |

#### Relationships

- `(:GCPPolicyBinding)-[:APPLIES_TO]->(:GCPVpc)`: Connects a GCP IAM policy binding to the concrete resource where the policy applies.

- `(:GCPCloudSQLInstance)-[:ASSOCIATED_WITH]->(:GCPVpc)`

- `(:GCPNetworkTag)-[:DEFINED_IN]->(:GCPVpc)`

- `(:GCPVpc)-[:HAS]->(:GCPSubnet)`

- `(:GCPVpcPeering)-[:LOCAL_NETWORK]->(:GCPVpc)`: Points from the peering to the local VPC network it is configured on.

- `(:GCPInstance)-[:MEMBER_OF_GCP_VPC]->(:GCPVpc)`: generated by analysis job `GCP Instance to VPC derived relationship analysis`.

- `(:GCPVpnGateway)-[:PART_OF_VPC]->(:GCPVpc)`: Points from the VPN gateway to the VPC network it is attached to.

- `(:GCPVpcPeering)-[:PEER_NETWORK]->(:GCPVpc)`: Points from the peering to the peer VPC network. The peer VPC may live in a
different project; if that project has not been synced, the target is a stub
GCPVpc node holding only its partial URI.

- `(:GCPVpc)-[:RESOURCE]->(:GCPFirewall)`

- `(:GCPVpc)-[:RESOURCE]->(:GCPForwardingRule)`

- `(:GCPProject)-[:RESOURCE]->(:GCPVpc)`

### GCPVpcPeering

Representation of one side of a GCP [VPC Network Peering](https://cloud.google.com/vpc/docs/vpc-peering)
connection. GCP reports each peering from each participating network's perspective, so Cartography
creates one GCPVpcPeering node per side; the two sides are joined through their shared
LOCAL_NETWORK / PEER_NETWORK edges to GCPVpc nodes, which may belong to different projects.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | A constructed unique ID for this VPC peering of the form `projects/{project}/global/networks/{network name}/networkPeerings/{peering name}`. The GCP API does not expose a resource URI for peerings, so Cartography derives one from the local network and peering name. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| auto_create_routes |  | Whether to automatically create routes for the peer network's subnets. |
| exchange_subnet_routes |  | Whether subnet routes are exchanged with the peer network. |
| export_custom_routes |  | Whether custom routes are exported to the peer network. |
| export_subnet_routes_with_public_ip |  | Whether subnet routes with public IP ranges are exported to the peer network. |
| import_custom_routes |  | Whether custom routes are imported from the peer network. |
| import_subnet_routes_with_public_ip |  | Whether subnet routes with public IP ranges are imported from the peer network. |
| name | Yes | The name of this VPC Network Peering connection. |
| network_partial_uri |  | The partial URI of the local VPC network this peering is configured on, e.g. `projects/{project}/global/networks/{network name}`. |
| peer_mtu |  | Maximum Transmission Unit in bytes of the peer network. |
| peer_network_partial_uri |  | The partial URI of the peer VPC network, e.g. `projects/{peer project}/global/networks/{peer network name}`. The peer network may belong to a different project. |
| peer_project_id |  | The project ID of the peer VPC network, parsed from the peer network URI. |
| project_id |  | The project ID of the local side of this peering (the project whose network the peering is configured on). |
| stack_type |  | Which IP stack(s) are allowed to be used by the peering, e.g. IPV4_ONLY or IPV4_IPV6. |
| state |  | The peering state, either ACTIVE or INACTIVE. A peering becomes ACTIVE only when both sides are connected. |
| state_details |  | Additional details about the current peering state. |
| update_strategy |  | The update strategy of the peering, e.g. INDEPENDENT or CONSERVATIVE. |

#### Relationships

- `(:GCPVpcPeering)-[:LOCAL_NETWORK]->(:GCPVpc)`: Points from the peering to the local VPC network it is configured on.

- `(:GCPVpcPeering)-[:PEER_NETWORK]->(:GCPVpc)`: Points from the peering to the peer VPC network. The peer VPC may live in a
different project; if that project has not been synced, the target is a stub
GCPVpc node holding only its partial URI.

- `(:GCPProject)-[:RESOURCE]->(:GCPVpcPeering)`

### GCPVpnGateway

This node label is loaded by more than one sync path:

- Representation of a GCP [HA VPN Gateway](https://cloud.google.com/compute/docs/reference/rest/v1/vpnGateways)
placeholder for gateways whose owning project has not been synced.
- Representation of a GCP [HA VPN Gateway](https://cloud.google.com/compute/docs/reference/rest/v1/vpnGateways).

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | A partial resource URI representing this HA VPN Gateway. Has the form `projects/{project}/regions/{region}/vpnGateways/{gateway name}`. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| creation_timestamp |  | The creation timestamp of this VPN Gateway. |
| description |  | A description for this VPN Gateway. |
| gateway_ip_version |  | The IP family of the gateway, e.g. IPV4 or IPV6. |
| name | Yes | The name of this VPN Gateway. |
| network_partial_uri |  | The partial URI of the VPC network this VPN Gateway is attached to, e.g. `projects/{project}/global/networks/{network name}`. |
| partial_uri | Yes | Same as `id`. |
| project_id |  | The project ID that this VPN Gateway belongs to. |
| region |  | The region of this VPN Gateway. |
| self_link |  | The full resource URI representing this VPN Gateway. Has the form `https://www.googleapis.com/compute/v1/{partial_uri}`. |
| stack_type |  | The stack type of the gateway, e.g. IPV4_ONLY or IPV4_IPV6. |

#### Relationships

- `(:GCPVpnTunnel)-[:CONNECTS_TO_GATEWAY]->(:GCPVpnGateway)`: Points from the VPN tunnel to the peer HA VPN gateway on the remote side.
The peer gateway may live in a different project; if that project has not been
synced, the target is a stub GCPVpnGateway node holding only its partial URI.

- `(:GCPVpnGateway)-[:PART_OF_VPC]->(:GCPVpc)`: Points from the VPN gateway to the VPC network it is attached to.

- `(:GCPProject)-[:RESOURCE]->(:GCPVpnGateway)`

- `(:GCPVpnTunnel)-[:USES_GATEWAY]->(:GCPVpnGateway)`: Points from the VPN tunnel to the local HA VPN gateway it runs on.

### GCPVpnTunnel

Representation of a GCP [Cloud VPN Tunnel](https://cloud.google.com/compute/docs/reference/rest/v1/vpnTunnels).
Cartography never ingests the tunnel's `sharedSecret`/`sharedSecretHash` fields.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | A partial resource URI representing this VPN Tunnel. Has the form `projects/{project}/regions/{region}/vpnTunnels/{tunnel name}`. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| creation_timestamp |  | The creation timestamp of this VPN Tunnel. |
| description |  | A description for this VPN Tunnel. |
| detailed_status |  | A detailed human-readable status message for the VPN tunnel. |
| ike_version |  | The IKE protocol version of the tunnel (1 or 2). |
| local_traffic_selector |  | Local traffic selector CIDR ranges to use when establishing the VPN tunnel. |
| name | Yes | The name of this VPN Tunnel. |
| partial_uri |  | Same as `id`. |
| peer_gcp_gateway_partial_uri |  | The partial URI of the peer HA VPN gateway, when the tunnel connects to another GCP VPN gateway. The peer gateway may belong to a different project. |
| peer_ip |  | The IP address of the peer VPN gateway. Set for tunnels to non-GCP peers. |
| project_id |  | The project ID that this VPN Tunnel belongs to. |
| region |  | The region of this VPN Tunnel. |
| remote_traffic_selector |  | Remote traffic selector CIDR ranges to use when establishing the VPN tunnel. |
| router_partial_uri |  | The partial URI of the Cloud Router associated with this tunnel, if any. |
| self_link |  | The full resource URI representing this VPN Tunnel. Has the form `https://www.googleapis.com/compute/v1/{partial_uri}`. |
| status |  | The status of the VPN tunnel, e.g. ESTABLISHED, WAITING_FOR_FULL_CONFIG, or FAILED. |
| target_vpn_gateway_partial_uri |  | The partial URI of the classic (legacy) target VPN gateway this tunnel is attached to, if any. |
| vpn_gateway_partial_uri |  | The partial URI of the HA VPN gateway on the local side of this tunnel. Unset for classic VPN tunnels. |

#### Relationships

- `(:GCPVpnTunnel)-[:CONNECTS_TO_GATEWAY]->(:GCPVpnGateway)`: Points from the VPN tunnel to the peer HA VPN gateway on the remote side.
The peer gateway may live in a different project; if that project has not been
synced, the target is a stub GCPVpnGateway node holding only its partial URI.

- `(:GCPProject)-[:RESOURCE]->(:GCPVpnTunnel)`

- `(:GCPVpnTunnel)-[:USES_GATEWAY]->(:GCPVpnGateway)`: Points from the VPN tunnel to the local HA VPN gateway it runs on.

### GCPWorkloadIdentityPool

Representation of a GCP [Workload Identity Pool](https://cloud.google.com/iam/docs/reference/rest/v1/projects.locations.workloadIdentityPools). A pool groups external identities that can impersonate GCP service accounts via federation.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The full resource name, e.g. `projects/{number}/locations/global/workloadIdentityPools/{pool_id}`. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| description |  | A description of the pool. |
| disabled |  | Whether the pool is disabled. |
| display_name |  | The friendly name of the pool. |
| mode |  | Pool mode. `SYSTEM_TRUST_DOMAIN` indicates a GKE-managed pool (`*.svc.id.goog`) whose providers are managed by Google and not enumerated by Cartography. Otherwise the field is unset or carries a user-managed mode. |
| name | Yes | Same as `id`. |
| project_id |  | Google Cloud project that owns this resource. |
| session_duration |  | Default session duration for federated tokens issued via this pool. |
| state |  | Pool state (`ACTIVE`, `DELETED`). |

#### Relationships

- `(:GCPWorkloadIdentityPool)-[:HAS_ALLOW_POLICY]->(:GCPPolicyBinding)`

- `(:GCPWorkloadIdentityProvider)-[:MEMBER_OF]->(:GCPWorkloadIdentityPool)`

- `(:GCPProject)-[:RESOURCE]->(:GCPWorkloadIdentityPool)`

### GCPWorkloadIdentityProvider

A Google Cloud Workload Identity Provider resource.

> **Ontology Mapping**: This node uses the ontology label [`IdentityProvider`](#ontology-identityprovider).

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The full provider resource name. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| attribute_condition |  | CEL expression that gates token claims before federation. |
| aws_account_id |  | AWS account ID this provider trusts (only set when `protocol = AWS`). |
| description |  | A description of the provider. |
| disabled |  | Whether the provider is explicitly disabled. |
| display_name |  | The friendly name of the provider. |
| enabled |  | Effective enabled flag: true only when both the provider and its parent pool are `state == ACTIVE` and not disabled. Used for the `IdentityProvider` ontology mapping. |
| name | Yes | Same as `id`. |
| oidc_allowed_audiences |  | OIDC allowed audiences (only set when `protocol = OIDC`). |
| oidc_issuer_uri |  | OIDC issuer URI (only set when `protocol = OIDC`). |
| pool_name |  | The resource name of the parent GCPWorkloadIdentityPool. |
| project_id |  | Google Cloud project that owns this resource. |
| protocol |  | One of `OIDC`, `AWS`, `SAML`, `X509`, depending on which sub-object is populated. |
| saml_idp_metadata_xml |  | SAML IdP metadata XML (only set when `protocol = SAML`). |
| state |  | Provider state (`ACTIVE`, `DELETED`). |
| *_ont_enabled* | Yes | Normalized field sourced from `enabled`. |
| *_ont_issuer* | Yes | Normalized field sourced from `oidc_issuer_uri`. |
| *_ont_name* | Yes | Normalized field sourced from `name`. |
| *_ont_protocol* | Yes | Normalized field sourced from `protocol`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |

#### Relationships

- `(:GCPWorkloadIdentityProvider)-[:MEMBER_OF]->(:GCPWorkloadIdentityPool)`

- `(:GCPProject)-[:RESOURCE]->(:GCPWorkloadIdentityProvider)`

### GKECluster

Representation of a GCP [GKE Cluster](https://cloud.google.com/kubernetes-engine/docs/reference/rest/v1/).

> **Ontology Mapping**: This node uses the ontology label [`ComputeCluster`](#ontology-computecluster).

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Stable identifier for this resource. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| basic_auth |  | Property generated by analysis job: `GCP GKE basic authentication exposure`. |
| cluster_ipv4cidr |  | The IP address range of the container pods in the cluster. |
| created_at |  | The date and time the cluster was created. |
| current_master_version |  | The current software version of the master endpoint. |
| database_encryption |  | Configuration of etcd encryption. |
| description |  | An optional description of the cluster. |
| endpoint |  | The IP address of the cluster's master endpoint. The endpoint can be accessed from the internet at https://username:password@endpoint/. |
| exposed_internet | Yes | Set to `True` if at least among `private_nodes`, `private_endpoint_enabled`, or `master_authorized_networks` are disabled. |
| initial_version |  | The initial Kubernetes version for the cluster. |
| legacy_abac |  | Whether legacy ABAC authorization is enabled on the GKE cluster. |
| location |  | The name of the Google Compute Engine zone or region in which the cluster resides. |
| logging_service |  | The logging service used to write logs. Available options: `logging.googleapis.com/kubernetes`, `logging.googleapis.com`, `none`. |
| master_authorized_networks |  | If enabled, it disallows all external traffic to access Kubernetes master through HTTPS except traffic from the given CIDR blocks, Google Compute Engine Public IPs and Google Prod IPs. |
| masterauth_password |  | The password to use for HTTP basic authentication to the master endpoint. If a password is provided for cluster creation, username must be non-empty. |
| masterauth_username |  | The username to use for HTTP basic authentication to the master endpoint. For clusters v1.6.0 and later, basic authentication can be disabled by leaving username unspecified (or setting it to the empty string). |
| monitoring_service |  | The monitoring service used to write metrics. Available options: `monitoring.googleapis.com/kubernetes`, `monitoring.googleapis.com`, `none`. |
| name |  | The name of the cluster. |
| network |  | The name of the Google Compute Engine network to which the cluster is connected. |
| network_policy |  | Set to `True` if a network policy provider has been enabled. |
| private_endpoint |  | The internal IP address of the cluster's master endpoint. |
| private_endpoint_enabled |  | Whether the master's internal IP address is used as the cluster endpoint. |
| private_nodes |  | If enabled, all nodes are given only private addresses and communicate with the master via private networking. |
| public_endpoint |  | The external IP address of the cluster's master endpoint. |
| self_link |  | Canonical Google Cloud API URL for this resource. |
| services_ipv4cidr |  | The IP address range of the Kubernetes services in the cluster. |
| shielded_nodes |  | Whether Shielded Nodes are enabled. |
| status |  | The current status of the cluster. |
| subnetwork |  | The name of the Google Compute Engine subnetwork to which the cluster is connected. |
| workload_identity_enabled | Yes | Whether the GKE cluster has a Workload Identity pool configured. |
| zone |  | The name of the Google Compute Engine zone in which the cluster resides. |
| *_ont_control_plane_public_access* | Yes | Normalized field sourced from `private_endpoint_enabled`. |
| *_ont_endpoint* | Yes | Normalized field sourced from `endpoint`. |
| *_ont_name* | Yes | Normalized field sourced from `name`. |
| *_ont_region* | Yes | Normalized field sourced from `location`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |
| *_ont_status* | Yes | Normalized field sourced from `status`. |
| *_ont_version* | Yes | Normalized field sourced from `current_master_version`. |

#### Relationships

- `(:GKECluster)-[:LABELED]->(:GCPLabel)`: Indicates that a GKE cluster has this legacy label.

- `(:GCPProject)-[:RESOURCE]->(:GKECluster)`

- `(:GKECluster)-[:TAGGED]->(:GCPLabel)`: Indicates that a GKE cluster is tagged with this label.
