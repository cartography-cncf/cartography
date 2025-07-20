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
class OktaUserFactorProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    factor_type: PropertyRef = PropertyRef("factor_type")
    provider: PropertyRef = PropertyRef("provider")
    status: PropertyRef = PropertyRef("status")
    created: PropertyRef = PropertyRef("created")
    okta_last_updated: PropertyRef = PropertyRef("okta_last_updated")


@dataclass(frozen=True)
class OktaUserFactorToUserProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:OktaUser)-[:FACTOR]->(:OktaUserFactor)
class OktaUserFactorToUserRel(CartographyRelSchema):
    target_node_label: str = "OktaUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("user_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "FACTOR"
    properties: OktaUserFactorToUserProperties = OktaUserFactorToUserProperties()


@dataclass(frozen=True)
class OktaUserFactorToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:OktaOrganization)-[:RESOURCE]->(:OktaUserFactor)
class OktaUserFactorToOrganizationRel(CartographyRelSchema):
    target_node_label: str = "OktaOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: OktaUserFactorToOrganizationRelProperties = (
        OktaUserFactorToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class OktaUserFactorSchema(CartographyNodeSchema):
    label: str = "OktaUserFactor"
    properties: OktaUserFactorProperties = OktaUserFactorProperties()
    sub_resource_relationship: OktaUserFactorToOrganizationRel = (
        OktaUserFactorToOrganizationRel()
    )
    other_relationsips: OtherRelationships = OtherRelationships(
        [
            OktaUserFactorToUserRel(),
        ]
    )
