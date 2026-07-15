from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class S3AccountPublicAccessBlockNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Unique identifier in the format: `{account_id}:{region}`"
    )
    account_id: PropertyRef = PropertyRef(
        "account_id", description="The AWS account ID"
    )
    region: PropertyRef = PropertyRef(
        "region", set_in_kwargs=True, description="The AWS region"
    )
    block_public_acls: PropertyRef = PropertyRef(
        "block_public_acls",
        description="Whether Amazon S3 blocks public access control lists (ACLs) for this bucket and objects",
    )
    ignore_public_acls: PropertyRef = PropertyRef(
        "ignore_public_acls",
        description="Whether Amazon S3 ignores public ACLs for this bucket and objects",
    )
    block_public_policy: PropertyRef = PropertyRef(
        "block_public_policy",
        description="Whether Amazon S3 blocks public bucket policies for this bucket",
    )
    restrict_public_buckets: PropertyRef = PropertyRef(
        "restrict_public_buckets",
        description="Whether Amazon S3 restricts public policies for this bucket",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )


@dataclass(frozen=True)
class S3AccountPublicAccessBlockRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class S3AccountPublicAccessBlockToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSS3AccountPublicAccessBlock`."

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: S3AccountPublicAccessBlockRelProperties = (
        S3AccountPublicAccessBlockRelProperties()
    )


@dataclass(frozen=True)
class S3AccountPublicAccessBlockSchema(CartographyNodeSchema):
    "Represents an `AWSS3AccountPublicAccessBlock` node in the AWS graph."

    label: str = "AWSS3AccountPublicAccessBlock"
    # DEPRECATED: legacy S3AccountPublicAccessBlock node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["S3AccountPublicAccessBlock"])
    properties: S3AccountPublicAccessBlockNodeProperties = (
        S3AccountPublicAccessBlockNodeProperties()
    )
    sub_resource_relationship: S3AccountPublicAccessBlockToAWSAccountRel = (
        S3AccountPublicAccessBlockToAWSAccountRel()
    )
