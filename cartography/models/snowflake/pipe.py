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
class SnowflakePipeNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Account-scoped identifier for the pipe."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", extra_index=True, description="Pipe name.")
    qualified_name: PropertyRef = PropertyRef(
        "qualified_name",
        description="Fully-qualified database.schema.pipe name.",
    )
    database_name: PropertyRef = PropertyRef(
        "database_name", description="Database containing the pipe."
    )
    schema_name: PropertyRef = PropertyRef(
        "schema_name", description="Schema containing the pipe."
    )
    definition: PropertyRef = PropertyRef(
        "definition",
        description="The COPY INTO statement the pipe runs for each ingested file.",
    )
    pattern: PropertyRef = PropertyRef(
        "pattern",
        description="Regular expression limiting which staged file paths the pipe ingests.",
    )
    integration: PropertyRef = PropertyRef(
        "integration",
        description="Notification integration the pipe reads its event queue from.",
    )
    auto_ingest: PropertyRef = PropertyRef(
        "auto_ingest",
        description=(
            "Whether the pipe loads files automatically from cloud storage event "
            "notifications rather than waiting for an explicit REST call."
        ),
    )
    aws_sns_topic: PropertyRef = PropertyRef(
        "aws_sns_topic",
        description="ARN of the SNS topic that notifies the pipe of new files.",
    )
    error_integration: PropertyRef = PropertyRef(
        "error_integration",
        description="Notification integration that receives the pipe's error notifications.",
    )
    invalid_reason: PropertyRef = PropertyRef(
        "invalid_reason",
        description=(
            "Why Snowflake considers the pipe unusable, for example a dropped stage "
            "or target table. Null while the pipe is healthy."
        ),
    )
    owner: PropertyRef = PropertyRef(
        "owner", description="Name of the role that owns the pipe."
    )
    comment: PropertyRef = PropertyRef("comment", description="Pipe comment.")
    created_on: PropertyRef = PropertyRef(
        "created_on", description="When the pipe was created."
    )


@dataclass(frozen=True)
class SnowflakePipeToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeAccount)-[:RESOURCE]->(:SnowflakePipe)
class SnowflakePipeToAccountRel(CartographyRelSchema):
    """A Snowflake account contains the pipe as a resource."""

    target_node_label: str = "SnowflakeAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SnowflakePipeToAccountRelProperties = (
        SnowflakePipeToAccountRelProperties()
    )


@dataclass(frozen=True)
class SnowflakePipeToSchemaRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeSchema)-[:CONTAINS]->(:SnowflakePipe)
class SnowflakePipeToSchemaRel(CartographyRelSchema):
    """A Snowflake schema holds the pipe in its namespace."""

    target_node_label: str = "SnowflakeSchema"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("parent_schema_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: SnowflakePipeToSchemaRelProperties = (
        SnowflakePipeToSchemaRelProperties()
    )


@dataclass(frozen=True)
class SnowflakePipeToIntegrationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakePipe)-[:USES_INTEGRATION]->(:SnowflakeNotificationIntegration)
class SnowflakePipeToIntegrationRel(CartographyRelSchema):
    """A Snowflake pipe reads its file-arrival events through this notification integration."""

    target_node_label: str = "SnowflakeNotificationIntegration"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("integration_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_INTEGRATION"
    properties: SnowflakePipeToIntegrationRelProperties = (
        SnowflakePipeToIntegrationRelProperties()
    )


@dataclass(frozen=True)
class SnowflakePipeToSnsTopicRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakePipe)-[:NOTIFIES]->(:AWSSNSTopic)
class SnowflakePipeToSnsTopicRel(CartographyRelSchema):
    """A Snowflake pipe is driven by file-arrival notifications from this SNS topic.

    Joining the pipe to the topic the aws module already ingested is what makes an
    ingestion path traceable from the S3 bucket that receives a file all the way
    to the Snowflake table it lands in.
    """

    target_node_label: str = "AWSSNSTopic"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("aws_sns_topic")},
    )
    # INWARD, so the edge reads (:AWSSNSTopic)-[:NOTIFIES]->(:SnowflakePipe).
    # Everywhere else in the codebase NOTIFIES means the source sends notifications to
    # the target, and an auto-ingest pipe is the *recipient*: the topic tells it a file
    # has arrived. Pointing the edge the other way would invert the data flow the
    # ingestion path is meant to show.
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "NOTIFIES"
    properties: SnowflakePipeToSnsTopicRelProperties = (
        SnowflakePipeToSnsTopicRelProperties()
    )


@dataclass(frozen=True)
class SnowflakePipeSchema(CartographyNodeSchema):
    """Represents a Snowflake pipe: a continuous COPY that loads staged files into a table."""

    label: str = "SnowflakePipe"
    properties: SnowflakePipeNodeProperties = SnowflakePipeNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([SNOWFLAKE_SECURABLE])
    sub_resource_relationship: SnowflakePipeToAccountRel = SnowflakePipeToAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            SnowflakePipeToSchemaRel(),
            SnowflakePipeToIntegrationRel(),
            SnowflakePipeToSnsTopicRel(),
        ],
    )
