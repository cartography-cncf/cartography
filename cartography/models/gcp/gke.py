from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class GCPGKEClusterNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", extra_index=True, description="Stable identifier for this resource."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
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
        description="The IP address of the cluster's master endpoint. The endpoint can be accessed from the internet at https://username:password@endpoint/.",
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
        description="Set to `True` if a network policy provider has been enabled.",
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
        description="Set to `True` if at least among `private_nodes`, `private_endpoint_enabled`, or `master_authorized_networks` are disabled.",
    )  # Populated by gcp_gke_asset_exposure.json.
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
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


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
class GCPGKEClusterSchema(CartographyNodeSchema):
    """Representation of a GCP [GKE Cluster](https://cloud.google.com/kubernetes-engine/docs/reference/rest/v1/)."""

    label: str = "GKECluster"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["ComputeCluster"])
    properties: GCPGKEClusterNodeProperties = GCPGKEClusterNodeProperties()
    sub_resource_relationship: GCPGKEClusterToProjectRel = GCPGKEClusterToProjectRel()
