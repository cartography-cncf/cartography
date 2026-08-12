from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class RenderDedicatedIPNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="ID of the Render dedicated IP set.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Name of the dedicated IP set."
    )
    description: PropertyRef = PropertyRef(
        "description", description="Free-form description of the dedicated IP set."
    )
    owner_id: PropertyRef = PropertyRef(
        "ownerId", description="ID of the owning Render workspace."
    )
    region: PropertyRef = PropertyRef("region", description="Region of the dedicated IP set.")
    ips: PropertyRef = PropertyRef(
        "ips", description="Assigned static IPv4 addresses."
    )
    status: PropertyRef = PropertyRef(
        "status",
        description="Lifecycle status: UNKNOWN, CREATING, PENDING, RUNNING, FAILED, DELETING, or DELETED.",
    )
    created_at: PropertyRef = PropertyRef(
        "createdAt", description="Time when the dedicated IP set was created."
    )
    updated_at: PropertyRef = PropertyRef(
        "updatedAt", description="Time when the dedicated IP set was last modified."
    )


@dataclass(frozen=True)
class RenderDedicatedIPToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:RenderTenant)-[:RESOURCE]->(:RenderDedicatedIP)
class RenderDedicatedIPToTenantRel(CartographyRelSchema):
    """Connects a Render workspace to a dedicated IP set that it contains."""

    target_node_label: str = "RenderTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("OWNER_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: RenderDedicatedIPToTenantRelProperties = (
        RenderDedicatedIPToTenantRelProperties()
    )


@dataclass(frozen=True)
class RenderDedicatedIPToEnvironmentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:RenderDedicatedIP)-[:APPLIES_TO]->(:RenderEnvironment)
class RenderDedicatedIPToEnvironmentRel(CartographyRelSchema):
    """
    Connects a dedicated IP set to an environment its outbound traffic applies to.

    Matched per-row on `environment_id`: transform() emits one row per (dedicated IP
    set, associated environment) pair when `environmentIds` is non-empty, mirroring
    RenderEnvGroupToServiceRel's pattern. When `environmentIds` is empty - meaning the
    set applies to every service in the workspace's region rather than specific
    environments - the row carries no environment_id and this edge simply does not fire.
    """

    target_node_label: str = "RenderEnvironment"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("environment_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "APPLIES_TO"
    properties: RenderDedicatedIPToEnvironmentRelProperties = (
        RenderDedicatedIPToEnvironmentRelProperties()
    )


@dataclass(frozen=True)
class RenderDedicatedIPSchema(CartographyNodeSchema):
    """A Render dedicated IP set: static outbound IPv4 addresses for a workspace/region."""

    label: str = "RenderDedicatedIP"
    properties: RenderDedicatedIPNodeProperties = RenderDedicatedIPNodeProperties()
    sub_resource_relationship: RenderDedicatedIPToTenantRel = (
        RenderDedicatedIPToTenantRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [RenderDedicatedIPToEnvironmentRel()],
    )
