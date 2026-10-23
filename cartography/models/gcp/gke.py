from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.ontology.labels import COMPUTE_CLUSTER


@dataclass(frozen=True)
class GCPGKEClusterNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", extra_index=True, description="Stable identifier for this resource."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    resource_name: PropertyRef = PropertyRef(
        "resource_name",
        extra_index=True,
        description="`projects/{project_id}/locations/{location}/clusters/{name}`, derived from `Cluster.selfLink` using the project ID (selfLink may carry the project number). Matched by `KubernetesCluster.gke_resource_name`.",
    )
    project_id: PropertyRef = PropertyRef(
        "project_id", description="ID of the project that owns the cluster."
    )
    gke_uid: PropertyRef = PropertyRef(
        "gke_uid",
        description="GKE API `Cluster.id`: the immutable Google-generated cluster identifier.",
    )
    autopilot_enabled: PropertyRef = PropertyRef(
        "autopilot_enabled",
        description="GKE API `Cluster.autopilot.enabled`: whether this is an Autopilot cluster.",
    )
    workload_pool: PropertyRef = PropertyRef(
        "workload_pool",
        description="GKE API `Cluster.workloadIdentityConfig.workloadPool` (e.g. `PROJECT_ID.svc.id.goog`).",
    )
    datapath_provider: PropertyRef = PropertyRef(
        "datapath_provider",
        description="GKE API `Cluster.networkConfig.datapathProvider` (`ADVANCED_DATAPATH` is Dataplane V2).",
    )
    dns_endpoint: PropertyRef = PropertyRef(
        "dns_endpoint",
        description="GKE API `Cluster.controlPlaneEndpointsConfig.dnsEndpointConfig.endpoint`: the DNS-based control plane hostname.",
    )
    dns_endpoint_enabled: PropertyRef = PropertyRef(
        "dns_endpoint_enabled",
        description="GKE API `dnsEndpointConfig.allowExternalTraffic`: whether clients outside Google can reach the DNS-based control plane endpoint (still authorized by IAM `container.clusters.connect`). Null when the API does not return `controlPlaneEndpointsConfig`.",
    )
    dns_allow_kubernetes_tokens: PropertyRef = PropertyRef(
        "dns_allow_kubernetes_tokens",
        description="GKE API `dnsEndpointConfig.enableK8sTokensViaDns`: whether Kubernetes ServiceAccount tokens are accepted on the DNS endpoint.",
    )
    dns_allow_kubernetes_certs: PropertyRef = PropertyRef(
        "dns_allow_kubernetes_certs",
        description="GKE API `dnsEndpointConfig.enableK8sCertsViaDns`: whether Kubernetes client certificates are accepted on the DNS endpoint.",
    )
    ip_endpoints_enabled: PropertyRef = PropertyRef(
        "ip_endpoints_enabled",
        description="GKE API `controlPlaneEndpointsConfig.ipEndpointsConfig.enabled`: whether the control plane is reachable by IP address at all.",
    )
    control_plane_public_access: PropertyRef = PropertyRef(
        "control_plane_public_access",
        description="True when the control plane is reachable from the internet through the DNS endpoint or a public IP endpoint. Falls back to `not privateClusterConfig.enablePrivateEndpoint` when `controlPlaneEndpointsConfig` is absent. IAM, authorized networks, and RBAC still apply.",
    )
    public_ip_endpoint_enabled: PropertyRef = PropertyRef(
        "public_ip_endpoint_enabled",
        description="GKE API `ipEndpointsConfig.enabled` and `ipEndpointsConfig.enablePublicEndpoint` are both true. An allocated public IP alone does not imply access.",
    )
    name: PropertyRef = PropertyRef("name", description="The name of the cluster.")
    self_link: PropertyRef = PropertyRef(
        "self_link", description="Canonical Google Cloud API URL for this resource."
    )
    description: PropertyRef = PropertyRef(
        "description", description="An optional description of the cluster."
    )
    logging_service: PropertyRef = PropertyRef(
        "logging_service",
        description="The logging service used to write logs. Available options: `logging.googleapis.com/kubernetes`, `logging.googleapis.com`, `none`.",
    )
    monitoring_service: PropertyRef = PropertyRef(
        "monitoring_service",
        description="The monitoring service used to write metrics. Available options: `monitoring.googleapis.com/kubernetes`, `monitoring.googleapis.com`, `none`.",
    )
    network: PropertyRef = PropertyRef(
        "network",
        description="The name of the Google Compute Engine network to which the cluster is connected.",
    )
    subnetwork: PropertyRef = PropertyRef(
        "subnetwork",
        description="The name of the Google Compute Engine subnetwork to which the cluster is connected.",
    )
    cluster_ipv4cidr: PropertyRef = PropertyRef(
        "cluster_ipv4cidr",
        description="The IP address range of the container pods in the cluster.",
    )
    zone: PropertyRef = PropertyRef(
        "zone",
        description="The name of the Google Compute Engine zone in which the cluster resides.",
    )
    location: PropertyRef = PropertyRef(
        "location",
        description="The name of the Google Compute Engine zone or region in which the cluster resides.",
    )
    endpoint: PropertyRef = PropertyRef(
        "endpoint",
        description="Legacy master endpoint IP address. Address presence alone does not imply that IP access is enabled.",
    )
    initial_version: PropertyRef = PropertyRef(
        "initial_version", description="The initial Kubernetes version for the cluster."
    )
    current_master_version: PropertyRef = PropertyRef(
        "current_master_version",
        description="The current software version of the master endpoint.",
    )
    status: PropertyRef = PropertyRef(
        "status", description="The current status of the cluster."
    )
    services_ipv4cidr: PropertyRef = PropertyRef(
        "services_ipv4cidr",
        description="The IP address range of the Kubernetes services in the cluster.",
    )
    database_encryption: PropertyRef = PropertyRef(
        "database_encryption", description="Configuration of etcd encryption."
    )
    network_policy: PropertyRef = PropertyRef(
        "network_policy",
        description="Network policy provider when enabled, including DATAPLANE_V2; otherwise false. This records the engine, not policy coverage.",
    )
    master_authorized_networks: PropertyRef = PropertyRef(
        "master_authorized_networks",
        description="If enabled, it disallows all external traffic to access Kubernetes master through HTTPS except traffic from the given CIDR blocks, Google Compute Engine Public IPs and Google Prod IPs.",
    )
    legacy_abac: PropertyRef = PropertyRef(
        "legacy_abac",
        description="Whether legacy ABAC authorization is enabled on the GKE cluster.",
    )
    shielded_nodes: PropertyRef = PropertyRef(
        "shielded_nodes", description="Whether Shielded Nodes are enabled."
    )
    workload_identity_enabled: PropertyRef = PropertyRef(
        "workload_identity_enabled",
        extra_index=True,
        description="Whether the GKE cluster has a Workload Identity pool configured.",
    )
    exposed_internet: PropertyRef = PropertyRef(
        "exposed_internet",
        extra_index=True,
        description="Set to `True` if `private_nodes` is disabled or `control_plane_public_access` is true. Authorized networks and IAM are not considered.",
    )  # Populated by the GCP_GKE_ASSET_EXPOSURE analysis job.
    private_nodes: PropertyRef = PropertyRef(
        "private_nodes",
        description="If enabled, all nodes are given only private addresses and communicate with the master via private networking.",
    )
    private_endpoint_enabled: PropertyRef = PropertyRef(
        "private_endpoint_enabled",
        description="Whether the master's internal IP address is used as the cluster endpoint.",
    )
    private_endpoint: PropertyRef = PropertyRef(
        "private_endpoint",
        description="The internal IP address of the cluster's master endpoint.",
    )
    public_endpoint: PropertyRef = PropertyRef(
        "public_endpoint",
        description="The external IP address of the cluster's master endpoint.",
    )
    masterauth_username: PropertyRef = PropertyRef(
        "masterauth_username",
        description="The username to use for HTTP basic authentication to the master endpoint. For clusters v1.6.0 and later, basic authentication can be disabled by leaving username unspecified (or setting it to the empty string).",
    )
    masterauth_password: PropertyRef = PropertyRef(
        "masterauth_password",
        description="The password to use for HTTP basic authentication to the master endpoint. If a password is provided for cluster creation, username must be non-empty.",
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="The date and time the cluster was created."
    )


