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
class OktaTrustedOriginProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    origin: PropertyRef = PropertyRef("origin")
    scopes: PropertyRef = PropertyRef("scopes")
    status: PropertyRef = PropertyRef("status")
    created: PropertyRef = PropertyRef("created")
    created_by: PropertyRef = PropertyRef("created_by")
    okta_last_updated: PropertyRef = PropertyRef("okta_last_updated")
    okta_last_updated_by: PropertyRef = PropertyRef("okta_last_updated_by")


@dataclass(frozen=True)
class OktaTrustedOriginToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:OktaOrganization)-[:RESOURCE]->(:OktaTrustedOrigin)
class OktaTrustedOriginToOrganizationRel(CartographyRelSchema):
    target_node_label: str = "OktaOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: OktaTrustedOriginToOrganizationRelProperties = (
        OktaTrustedOriginToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class OktaTrustedOriginSchema(CartographyNodeSchema):
    label: str = "OktaTrustedOrigin"
    properties: OktaTrustedOriginProperties = OktaTrustedOriginProperties()
    sub_resource_relationship: OktaTrustedOriginToOrganizationRel = (
        OktaTrustedOriginToOrganizationRel()
    )
