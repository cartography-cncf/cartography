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
class AppRunnerServiceNodeProperties(CartographyNodeProperties):
    access_role_arn: PropertyRef = PropertyRef("AccessRoleArn")
    arn: PropertyRef = PropertyRef("ServiceArn", extra_index=True)
    auto_deployments_enabled: PropertyRef = PropertyRef("AutoDeploymentsEnabled")
    cpu: PropertyRef = PropertyRef("Cpu")
    created_at: PropertyRef = PropertyRef("CreatedAt")
    egress_type: PropertyRef = PropertyRef("EgressType")
    id: PropertyRef = PropertyRef("ServiceId")
    image_identifier: PropertyRef = PropertyRef("ImageIdentifier")
    instance_role_arn: PropertyRef = PropertyRef("InstanceRoleArn")
    is_publicly_accessible: PropertyRef = PropertyRef("IsPubliclyAccessible")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    memory: PropertyRef = PropertyRef("Memory")
    name: PropertyRef = PropertyRef("ServiceName")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    service_url: PropertyRef = PropertyRef("ServiceUrl")
    status: PropertyRef = PropertyRef("Status")
    updated_at: PropertyRef = PropertyRef("UpdatedAt")


@dataclass(frozen=True)
class AppRunnerServiceToAWSAccountRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AppRunnerService)<-[:RESOURCE]-(:AWSAccount)
class AppRunnerServiceToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AppRunnerServiceToAWSAccountRelRelProperties = (
        AppRunnerServiceToAWSAccountRelRelProperties()
    )


@dataclass(frozen=True)
class AppRunnerServiceSchema(CartographyNodeSchema):
    label: str = "AppRunnerService"
    properties: AppRunnerServiceNodeProperties = AppRunnerServiceNodeProperties()
    sub_resource_relationship: AppRunnerServiceToAWSAccountRel = (
        AppRunnerServiceToAWSAccountRel()
    )
