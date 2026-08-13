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
class MiradoreUserNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Tenant-scoped identifier for the user, as `<site name>/<Miradore ID>`.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    miradore_id: PropertyRef = PropertyRef(
        "miradore_id",
        extra_index=True,
        description="Raw Miradore ID of the user, which is only unique within the tenant.",
    )
    email: PropertyRef = PropertyRef(
        "email",
        extra_index=True,
        description="User email address.",
    )
    name: PropertyRef = PropertyRef(
        "name",
        description="User display name as rendered by Miradore.",
    )
    firstname: PropertyRef = PropertyRef("firstname", description="First name.")
    lastname: PropertyRef = PropertyRef("lastname", description="Last name.")
    middle: PropertyRef = PropertyRef("middle", description="Middle name.")
    phone_number: PropertyRef = PropertyRef(
        "phone_number",
        description="User phone number.",
    )
    status: PropertyRef = PropertyRef(
        "status",
        description="Account status: New, Active, Retired or System.",
    )
    retired: PropertyRef = PropertyRef(
        "retired",
        description="Whether the account has been retired, derived from the status.",
    )
    source: PropertyRef = PropertyRef(
        "source",
        description="How the account was created: Unknown, GUI, CSV, API or AD.",
    )
    created: PropertyRef = PropertyRef(
        "created",
        description="Timestamp when the account was created.",
    )
    modified: PropertyRef = PropertyRef(
        "modified",
        description="Timestamp when the account was last modified.",
    )


@dataclass(frozen=True)
class MiradoreUserToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:MiradoreTenant)-[:RESOURCE]->(:MiradoreUser)
@dataclass(frozen=True)
class MiradoreUserToTenantRel(CartographyRelSchema):
    """Links a Miradore tenant to one of its user accounts."""

    target_node_label: str = "MiradoreTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: MiradoreUserToTenantRelProperties = MiradoreUserToTenantRelProperties()


@dataclass(frozen=True)
class MiradoreUserSchema(CartographyNodeSchema):
    """A user account in Miradore."""

    label: str = "MiradoreUser"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([USER_ACCOUNT])
    properties: MiradoreUserNodeProperties = MiradoreUserNodeProperties()
    sub_resource_relationship: MiradoreUserToTenantRel = MiradoreUserToTenantRel()
