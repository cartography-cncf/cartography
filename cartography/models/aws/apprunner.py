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
class AppRunnerServiceNodeProperties(CartographyNodeProperties):
    access_role_arn: PropertyRef = PropertyRef(
        "AccessRoleArn",
        description="ARN of the IAM role App Runner uses to pull the source image from ECR. Only set for image-based services in a private ECR repository",
    )
    arn: PropertyRef = PropertyRef(
        "ServiceArn",
        extra_index=True,
        description="The Amazon Resource Name (ARN) of the App Runner service",
    )
    auto_deployments_enabled: PropertyRef = PropertyRef(
        "AutoDeploymentsEnabled",
        description="Whether App Runner automatically redeploys the service when the source image or code changes",
    )
    code_repository_url: PropertyRef = PropertyRef(
        "CodeRepositoryUrl",
        description="URL of the source code repository the service builds from. Only set for source-code-based services",
    )
    cpu: PropertyRef = PropertyRef(
        "Cpu",
        description="Number of CPU units reserved for each instance of the service",
    )
    created_at: PropertyRef = PropertyRef(
        "CreatedAt", description="Time at which the App Runner service was created"
    )
    egress_type: PropertyRef = PropertyRef(
        "EgressType",
        description="Type of egress the service uses for outbound traffic, either DEFAULT for the public internet or VPC for a VPC connector",
    )
    id: PropertyRef = PropertyRef(
        "ServiceArn", description="The ARN of the App Runner service"
    )
    image_identifier: PropertyRef = PropertyRef(
        "ImageIdentifier",
        description="Identifier of the source image the service runs, in the form of an ECR image URI. Only set for image-based services",
    )
    instance_role_arn: PropertyRef = PropertyRef(
        "InstanceRoleArn",
        description="ARN of the IAM role that provides permissions to the running service, equivalent to a task role",
    )
    is_publicly_accessible: PropertyRef = PropertyRef(
        "IsPubliclyAccessible",
        description="Whether the service is reachable from the public internet. False means it is only reachable through a VPC ingress connection",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    memory: PropertyRef = PropertyRef(
        "Memory",
        description="Amount of memory reserved for each instance of the service",
    )
    name: PropertyRef = PropertyRef(
        "ServiceName",
        description="The customer-supplied name of the App Runner service",
    )
    region: PropertyRef = PropertyRef(
        "Region", set_in_kwargs=True, description="The region of the App Runner service"
    )
    service_url: PropertyRef = PropertyRef(
        "ServiceUrl",
        description="Subdomain URL that App Runner generated for this service. The URL is unpredictable and only resolves when the service is publicly accessible",
    )
    status: PropertyRef = PropertyRef(
        "Status",
        description="Current state of the service, for example RUNNING, PAUSED, CREATE_FAILED or DELETED",
    )
    updated_at: PropertyRef = PropertyRef(
        "UpdatedAt",
        description="Time at which the App Runner service was last updated",
    )


@dataclass(frozen=True)
class AppRunnerServiceToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AWSAppRunnerService)<-[:RESOURCE]-(:AWSAccount)
class AppRunnerServiceToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AppRunnerServiceToAWSAccountRelProperties = (
        AppRunnerServiceToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class AppRunnerServiceToAWSRoleRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AWSAppRunnerService)-[:USES_ACCESS_ROLE]->(:AWSRole)
class AppRunnerServiceToAccessRoleRel(CartographyRelSchema):
    target_node_label: str = "AWSRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("AccessRoleArn")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_ACCESS_ROLE"
    properties: AppRunnerServiceToAWSRoleRelProperties = (
        AppRunnerServiceToAWSRoleRelProperties()
    )


@dataclass(frozen=True)
# (:AWSAppRunnerService)-[:USES_INSTANCE_ROLE]->(:AWSRole)
class AppRunnerServiceToInstanceRoleRel(CartographyRelSchema):
    target_node_label: str = "AWSRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("InstanceRoleArn")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_INSTANCE_ROLE"
    properties: AppRunnerServiceToAWSRoleRelProperties = (
        AppRunnerServiceToAWSRoleRelProperties()
    )


@dataclass(frozen=True)
class AppRunnerServiceSchema(CartographyNodeSchema):
    label: str = "AWSAppRunnerService"
    properties: AppRunnerServiceNodeProperties = AppRunnerServiceNodeProperties()
    sub_resource_relationship: AppRunnerServiceToAWSAccountRel = (
        AppRunnerServiceToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AppRunnerServiceToAccessRoleRel(),
            AppRunnerServiceToInstanceRoleRel(),
        ],
    )
