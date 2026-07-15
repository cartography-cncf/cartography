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
    id: PropertyRef = PropertyRef(
        "ModelPackageArn", description="The ARN of the Model Package"
    )
    arn: PropertyRef = PropertyRef(
        "ModelPackageArn", extra_index=True, description="The ARN of the Model Package"
    )
    model_package_name: PropertyRef = PropertyRef(
        "ModelPackageName", description="The name of the Model Package"
    )
    model_package_group_name: PropertyRef = PropertyRef(
        "ModelPackageGroupName",
        description="The name of the group this package belongs to",
    )
    model_package_version: PropertyRef = PropertyRef(
        "ModelPackageVersion", description="The version number of the Model Package"
    )
    model_package_description: PropertyRef = PropertyRef(
        "ModelPackageDescription",
        description="Human-readable description of the model package.",
    )
    model_package_status: PropertyRef = PropertyRef(
        "ModelPackageStatus", description="The status of the Model Package"
    )
    model_approval_status: PropertyRef = PropertyRef(
        "ModelApprovalStatus", description="The approval status of the Model Package"
    )
    creation_time: PropertyRef = PropertyRef(
        "CreationTime", description="When the Model Package was created"
    )
    last_modified_time: PropertyRef = PropertyRef(
        "LastModifiedTime",
        description="Timestamp when the model package was last modified.",
    )
    model_artifacts_s3_bucket_id: PropertyRef = PropertyRef(
        "ModelArtifactsS3BucketId",
        description="The S3 bucket ID where model artifacts are stored",
    )
    region: PropertyRef = PropertyRef(
        "Region",
        set_in_kwargs=True,
        description="The AWS region where the Model Package exists",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )


@dataclass(frozen=True)
class AWSSageMakerModelPackageToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSSageMakerModelPackageToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSSageMakerModelPackage`."

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
    "Represents a `MEMBER_OF` relationship from `AWSSageMakerModelPackage` to `AWSSageMakerModelPackageGroup`."

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
    "Represents a `REFERENCES_ARTIFACTS_IN` relationship from `AWSSageMakerModelPackage` to `AWSS3Bucket`."

    target_node_label: str = "AWSS3Bucket"
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
    "Represents an `AWSSageMakerModelPackage` node in the AWS graph."

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
