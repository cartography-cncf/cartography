from cartography.models.ontology.mapping.specs import OntologyFieldMapping
from cartography.models.ontology.mapping.specs import OntologyMapping
from cartography.models.ontology.mapping.specs import OntologyNodeMapping

# Cluster _ont_status is normalized per provider to the shared canonical set for the
# Cluster family: active, creating, updating, deleting, failed, unknown.
# The raw provider value stays on each source node's own status property.

# AWS EKS cluster status
_AWS_EKS_STATUS = {
    "CREATING": "creating",
    "PENDING": "creating",
    "ACTIVE": "active",
    "UPDATING": "updating",
    "DELETING": "deleting",
    "FAILED": "failed",
}

# AWS ECS cluster status
_AWS_ECS_STATUS = {
    "ACTIVE": "active",
    "PROVISIONING": "creating",
    "DEPROVISIONING": "deleting",
    "INACTIVE": "deleting",
    "FAILED": "failed",
}

# Azure AKS provisioning state (ARM)
_AZURE_AKS_STATUS = {
    "Succeeded": "active",
    "Creating": "creating",
    "Updating": "updating",
    "Deleting": "deleting",
    "Failed": "failed",
    "Canceled": "failed",
}

# GCP GKE cluster status
_GCP_GKE_STATUS = {
    "STATUS_UNSPECIFIED": "unknown",
    "PROVISIONING": "creating",
    "RUNNING": "active",
    "RECONCILING": "updating",
    "STOPPING": "deleting",
    "ERROR": "failed",
    "DEGRADED": "failed",
}

# Scaleway Kapsule cluster status
_SCALEWAY_KAPSULE_STATUS = {
    "unknown": "unknown",
    "creating": "creating",
    "ready": "active",
    "updating": "updating",
    "deleting": "deleting",
    "deleted": "deleting",
    "locked": "failed",
    "pool_required": "failed",
}

aws_eks_mapping = OntologyMapping(
    module_name="aws",
    nodes=[
        OntologyNodeMapping(
            node_label="AWSEKSCluster",
            fields=[
                OntologyFieldMapping(ontology_field="name", node_field="name"),
                OntologyFieldMapping(ontology_field="region", node_field="region"),
                OntologyFieldMapping(ontology_field="version", node_field="version"),
                OntologyFieldMapping(ontology_field="endpoint", node_field="endpoint"),
                OntologyFieldMapping(
                    ontology_field="status",
                    node_field="status",
                    special_handling="mapping",
                    extra={"map": _AWS_EKS_STATUS},
                ),
                OntologyFieldMapping(
                    ontology_field="control_plane_public_access",
                    node_field="endpoint_public_access",
                ),
            ],
        ),
    ],
)

aws_ecs_mapping = OntologyMapping(
    module_name="aws",
    nodes=[
        OntologyNodeMapping(
            node_label="AWSECSCluster",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name",
                    node_field="name",
                ),
                OntologyFieldMapping(ontology_field="region", node_field="region"),
                # version: Not applicable for ECS clusters
                # endpoint: Not applicable for ECS clusters
                OntologyFieldMapping(
                    ontology_field="status",
                    node_field="status",
                    special_handling="mapping",
                    extra={"map": _AWS_ECS_STATUS},
                ),
            ],
        ),
    ],
)

aws_emr_mapping = OntologyMapping(
    module_name="aws",
    nodes=[
        OntologyNodeMapping(
            node_label="AWSEMRCluster",
            fields=[
                OntologyFieldMapping(ontology_field="name", node_field="name"),
                OntologyFieldMapping(ontology_field="region", node_field="region"),
                OntologyFieldMapping(
                    ontology_field="version",
                    node_field="release_label",
                ),
                # endpoint: Not applicable for EMR clusters
                # status: Not exposed as a direct field in AWSEMRCluster node
            ],
        ),
    ],
)

