from dataclasses import dataclass

from cartography.models.aws.extra_labels import LEGACY_S3_ACCOUNT_PUBLIC_ACCESS_BLOCK
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
        description="Whether Amazon S3 blocks public access control lists (ACLs) for every bucket and object in the account",
    )
    ignore_public_acls: PropertyRef = PropertyRef(
        "ignore_public_acls",
        description="Whether Amazon S3 ignores public ACLs for every bucket and object in the account",
    )
    block_public_policy: PropertyRef = PropertyRef(
        "block_public_policy",
        description="Whether Amazon S3 blocks public bucket policies for every bucket in the account",
    )
    restrict_public_buckets: PropertyRef = PropertyRef(
        "restrict_public_buckets",
        description="Whether Amazon S3 restricts public policies for every bucket in the account",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class S3AccountPublicAccessBlockRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class S3AccountPublicAccessBlockToAWSAccountRel(CartographyRelSchema):
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
    """Representation of an AWS [S3 Account Public Access Block](https://docs.aws.amazon.com/AmazonS3/latest/dev/access-control-block-public-access.html) configuration, which provides account-level settings to block public access to S3 resources."""

    label: str = "AWSS3AccountPublicAccessBlock"
    # DEPRECATED: legacy S3AccountPublicAccessBlock node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [LEGACY_S3_ACCOUNT_PUBLIC_ACCESS_BLOCK]
    )
    properties: S3AccountPublicAccessBlockNodeProperties = (
        S3AccountPublicAccessBlockNodeProperties()
    )
    sub_resource_relationship: S3AccountPublicAccessBlockToAWSAccountRel = (
        S3AccountPublicAccessBlockToAWSAccountRel()
    )