@dataclass(frozen=True)
class GCPGKEClusterToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:GCPProject)-[:RESOURCE]->(:GKECluster)
class GCPGKEClusterToProjectRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPGKEClusterToProjectRelProperties = (
        GCPGKEClusterToProjectRelProperties()
    )


@dataclass(frozen=True)
class GKEClusterToWorkloadIdentityPoolRel(CartographyRelSchema):
    """Links a cluster to its Google-managed workload identity pool."""

    target_node_label: str = "GCPWorkloadIdentityPool"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "pool_id": PropertyRef("workload_pool"),
            "project_id": PropertyRef("project_id"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_WORKLOAD_IDENTITY_POOL"
    properties: GCPGKEClusterToProjectRelProperties = (
        GCPGKEClusterToProjectRelProperties()
    )


@dataclass(frozen=True)
class GCPGKEClusterSchema(CartographyNodeSchema):
    """Representation of a GCP [GKE Cluster](https://cloud.google.com/kubernetes-engine/docs/reference/rest/v1/)."""

    label: str = "GKECluster"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([COMPUTE_CLUSTER])
    properties: GCPGKEClusterNodeProperties = GCPGKEClusterNodeProperties()
    sub_resource_relationship: GCPGKEClusterToProjectRel = GCPGKEClusterToProjectRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [GKEClusterToWorkloadIdentityPoolRel()]
    )


