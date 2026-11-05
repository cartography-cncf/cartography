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
from cartography.models.ontology.labels import USER_GROUP


@dataclass(frozen=True)
class TencentCloudCAMGroupNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="ID of the CAM user group.")
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Name of the CAM user group."
    )
    remark: PropertyRef = PropertyRef(
        "remark", description="Description of the CAM user group."
    )
    create_time: PropertyRef = PropertyRef(
        "create_time", description="Time the group was created."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class TencentCloudCAMGroupToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:TencentCloudAccount)-[:RESOURCE]->(:TencentCloudCAMGroup)
class TencentCloudCAMGroupToAccountRel(CartographyRelSchema):
    """Connects a `TencentCloudAccount` to its CAM user groups."""

    target_node_label: str = "TencentCloudAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: TencentCloudCAMGroupToAccountRelProperties = (
        TencentCloudCAMGroupToAccountRelProperties()
    )


@dataclass(frozen=True)
class TencentCloudCAMGroupToUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:TencentCloudCAMUser)-[:MEMBER_OF]->(:TencentCloudCAMGroup)
class TencentCloudCAMGroupToUserRel(CartographyRelSchema):
    """Connects a CAM sub-user to each group it belongs to."""

    target_node_label: str = "TencentCloudCAMUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("member_uins", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "MEMBER_OF"
    properties: TencentCloudCAMGroupToUserRelProperties = (
        TencentCloudCAMGroupToUserRelProperties()
    )


@dataclass(frozen=True)
class TencentCloudCAMGroupSchema(CartographyNodeSchema):
    """A CAM user group. Policies attached to a group apply to all of its members."""

    label: str = "TencentCloudCAMGroup"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([USER_GROUP])
    properties: TencentCloudCAMGroupNodeProperties = (
        TencentCloudCAMGroupNodeProperties()
    )
    sub_resource_relationship: TencentCloudCAMGroupToAccountRel = (
        TencentCloudCAMGroupToAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [TencentCloudCAMGroupToUserRel()],
    )
