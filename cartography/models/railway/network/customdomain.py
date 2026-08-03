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
class RailwayCustomDomainNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="ID of the Railway custom domain.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    domain: PropertyRef = PropertyRef(
        "domain",
        extra_index=True,
        description="Fully qualified customer-owned domain name.",
    )
    target_port: PropertyRef = PropertyRef(
        "targetPort", description="Port on the service to which the domain routes."
    )
    is_railway_domain: PropertyRef = PropertyRef(
        "isRailwayDomain", description="Whether Railway manages the domain."
    )
    sync_status: PropertyRef = PropertyRef(
        "syncStatus", description="Provisioning status of the domain."
    )
    # Flattened from the nested `status` object. An unverified domain does not resolve yet,
    # so it is not an exposure; a bad certificate_status is worth alerting on.
    verified: PropertyRef = PropertyRef(
        "verified", description="Whether DNS verification has succeeded."
    )
    certificate_status: PropertyRef = PropertyRef(
        "certificate_status", description="TLS certificate provisioning status."
    )
    verification_dns_host: PropertyRef = PropertyRef(
        "verification_dns_host",
        description="DNS host Railway expects for domain verification.",
    )
    service_id: PropertyRef = PropertyRef(
        "service_id", description="ID of the service fronted by the domain."
    )
    environment_id: PropertyRef = PropertyRef(
        "environment_id", description="ID of the environment fronted by the domain."
    )


@dataclass(frozen=True)
class RailwayCustomDomainToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:RailwayProject)-[:RESOURCE]->(:RailwayCustomDomain)
class RailwayCustomDomainToProjectRel(CartographyRelSchema):
    """Connects a Railway project to a custom domain that it contains."""

    target_node_label: str = "RailwayProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: RailwayCustomDomainToProjectRelProperties = (
        RailwayCustomDomainToProjectRelProperties()
    )


@dataclass(frozen=True)
class RailwayCustomDomainToServiceInstanceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:RailwayServiceInstance)-[:EXPOSE]->(:RailwayCustomDomain)
#
# Only for domains that have passed DNS verification. An unverified domain does not resolve,
# so treating it as a public entry point would make exposure traversals disagree with
# is_publicly_exposed and over-report the attack surface. The matcher keys off
# exposed_service_id / exposed_environment_id, which transform() leaves null until the domain
# is verified, so no edge is created for one that is not. The plain service_id and
# environment_id properties stay on the node, so the association is still queryable.
class RailwayCustomDomainToServiceInstanceRel(CartographyRelSchema):
    """Identifies the Railway service instance exposed by a verified custom domain."""

    target_node_label: str = "RailwayServiceInstance"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "service_id": PropertyRef("exposed_service_id"),
            "environment_id": PropertyRef("exposed_environment_id"),
        },
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "EXPOSE"
    properties: RailwayCustomDomainToServiceInstanceRelProperties = (
        RailwayCustomDomainToServiceInstanceRelProperties()
    )


@dataclass(frozen=True)
class RailwayCustomDomainSchema(CartographyNodeSchema):
    """A customer-owned domain configured for a Railway service."""

    label: str = "RailwayCustomDomain"
    properties: RailwayCustomDomainNodeProperties = RailwayCustomDomainNodeProperties()
    sub_resource_relationship: RailwayCustomDomainToProjectRel = (
        RailwayCustomDomainToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            RailwayCustomDomainToServiceInstanceRel(),
        ],
    )
