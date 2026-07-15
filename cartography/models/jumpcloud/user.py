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
    id: PropertyRef = PropertyRef("id", description="JumpCloud user ID.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last update.",
    )
    username: PropertyRef = PropertyRef(
        "username",
        extra_index=True,
        description="Username.",
    )
    email: PropertyRef = PropertyRef(
        "email",
        extra_index=True,
        description="User email address.",
    )
    firstname: PropertyRef = PropertyRef("firstname", description="First name.")
    lastname: PropertyRef = PropertyRef("lastname", description="Last name.")
    displayname: PropertyRef = PropertyRef(
        "displayname",
        description="Display name.",
    )
    activated: PropertyRef = PropertyRef(
        "activated",
        description="Whether the account is activated.",
    )
    suspended: PropertyRef = PropertyRef(
        "suspended",
        description="Whether the account is suspended.",
    )
    account_locked: PropertyRef = PropertyRef(
        "account_locked",
        description="Whether the account is locked.",
    )
    mfa_configured: PropertyRef = PropertyRef(
        "mfa_configured",
        description="Whether MFA is configured for the user.",
    )
    created: PropertyRef = PropertyRef(
        "created",
        description="Timestamp when the account was created.",
    )
    lastlogin: PropertyRef = PropertyRef(
        "lastlogin",
        description="Timestamp of the last login.",
    )


@dataclass(frozen=True)
class JumpCloudTenantToUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:JumpCloudTenant)-[:RESOURCE]->(:JumpCloudUser)
class JumpCloudTenantToUserRel(CartographyRelSchema):
    """The tenant contains the user."""

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
    """A user account in JumpCloud."""

    label: str = "JumpCloudUser"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["UserAccount"])
    properties: JumpCloudUserNodeProperties = JumpCloudUserNodeProperties()
    sub_resource_relationship: JumpCloudTenantToUserRel = JumpCloudTenantToUserRel()
