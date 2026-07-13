from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class LastpassUserNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="LastPass user ID.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )
    name: PropertyRef = PropertyRef("fullname", description="Full name of the user.")
    email: PropertyRef = PropertyRef(
        "username",
        extra_index=True,
        description="Email address of the user.",
    )
    created: PropertyRef = PropertyRef(
        "created",
        description="Timestamp when the account was created.",
    )
    last_pw_change: PropertyRef = PropertyRef(
        "last_pw_change",
        description="Timestamp of the last master password change.",
    )
    last_login: PropertyRef = PropertyRef(
        "last_login",
        description="Timestamp of the last login.",
    )
    neverloggedin: PropertyRef = PropertyRef(
        "neverloggedin",
        description="Whether the user has never logged in.",
    )
    disabled: PropertyRef = PropertyRef(
        "disabled",
        description="Whether the account is disabled.",
    )
    admin: PropertyRef = PropertyRef(
        "admin",
        description="Whether the account is an administrator.",
    )
    totalscore: PropertyRef = PropertyRef(
        "totalscore",
        description="LastPass security score, with a maximum of 100.",
    )
    mpstrength: PropertyRef = PropertyRef(
        "mpstrength",
        description="Master password strength score, with a maximum of 100.",
    )
    sites: PropertyRef = PropertyRef(
        "sites",
        description="Number of site credentials stored.",
    )
    notes: PropertyRef = PropertyRef(
        "notes",
        description="Number of secure notes stored.",
    )
    formfills: PropertyRef = PropertyRef(
        "formfills",
        description="Number of form-fill profiles stored.",
    )
    applications: PropertyRef = PropertyRef(
        "applications",
        description="Number of mobile applications stored.",
    )
    attachments: PropertyRef = PropertyRef(
        "attachments",
        description="Number of file attachments stored.",
    )
    password_reset_required: PropertyRef = PropertyRef(
        "password_reset_required",
        description="Whether the user must reset their password.",
    )
    multifactor: PropertyRef = PropertyRef(
        "multifactor",
        description="Configured multifactor authentication method.",
    )


@dataclass(frozen=True)
class LastpassUserToHumanRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:LastpassUser)<-[:IDENTITY_LASTPASS]-(:Human)
class LastpassHumanToUserRel(CartographyRelSchema):
    """Links a Human identity to the LastPass user account with the same email."""

    target_node_label: str = "Human"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"email": PropertyRef("username")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "IDENTITY_LASTPASS"
    properties: LastpassUserToHumanRelProperties = LastpassUserToHumanRelProperties()


@dataclass(frozen=True)
class LastpassTenantToLastpassUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:LastpassTenant)-[:RESOURCE]->(:LastpassUser)
class LastpassTenantToUserRel(CartographyRelSchema):
    """Contains a LastPass user in a LastPass tenant."""

    target_node_label: str = "LastpassTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: LastpassTenantToLastpassUserRelProperties = (
        LastpassTenantToLastpassUserRelProperties()
    )


@dataclass(frozen=True)
# (:LastpassUser)-[:RESOURCE]->(:LastpassTenant) - Backwards compatibility
class LastpassUserToTenantDeprecatedRel(CartographyRelSchema):
    """Deprecated reverse tenant edge retained for backward compatibility."""

    target_node_label: str = "LastpassTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RESOURCE"
    properties: LastpassTenantToLastpassUserRelProperties = (
        LastpassTenantToLastpassUserRelProperties()
    )


@dataclass(frozen=True)
class LastpassUserSchema(CartographyNodeSchema):
    """Representation of a LastPass user account."""

    label: str = "LastpassUser"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        ["UserAccount"]
    )  # UserAccount label is used for ontology mapping
    properties: LastpassUserNodeProperties = LastpassUserNodeProperties()
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[
            LastpassHumanToUserRel(),
            # DEPRECATED: for backward compatibility, will be removed in v1.0.0
            LastpassUserToTenantDeprecatedRel(),
        ],
    )
    sub_resource_relationship: LastpassTenantToUserRel = LastpassTenantToUserRel()
