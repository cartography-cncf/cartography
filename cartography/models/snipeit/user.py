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
class SnipeitUserNodeProperties(CartographyNodeProperties):
    """
    Ref: https://snipe-it.readme.io/reference/users
    """

    # Common properties
    id: PropertyRef = PropertyRef("id", description="Snipe-IT user ID.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last update.",
    )

    # SnipeIT specific properties
    company: PropertyRef = PropertyRef(
        "company_id.name",
        extra_index=True,
        description="Company linked to the user.",
    )
    email: PropertyRef = PropertyRef(
        "email",
        extra_index=True,
        description="Email address.",
    )
    username: PropertyRef = PropertyRef("username", description="Username.")


@dataclass(frozen=True)
class SnipeitTenantToSnipeitUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnipeitTenant)-[:RESOURCE]->(:SnipeitUser)
class SnipeitTenantToSnipeitUserRel(CartographyRelSchema):
    """The tenant contains the user."""

    target_node_label: str = "SnipeitTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SnipeitTenantToSnipeitUserRelProperties = (
        SnipeitTenantToSnipeitUserRelProperties()
    )


@dataclass(frozen=True)
# (:SnipeitTenant)-[:HAS_USER]->(:SnipeitUser) - Backwards compatibility
class SnipeitTenantToSnipeitUserDeprecatedRel(CartographyRelSchema):
    """Deprecated compatibility edge linking a tenant to its user."""

    target_node_label: str = "SnipeitTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_USER"
    properties: SnipeitTenantToSnipeitUserRelProperties = (
        SnipeitTenantToSnipeitUserRelProperties()
    )


@dataclass(frozen=True)
class SnipeitUserSchema(CartographyNodeSchema):
    """A user account managed by Snipe-IT."""

    label: str = "SnipeitUser"  # The label of the node
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        ["UserAccount"]
    )  # UserAccount label is used for ontology mapping
    properties: SnipeitUserNodeProperties = (
        SnipeitUserNodeProperties()
    )  # An object representing all properties
    sub_resource_relationship: SnipeitTenantToSnipeitUserRel = (
        SnipeitTenantToSnipeitUserRel()
    )
    # DEPRECATED: for backward compatibility, will be removed in v1.0.0
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[SnipeitTenantToSnipeitUserDeprecatedRel()],
    )
