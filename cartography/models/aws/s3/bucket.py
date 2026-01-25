from dataclasses import dataclass
from typing import Optional

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher

# ============================================================================
# Base S3Bucket Schema - Core properties only
# ============================================================================


@dataclass(frozen=True)
class S3BucketNodeProperties(CartographyNodeProperties):
    """Base properties for S3Bucket nodes."""

    id: PropertyRef = PropertyRef("Name")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("Name")
    region: PropertyRef = PropertyRef("Region")
    arn: PropertyRef = PropertyRef("Arn", extra_index=True)
    creationdate: PropertyRef = PropertyRef("CreationDate")


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
    """
    Base schema for S3Bucket nodes with core properties.

    This is the primary schema that creates the S3Bucket node and its
    relationship to the AWSAccount. Use composite schemas below to add
    additional properties without overwriting existing ones.
    """

    label: str = "S3Bucket"
    properties: S3BucketNodeProperties = S3BucketNodeProperties()
    sub_resource_relationship: S3BucketToAWSAccountRel = S3BucketToAWSAccountRel()


# ============================================================================
# Composite Schemas - Additional properties that merge onto existing S3Bucket
# ============================================================================
# These schemas use the Composite Node Pattern to add properties to S3Bucket
# nodes without affecting other properties. When a fetch fails, we simply
# don't call load() for that composite schema, preserving existing values.
# ============================================================================


@dataclass(frozen=True)
class S3BucketPolicyProperties(CartographyNodeProperties):
    """Properties from bucket policy analysis."""

    id: PropertyRef = PropertyRef("Name")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    anonymous_access: PropertyRef = PropertyRef("anonymous_access")
    anonymous_actions: PropertyRef = PropertyRef("anonymous_actions")


@dataclass(frozen=True)
class S3BucketPolicySchema(CartographyNodeSchema):
    """Composite schema for S3 bucket policy-derived properties."""

    label: str = "S3Bucket"
    properties: S3BucketPolicyProperties = S3BucketPolicyProperties()
    sub_resource_relationship: Optional[CartographyRelSchema] = None


@dataclass(frozen=True)
class S3BucketEncryptionProperties(CartographyNodeProperties):
    """Properties from bucket encryption configuration."""

    id: PropertyRef = PropertyRef("Name")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    default_encryption: PropertyRef = PropertyRef("default_encryption")
    encryption_algorithm: PropertyRef = PropertyRef("encryption_algorithm")
    encryption_key_id: PropertyRef = PropertyRef("encryption_key_id")
    bucket_key_enabled: PropertyRef = PropertyRef("bucket_key_enabled")


@dataclass(frozen=True)
class S3BucketEncryptionSchema(CartographyNodeSchema):
    """Composite schema for S3 bucket encryption properties."""

    label: str = "S3Bucket"
    properties: S3BucketEncryptionProperties = S3BucketEncryptionProperties()
    sub_resource_relationship: Optional[CartographyRelSchema] = None


@dataclass(frozen=True)
class S3BucketVersioningProperties(CartographyNodeProperties):
    """Properties from bucket versioning configuration."""

    id: PropertyRef = PropertyRef("Name")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    versioning_status: PropertyRef = PropertyRef("versioning_status")
    mfa_delete: PropertyRef = PropertyRef("mfa_delete")


@dataclass(frozen=True)
class S3BucketVersioningSchema(CartographyNodeSchema):
    """Composite schema for S3 bucket versioning properties."""

    label: str = "S3Bucket"
    properties: S3BucketVersioningProperties = S3BucketVersioningProperties()
    sub_resource_relationship: Optional[CartographyRelSchema] = None


@dataclass(frozen=True)
class S3BucketPublicAccessBlockProperties(CartographyNodeProperties):
    """Properties from bucket public access block configuration."""

    id: PropertyRef = PropertyRef("Name")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    block_public_acls: PropertyRef = PropertyRef("block_public_acls")
    ignore_public_acls: PropertyRef = PropertyRef("ignore_public_acls")
    block_public_policy: PropertyRef = PropertyRef("block_public_policy")
    restrict_public_buckets: PropertyRef = PropertyRef("restrict_public_buckets")


@dataclass(frozen=True)
class S3BucketPublicAccessBlockSchema(CartographyNodeSchema):
    """Composite schema for S3 bucket public access block properties."""

    label: str = "S3Bucket"
    properties: S3BucketPublicAccessBlockProperties = (
        S3BucketPublicAccessBlockProperties()
    )
    sub_resource_relationship: Optional[CartographyRelSchema] = None


@dataclass(frozen=True)
class S3BucketOwnershipProperties(CartographyNodeProperties):
    """Properties from bucket ownership controls configuration."""

    id: PropertyRef = PropertyRef("Name")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    object_ownership: PropertyRef = PropertyRef("object_ownership")


@dataclass(frozen=True)
class S3BucketOwnershipSchema(CartographyNodeSchema):
    """Composite schema for S3 bucket ownership properties."""

    label: str = "S3Bucket"
    properties: S3BucketOwnershipProperties = S3BucketOwnershipProperties()
    sub_resource_relationship: Optional[CartographyRelSchema] = None


@dataclass(frozen=True)
class S3BucketLoggingProperties(CartographyNodeProperties):
    """Properties from bucket logging configuration."""

    id: PropertyRef = PropertyRef("Name")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    logging_enabled: PropertyRef = PropertyRef("logging_enabled")
    logging_target_bucket: PropertyRef = PropertyRef("logging_target_bucket")


@dataclass(frozen=True)
class S3BucketLoggingSchema(CartographyNodeSchema):
    """Composite schema for S3 bucket logging properties."""

    label: str = "S3Bucket"
    properties: S3BucketLoggingProperties = S3BucketLoggingProperties()
    sub_resource_relationship: Optional[CartographyRelSchema] = None
