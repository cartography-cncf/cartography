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
class AWSSageMakerModelPackageNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("ModelPackageArn")
    arn: PropertyRef = PropertyRef("ModelPackageArn", extra_index=True)
    model_package_name: PropertyRef = PropertyRef("ModelPackageName")
    model_package_group_name: PropertyRef = PropertyRef("ModelPackageGroupName")
    model_package_version: PropertyRef = PropertyRef("ModelPackageVersion")
    model_package_description: PropertyRef = PropertyRef("ModelPackageDescription")
    model_package_status: PropertyRef = PropertyRef("ModelPackageStatus")
    model_approval_status: PropertyRef = PropertyRef("ModelApprovalStatus")
    creation_time: PropertyRef = PropertyRef("CreationTime")
    last_modified_time: PropertyRef = PropertyRef("LastModifiedTime")
    model_artifacts_s3_bucket_id: PropertyRef = PropertyRef("ModelArtifactsS3BucketId")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSSageMakerModelPackageToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSSageMakerModelPackageToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AWSSageMakerModelPackageToAWSAccountRelProperties = (
        AWSSageMakerModelPackageToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class AWSSageMakerModelPackageToModelPackageGroupRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSSageMakerModelPackageToModelPackageGroupRel(CartographyRelSchema):
    target_node_label: str = "AWSSageMakerModelPackageGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"model_package_group_name": PropertyRef("ModelPackageGroupName")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF"
    properties: AWSSageMakerModelPackageToModelPackageGroupRelProperties = (
        AWSSageMakerModelPackageToModelPackageGroupRelProperties()
    )


@dataclass(frozen=True)
class AWSSageMakerModelPackageToS3BucketRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSSageMakerModelPackageToS3BucketRel(CartographyRelSchema):
    target_node_label: str = "S3Bucket"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ModelArtifactsS3BucketId")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "REFERENCES_ARTIFACTS_IN"
    properties: AWSSageMakerModelPackageToS3BucketRelProperties = (
        AWSSageMakerModelPackageToS3BucketRelProperties()
    )


@dataclass(frozen=True)
class AWSSageMakerModelPackageSchema(CartographyNodeSchema):
    label: str = "AWSSageMakerModelPackage"
    properties: AWSSageMakerModelPackageNodeProperties = (
        AWSSageMakerModelPackageNodeProperties()
    )
    sub_resource_relationship: AWSSageMakerModelPackageToAWSAccountRel = (
        AWSSageMakerModelPackageToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AWSSageMakerModelPackageToModelPackageGroupRel(),
            AWSSageMakerModelPackageToS3BucketRel(),
        ]
    )
