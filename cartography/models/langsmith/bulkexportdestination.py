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
class LangSmithBulkExportDestinationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Destination UUID.")
    name: PropertyRef = PropertyRef(
        "display_name", description="Destination display name."
    )
    destination_type: PropertyRef = PropertyRef(
        "destination_type", description="Storage type, for example s3."
    )
    bucket_name: PropertyRef = PropertyRef(
        "bucket_name", extra_index=True, description="Bucket that receives exports."
    )
    prefix: PropertyRef = PropertyRef("prefix", description="Key prefix for exports.")
    region: PropertyRef = PropertyRef("region", description="Bucket region.")
    endpoint_url: PropertyRef = PropertyRef(
        "endpoint_url",
        description="Custom S3-compatible endpoint. Empty for Amazon S3.",
    )
    aws_role_arn: PropertyRef = PropertyRef(
        "aws_role_arn",
        description="IAM role LangSmith assumes to write exports, when one is configured.",
    )
    credential_fields: PropertyRef = PropertyRef(
        "credential_fields",
        description=(
            "Names of the static credentials stored for the destination, for example "
            "access_key_id. Values are never ingested."
        ),
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Timestamp when the destination was created."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class LangSmithBulkExportDestinationToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:LangSmithWorkspace)-[:RESOURCE]->(:LangSmithBulkExportDestination)
class LangSmithBulkExportDestinationToWorkspaceRel(CartographyRelSchema):
    """Links a bulk export destination to the workspace it belongs to."""

    target_node_label: str = "LangSmithWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: LangSmithBulkExportDestinationToWorkspaceRelProperties = (
        LangSmithBulkExportDestinationToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class LangSmithBulkExportDestinationToS3BucketRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:LangSmithBulkExportDestination)-[:EXPORTS_TO]->(:S3Bucket)
class LangSmithBulkExportDestinationToS3BucketRel(CartographyRelSchema):
    """Links a destination on Amazon S3 to the bucket it writes traces to."""

    target_node_label: str = "S3Bucket"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("aws_bucket_name")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "EXPORTS_TO"
    properties: LangSmithBulkExportDestinationToS3BucketRelProperties = (
        LangSmithBulkExportDestinationToS3BucketRelProperties()
    )


@dataclass(frozen=True)
class LangSmithBulkExportDestinationSchema(CartographyNodeSchema):
    """Object storage that LangSmith bulk-exports a workspace's traces to."""

    label: str = "LangSmithBulkExportDestination"
    properties: LangSmithBulkExportDestinationNodeProperties = (
        LangSmithBulkExportDestinationNodeProperties()
    )
    sub_resource_relationship: LangSmithBulkExportDestinationToWorkspaceRel = (
        LangSmithBulkExportDestinationToWorkspaceRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [LangSmithBulkExportDestinationToS3BucketRel()],
    )
