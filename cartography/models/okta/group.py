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
class OktaGroupProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    description: PropertyRef = PropertyRef("description")
    sam_account_name: PropertyRef = PropertyRef("sam_account_name")
    dn: PropertyRef = PropertyRef("dn")
    windows_domain_qualified_name: PropertyRef = PropertyRef(
        "windows_domain_qualified_name"
    )
    external_id: PropertyRef = PropertyRef("external_id")


@dataclass(frozen=True)
class OktaGroupToUserProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:OktaUser)-[:MEMBER_OF_OKTA_GROUP]->(:OktaGroup)
class OktaGroupToUserRel(CartographyRelSchema):
    target_node_label: str = "OktaUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("members", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "MEMBER_OF_OKTA_GROUP"
    properties: OktaGroupToUserProperties = OktaGroupToUserProperties()


@dataclass(frozen=True)
class OktaGroupToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:OktaOrganization)-[:RESOURCE]->(:OktaGroup)
class OktaGroupToOrganizationRel(CartographyRelSchema):
    target_node_label: str = "OktaOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: OktaGroupToOrganizationRelProperties = (
        OktaGroupToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class OktaGroupSchema(CartographyNodeSchema):
    label: str = "OktaGroup"
    properties: OktaGroupProperties = OktaGroupProperties()
    sub_resource_relationship: OktaGroupToOrganizationRel = OktaGroupToOrganizationRel()
    other_relationsips: OtherRelationships = OtherRelationships(
        [
            OktaGroupToUserRel(),
        ]
    )
