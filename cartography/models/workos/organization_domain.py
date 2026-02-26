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
class WorkOSOrganizationDomainNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    domain: PropertyRef = PropertyRef("domain")
    organization_id: PropertyRef = PropertyRef("organization_id")
    state: PropertyRef = PropertyRef("state")
    verification_strategy: PropertyRef = PropertyRef("verification_strategy")
    verification_token: PropertyRef = PropertyRef("verification_token")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class WorkOSOrganizationDomainToEnvironmentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:WorkOSEnvironment)-[:RESOURCE]->(:WorkOSOrganizationDomain)
class WorkOSOrganizationDomainToEnvironmentRel(CartographyRelSchema):
    target_node_label: str = "WorkOSEnvironment"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKOS_CLIENT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: WorkOSOrganizationDomainToEnvironmentRelProperties = (
        WorkOSOrganizationDomainToEnvironmentRelProperties()
    )


@dataclass(frozen=True)
class WorkOSOrganizationDomainToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:WorkOSOrganizationDomain)-[:DOMAIN_OF]->(:WorkOSOrganization)
class WorkOSOrganizationDomainToOrganizationRel(CartographyRelSchema):
    target_node_label: str = "WorkOSOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("organization_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "DOMAIN_OF"
    properties: WorkOSOrganizationDomainToOrganizationRelProperties = (
        WorkOSOrganizationDomainToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class WorkOSOrganizationDomainSchema(CartographyNodeSchema):
    label: str = "WorkOSOrganizationDomain"
    properties: WorkOSOrganizationDomainNodeProperties = (
        WorkOSOrganizationDomainNodeProperties()
    )
    sub_resource_relationship: WorkOSOrganizationDomainToEnvironmentRel = (
        WorkOSOrganizationDomainToEnvironmentRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[WorkOSOrganizationDomainToOrganizationRel()],
    )
