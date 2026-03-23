from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class JumpCloudApplicationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    description: PropertyRef = PropertyRef("description")


@dataclass(frozen=True)
class JumpCloudApplicationToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:JumpCloudTenant)-[:RESOURCE]->(:JumpCloudSaaSApplication)
class JumpCloudApplicationToTenantRel(CartographyRelSchema):
    target_node_label: str = "JumpCloudTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: JumpCloudApplicationToTenantRelProperties = (
        JumpCloudApplicationToTenantRelProperties()
    )


@dataclass(frozen=True)
class JumpCloudApplicationToUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:JumpCloudUser)-[:USES]->(:JumpCloudSaaSApplication)
class JumpCloudApplicationToUserRel(CartographyRelSchema):
    target_node_label: str = "JumpCloudUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("user_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "USES"
    properties: JumpCloudApplicationToUserRelProperties = (
        JumpCloudApplicationToUserRelProperties()
    )


@dataclass(frozen=True)
class JumpCloudApplicationSchema(CartographyNodeSchema):
    label: str = "JumpCloudSaaSApplication"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["ThirdPartyApp"])
    properties: JumpCloudApplicationNodeProperties = (
        JumpCloudApplicationNodeProperties()
    )
    sub_resource_relationship: JumpCloudApplicationToTenantRel = (
        JumpCloudApplicationToTenantRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[JumpCloudApplicationToUserRel()],
    )
