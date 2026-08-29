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
class RailwayServiceDomainNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="ID of the Railway service domain.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    # Exposure signal: a Railway-generated domain is always internet-facing.
    domain: PropertyRef = PropertyRef(
        "domain",
        extra_index=True,
        description="Fully qualified Railway-provided domain name.",
    )
    suffix: PropertyRef = PropertyRef("suffix", description="Railway domain suffix.")
    target_port: PropertyRef = PropertyRef(
        "targetPort", description="Port on the service to which the domain routes."
    )
    sync_status: PropertyRef = PropertyRef(
        "syncStatus", description="Provisioning status of the domain."
    )
    service_id: PropertyRef = PropertyRef(
        "service_id", description="ID of the service fronted by the domain."
    )
    environment_id: PropertyRef = PropertyRef(
        "environment_id", description="ID of the environment fronted by the domain."
    )
    created_at: PropertyRef = PropertyRef(
        "createdAt", description="Time when the domain was created."
    )


@dataclass(frozen=True)
class RailwayServiceDomainToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:RailwayProject)-[:RESOURCE]->(:RailwayServiceDomain)
class RailwayServiceDomainToProjectRel(CartographyRelSchema):
    """Connects a Railway project to a service domain that it contains."""

    target_node_label: str = "RailwayProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: RailwayServiceDomainToProjectRelProperties = (
        RailwayServiceDomainToProjectRelProperties()
    )


@dataclass(frozen=True)
class RailwayServiceDomainToServiceInstanceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:RailwayServiceDomain)-[:EXPOSE]->(:RailwayServiceInstance)
#
# EXPOSE always points from the internet-facing entrypoint to the asset it puts at risk,
# matching the LoadBalancer-[:EXPOSE]->workload convention used by AWS, GCP, Azure and
# Kubernetes. That is what makes a cross-provider traversal of this edge meaningful.
#
# Keyed by the (service, environment) pair, since that is what the Railway payload carries.
# The matcher uses exposed_* rather than the plain ids: transform() leaves those null unless
# the domain's syncStatus says it is actually serving, so a domain that is still CREATING or
# on its way out gets no EXPOSE edge and cannot inflate the attack surface.
class RailwayServiceDomainToServiceInstanceRel(CartographyRelSchema):
    """Identifies the Railway service instance exposed by a serving domain."""

    target_node_label: str = "RailwayServiceInstance"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "service_id": PropertyRef("exposed_service_id"),
            "environment_id": PropertyRef("exposed_environment_id"),
        },
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "EXPOSE"
    properties: RailwayServiceDomainToServiceInstanceRelProperties = (
        RailwayServiceDomainToServiceInstanceRelProperties()
    )


@dataclass(frozen=True)
class RailwayServiceDomainSchema(CartographyNodeSchema):
    """A Railway-provided public domain for a service."""

    label: str = "RailwayServiceDomain"
    properties: RailwayServiceDomainNodeProperties = (
        RailwayServiceDomainNodeProperties()
    )
    sub_resource_relationship: RailwayServiceDomainToProjectRel = (
        RailwayServiceDomainToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            RailwayServiceDomainToServiceInstanceRel(),
        ],
    )
