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
class SnowflakeSequenceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Account-scoped identifier for the sequence."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="The sequence name."
    )
    qualified_name: PropertyRef = PropertyRef(
        "qualified_name",
        extra_index=True,
        description="The fully-qualified name, as DATABASE.SCHEMA.SEQUENCE.",
    )
    database_name: PropertyRef = PropertyRef(
        "database_name",
        extra_index=True,
        description="Name of the database that contains the sequence.",
    )
    schema_name: PropertyRef = PropertyRef(
        "schema_name",
        extra_index=True,
        description="Name of the schema that contains the sequence.",
    )
    start_value: PropertyRef = PropertyRef(
        "start_value", description="First value the sequence produced."
    )
    increment: PropertyRef = PropertyRef(
        "increment", description="Step between successive sequence values."
    )
    next_value: PropertyRef = PropertyRef(
        "next_value", description="Next value the sequence will produce."
    )
    owner: PropertyRef = PropertyRef(
        "owner", description="Name of the role that owns the sequence."
    )
    comment: PropertyRef = PropertyRef("comment", description="Sequence comment.")
    created_on: PropertyRef = PropertyRef(
        "created_on", description="When the sequence was created."
    )


@dataclass(frozen=True)
class SnowflakeSequenceToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeAccount)-[:RESOURCE]->(:SnowflakeSequence)
class SnowflakeSequenceToAccountRel(CartographyRelSchema):
    """A Snowflake account contains the sequence as a resource."""

    target_node_label: str = "SnowflakeAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SnowflakeSequenceToAccountRelProperties = (
        SnowflakeSequenceToAccountRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeSequenceToSchemaRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeSchema)-[:CONTAINS]->(:SnowflakeSequence)
class SnowflakeSequenceToSchemaRel(CartographyRelSchema):
    """A Snowflake schema contains the sequence."""

    target_node_label: str = "SnowflakeSchema"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("parent_schema_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: SnowflakeSequenceToSchemaRelProperties = (
        SnowflakeSequenceToSchemaRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeSequenceSchema(CartographyNodeSchema):
    """Represents a Snowflake sequence, a generator of monotonically increasing numbers."""

    label: str = "SnowflakeSequence"
    properties: SnowflakeSequenceNodeProperties = SnowflakeSequenceNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([SNOWFLAKE_SECURABLE])
    # Scoped to the account, not the schema: cleanup has to be able to delete a
    # sequence whose schema was dropped between syncs.
    sub_resource_relationship: SnowflakeSequenceToAccountRel = (
        SnowflakeSequenceToAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [SnowflakeSequenceToSchemaRel()],
    )
