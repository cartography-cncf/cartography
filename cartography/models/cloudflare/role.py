from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class CloudflareRoleNodeProperties(CartographyNodeProperties):
    description: PropertyRef = PropertyRef("description")
    name: PropertyRef = PropertyRef("name")
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class CloudflareRoleToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:CloudflareRole)<-[:RESOURCE]-(:CloudflareAccount)
class CloudflareRoleToAccountRel(CartographyRelSchema):
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
    label: str = "CloudflareRole"
    properties: CloudflareRoleNodeProperties = CloudflareRoleNodeProperties()
    sub_resource_relationship: CloudflareRoleToAccountRel = CloudflareRoleToAccountRel()
