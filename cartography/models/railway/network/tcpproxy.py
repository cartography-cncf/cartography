from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class RailwayTCPProxyNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="ID of the Railway TCP proxy.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    # Exposure signal: a TCP proxy publishes a raw port on the public internet, with no TLS
    # termination or auth in front of it. This is the highest-signal Railway exposure.
    domain: PropertyRef = PropertyRef(
        "domain", extra_index=True, description="Public hostname of the proxy."
    )
    proxy_port: PropertyRef = PropertyRef(
        "proxyPort", description="Public port to which clients connect."
    )
    application_port: PropertyRef = PropertyRef(
        "applicationPort",
        description="Service port to which the proxy forwards traffic.",
    )
    sync_status: PropertyRef = PropertyRef(
        "syncStatus", description="Provisioning status of the proxy."
    )
    service_id: PropertyRef = PropertyRef(
        "service_id", description="ID of the service behind the proxy."
    )
    environment_id: PropertyRef = PropertyRef(
        "environment_id", description="ID of the environment served by the proxy."
    )
    created_at: PropertyRef = PropertyRef(
        "createdAt", description="Time when the proxy was created."
    )


@dataclass(frozen=True)
class RailwayTCPProxyToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:RailwayProject)-[:RESOURCE]->(:RailwayTCPProxy)
class RailwayTCPProxyToProjectRel(CartographyRelSchema):
    """Connects a Railway project to a TCP proxy that it contains."""

    target_node_label: str = "RailwayProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: RailwayTCPProxyToProjectRelProperties = (
        RailwayTCPProxyToProjectRelProperties()
    )


@dataclass(frozen=True)
class RailwayTCPProxyToServiceInstanceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:RailwayTCPProxy)-[:EXPOSE]->(:RailwayServiceInstance)
#
# EXPOSE always points from the internet-facing entrypoint to the asset it puts at risk, matching
# the LoadBalancer-[:EXPOSE]->workload convention used by AWS, GCP, Azure and Kubernetes.
#
# Gated on the proxy's syncStatus through exposed_*, exactly like the two domain types: a
# proxy that is not serving yet, or is being torn down, is not a public entry point.
class RailwayTCPProxyToServiceInstanceRel(CartographyRelSchema):
    """Identifies the Railway service instance exposed by a serving TCP proxy."""

    target_node_label: str = "RailwayServiceInstance"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "service_id": PropertyRef("exposed_service_id"),
            "environment_id": PropertyRef("exposed_environment_id"),
        },
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "EXPOSE"
    properties: RailwayTCPProxyToServiceInstanceRelProperties = (
        RailwayTCPProxyToServiceInstanceRelProperties()
    )


@dataclass(frozen=True)
class RailwayTCPProxySchema(CartographyNodeSchema):
    """A public Railway TCP proxy forwarding traffic to a service."""

    label: str = "RailwayTCPProxy"
    properties: RailwayTCPProxyNodeProperties = RailwayTCPProxyNodeProperties()
    sub_resource_relationship: RailwayTCPProxyToProjectRel = (
        RailwayTCPProxyToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            RailwayTCPProxyToServiceInstanceRel(),
        ],
    )
