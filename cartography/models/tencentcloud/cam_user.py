from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.ontology.labels import USER_ACCOUNT


@dataclass(frozen=True)
class TencentCloudCAMUserNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="UIN of the CAM sub-user, as a string."
    )
    uid: PropertyRef = PropertyRef("uid", description="UID of the CAM sub-user.")
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Login name of the CAM sub-user."
    )
    nick_name: PropertyRef = PropertyRef(
        "nick_name", description="Display name of the CAM sub-user."
    )
    remark: PropertyRef = PropertyRef(
        "remark", description="Free-form remark attached to the CAM sub-user."
    )
    email: PropertyRef = PropertyRef(
        "email", extra_index=True, description="Email address of the CAM sub-user."
    )
    console_login: PropertyRef = PropertyRef(
        "console_login",
        description="`True` when the sub-user may sign in to the Tencent Cloud console.",
    )
    create_time: PropertyRef = PropertyRef(
        "create_time", description="Time the sub-user was created."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class TencentCloudCAMUserToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:TencentCloudAccount)-[:RESOURCE]->(:TencentCloudCAMUser)
class TencentCloudCAMUserToAccountRel(CartographyRelSchema):
    """Connects a `TencentCloudAccount` to the CAM sub-users it owns."""

    target_node_label: str = "TencentCloudAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: TencentCloudCAMUserToAccountRelProperties = (
        TencentCloudCAMUserToAccountRelProperties()
    )


@dataclass(frozen=True)
class TencentCloudCAMUserSchema(CartographyNodeSchema):
    """A CAM sub-user: an identity created under a Tencent Cloud root account."""

    label: str = "TencentCloudCAMUser"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([USER_ACCOUNT])
    properties: TencentCloudCAMUserNodeProperties = TencentCloudCAMUserNodeProperties()
    sub_resource_relationship: TencentCloudCAMUserToAccountRel = (
        TencentCloudCAMUserToAccountRel()
    )
