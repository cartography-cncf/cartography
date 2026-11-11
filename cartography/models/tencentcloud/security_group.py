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
from cartography.models.ontology.labels import NETWORK_ACCESS_CONTROL


@dataclass(frozen=True)
class TencentCloudSecurityGroupNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Security group ID, e.g. `sg-ohuuioma`."
    )
    name: PropertyRef = PropertyRef("name", description="Name of the security group.")
    description: PropertyRef = PropertyRef(
        "description", description="Description of the security group."
    )
    region: PropertyRef = PropertyRef(
        "region", extra_index=True, description="Region the security group is in."
    )
    project_id: PropertyRef = PropertyRef(
        "project_id",
        description="ID of the Tencent Cloud project the group belongs to.",
    )
    is_default: PropertyRef = PropertyRef(
        "is_default", description="`True` for the default security group."
    )
    tags: PropertyRef = PropertyRef(
        "tags", description="Tags on the security group, as `key:value` strings."
    )
    created_time: PropertyRef = PropertyRef(
        "created_time", description="Time the security group was created."
    )
    update_time: PropertyRef = PropertyRef(
        "update_time", description="Time the security group was last updated."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class TencentCloudSecurityGroupToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:TencentCloudAccount)-[:RESOURCE]->(:TencentCloudSecurityGroup)
class TencentCloudSecurityGroupToAccountRel(CartographyRelSchema):
    """Connects a `TencentCloudAccount` to its security groups."""

    target_node_label: str = "TencentCloudAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: TencentCloudSecurityGroupToAccountRelProperties = (
        TencentCloudSecurityGroupToAccountRelProperties()
    )


@dataclass(frozen=True)
class TencentCloudSecurityGroupSchema(CartographyNodeSchema):
    """A security group: a stateful firewall attached to CVM instances, load balancers and
    other network interfaces. Tencent Cloud security groups are regional, not VPC-scoped.
    """

    label: str = "TencentCloudSecurityGroup"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([NETWORK_ACCESS_CONTROL])
    properties: TencentCloudSecurityGroupNodeProperties = (
        TencentCloudSecurityGroupNodeProperties()
    )
    sub_resource_relationship: TencentCloudSecurityGroupToAccountRel = (
        TencentCloudSecurityGroupToAccountRel()
    )
