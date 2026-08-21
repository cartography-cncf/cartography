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
class RenderKeyValueNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="ID of the Render Key Value instance."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Name of the Key Value instance."
    )
    owner_id: PropertyRef = PropertyRef(
        "ownerId", description="ID of the owning Render workspace."
    )
    environment_id: PropertyRef = PropertyRef(
        "environmentId",
        extra_index=True,
        description="ID of the environment this instance is deployed in.",
    )
    status: PropertyRef = PropertyRef(
        "status", description="Lifecycle status of the instance."
    )
    region: PropertyRef = PropertyRef("region", description="Deployment region.")
    plan: PropertyRef = PropertyRef("plan", description="Instance plan/size.")
    version: PropertyRef = PropertyRef(
        "version", description="Valkey/Redis-compatible engine version."
    )
    dashboard_url: PropertyRef = PropertyRef(
        "dashboardUrl", description="URL of the instance in the Render dashboard."
    )
    created_at: PropertyRef = PropertyRef(
        "createdAt", description="Time when the instance was created."
    )
    updated_at: PropertyRef = PropertyRef(
        "updatedAt", description="Time when the instance was last modified."
    )


@dataclass(frozen=True)
class RenderKeyValueToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:RenderTenant)-[:RESOURCE]->(:RenderKeyValue)
class RenderKeyValueToTenantRel(CartographyRelSchema):
    """Connects a Render workspace to a Key Value instance that it contains."""

    target_node_label: str = "RenderTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("OWNER_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: RenderKeyValueToTenantRelProperties = (
        RenderKeyValueToTenantRelProperties()
    )


@dataclass(frozen=True)
class RenderKeyValueToEnvironmentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:RenderEnvironment)-[:CONTAINS]->(:RenderKeyValue)
class RenderKeyValueToEnvironmentRel(CartographyRelSchema):
    """Connects a Render environment to a Key Value instance deployed within it."""

    target_node_label: str = "RenderEnvironment"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("environmentId")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: RenderKeyValueToEnvironmentRelProperties = (
        RenderKeyValueToEnvironmentRelProperties()
    )


@dataclass(frozen=True)
class RenderKeyValueSchema(CartographyNodeSchema):
    """A Render Key Value (Valkey/Redis-compatible) instance."""

    label: str = "RenderKeyValue"
    properties: RenderKeyValueNodeProperties = RenderKeyValueNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([DATABASE])
    sub_resource_relationship: RenderKeyValueToTenantRel = RenderKeyValueToTenantRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [RenderKeyValueToEnvironmentRel()],
    )