azure_aks_mapping = OntologyMapping(
    module_name="azure",
    nodes=[
        OntologyNodeMapping(
            node_label="AzureKubernetesCluster",
            fields=[
                OntologyFieldMapping(ontology_field="name", node_field="name"),
                OntologyFieldMapping(
                    ontology_field="region",
                    node_field="location",
                ),
                OntologyFieldMapping(
                    ontology_field="version",
                    node_field="kubernetes_version",
                ),
                OntologyFieldMapping(ontology_field="endpoint", node_field="fqdn"),
                OntologyFieldMapping(
                    ontology_field="status",
                    node_field="provisioning_state",
                    special_handling="mapping",
                    extra={"map": _AZURE_AKS_STATUS},
                ),
                OntologyFieldMapping(
                    ontology_field="control_plane_public_access",
                    node_field="api_server_public_access",
                ),
            ],
        ),
    ],
)

gcp_gke_mapping = OntologyMapping(
    module_name="gcp",
    nodes=[
        OntologyNodeMapping(
            node_label="GKECluster",
            fields=[
                OntologyFieldMapping(ontology_field="name", node_field="name"),
                OntologyFieldMapping(
                    ontology_field="region",
                    node_field="location",
                ),
                OntologyFieldMapping(
                    ontology_field="version",
                    node_field="current_master_version",
                ),
                OntologyFieldMapping(
                    ontology_field="endpoint",
                    node_field="endpoint",
                ),
                OntologyFieldMapping(
                    ontology_field="status",
                    node_field="status",
                    special_handling="mapping",
                    extra={"map": _GCP_GKE_STATUS},
                ),
                # privateClusterConfig.enablePrivateEndpoint=true means the master is only
                # reachable from its internal IP, so its inverse encodes "public endpoint reachable".
                OntologyFieldMapping(
                    ontology_field="control_plane_public_access",
                    node_field="private_endpoint_enabled",
                    special_handling="invert_boolean",
                ),
            ],
        ),
    ],
)

kubernetes_mapping = OntologyMapping(
    module_name="kubernetes",
    nodes=[
        OntologyNodeMapping(
            node_label="KubernetesCluster",
            fields=[
                OntologyFieldMapping(ontology_field="name", node_field="name"),
                # region: Not available in KubernetesCluster node
                OntologyFieldMapping(
                    ontology_field="version",
                    node_field="version",
                ),
                # endpoint: Not available in KubernetesCluster node
                # status: Not available in KubernetesCluster node
                # control_plane_public_access: Not available for self-managed clusters
            ],
        ),
    ],
)

scaleway_kapsule_mapping = OntologyMapping(
    module_name="scaleway",
    nodes=[
        OntologyNodeMapping(
            node_label="ScalewayKapsuleCluster",
            fields=[
                OntologyFieldMapping(ontology_field="name", node_field="name"),
                OntologyFieldMapping(ontology_field="region", node_field="region"),
                OntologyFieldMapping(ontology_field="version", node_field="version"),
                OntologyFieldMapping(
                    ontology_field="endpoint",
                    node_field="cluster_url",
                ),
                OntologyFieldMapping(
                    ontology_field="status",
                    node_field="status",
                    special_handling="mapping",
                    extra={"map": _SCALEWAY_KAPSULE_STATUS},
                ),
                # control_plane_public_access: Kapsule's apiserver is always
                # internet-reachable; access can be restricted by IP allowlists
                # (ACLs) but the endpoint itself is public. The ACL config isn't
                # exposed on the cluster node, so leave this unmapped.
            ],
        ),
    ],
)

CLUSTERS_ONTOLOGY_MAPPING: dict[str, OntologyMapping] = {
    "aws_eks": aws_eks_mapping,
    "aws_ecs": aws_ecs_mapping,
    "aws_emr": aws_emr_mapping,
    "azure_aks": azure_aks_mapping,
    "gcp_gke": gcp_gke_mapping,
    "kubernetes": kubernetes_mapping,
    "scaleway_kapsule": scaleway_kapsule_mapping,
}
