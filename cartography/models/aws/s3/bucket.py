from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class S3BucketNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("Name")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("Name")
    region: PropertyRef = PropertyRef("Region")
    arn: PropertyRef = PropertyRef("Arn", extra_index=True)
    creationdate: PropertyRef = PropertyRef("CreationDate")
    # Policy properties
    anonymous_access: PropertyRef = PropertyRef("anonymous_access")
    anonymous_actions: PropertyRef = PropertyRef("anonymous_actions")
    # Encryption properties
    default_encryption: PropertyRef = PropertyRef("default_encryption")
    encryption_algorithm: PropertyRef = PropertyRef("encryption_algorithm")
    encryption_key_id: PropertyRef = PropertyRef("encryption_key_id")
    bucket_key_enabled: PropertyRef = PropertyRef("bucket_key_enabled")
    # Versioning properties
    versioning_status: PropertyRef = PropertyRef("versioning_status")
    mfa_delete: PropertyRef = PropertyRef("mfa_delete")
    # Public access block properties
    block_public_acls: PropertyRef = PropertyRef("block_public_acls")
    ignore_public_acls: PropertyRef = PropertyRef("ignore_public_acls")
    block_public_policy: PropertyRef = PropertyRef("block_public_policy")
    restrict_public_buckets: PropertyRef = PropertyRef("restrict_public_buckets")
    # Ownership controls
    object_ownership: PropertyRef = PropertyRef("object_ownership")
    # Logging properties
    logging_enabled: PropertyRef = PropertyRef("logging_enabled")
    logging_target_bucket: PropertyRef = PropertyRef("logging_target_bucket")


@dataclass(frozen=True)
class S3BucketToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class S3BucketToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: S3BucketToAWSAccountRelProperties = S3BucketToAWSAccountRelProperties()


@dataclass(frozen=True)
class S3BucketSchema(CartographyNodeSchema):
    label: str = "S3Bucket"
    properties: S3BucketNodeProperties = S3BucketNodeProperties()
    sub_resource_relationship: S3BucketToAWSAccountRel = S3BucketToAWSAccountRel()
