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
class OktaUserFactorNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    factor_type: PropertyRef = PropertyRef("factor_type")
    provider: PropertyRef = PropertyRef("provider")
    status: PropertyRef = PropertyRef("status")
    created: PropertyRef = PropertyRef("created")
    okta_last_updated: PropertyRef = PropertyRef("okta_last_updated")


@dataclass(frozen=True)
class OktaUserFactorToOktaUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class OktaUserFactorToOktaUserRel(CartographyRelSchema):
    """
    (:OktaUserFactor)<-[:FACTOR]-(:OktaUser)
    """
    target_node_label: str = "OktaUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("user_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "FACTOR"
    properties: OktaUserFactorToOktaUserRelProperties = (
        OktaUserFactorToOktaUserRelProperties()
    )


@dataclass(frozen=True)
class OktaUserFactorToOktaOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class OktaUserFactorToOktaOrganizationRel(CartographyRelSchema):
    """
    (:OktaUserFactor)<-[:RESOURCE]-(:OktaOrganization)
    """
    target_node_label: str = "OktaOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("OKTA_ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: OktaUserFactorToOktaOrganizationRelProperties = (
        OktaUserFactorToOktaOrganizationRelProperties()
    )


@dataclass(frozen=True)
class OktaUserFactorSchema(CartographyNodeSchema):
    label: str = "OktaUserFactor"
    properties: OktaUserFactorNodeProperties = OktaUserFactorNodeProperties()
    sub_resource_relationship: OktaUserFactorToOktaOrganizationRel = (
        OktaUserFactorToOktaOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[OktaUserFactorToOktaUserRel()],
    )
