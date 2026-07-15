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


@dataclass(frozen=True)
class AWSSageMakerModelNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("ModelArn", description="The ARN of the Model")
    arn: PropertyRef = PropertyRef(
        "ModelArn", extra_index=True, description="The ARN of the Model"
    )
    model_name: PropertyRef = PropertyRef(
        "ModelName", description="The name of the Model"
    )
    creation_time: PropertyRef = PropertyRef(
        "CreationTime", description="When the Model was created"
    )
    execution_role_arn: PropertyRef = PropertyRef(
        "ExecutionRoleArn",
        description="The IAM role ARN that SageMaker assumes to perform operations",
    )
    primary_container_image: PropertyRef = PropertyRef(
        "PrimaryContainerImage",
        description="The Docker image for the primary container",
    )
    model_package_name: PropertyRef = PropertyRef(
        "ModelPackageName",
        description="The Model Package name if the model is based on one",
    )
    model_artifacts_s3_bucket_id: PropertyRef = PropertyRef(
        "ModelArtifactsS3BucketId",
        description="The S3 bucket ID where model artifacts are stored",
    )
    enable_network_isolation: PropertyRef = PropertyRef(
        "EnableNetworkIsolation",
        description="Whether network isolation is enabled for model containers.",
    )
    vpc_config_security_group_ids: PropertyRef = PropertyRef(
        "VpcConfig.SecurityGroupIds",
        description="Identifiers of the VPC config security group linked to this `AWSSageMakerModel` node.",
    )
    vpc_config_subnets: PropertyRef = PropertyRef(
        "VpcConfig.Subnets",
        description="Subnet IDs used by the model's VPC configuration.",
    )
    region: PropertyRef = PropertyRef(
        "Region",
        set_in_kwargs=True,
        description="The AWS region where the Model exists",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )


@dataclass(frozen=True)
class AWSSageMakerModelToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSSageMakerModelToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSSageMakerModel`."

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AWSSageMakerModelToAWSAccountRelProperties = (
        AWSSageMakerModelToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class AWSSageMakerModelToRoleRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSSageMakerModelToRoleRel(CartographyRelSchema):
    "Represents a `HAS_EXECUTION_ROLE` relationship from `AWSSageMakerModel` to `AWSRole`."

    target_node_label: str = "AWSRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("ExecutionRoleArn")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_EXECUTION_ROLE"
    properties: AWSSageMakerModelToRoleRelProperties = (
        AWSSageMakerModelToRoleRelProperties()
    )


@dataclass(frozen=True)
class AWSSageMakerModelToS3BucketRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSSageMakerModelToS3BucketRel(CartographyRelSchema):
    "Represents a `REFERENCES_ARTIFACTS_IN` relationship from `AWSSageMakerModel` to `AWSS3Bucket`."

    target_node_label: str = "AWSS3Bucket"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ModelArtifactsS3BucketId")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "REFERENCES_ARTIFACTS_IN"
    properties: AWSSageMakerModelToS3BucketRelProperties = (
        AWSSageMakerModelToS3BucketRelProperties()
    )


@dataclass(frozen=True)
class AWSSageMakerModelToModelPackageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSSageMakerModelToModelPackageRel(CartographyRelSchema):
    "Represents a `DERIVES_FROM` relationship from `AWSSageMakerModel` to `AWSSageMakerModelPackage`."

    target_node_label: str = "AWSSageMakerModelPackage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("ModelPackageArn")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "DERIVES_FROM"
    properties: AWSSageMakerModelToModelPackageRelProperties = (
        AWSSageMakerModelToModelPackageRelProperties()
    )


@dataclass(frozen=True)
class AWSSageMakerModelSchema(CartographyNodeSchema):
    "Represents an `AWSSageMakerModel` node in the AWS graph."

    label: str = "AWSSageMakerModel"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["AIModel"])
    properties: AWSSageMakerModelNodeProperties = AWSSageMakerModelNodeProperties()
    sub_resource_relationship: AWSSageMakerModelToAWSAccountRel = (
        AWSSageMakerModelToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AWSSageMakerModelToRoleRel(),
            AWSSageMakerModelToS3BucketRel(),
            AWSSageMakerModelToModelPackageRel(),
        ]
    )
