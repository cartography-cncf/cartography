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
class Route53RegisteredDomainNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        extra_index=True,
        description="Domain name used as the unique identifier.",
    )
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="Registered domain name.",
    )
    auto_renew: PropertyRef = PropertyRef(
        "auto_renew",
        description="Whether the domain is set to auto-renew.",
    )
    transfer_lock: PropertyRef = PropertyRef(
        "transfer_lock",
        description="Whether the domain has a transfer lock enabled.",
    )
    expiry: PropertyRef = PropertyRef(
        "expiry",
        description="Domain registration expiration timestamp.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class Route53RegisteredDomainToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AWSAccount)-[:RESOURCE]->(:Route53RegisteredDomain)
class Route53RegisteredDomainToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: Route53RegisteredDomainToAWSAccountRelProperties = (
        Route53RegisteredDomainToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class Route53RegisteredDomainToAWSDNSZoneRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AWSDNSZone)-[:REGISTERED_DOMAIN]->(:Route53RegisteredDomain)
class Route53RegisteredDomainToAWSDNSZoneRel(CartographyRelSchema):
    """Link hosted zones whose name matches this registered domain."""

    target_node_label: str = "AWSDNSZone"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"name": PropertyRef("name")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "REGISTERED_DOMAIN"
    properties: Route53RegisteredDomainToAWSDNSZoneRelProperties = (
        Route53RegisteredDomainToAWSDNSZoneRelProperties()
    )


@dataclass(frozen=True)
class Route53RegisteredDomainSchema(CartographyNodeSchema):
    """
    A domain registered through Route 53 Domains
    (https://docs.aws.amazon.com/Route53/latest/APIReference/API_domains_DomainSummary.html).
    """

    label: str = "Route53RegisteredDomain"
    properties: Route53RegisteredDomainNodeProperties = (
        Route53RegisteredDomainNodeProperties()
    )
    sub_resource_relationship: Route53RegisteredDomainToAWSAccountRel = (
        Route53RegisteredDomainToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            Route53RegisteredDomainToAWSDNSZoneRel(),
        ],
    )
