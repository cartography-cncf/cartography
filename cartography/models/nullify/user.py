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
class NullifyUserNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    username: PropertyRef = PropertyRef("username", extra_index=True)
    email: PropertyRef = PropertyRef("email", extra_index=True)
    role: PropertyRef = PropertyRef("role")
    is_bot: PropertyRef = PropertyRef("isBot")
    created_at: PropertyRef = PropertyRef("createdAt")
    updated_at: PropertyRef = PropertyRef("updatedAt")


@dataclass(frozen=True)
class NullifyUserToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:NullifyTenant)-[:RESOURCE]->(:NullifyUser)
class NullifyUserToTenantRel(CartographyRelSchema):
    target_node_label: str = "NullifyTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: NullifyUserToTenantRelProperties = NullifyUserToTenantRelProperties()


@dataclass(frozen=True)
class NullifyUserSchema(CartographyNodeSchema):
    label: str = "NullifyUser"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["UserAccount"])
    properties: NullifyUserNodeProperties = NullifyUserNodeProperties()
    sub_resource_relationship: NullifyUserToTenantRel = NullifyUserToTenantRel()
