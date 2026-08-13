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
class SnowflakeSchemaNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Account-scoped identifier for the schema."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="The schema name."
    )
    qualified_name: PropertyRef = PropertyRef(
        "qualified_name",
        extra_index=True,
        description="The fully-qualified schema name, as DATABASE.SCHEMA.",
    )
    database_name: PropertyRef = PropertyRef(
        "database_name",
        extra_index=True,
        description="Name of the database that contains the schema.",
    )
    kind: PropertyRef = PropertyRef(
        "kind", description="The schema kind reported by Snowflake."
    )
    managed_access: PropertyRef = PropertyRef(
        "managed_access",
        description=(
            "Whether the schema uses managed access, which reserves granting on its "
            "objects to the schema owner instead of each object's owner."
        ),
    )
    owner: PropertyRef = PropertyRef(
        "owner", description="Name of the role that owns the schema."
    )
    owner_role_type: PropertyRef = PropertyRef(
        "owner_role_type",
        description="Whether the owner is a ROLE or a DATABASE_ROLE.",
    )
    comment: PropertyRef = PropertyRef("comment", description="Schema comment.")
    options: PropertyRef = PropertyRef(
        "options",
        description="Schema options such as TRANSIENT, as reported by Snowflake.",
    )
    retention_time: PropertyRef = PropertyRef(
        "retention_time",
        description="Days a dropped schema stays recoverable through UNDROP.",
    )
    external_volume: PropertyRef = PropertyRef(
        "external_volume",
        description=(
            "Name of the external volume Iceberg tables created in this schema "
            "default to."
        ),
    )
    catalog: PropertyRef = PropertyRef(
        "catalog",
        description=(
            "Name of the catalog Iceberg tables created in this schema default to."
        ),
    )
    created_on: PropertyRef = PropertyRef(
        "created_on", description="When the schema was created."
    )
    dropped_on: PropertyRef = PropertyRef(
        "dropped_on",
        description="When the schema was dropped, if it is pending purge.",
    )


@dataclass(frozen=True)
class SnowflakeSchemaToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeAccount)-[:RESOURCE]->(:SnowflakeSchema)
class SnowflakeSchemaToAccountRel(CartographyRelSchema):
    """A Snowflake account contains the schema as a resource."""

    target_node_label: str = "SnowflakeAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SnowflakeSchemaToAccountRelProperties = (
        SnowflakeSchemaToAccountRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeSchemaToDatabaseRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeDatabase)-[:CONTAINS]->(:SnowflakeSchema)
class SnowflakeSchemaToDatabaseRel(CartographyRelSchema):
    """A Snowflake database contains the schema."""

    target_node_label: str = "SnowflakeDatabase"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("parent_database_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: SnowflakeSchemaToDatabaseRelProperties = (
        SnowflakeSchemaToDatabaseRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeSchemaToExternalVolumeRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeSchema)-[:DEFAULT_EXTERNAL_VOLUME]->(:SnowflakeExternalVolume)
class SnowflakeSchemaToExternalVolumeRel(CartographyRelSchema):
    """Iceberg tables created in this schema land on this external volume by default.

    The volume points at customer-owned cloud storage, so this edge is how schema
    data reaches an S3, GCS or Azure location.
    """

    target_node_label: str = "SnowflakeExternalVolume"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("external_volume_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "DEFAULT_EXTERNAL_VOLUME"
    properties: SnowflakeSchemaToExternalVolumeRelProperties = (
        SnowflakeSchemaToExternalVolumeRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeSchemaSchema(CartographyNodeSchema):
    """Represents a Snowflake schema, the namespace tables and views live in."""

    label: str = "SnowflakeSchema"
    properties: SnowflakeSchemaNodeProperties = SnowflakeSchemaNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([SNOWFLAKE_SECURABLE])
    # Scoped to the account, not the database: cleanup has to be able to delete a
    # schema whose database was dropped between syncs.
    sub_resource_relationship: SnowflakeSchemaToAccountRel = (
        SnowflakeSchemaToAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            SnowflakeSchemaToDatabaseRel(),
            SnowflakeSchemaToExternalVolumeRel(),
        ],
    )
