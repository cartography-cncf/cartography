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
class AWSSageMakerModelNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("ModelArn")
    arn: PropertyRef = PropertyRef("ModelArn", extra_index=True)
    model_name: PropertyRef = PropertyRef("ModelName")
    creation_time: PropertyRef = PropertyRef("CreationTime")
    execution_role_arn: PropertyRef = PropertyRef("ExecutionRoleArn")
    primary_container_image: PropertyRef = PropertyRef("PrimaryContainerImage")
    model_package_name: PropertyRef = PropertyRef("ModelPackageName")
    model_artifacts_s3_bucket_id: PropertyRef = PropertyRef("ModelArtifactsS3BucketId")
    enable_network_isolation: PropertyRef = PropertyRef("EnableNetworkIsolation")
    vpc_config_security_group_ids: PropertyRef = PropertyRef(
        "VpcConfig.SecurityGroupIds"
    )
    vpc_config_subnets: PropertyRef = PropertyRef("VpcConfig.Subnets")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSSageMakerModelToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSSageMakerModelToAWSAccountRel(CartographyRelSchema):
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
    target_node_label: str = "S3Bucket"
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
    label: str = "AWSSageMakerModel"
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
