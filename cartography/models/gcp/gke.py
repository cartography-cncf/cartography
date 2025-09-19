from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class GCPGKEClusterNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", extra_index=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    self_link: PropertyRef = PropertyRef("self_link")
    description: PropertyRef = PropertyRef("description")
    logging_service: PropertyRef = PropertyRef("logging_service")
    monitoring_service: PropertyRef = PropertyRef("monitoring_service")
    network: PropertyRef = PropertyRef("network")
    subnetwork: PropertyRef = PropertyRef("subnetwork")
    cluster_ipv4cidr: PropertyRef = PropertyRef("cluster_ipv4cidr")
    zone: PropertyRef = PropertyRef("zone")
    location: PropertyRef = PropertyRef("location")
    endpoint: PropertyRef = PropertyRef("endpoint")
    initial_version: PropertyRef = PropertyRef("initial_version")
    current_master_version: PropertyRef = PropertyRef("current_master_version")
    status: PropertyRef = PropertyRef("status")
    services_ipv4cidr: PropertyRef = PropertyRef("services_ipv4cidr")
    database_encryption: PropertyRef = PropertyRef("database_encryption")
    network_policy: PropertyRef = PropertyRef("network_policy")
    master_authorized_networks: PropertyRef = PropertyRef("master_authorized_networks")
    legacy_abac: PropertyRef = PropertyRef("legacy_abac")
    shielded_nodes: PropertyRef = PropertyRef("shielded_nodes")
    private_nodes: PropertyRef = PropertyRef("private_nodes")
    private_endpoint_enabled: PropertyRef = PropertyRef("private_endpoint_enabled")
    private_endpoint: PropertyRef = PropertyRef("private_endpoint")
    public_endpoint: PropertyRef = PropertyRef("public_endpoint")
    masterauth_username: PropertyRef = PropertyRef("masterauth_username")
    masterauth_password: PropertyRef = PropertyRef("masterauth_password")
    created_at: PropertyRef = PropertyRef("created_at")


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
class GCPGKEClusterSchema(CartographyNodeSchema):
    label: str = "GKECluster"
    properties: GCPGKEClusterNodeProperties = GCPGKEClusterNodeProperties()
    sub_resource_relationship: GCPGKEClusterToProjectRel = GCPGKEClusterToProjectRel()
