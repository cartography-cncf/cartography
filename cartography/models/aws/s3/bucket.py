from dataclasses import dataclass
from typing import Optional

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

# ============================================================================
# Base AWSS3Bucket Schema - Core properties only
# ============================================================================


@dataclass(frozen=True)
class S3BucketNodeProperties(CartographyNodeProperties):
    """Base properties for AWSS3Bucket nodes."""

    id: PropertyRef = PropertyRef("Name", description="Same as `name`, as seen below")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )
    name: PropertyRef = PropertyRef(
        "Name",
        description="The name of the bucket.  This is guaranteed to be [globally unique](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html#S3.Client.list_buckets)",
    )
    region: PropertyRef = PropertyRef(
        "Region",
        description="The region that the bucket is in. Only defined if the S3 bucket has a [location constraint](https://docs.aws.amazon.com/AmazonS3/latest/dev/UsingBucket.html#access-bucket-intro)",
    )
    arn: PropertyRef = PropertyRef(
        "Arn",
        extra_index=True,
        description="Amazon Resource Name (ARN) of this `AWSS3Bucket` node.",
    )
    creationdate: PropertyRef = PropertyRef(
        "CreationDate", description="Date-time when the bucket was created"
    )


@dataclass(frozen=True)
class S3BucketToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class S3BucketToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSS3Bucket`."

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: S3BucketToAWSAccountRelProperties = S3BucketToAWSAccountRelProperties()


@dataclass(frozen=True)
class S3BucketSchema(CartographyNodeSchema):
    "Represents an Amazon Simple Storage Service (S3) bucket."

    # Implementation note:
    # Base schema for AWSS3Bucket nodes with core properties.
    #
    # This is the primary schema that creates the AWSS3Bucket node and its
    # relationship to the AWSAccount. Use composite schemas below to add
    # additional properties without overwriting existing ones.

    label: str = "AWSS3Bucket"
    properties: S3BucketNodeProperties = S3BucketNodeProperties()
    # DEPRECATED: legacy S3Bucket node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["S3Bucket", "ObjectStorage"])
    sub_resource_relationship: S3BucketToAWSAccountRel = S3BucketToAWSAccountRel()


# ============================================================================
# Composite Schemas - Additional properties that merge onto existing AWSS3Bucket
# ============================================================================
# These schemas use the Composite Node Pattern to add properties to AWSS3Bucket
# nodes without affecting other properties. When a fetch fails, we simply
# don't call load() for that composite schema, preserving existing values.
# ============================================================================


@dataclass(frozen=True)
class S3BucketPolicyProperties(CartographyNodeProperties):
    """Properties from bucket policy analysis."""

    id: PropertyRef = PropertyRef("Name", description="Same as `name`, as seen below")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )
    anonymous_access: PropertyRef = PropertyRef(
        "anonymous_access",
        extra_index=True,
        description="True if this bucket has a policy applied to it that allows anonymous access or if it is open to the internet.  These policy determinations are made by using the [policyuniverse](https://github.com/Netflix-Skunkworks/policyuniverse) library.",
    )
    anonymous_actions: PropertyRef = PropertyRef(
        "anonymous_actions",
        description="List of anonymous internet accessible actions that may be run on the bucket.  This list is taken by running [policyuniverse](https://github.com/Netflix-Skunkworks/policyuniverse#internet-accessible-policy) on the policy that applies to the bucket.",
    )


@dataclass(frozen=True)
class S3BucketPolicySchema(CartographyNodeSchema):
    "Represents an Amazon Simple Storage Service (S3) bucket."

    # Implementation note:
    # Composite schema for S3 bucket policy-derived properties.

    label: str = "AWSS3Bucket"
    # DEPRECATED: legacy S3Bucket node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["S3Bucket"])
    properties: S3BucketPolicyProperties = S3BucketPolicyProperties()
    sub_resource_relationship: Optional[CartographyRelSchema] = None


@dataclass(frozen=True)
class S3BucketEncryptionProperties(CartographyNodeProperties):
    """Properties from bucket encryption configuration."""

    id: PropertyRef = PropertyRef("Name", description="Same as `name`, as seen below")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )
    default_encryption: PropertyRef = PropertyRef(
        "default_encryption",
        description="True if this bucket has [default encryption](https://docs.aws.amazon.com/AmazonS3/latest/userguide/bucket-encryption.html) enabled.",
    )
    encryption_algorithm: PropertyRef = PropertyRef(
        "encryption_algorithm",
        description="The encryption algorithm used for default encryption. Only defined if the S3 bucket has default encryption enabled.",
    )
    encryption_key_id: PropertyRef = PropertyRef(
        "encryption_key_id",
        description="The KMS key ID used for default encryption. Only defined if the S3 bucket has SSE-KMS enabled as the default encryption method.",
    )
    bucket_key_enabled: PropertyRef = PropertyRef(
        "bucket_key_enabled",
        description="True if a bucket key is enabled, when using SSE-KMS as the default encryption method.",
    )


@dataclass(frozen=True)
class S3BucketToKMSKeyRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# Canonical ontology edge: (:ObjectStorage)-[:ENCRYPTED_BY]->(:EncryptionKey).
# Created when default encryption uses a customer-managed KMS key and
# `KMSMasterKeyID` is reported as the key ARN.
class S3BucketToKMSKeyRel(CartographyRelSchema):
    "Represents a `ENCRYPTED_BY` relationship from `AWSS3Bucket` to `AWSKMSKey`."

    target_node_label: str = "AWSKMSKey"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("encryption_key_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ENCRYPTED_BY"
    properties: S3BucketToKMSKeyRelProperties = S3BucketToKMSKeyRelProperties()


@dataclass(frozen=True)
# Same canonical edge as above, but matching when `KMSMasterKeyID` is reported as
# a bare key id rather than a full ARN (S3 returns either form depending on how
# the bucket policy was configured). The two matchers are mutually exclusive, so
# a bucket gets at most one ENCRYPTED_BY edge. Alias references (alias/<name>)
# are not resolved here as they point at a AWSKMSAlias node, not a AWSKMSKey.
class S3BucketToKMSKeyByIdRel(CartographyRelSchema):
    "Represents a `ENCRYPTED_BY` relationship from `AWSS3Bucket` to `AWSKMSKey`."

    target_node_label: str = "AWSKMSKey"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("encryption_key_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ENCRYPTED_BY"
    properties: S3BucketToKMSKeyRelProperties = S3BucketToKMSKeyRelProperties()


@dataclass(frozen=True)
class S3BucketEncryptionSchema(CartographyNodeSchema):
    "Represents an Amazon Simple Storage Service (S3) bucket."

    # Implementation note:
    # Composite schema for S3 bucket encryption properties.

    label: str = "AWSS3Bucket"
    # DEPRECATED: legacy S3Bucket node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["S3Bucket"])
    properties: S3BucketEncryptionProperties = S3BucketEncryptionProperties()
    sub_resource_relationship: Optional[CartographyRelSchema] = None
    other_relationships: OtherRelationships = OtherRelationships(
        [
            S3BucketToKMSKeyRel(),
            S3BucketToKMSKeyByIdRel(),
        ]
    )


@dataclass(frozen=True)
class S3BucketVersioningProperties(CartographyNodeProperties):
    """Properties from bucket versioning configuration."""

    id: PropertyRef = PropertyRef("Name", description="Same as `name`, as seen below")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )
    versioning_status: PropertyRef = PropertyRef(
        "versioning_status", description="The versioning state of the bucket."
    )
    mfa_delete: PropertyRef = PropertyRef(
        "mfa_delete",
        description="Specifies whether MFA delete is enabled in the bucket versioning configuration.",
    )


@dataclass(frozen=True)
class S3BucketVersioningSchema(CartographyNodeSchema):
    "Represents an Amazon Simple Storage Service (S3) bucket."

    # Implementation note:
    # Composite schema for S3 bucket versioning properties.

    label: str = "AWSS3Bucket"
    # DEPRECATED: legacy S3Bucket node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["S3Bucket"])
    properties: S3BucketVersioningProperties = S3BucketVersioningProperties()
    sub_resource_relationship: Optional[CartographyRelSchema] = None


@dataclass(frozen=True)
class S3BucketPublicAccessBlockProperties(CartographyNodeProperties):
    """Properties from bucket public access block configuration."""

    id: PropertyRef = PropertyRef("Name", description="Same as `name`, as seen below")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )
    block_public_acls: PropertyRef = PropertyRef(
        "block_public_acls",
        description="Specifies whether Amazon S3 should block public bucket policies for this bucket.",
    )
    ignore_public_acls: PropertyRef = PropertyRef(
        "ignore_public_acls",
        description="Specifies whether Amazon S3 should ignore public ACLs for this bucket and objects in this bucket.",
    )
    block_public_policy: PropertyRef = PropertyRef(
        "block_public_policy",
        description="Whether this `AWSS3Bucket` node is configured to block public policy.",
    )
    restrict_public_buckets: PropertyRef = PropertyRef(
        "restrict_public_buckets",
        description="Specifies whether Amazon S3 should restrict public bucket policies for this bucket.",
    )


@dataclass(frozen=True)
class S3BucketPublicAccessBlockSchema(CartographyNodeSchema):
    "Represents an Amazon Simple Storage Service (S3) bucket."

    # Implementation note:
    # Composite schema for S3 bucket public access block properties.

    label: str = "AWSS3Bucket"
    # DEPRECATED: legacy S3Bucket node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["S3Bucket"])
    properties: S3BucketPublicAccessBlockProperties = (
        S3BucketPublicAccessBlockProperties()
    )
    sub_resource_relationship: Optional[CartographyRelSchema] = None


@dataclass(frozen=True)
class S3BucketOwnershipProperties(CartographyNodeProperties):
    """Properties from bucket ownership controls configuration."""

    id: PropertyRef = PropertyRef("Name", description="Same as `name`, as seen below")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )
    object_ownership: PropertyRef = PropertyRef(
        "object_ownership",
        description="The bucket's [Object Ownership](https://docs.aws.amazon.com/AmazonS3/latest/userguide/about-object-ownership.html) setting. `BucketOwnerEnforced` indicates that ACLs on the bucket and its objects are ignored. `BucketOwnerPreferred` and `ObjectWriter` indicate that ACLs still function; see [the AWS documentation](https://docs.aws.amazon.com/AmazonS3/latest/userguide/about-object-ownership.html#object-ownership-overview) for details.",
    )


@dataclass(frozen=True)
class S3BucketOwnershipSchema(CartographyNodeSchema):
    "Represents an Amazon Simple Storage Service (S3) bucket."

    # Implementation note:
    # Composite schema for S3 bucket ownership properties.

    label: str = "AWSS3Bucket"
    # DEPRECATED: legacy S3Bucket node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["S3Bucket"])
    properties: S3BucketOwnershipProperties = S3BucketOwnershipProperties()
    sub_resource_relationship: Optional[CartographyRelSchema] = None


@dataclass(frozen=True)
class S3BucketLoggingProperties(CartographyNodeProperties):
    """Properties from bucket logging configuration."""

    id: PropertyRef = PropertyRef("Name", description="Same as `name`, as seen below")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )
    logging_enabled: PropertyRef = PropertyRef(
        "logging_enabled",
        description="True if this bucket has [logging enabled](https://docs.aws.amazon.com/AmazonS3/latest/API/API_GetBucketLogging.html) enabled.",
    )
    logging_target_bucket: PropertyRef = PropertyRef(
        "logging_target_bucket",
        description="The name of the target bucket where access logs are stored. Only defined if logging is enabled.",
    )


@dataclass(frozen=True)
class S3BucketLoggingSchema(CartographyNodeSchema):
    "Represents an Amazon Simple Storage Service (S3) bucket."

    # Implementation note:
    # Composite schema for S3 bucket logging properties.

    label: str = "AWSS3Bucket"
    # DEPRECATED: legacy S3Bucket node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["S3Bucket"])
    properties: S3BucketLoggingProperties = S3BucketLoggingProperties()
    sub_resource_relationship: Optional[CartographyRelSchema] = None
