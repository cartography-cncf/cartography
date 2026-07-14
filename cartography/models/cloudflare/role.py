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


@dataclass(frozen=True)
class CloudflareRoleNodeProperties(CartographyNodeProperties):
    description: PropertyRef = PropertyRef(
        "description",
        description="Description of the role's permissions.",
    )
    name: PropertyRef = PropertyRef("name", description="Role name.")
    id: PropertyRef = PropertyRef("id", description="Role ID.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last update.",
    )


@dataclass(frozen=True)
class CloudflareRoleToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:CloudflareRole)<-[:RESOURCE]-(:CloudflareAccount)
class CloudflareRoleToAccountRel(CartographyRelSchema):
    """The account contains the role."""

    target_node_label: str = "CloudflareAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("account_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: CloudflareRoleToAccountRelProperties = (
        CloudflareRoleToAccountRelProperties()
    )


@dataclass(frozen=True)
class CloudflareRoleSchema(CartographyNodeSchema):
    """A permission role in Cloudflare."""

    label: str = "CloudflareRole"
    properties: CloudflareRoleNodeProperties = CloudflareRoleNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["PermissionRole"])
    sub_resource_relationship: CloudflareRoleToAccountRel = CloudflareRoleToAccountRel()
