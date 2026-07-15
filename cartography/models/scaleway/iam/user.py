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
class ScalewayUserNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="ID of user.")
    email: PropertyRef = PropertyRef(
        "email", extra_index=True, description="Email of user."
    )
    username: PropertyRef = PropertyRef(
        "username", description="User identifier unique to the Organization."
    )
    first_name: PropertyRef = PropertyRef(
        "first_name", description="First name of the user."
    )
    last_name: PropertyRef = PropertyRef(
        "last_name", description="Last name of the user."
    )
    phone_number: PropertyRef = PropertyRef(
        "phone_number", description="Phone number of the user."
    )
    locale: PropertyRef = PropertyRef("locale", description="Locale of the user.")
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Date user was created."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="Date of last user update."
    )
    deletable: PropertyRef = PropertyRef(
        "deletable", description="Deletion status of user. Owners cannot be deleted."
    )
    last_login_at: PropertyRef = PropertyRef(
        "last_login_at", description="Date of the last login."
    )
    type: PropertyRef = PropertyRef(
        "type", description="Type of user (`unknown_type`, `guest`, `owner`, `member`)"
    )
    status: PropertyRef = PropertyRef(
        "status",
        description="Status of user invitation (`unknown_status`, `invitation_pending`, `activated`)",
    )
    mfa: PropertyRef = PropertyRef("mfa", description="Defines whether MFA is enabled.")
    account_root_user_id: PropertyRef = PropertyRef(
        "account_root_user_id",
        description="ID of the account root user associated with the user.",
    )
    tags: PropertyRef = PropertyRef(
        "tags", description="Tags associated with the user."
    )
    locked: PropertyRef = PropertyRef(
        "locked", description="Defines whether the user is locked."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Timestamp of the last update"
    )


@dataclass(frozen=True)
class ScalewayUserToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayOrganization)-[:RESOURCE]->(:ScalewayUser)
class ScalewayUserToOrganizationRel(CartographyRelSchema):
    """Connects `ScalewayOrganization` to `ScalewayUser` through `RESOURCE`."""

    target_node_label: str = "ScalewayOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ScalewayUserToOrganizationRelProperties = (
        ScalewayUserToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class ScalewayUserSchema(CartographyNodeSchema):
    """Represents a User in Scaleway."""

    label: str = "ScalewayUser"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        ["UserAccount"]
    )  # UserAccount label is used for ontology mapping
    properties: ScalewayUserNodeProperties = ScalewayUserNodeProperties()
    sub_resource_relationship: ScalewayUserToOrganizationRel = (
        ScalewayUserToOrganizationRel()
    )
