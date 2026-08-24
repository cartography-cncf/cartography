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

# Deliberately no `Tag` ontology label here: the canonical Tag concept is a
# key/value pair, whereas a Snowflake tag is only the *definition* of a key and
# carries no value of its own, so labelling it Tag would misrepresent the data.


@dataclass(frozen=True)
class SnowflakeTagNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Account-scoped identifier for the tag."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", extra_index=True, description="Tag name.")
    qualified_name: PropertyRef = PropertyRef(
        "qualified_name",
        description="Fully-qualified database.schema.tag name.",
    )
    database_name: PropertyRef = PropertyRef(
        "database_name", description="Database containing the tag."
    )
    schema_name: PropertyRef = PropertyRef(
        "schema_name", description="Schema containing the tag."
    )
    allowed_values: PropertyRef = PropertyRef(
        "allowed_values",
        description=(
            "Values the tag may be set to. Empty when the tag accepts any string, "
            "which is what makes a governance tag hard to rely on."
        ),
    )
    owner: PropertyRef = PropertyRef(
        "owner", description="Name of the role that owns the tag."
    )
    comment: PropertyRef = PropertyRef("comment", description="Tag comment.")
    created_on: PropertyRef = PropertyRef(
        "created_on", description="When the tag was created."
    )


@dataclass(frozen=True)
class SnowflakeTagToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeAccount)-[:RESOURCE]->(:SnowflakeTag)
class SnowflakeTagToAccountRel(CartographyRelSchema):
    """A Snowflake account contains the tag as a resource."""

    target_node_label: str = "SnowflakeAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SnowflakeTagToAccountRelProperties = (
        SnowflakeTagToAccountRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeTagToSchemaRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeSchema)-[:CONTAINS]->(:SnowflakeTag)
class SnowflakeTagToSchemaRel(CartographyRelSchema):
    """A Snowflake schema holds the tag definition in its namespace."""

    target_node_label: str = "SnowflakeSchema"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("parent_schema_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: SnowflakeTagToSchemaRelProperties = SnowflakeTagToSchemaRelProperties()


@dataclass(frozen=True)
class SnowflakeTagSchema(CartographyNodeSchema):
    """Represents a Snowflake tag definition: a governance key that can later be attached to objects and columns."""

    label: str = "SnowflakeTag"
    properties: SnowflakeTagNodeProperties = SnowflakeTagNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([SNOWFLAKE_SECURABLE])
    sub_resource_relationship: SnowflakeTagToAccountRel = SnowflakeTagToAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            SnowflakeTagToSchemaRel(),
        ],
    )
