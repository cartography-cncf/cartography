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
class RenderEnvGroupNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="ID of the Render environment group."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Name of the environment group."
    )
    owner_id: PropertyRef = PropertyRef(
        "ownerId", description="ID of the owning Render workspace."
    )
    environment_id: PropertyRef = PropertyRef(
        "environmentId",
        extra_index=True,
        description="ID of the environment this group belongs to, if any.",
    )
    created_at: PropertyRef = PropertyRef(
        "createdAt", description="Time when the environment group was created."
    )
    updated_at: PropertyRef = PropertyRef(
        "updatedAt", description="Time when the environment group was last modified."
    )


@dataclass(frozen=True)
class RenderEnvGroupToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:RenderTenant)-[:RESOURCE]->(:RenderEnvGroup)
class RenderEnvGroupToTenantRel(CartographyRelSchema):
    """Connects a Render workspace to an environment group that it contains."""

    target_node_label: str = "RenderTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("OWNER_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: RenderEnvGroupToTenantRelProperties = (
        RenderEnvGroupToTenantRelProperties()
    )


@dataclass(frozen=True)
class RenderEnvGroupToEnvironmentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:RenderEnvironment)-[:CONTAINS]->(:RenderEnvGroup)
class RenderEnvGroupToEnvironmentRel(CartographyRelSchema):
    """Connects a Render environment to an environment group that belongs to it."""

    target_node_label: str = "RenderEnvironment"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("environmentId")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: RenderEnvGroupToEnvironmentRelProperties = (
        RenderEnvGroupToEnvironmentRelProperties()
    )


@dataclass(frozen=True)
class RenderEnvGroupToServiceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:RenderEnvGroup)-[:LINKED_TO]->(:RenderService)
class RenderEnvGroupToServiceRel(CartographyRelSchema):
    """
    Connects an environment group to a service that consumes its env vars/secret files.

    Matched per-row on `service_id`: transform() emits one row per (group, linked service)
    pair (see cartography/intel/render/envgroups.py), so a group linked to several services
    produces several rows sharing the same group `id` - the node MERGEs to one, and each row
    independently creates its own edge to a different service.
    """

    target_node_label: str = "RenderService"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("service_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "LINKED_TO"
    properties: RenderEnvGroupToServiceRelProperties = (
        RenderEnvGroupToServiceRelProperties()
    )


@dataclass(frozen=True)
class RenderEnvGroupSchema(CartographyNodeSchema):
    """
    A Render environment group: shared env vars/secret files linked to one or more services.

    Only group metadata is ingested - the group's env var values and secret file contents are
    never fetched by this module, mirroring the name-only handling of RenderSecretFile.
    """

    label: str = "RenderEnvGroup"
    properties: RenderEnvGroupNodeProperties = RenderEnvGroupNodeProperties()
    sub_resource_relationship: RenderEnvGroupToTenantRel = RenderEnvGroupToTenantRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [RenderEnvGroupToEnvironmentRel(), RenderEnvGroupToServiceRel()],
    )
