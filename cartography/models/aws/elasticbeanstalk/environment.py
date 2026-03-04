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
class ElasticBeanstalkEnvironmentNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("EnvironmentId")
    arn: PropertyRef = PropertyRef("EnvironmentArn", extra_index=True)
    environment_name: PropertyRef = PropertyRef("EnvironmentName")
    application_name: PropertyRef = PropertyRef("ApplicationName")
    version_label: PropertyRef = PropertyRef("VersionLabel")
    solution_stack_name: PropertyRef = PropertyRef("SolutionStackName")
    platform_arn: PropertyRef = PropertyRef("PlatformArn")
    endpoint_url: PropertyRef = PropertyRef("EndpointURL")
    cname: PropertyRef = PropertyRef("CNAME")
    status: PropertyRef = PropertyRef("Status")
    abortable_operation_in_progress: PropertyRef = PropertyRef(
        "AbortableOperationInProgress"
    )
    health: PropertyRef = PropertyRef("Health")
    health_status: PropertyRef = PropertyRef("HealthStatus")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:AWSAccount) -[:RESOURCE]-> (:ElasticBeanstalkEnvironment)


@dataclass(frozen=True)
class ElasticBeanstalkEnvironmentToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ElasticBeanstalkEnvironmentToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ElasticBeanstalkEnvironmentToAWSAccountRelProperties = (
        ElasticBeanstalkEnvironmentToAWSAccountRelProperties()
    )


# (:ElasticBeanstalkEnvironment) -[:HAS_INSTANCE]-> (:EC2Instance)


@dataclass(frozen=True)
class ElasticBeanstalkToInstanceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ElasticBeanstalkToInstanceRel(CartographyRelSchema):
    target_node_label: str = "EC2Instance"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        # This INSTANCE_IDS field is set by transform_elasticbeanstalk_environments
        {"id": PropertyRef("INSTANCE_IDS", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_INSTANCE"
    properties: ElasticBeanstalkToInstanceRelProperties = (
        ElasticBeanstalkToInstanceRelProperties()
    )


# (:ElasticBeanstalkEnvironment) -[:HAS_AUTO_SCALING_GROUP]-> (:AutoScalingGroup)


@dataclass(frozen=True)
class ElasticBeanstalkToAutoScalingGroupRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ElasticBeanstalkToAutoScalingGroupRel(CartographyRelSchema):
    target_node_label: str = "AutoScalingGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        # This ASG_NAMES field is set by transform_elasticbeanstalk_environments
        {"name": PropertyRef("ASG_NAMES", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_AUTO_SCALING_GROUP"
    properties: ElasticBeanstalkToAutoScalingGroupRelProperties = (
        ElasticBeanstalkToAutoScalingGroupRelProperties()
    )


# (:ElasticBeanstalkEnvironment) -[:HAS_LAUNCH_CONFIG]-> (:LaunchConfiguration)


@dataclass(frozen=True)
class ElasticBeanstalkToLaunchConfigurationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ElasticBeanstalkToLaunchConfigurationRel(CartographyRelSchema):
    target_node_label: str = "LaunchConfiguration"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        # This LAUNCHCONFIG_NAMES field is set by transform_elasticbeanstalk_environments
        {"name": PropertyRef("LAUNCHCONFIG_NAMES", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_LAUNCH_CONFIG"
    properties: ElasticBeanstalkToLaunchConfigurationRelProperties = (
        ElasticBeanstalkToLaunchConfigurationRelProperties()
    )


# (:ElasticBeanstalkEnvironment) -[:HAS_LAUNCH_TEMPLATE]-> (:LaunchTemplate)


@dataclass(frozen=True)
class ElasticBeanstalkToLaunchTemplateRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ElasticBeanstalkToLaunchTemplateRel(CartographyRelSchema):
    target_node_label: str = "LaunchTemplate"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        # This LAUNCHTEMPLATE_IDS field is set by transform_elasticbeanstalk_environments
        {"id": PropertyRef("LAUNCHTEMPLATE_IDS", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_LAUNCH_TEMPLATE"
    properties: ElasticBeanstalkToLaunchTemplateRelProperties = (
        ElasticBeanstalkToLaunchTemplateRelProperties()
    )


# (:ElasticBeanstalkEnvironment) -[:HAS_LOAD_BALANCER]-> (:AWSLoadBalancer)


@dataclass(frozen=True)
class ElasticBeanstalkToAWSLoadBalancerRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ElasticBeanstalkToAWSLoadBalancerRel(CartographyRelSchema):
    target_node_label: str = "AWSLoadBalancer"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        # This LOADBALANCER_NAMES field is set by transform_elasticbeanstalk_environments
        {"arn": PropertyRef("LOADBALANCER_NAMES", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_LOAD_BALANCER"
    properties: ElasticBeanstalkToAWSLoadBalancerRelProperties = (
        ElasticBeanstalkToAWSLoadBalancerRelProperties()
    )


# (:ElasticBeanstalkEnvironment) -[:HAS_LOAD_BALANCER]-> (:AWSLoadBalancerV2)


@dataclass(frozen=True)
class ElasticBeanstalkToAWSLoadBalancerV2RelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ElasticBeanstalkToAWSLoadBalancerV2Rel(CartographyRelSchema):
    target_node_label: str = "AWSLoadBalancerV2"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        # This LOADBALANCER_NAMES field is set by transform_elasticbeanstalk_environments
        {"arn": PropertyRef("LOADBALANCER_NAMES", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_LOAD_BALANCER"
    properties: ElasticBeanstalkToAWSLoadBalancerV2RelProperties = (
        ElasticBeanstalkToAWSLoadBalancerV2RelProperties()
    )


# (:ElasticBeanstalkEnvironment) -[:HAS_QUEUE]-> (:SQSQueue)


@dataclass(frozen=True)
class ElasticBeanstalkToQueueRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ElasticBeanstalkToQueueRel(CartographyRelSchema):
    target_node_label: str = "SQSQueue"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        # This QUEUE_URLS field is set by transform_elasticbeanstalk_environments
        {"url": PropertyRef("QUEUE_URLS", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_SQS_QUEUE"
    properties: ElasticBeanstalkToQueueRelProperties = (
        ElasticBeanstalkToQueueRelProperties()
    )


# Note: No relationship is built for TRIGGER_NAMES, because we don't currently have them in the AWS model


@dataclass(frozen=True)
class ElasticBeanstalkEnvironmentSchema(CartographyNodeSchema):
    label: str = "ElasticBeanstalkEnvironment"
    properties: ElasticBeanstalkEnvironmentNodeProperties = (
        ElasticBeanstalkEnvironmentNodeProperties()
    )
    sub_resource_relationship: ElasticBeanstalkEnvironmentToAWSAccountRel = (
        ElasticBeanstalkEnvironmentToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ElasticBeanstalkToInstanceRel(),
            ElasticBeanstalkToAutoScalingGroupRel(),
            ElasticBeanstalkToLaunchConfigurationRel(),
            ElasticBeanstalkToLaunchTemplateRel(),
            ElasticBeanstalkToAWSLoadBalancerRel(),
            ElasticBeanstalkToAWSLoadBalancerV2Rel(),
            ElasticBeanstalkToQueueRel(),
        ],
    )
