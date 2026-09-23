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
class ZoomUserNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Account-scoped Zoom ID, or account-scoped normalized email for pending invitations.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    account_id: PropertyRef = PropertyRef(
        "ACCOUNT_ID",
        set_in_kwargs=True,
        description="Zoom account containing this user or invitation.",
    )
    zoom_id: PropertyRef = PropertyRef(
        "zoom_id", description="Provider user ID; absent for pending invitations."
    )
    email: PropertyRef = PropertyRef(
        "email",
        extra_index=True,
        description="Trimmed lowercase email used for identity correlation.",
    )
    first_name: PropertyRef = PropertyRef(
        "first_name", description="User's first name."
    )
    last_name: PropertyRef = PropertyRef("last_name", description="User's last name.")
    display_name: PropertyRef = PropertyRef(
        "display_name", description="User's display name."
    )
    department: PropertyRef = PropertyRef(
        "department", description="User's department."
    )
    status: PropertyRef = PropertyRef(
        "status", description="Account membership status: active, inactive, or pending."
    )
    type: PropertyRef = PropertyRef(
        "type",
        description="Assigned plan type: 1 Basic, 2 Licensed, 4 Unassigned without Meetings Basic, 99 legacy None.",
    )
    plan_type: PropertyRef = PropertyRef(
        "plan_type",
        description="Readable assigned plan type; not purchased seats, billing, or complete product entitlements.",
    )
    role_id: PropertyRef = PropertyRef(
        "role_id",
        description="Assigned account role ID; role permissions are not ingested.",
    )
    group_ids: PropertyRef = PropertyRef(
        "group_ids", description="IDs of groups where the user is a member."
    )
    login_types: PropertyRef = PropertyRef(
        "login_types",
        description="Provider login method codes; 101 denotes SSO, 100 Zoom work email.",
    )
    created_at: PropertyRef = PropertyRef(
        "created_at",
        description="Provider user_created_at as a native datetime, when available.",
    )
    last_login_time: PropertyRef = PropertyRef(
        "last_login_time",
        extra_index=True,
        description="Provider last_login_time as a native datetime with Zoom's three-day reporting buffer; not precise activity telemetry.",
    )


@dataclass(frozen=True)
class ZoomAccountToUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ZoomAccountToUserRel(CartographyRelSchema):
    """Contains a user or pending invitation in its Zoom account."""

    target_node_label: str = "ZoomAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ZoomAccountToUserRelProperties = ZoomAccountToUserRelProperties()


@dataclass(frozen=True)
class ZoomUserSchema(CartographyNodeSchema):
    """A Zoom user account or an invitation awaiting activation.

    Ontology Mapping: The UserAccount label enables cross-platform user queries.
    Pending invitations are inactive and are replaced by provider-ID nodes on activation.
    """

    label: str = "ZoomUser"
    properties: ZoomUserNodeProperties = ZoomUserNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([USER_ACCOUNT])
    sub_resource_relationship: ZoomAccountToUserRel = ZoomAccountToUserRel()
