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
class RenderBlueprintNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="ID of the Render blueprint.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Name of the blueprint."
    )
    owner_id: PropertyRef = PropertyRef(
        "ownerId", description="ID of the owning Render workspace."
    )
    status: PropertyRef = PropertyRef(
        "status", description="Sync status of the blueprint, e.g. `synced`, `created`."
    )
    auto_sync: PropertyRef = PropertyRef(
        "autoSync",
        description="Whether the blueprint automatically syncs on repo push.",
    )
    repo: PropertyRef = PropertyRef(
        "repo", description="URL of the source repository backing this blueprint."
    )
    branch: PropertyRef = PropertyRef(
        "branch", description="Repository branch this blueprint tracks."
    )
    path: PropertyRef = PropertyRef(
        "path", description="Path to the render.yaml file within the repository."
    )
    last_sync: PropertyRef = PropertyRef(
        "lastSync", description="Time of the blueprint's last sync."
    )


@dataclass(frozen=True)
class RenderBlueprintToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:RenderTenant)-[:RESOURCE]->(:RenderBlueprint)
class RenderBlueprintToTenantRel(CartographyRelSchema):
    """Connects a Render workspace to a blueprint that it contains."""

    target_node_label: str = "RenderTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("OWNER_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: RenderBlueprintToTenantRelProperties = (
        RenderBlueprintToTenantRelProperties()
    )


# A single RenderBlueprint row only ever has one of service_id / postgres_id /
# key_value_id / env_group_id populated (see cartography/intel/render/blueprints.py);
# the other three matchers below are simply absent on that row, so only the one
# matching target label produces an edge. This mirrors RenderIPAllowRule's optional-
# match pattern.


@dataclass(frozen=True)
class RenderBlueprintToServiceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:RenderBlueprint)-[:CONTAINS]->(:RenderService)
class RenderBlueprintToServiceRel(CartographyRelSchema):
    """Connects a blueprint to a service it manages."""

    target_node_label: str = "RenderService"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("service_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CONTAINS"
    properties: RenderBlueprintToServiceRelProperties = (
        RenderBlueprintToServiceRelProperties()
    )


@dataclass(frozen=True)
class RenderBlueprintToPostgresRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:RenderBlueprint)-[:CONTAINS]->(:RenderPostgres)
class RenderBlueprintToPostgresRel(CartographyRelSchema):
    """Connects a blueprint to a Postgres instance it manages."""

    target_node_label: str = "RenderPostgres"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("postgres_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CONTAINS"
    properties: RenderBlueprintToPostgresRelProperties = (
        RenderBlueprintToPostgresRelProperties()
    )


@dataclass(frozen=True)
class RenderBlueprintToKeyValueRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:RenderBlueprint)-[:CONTAINS]->(:RenderKeyValue)
class RenderBlueprintToKeyValueRel(CartographyRelSchema):
    """Connects a blueprint to a Key Value instance it manages."""

    target_node_label: str = "RenderKeyValue"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("key_value_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CONTAINS"
    properties: RenderBlueprintToKeyValueRelProperties = (
        RenderBlueprintToKeyValueRelProperties()
    )


@dataclass(frozen=True)
class RenderBlueprintToEnvGroupRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:RenderBlueprint)-[:CONTAINS]->(:RenderEnvGroup)
class RenderBlueprintToEnvGroupRel(CartographyRelSchema):
    """Connects a blueprint to an environment group it manages."""

    target_node_label: str = "RenderEnvGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("env_group_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CONTAINS"
    properties: RenderBlueprintToEnvGroupRelProperties = (
        RenderBlueprintToEnvGroupRelProperties()
    )


@dataclass(frozen=True)
class RenderBlueprintSchema(CartographyNodeSchema):
    """
    A Render blueprint (Infrastructure as Code definition, `render.yaml`) that manages
    one or more services, Postgres instances, Key Value instances, and/or environment
    groups. Blueprint resources of a type this module doesn't model (e.g.
    `artifact_source`) are not linked - see blueprints.py.
    """

    label: str = "RenderBlueprint"
    properties: RenderBlueprintNodeProperties = RenderBlueprintNodeProperties()
    sub_resource_relationship: RenderBlueprintToTenantRel = RenderBlueprintToTenantRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            RenderBlueprintToServiceRel(),
            RenderBlueprintToPostgresRel(),
            RenderBlueprintToKeyValueRel(),
            RenderBlueprintToEnvGroupRel(),
        ],
    )
