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
class S3ObjectNodeProperties(CartographyNodeProperties):
    """
    Properties for S3 Object based on ListObjectsV2 API response
    """

    id: PropertyRef = PropertyRef("ARN")
    arn: PropertyRef = PropertyRef("ARN", extra_index=True)
    key: PropertyRef = PropertyRef("Key", extra_index=True)
    bucket_name: PropertyRef = PropertyRef("BucketName", extra_index=True)
    size: PropertyRef = PropertyRef("Size")
    storage_class: PropertyRef = PropertyRef("StorageClass")
    last_modified: PropertyRef = PropertyRef("LastModified", extra_index=True)
    etag: PropertyRef = PropertyRef("ETag")
    # Owner fields (only present if FetchOwner=true)
    owner_id: PropertyRef = PropertyRef("OwnerId")
    owner_display_name: PropertyRef = PropertyRef("OwnerDisplayName")
    # Checksum field (if present)
    checksum_algorithm: PropertyRef = PropertyRef("ChecksumAlgorithm")
    # Restore status for archived objects (Glacier)
    is_restore_in_progress: PropertyRef = PropertyRef("IsRestoreInProgress")
    restore_expiry_date: PropertyRef = PropertyRef("RestoreExpiryDate")
    # Version fields (if versioning enabled)
    version_id: PropertyRef = PropertyRef("VersionId")
    is_latest: PropertyRef = PropertyRef("IsLatest")
    is_delete_marker: PropertyRef = PropertyRef("IsDeleteMarker")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class S3ObjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class S3ObjectToS3BucketRel(CartographyRelSchema):
    target_node_label: str = "S3Bucket"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("BucketARN")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "STORES"
    properties: S3ObjectRelProperties = S3ObjectRelProperties()


@dataclass(frozen=True)
class S3ObjectToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: S3ObjectRelProperties = S3ObjectRelProperties()


@dataclass(frozen=True)
class S3ObjectToAWSPrincipalRel(CartographyRelSchema):
    target_node_label: str = "AWSPrincipal"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("OwnerId")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "OWNS"
    properties: S3ObjectRelProperties = S3ObjectRelProperties()


@dataclass(frozen=True)
class S3ObjectSchema(CartographyNodeSchema):
    label: str = "S3Object"
    properties: S3ObjectNodeProperties = S3ObjectNodeProperties()
    sub_resource_relationship: S3ObjectToAWSAccountRel = S3ObjectToAWSAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            S3ObjectToS3BucketRel(),
            S3ObjectToAWSPrincipalRel(),
        ],
    )
