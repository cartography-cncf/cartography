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
from cartography.models.ontology.labels import PERMISSION_ROLE


@dataclass(frozen=True)
class PylonRoleNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Pylon role ID.")
    name: PropertyRef = PropertyRef("name", description="Role name.")
    slug: PropertyRef = PropertyRef(
        "slug",
        extra_index=True,
        description="Role slug, for example `admin`.",
    )
    permissions: PropertyRef = PropertyRef(
        "permissions",
        description=(
            "Sorted list of actions that the role grants, for example "
            "`read:issue`. An action can apply only to the objects that match "
            "a filter; see `filtered_permissions`."
        ),
    )
    filtered_permissions: PropertyRef = PropertyRef(
        "filtered_permissions",
        description=(
            "Sorted list of granted actions that apply only to objects that "
            "match a filter, including filters that the Pylon API can't "
            "represent."
        ),
    )
    field_restricted_permissions: PropertyRef = PropertyRef(
        "field_restricted_permissions",
        description=(
            "Sorted list of granted actions that also hide or lock fields "
            "through restrictions that the Pylon API can't represent."
        ),
    )
    issue_access_default_actions: PropertyRef = PropertyRef(
        "issue_access_default_actions",
        description=(
            "Sorted list of actions that the role grants on an issue that "
            "matches none of its issue access rules."
        ),
    )
    issue_access_rule_count: PropertyRef = PropertyRef(
        "issue_access_rule_count",
        description=(
            "Number of issue access rules that limit which issues the role "
            "can access."
        ),
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class PylonRoleToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:PylonOrganization)-[:RESOURCE]->(:PylonRole)
class PylonRoleToOrganizationRel(CartographyRelSchema):
    """The organization contains the role."""

    target_node_label: str = "PylonOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: PylonRoleToOrganizationRelProperties = (
        PylonRoleToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class PylonRoleSchema(CartographyNodeSchema):
    """A user role in a Pylon organization, read from `GET /user-roles`.

    Pylon has built-in roles, such as Admin and Member, and custom roles on the
    Enterprise plan. The API doesn't say which roles are built in. API tokens
    with their own identity also hold a role, but the API can't list tokens.
    """

    label: str = "PylonRole"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([PERMISSION_ROLE])
    properties: PylonRoleNodeProperties = PylonRoleNodeProperties()
    sub_resource_relationship: PylonRoleToOrganizationRel = PylonRoleToOrganizationRel()
