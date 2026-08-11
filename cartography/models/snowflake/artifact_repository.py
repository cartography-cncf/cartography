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
from cartography.models.snowflake.extra_labels import SNOWFLAKE_SECURABLE


@dataclass(frozen=True)
class SnowflakeArtifactRepositoryNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Account-scoped identifier for the artifact repository."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Artifact repository name."
    )
    qualified_name: PropertyRef = PropertyRef(
        "qualified_name",
        description="Fully-qualified database.schema.repository name.",
    )
    database_name: PropertyRef = PropertyRef(
        "database_name", description="Database containing the artifact repository."
    )
    schema_name: PropertyRef = PropertyRef(
        "schema_name", description="Schema containing the artifact repository."
    )
    repository_type: PropertyRef = PropertyRef(
        "repository_type",
        description="Kind of package index the repository proxies, such as PIP.",
    )
    api_integration: PropertyRef = PropertyRef(
        "api_integration",
        description="API integration the repository fetches upstream packages through.",
    )
    owner: PropertyRef = PropertyRef(
        "owner", description="Name of the role that owns the artifact repository."
    )
    comment: PropertyRef = PropertyRef(
        "comment", description="Artifact repository comment."
    )
    created_on: PropertyRef = PropertyRef(
        "created_on", description="When the artifact repository was created."
    )


@dataclass(frozen=True)
class SnowflakeArtifactRepositoryToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeAccount)-[:RESOURCE]->(:SnowflakeArtifactRepository)
class SnowflakeArtifactRepositoryToAccountRel(CartographyRelSchema):
    """A Snowflake account contains the artifact repository as a resource."""

    target_node_label: str = "SnowflakeAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SnowflakeArtifactRepositoryToAccountRelProperties = (
        SnowflakeArtifactRepositoryToAccountRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeArtifactRepositoryToSchemaRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeSchema)-[:CONTAINS]->(:SnowflakeArtifactRepository)
class SnowflakeArtifactRepositoryToSchemaRel(CartographyRelSchema):
    """A Snowflake schema holds the artifact repository in its namespace."""

    target_node_label: str = "SnowflakeSchema"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("parent_schema_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: SnowflakeArtifactRepositoryToSchemaRelProperties = (
        SnowflakeArtifactRepositoryToSchemaRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeArtifactRepositoryToApiIntegrationRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeArtifactRepository)-[:USES_INTEGRATION]->(:SnowflakeApiIntegration)
class SnowflakeArtifactRepositoryToApiIntegrationRel(CartographyRelSchema):
    """A Snowflake artifact repository fetches upstream packages through this API integration.

    The integration is what decides which external package index Snowflake will
    pull code from, so it is the control point for a supply-chain risk.
    """

    target_node_label: str = "SnowflakeApiIntegration"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("api_integration_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_INTEGRATION"
    properties: SnowflakeArtifactRepositoryToApiIntegrationRelProperties = (
        SnowflakeArtifactRepositoryToApiIntegrationRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeArtifactRepositorySchema(CartographyNodeSchema):
    """Represents a Snowflake artifact repository: a schema-level proxy to an external package index."""

    label: str = "SnowflakeArtifactRepository"
    properties: SnowflakeArtifactRepositoryNodeProperties = (
        SnowflakeArtifactRepositoryNodeProperties()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([SNOWFLAKE_SECURABLE])
    sub_resource_relationship: SnowflakeArtifactRepositoryToAccountRel = (
        SnowflakeArtifactRepositoryToAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            SnowflakeArtifactRepositoryToSchemaRel(),
            SnowflakeArtifactRepositoryToApiIntegrationRel(),
        ],
    )
