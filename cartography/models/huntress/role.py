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
class HuntressRoleNodeProperties(CartographyNodeProperties):
    # Huntress exposes no role object: a membership carries a bare `permissions` string.
    # The id is synthesized so that the same permission label granted on the account and
    # on an organization stays two distinct grants.
    id: PropertyRef = PropertyRef(
        "id",
        description=(
            "Synthesized as `<scope>/<account or organization ID>/<permission label>`."
        ),
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description=(
            "Permission label granted by the role: `Admin`, `Security Engineer`, "
            "`User`, `Read-only`, `Finance`, `Marketing`, `Admin-Read-only` or "
            "`Provisioner`."
        ),
    )
    scope: PropertyRef = PropertyRef(
        "scope",
        description="Level the role is granted at: `account` or `org`.",
    )
    organization_id: PropertyRef = PropertyRef(
        "organization_id",
        description="Organization the role is scoped to, or null for an account-wide role.",
    )


@dataclass(frozen=True)
class HuntressRoleToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:HuntressAccount)-[:RESOURCE]->(:HuntressRole)
@dataclass(frozen=True)
class HuntressRoleToAccountRel(CartographyRelSchema):
    """Links a Huntress account to one of the console roles granted within it."""

    target_node_label: str = "HuntressAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: HuntressRoleToAccountRelProperties = (
        HuntressRoleToAccountRelProperties()
    )


@dataclass(frozen=True)
class HuntressRoleSchema(CartographyNodeSchema):
    """A console permission set granted to Huntress users, synthesized from memberships.

    Huntress ships a fixed set of permission labels and returns them as a bare string on
    each membership. Materializing them as nodes rather than a property puts Huntress
    console access into the cross-provider rules that walk
    `(:UserAccount)-[:HAS_ROLE]->(:PermissionRole)`.
    """

    label: str = "HuntressRole"
    properties: HuntressRoleNodeProperties = HuntressRoleNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([PERMISSION_ROLE])
    sub_resource_relationship: HuntressRoleToAccountRel = HuntressRoleToAccountRel()
