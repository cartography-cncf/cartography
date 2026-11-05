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
from cartography.models.ontology.labels import PERMISSION_ROLE


@dataclass(frozen=True)
class TencentCloudCAMRoleNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="ID of the CAM role.")
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Name of the CAM role."
    )
    arn: PropertyRef = PropertyRef(
        "arn",
        extra_index=True,
        description="Resource name of the role, e.g. `qcs::cam::uin/100000000001:roleName/my-role`.",
    )
    description: PropertyRef = PropertyRef(
        "description", description="Description of the role."
    )
    role_type: PropertyRef = PropertyRef(
        "role_type",
        description="Role type: `user`, `system`, or `service_linked`.",
    )
    console_login: PropertyRef = PropertyRef(
        "console_login",
        description="`True` when the role may be used to sign in to the console.",
    )
    session_duration: PropertyRef = PropertyRef(
        "session_duration",
        description="Maximum session duration of the role, in seconds.",
    )
    trust_policy: PropertyRef = PropertyRef(
        "trust_policy",
        description="Raw JSON trust policy (role carrier policy) that controls who may assume the role.",
    )
    trusted_principals: PropertyRef = PropertyRef(
        "trusted_principals",
        description="Tencent Cloud principals (`qcs::cam::...`) the trust policy allows to assume the role.",
    )
    trusted_services: PropertyRef = PropertyRef(
        "trusted_services",
        description="Tencent Cloud services (e.g. `cvm.qcloud.com`) the trust policy allows to assume the role.",
    )
    add_time: PropertyRef = PropertyRef(
        "add_time", description="Time the role was created."
    )
    update_time: PropertyRef = PropertyRef(
        "update_time", description="Time the role was last updated."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class TencentCloudCAMRoleToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:TencentCloudAccount)-[:RESOURCE]->(:TencentCloudCAMRole)
class TencentCloudCAMRoleToAccountRel(CartographyRelSchema):
    """Connects a `TencentCloudAccount` to its CAM roles."""

    target_node_label: str = "TencentCloudAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: TencentCloudCAMRoleToAccountRelProperties = (
        TencentCloudCAMRoleToAccountRelProperties()
    )


@dataclass(frozen=True)
class TencentCloudCAMRoleSchema(CartographyNodeSchema):
    """A CAM role: an identity that trusted principals or services can assume."""

    label: str = "TencentCloudCAMRole"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([PERMISSION_ROLE])
    properties: TencentCloudCAMRoleNodeProperties = TencentCloudCAMRoleNodeProperties()
    sub_resource_relationship: TencentCloudCAMRoleToAccountRel = (
        TencentCloudCAMRoleToAccountRel()
    )
