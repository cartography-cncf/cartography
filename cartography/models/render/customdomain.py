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
class RenderCustomDomainNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="ID of the Render custom domain.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="The domain name."
    )
    owner_id: PropertyRef = PropertyRef(
        "ownerId", description="ID of the owning Render workspace."
    )
    service_id: PropertyRef = PropertyRef(
        "serviceId", extra_index=True, description="ID of the service the domain is attached to."
    )
    domain_type: PropertyRef = PropertyRef(
        "domainType", description="Whether the domain is an `apex` or `subdomain`."
    )
    public_suffix: PropertyRef = PropertyRef(
        "publicSuffix", description="The domain's public suffix."
    )
    redirect_for_name: PropertyRef = PropertyRef(
        "redirectForName",
        description="The domain name this domain redirects to, if configured as a redirect.",
    )
    verification_status: PropertyRef = PropertyRef(
        "verificationStatus",
        extra_index=True,
        description="Whether the domain is `verified` or `unverified`.",
    )
    created_at: PropertyRef = PropertyRef(
        "createdAt", description="Time when the custom domain was created."
    )


@dataclass(frozen=True)
class RenderCustomDomainToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:RenderTenant)-[:RESOURCE]->(:RenderCustomDomain)
class RenderCustomDomainToTenantRel(CartographyRelSchema):
    """Connects a Render workspace to a custom domain that it contains."""

    target_node_label: str = "RenderTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("OWNER_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: RenderCustomDomainToTenantRelProperties = (
        RenderCustomDomainToTenantRelProperties()
    )


@dataclass(frozen=True)
class RenderCustomDomainToServiceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:RenderService)-[:HAS_DOMAIN]->(:RenderCustomDomain)
class RenderCustomDomainToServiceRel(CartographyRelSchema):
    """Connects a Render service to a custom domain configured on it."""

    target_node_label: str = "RenderService"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("serviceId")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_DOMAIN"
    properties: RenderCustomDomainToServiceRelProperties = (
        RenderCustomDomainToServiceRelProperties()
    )


@dataclass(frozen=True)
class RenderCustomDomainSchema(CartographyNodeSchema):
    """A custom domain configured on a Render service."""

    label: str = "RenderCustomDomain"
    properties: RenderCustomDomainNodeProperties = RenderCustomDomainNodeProperties()
    sub_resource_relationship: RenderCustomDomainToTenantRel = (
        RenderCustomDomainToTenantRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [RenderCustomDomainToServiceRel()],
    )
