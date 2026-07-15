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
class WorkOSRoleNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="WorkOS role ID.")
    slug: PropertyRef = PropertyRef(
        "slug", extra_index=True, description="Unique role slug."
    )
    name: PropertyRef = PropertyRef("name", description="Role name.")
    description: PropertyRef = PropertyRef(
        "description", description="Role description."
    )
    type: PropertyRef = PropertyRef(
        "type", description="Role scope type, such as environment or organization."
    )
    organization_id: PropertyRef = PropertyRef(
        "organization_id", description="ID of the organization that owns the role."
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="RFC 3339 timestamp when the role was created."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="RFC 3339 timestamp when the role was updated."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Timestamp of the last update."
    )


@dataclass(frozen=True)
class WorkOSRoleToEnvironmentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:WorkOSEnvironment)-[:RESOURCE]->(:WorkOSRole)
class WorkOSRoleToEnvironmentRel(CartographyRelSchema):
    """The WorkOS environment contains this role as a resource."""

    target_node_label: str = "WorkOSEnvironment"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKOS_CLIENT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: WorkOSRoleToEnvironmentRelProperties = (
        WorkOSRoleToEnvironmentRelProperties()
    )


@dataclass(frozen=True)
class WorkOSRoleToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:WorkOSRole)<-[:HAS]-(:WorkOSOrganization)
class WorkOSRoleToOrganizationRel(CartographyRelSchema):
    """The WorkOS organization has this role."""

    target_node_label: str = "WorkOSOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("organization_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS"
    properties: WorkOSRoleToOrganizationRelProperties = (
        WorkOSRoleToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class WorkOSRoleSchema(CartographyNodeSchema):
    """A WorkOS role with the canonical PermissionRole label."""

    label: str = "WorkOSRole"
    properties: WorkOSRoleNodeProperties = WorkOSRoleNodeProperties()
    sub_resource_relationship: WorkOSRoleToEnvironmentRel = WorkOSRoleToEnvironmentRel()
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[WorkOSRoleToOrganizationRel()],
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["PermissionRole"])
