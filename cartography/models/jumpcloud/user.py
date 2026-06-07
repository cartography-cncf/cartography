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
class JumpCloudUserNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    username: PropertyRef = PropertyRef("username", extra_index=True)
    email: PropertyRef = PropertyRef("email", extra_index=True)
    firstname: PropertyRef = PropertyRef("firstname")
    lastname: PropertyRef = PropertyRef("lastname")
    displayname: PropertyRef = PropertyRef("displayname")
    activated: PropertyRef = PropertyRef("activated")
    suspended: PropertyRef = PropertyRef("suspended")
    account_locked: PropertyRef = PropertyRef("account_locked")
    mfa_configured: PropertyRef = PropertyRef("mfa_configured")
    created: PropertyRef = PropertyRef("created")
    lastlogin: PropertyRef = PropertyRef("lastlogin")


@dataclass(frozen=True)
class JumpCloudTenantToUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:JumpCloudTenant)-[:RESOURCE]->(:JumpCloudUser)
class JumpCloudTenantToUserRel(CartographyRelSchema):
    target_node_label: str = "JumpCloudTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: JumpCloudTenantToUserRelProperties = (
        JumpCloudTenantToUserRelProperties()
    )


@dataclass(frozen=True)
class JumpCloudUserSchema(CartographyNodeSchema):
    label: str = "JumpCloudUser"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["UserAccount"])
    properties: JumpCloudUserNodeProperties = JumpCloudUserNodeProperties()
    sub_resource_relationship: JumpCloudTenantToUserRel = JumpCloudTenantToUserRel()
