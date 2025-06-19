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
class OktaAdministrationRoleProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("type")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    label: PropertyRef = PropertyRef("label")


@dataclass(frozen=True)
class OktaAdministrationRoleToUserProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:OktaUser)-[:MEMBER_OF_OKTA_ROLE]->(:OktaAdministrationRole)
class OktaAdministrationRoleToUserRel(CartographyRelSchema):
    target_node_label: str = "OktaUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("users", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "MEMBER_OF_OKTA_ROLE"
    properties: OktaAdministrationRoleToUserProperties = (
        OktaAdministrationRoleToUserProperties()
    )


@dataclass(frozen=True)
class OktaAdministrationRoleToGroupProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:OktaGroup)-[:CONTAINS]->(:OktaAdministrationRole)
class OktaAdministrationRoleToGroupRel(CartographyRelSchema):
    target_node_label: str = "OktaGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: OktaAdministrationRoleToGroupProperties = (
        OktaAdministrationRoleToGroupProperties()
    )


@dataclass(frozen=True)
class OktaAdministrationRoleToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:OktaOrganization)-[:RESOURCE]->(:OktaAdministrationRole)
class OktaAdministrationRoleToOrganizationRel(CartographyRelSchema):
    target_node_label: str = "OktaOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: OktaAdministrationRoleToOrganizationRelProperties = (
        OktaAdministrationRoleToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class OktaAdministrationRoleSchema(CartographyNodeSchema):
    label: str = "OktaAdministrationRole"
    properties: OktaAdministrationRoleProperties = OktaAdministrationRoleProperties()
    sub_resource_relationship: OktaAdministrationRoleToOrganizationRel = (
        OktaAdministrationRoleToOrganizationRel()
    )
    other_relationsips: OtherRelationships = OtherRelationships(
        [
            OktaAdministrationRoleToUserRel(),
            OktaAdministrationRoleToGroupRel(),
        ]
    )
