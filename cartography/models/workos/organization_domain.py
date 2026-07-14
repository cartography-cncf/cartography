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
    id: PropertyRef = PropertyRef("id", description="WorkOS organization domain ID.")
    domain: PropertyRef = PropertyRef("domain", description="Organization domain name.")
    organization_id: PropertyRef = PropertyRef(
        "organization_id", description="ID of the organization that owns the domain."
    )
    state: PropertyRef = PropertyRef("state", description="Domain verification state.")
    verification_strategy: PropertyRef = PropertyRef(
        "verification_strategy", description="Strategy used to verify the domain."
    )
    verification_token: PropertyRef = PropertyRef(
        "verification_token", description="Token used to verify the domain."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Timestamp of the last update."
    )


@dataclass(frozen=True)
class WorkOSOrganizationDomainToEnvironmentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:WorkOSEnvironment)-[:RESOURCE]->(:WorkOSOrganizationDomain)
class WorkOSOrganizationDomainToEnvironmentRel(CartographyRelSchema):
    """The WorkOS environment contains this organization domain as a resource."""

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
    """The WorkOS organization domain belongs to its organization."""

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
    """A domain associated with a WorkOS organization."""

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