@dataclass(frozen=True)
class GKENodePoolNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="`{GKECluster.resource_name}/nodePools/{name}`. Matched by Kubernetes nodes through their `cloud.google.com/gke-nodepool` label.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", description="GKE API `NodePool.name`.")
    cluster_resource_name: PropertyRef = PropertyRef(
        "cluster_resource_name",
        description="`resource_name` of the owning GKECluster.",
    )
    service_account: PropertyRef = PropertyRef(
        "service_account",
        description="GKE API `NodePool.config.serviceAccount`: the Google service account the nodes run as. `default` is resolved to the project's Compute Engine default service account email.",
    )
    oauth_scopes: PropertyRef = PropertyRef(
        "oauth_scopes",
        description="GKE API `NodePool.config.oauthScopes` available to the node service account.",
    )
    workload_metadata_mode: PropertyRef = PropertyRef(
        "workload_metadata_mode",
        description="GKE API `NodePool.config.workloadMetadataConfig.mode`. `GKE_METADATA` serves Workload Identity credentials to pods; `GCE_METADATA` exposes the node service account to pods.",
    )
    instance_group_urls: PropertyRef = PropertyRef(
        "instance_group_urls",
        description="GKE API `NodePool.instanceGroupUrls`. Autopilot instance groups are not visible to the Compute API.",
    )
    status: PropertyRef = PropertyRef(
        "status", description="GKE API `NodePool.status`."
    )
    version: PropertyRef = PropertyRef(
        "version",
        description="GKE API `NodePool.version`: the nodes' Kubernetes version.",
    )


@dataclass(frozen=True)
class GKENodePoolToClusterRel(CartographyRelSchema):
    """Links a GKE cluster to its node pools."""

    target_node_label: str = "GKECluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("cluster_id")}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_NODE_POOL"
    properties: GCPGKEClusterToProjectRelProperties = (
        GCPGKEClusterToProjectRelProperties()
    )


@dataclass(frozen=True)
class GKENodePoolToServiceAccountRel(CartographyRelSchema):
    """Links a node pool to the Google service account its nodes run as."""

    target_node_label: str = "GCPServiceAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"email": PropertyRef("service_account")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RUNS_AS"
    properties: GCPGKEClusterToProjectRelProperties = (
        GCPGKEClusterToProjectRelProperties()
    )


@dataclass(frozen=True)
class GKENodePoolSchema(CartographyNodeSchema):
    """A GKE node pool, including the node credential and metadata configuration."""

    label: str = "GKENodePool"
    properties: GKENodePoolNodeProperties = GKENodePoolNodeProperties()
    sub_resource_relationship: GCPGKEClusterToProjectRel = GCPGKEClusterToProjectRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GKENodePoolToClusterRel(),
            GKENodePoolToServiceAccountRel(),
        ]
    )
