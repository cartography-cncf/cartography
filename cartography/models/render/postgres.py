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
from cartography.models.ontology.labels import DATABASE


@dataclass(frozen=True)
class RenderPostgresNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="ID of the Render Postgres instance."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Name of the Postgres instance."
    )
    owner_id: PropertyRef = PropertyRef(
        "ownerId", description="ID of the owning Render workspace."
    )
    environment_id: PropertyRef = PropertyRef(
        "environmentId",
        extra_index=True,
        description="ID of the environment this database is deployed in.",
    )
    database_name: PropertyRef = PropertyRef(
        "databaseName", description="Name of the underlying Postgres database."
    )
    database_user: PropertyRef = PropertyRef(
        "databaseUser", description="Default database user."
    )
    plan: PropertyRef = PropertyRef("plan", description="Instance plan/size.")
    region: PropertyRef = PropertyRef("region", description="Deployment region.")
    version: PropertyRef = PropertyRef(
        "version", description="Postgres engine version."
    )
    status: PropertyRef = PropertyRef(
        "status", description="Lifecycle status of the database."
    )
    suspended: PropertyRef = PropertyRef(
        "suspended", description="Whether the database is suspended."
    )
    high_availability_enabled: PropertyRef = PropertyRef(
        "highAvailabilityEnabled",
        description="Whether high availability (a standby replica) is enabled.",
    )
    created_at: PropertyRef = PropertyRef(
        "createdAt", description="Time when the database was created."
    )
    updated_at: PropertyRef = PropertyRef(
        "updatedAt", description="Time when the database was last modified."
    )


@dataclass(frozen=True)
class RenderPostgresToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:RenderTenant)-[:RESOURCE]->(:RenderPostgres)
class RenderPostgresToTenantRel(CartographyRelSchema):
    """Connects a Render workspace to a Postgres instance that it contains."""

    target_node_label: str = "RenderTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("OWNER_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: RenderPostgresToTenantRelProperties = (
        RenderPostgresToTenantRelProperties()
    )


@dataclass(frozen=True)
class RenderPostgresToEnvironmentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:RenderEnvironment)-[:CONTAINS]->(:RenderPostgres)
class RenderPostgresToEnvironmentRel(CartographyRelSchema):
    """Connects a Render environment to a Postgres instance deployed within it."""

    target_node_label: str = "RenderEnvironment"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("environmentId")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: RenderPostgresToEnvironmentRelProperties = (
        RenderPostgresToEnvironmentRelProperties()
    )


@dataclass(frozen=True)
class RenderPostgresSchema(CartographyNodeSchema):
    """A Render-managed Postgres database instance."""

    label: str = "RenderPostgres"
    properties: RenderPostgresNodeProperties = RenderPostgresNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([DATABASE])
    sub_resource_relationship: RenderPostgresToTenantRel = RenderPostgresToTenantRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [RenderPostgresToEnvironmentRel()],
    )
