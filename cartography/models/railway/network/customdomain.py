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
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    domain: PropertyRef = PropertyRef("domain", extra_index=True)
    target_port: PropertyRef = PropertyRef("targetPort")
    is_railway_domain: PropertyRef = PropertyRef("isRailwayDomain")
    sync_status: PropertyRef = PropertyRef("syncStatus")
    # Flattened from the nested `status` object. An unverified domain does not resolve yet,
    # so it is not an exposure; a bad certificate_status is worth alerting on.
    verified: PropertyRef = PropertyRef("verified")
    certificate_status: PropertyRef = PropertyRef("certificate_status")
    verification_dns_host: PropertyRef = PropertyRef("verification_dns_host")
    service_id: PropertyRef = PropertyRef("service_id")
    environment_id: PropertyRef = PropertyRef("environment_id")


@dataclass(frozen=True)
class RailwayCustomDomainToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:RailwayProject)-[:RESOURCE]->(:RailwayCustomDomain)
class RailwayCustomDomainToProjectRel(CartographyRelSchema):
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
