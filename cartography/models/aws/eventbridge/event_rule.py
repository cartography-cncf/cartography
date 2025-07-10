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
class EventRuleNodeProperties(CartographyNodeProperties):
    """Properties for CloudWatch Event Rule nodes"""

    id: PropertyRef = PropertyRef("Arn")
    arn: PropertyRef = PropertyRef("Arn", extra_index=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)

    name: PropertyRef = PropertyRef("Name", extra_index=True)
    state: PropertyRef = PropertyRef("State")
    description: PropertyRef = PropertyRef("Description")
    event_pattern: PropertyRef = PropertyRef("EventPattern")
    schedule_expression: PropertyRef = PropertyRef("ScheduleExpression")
    role_arn: PropertyRef = PropertyRef("RoleArn")
    event_bus_name: PropertyRef = PropertyRef("EventBusName")
    managed_by: PropertyRef = PropertyRef("ManagedBy")
    created_by: PropertyRef = PropertyRef("CreatedBy")

    # removed target arn lists

    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)


@dataclass(frozen=True)
class _EventRuleRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EventRuleToAWSAccountRel(CartographyRelSchema):
    """(:EventRule)<-[:RESOURCE]-(:AWSAccount)"""

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: _EventRuleRelProperties = _EventRuleRelProperties()


@dataclass(frozen=True)
class EventRuleToIAMRoleRel(CartographyRelSchema):
    """(:EventRule)-[:USES_ROLE]->(:AWSRole)
    Important for security analysis - shows which role the rule assumes
    when invoking targets.
    """

    target_node_label: str = "AWSRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("RoleArn")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_ROLE"
    properties: _EventRuleRelProperties = _EventRuleRelProperties()


@dataclass(frozen=True)
class EventRuleToLambdaFunctionRel(CartographyRelSchema):
    """(:EventRule)-[:TRIGGERS]->(:AWSLambda)
    Most common EventBridge target - Lambda functions.
    Note: Lambda functions store their ARN in the 'id' field.
    """

    target_node_label: str = "AWSLambda"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("lambda_functions_arns", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "TRIGGERS"
    properties: _EventRuleRelProperties = _EventRuleRelProperties()


@dataclass(frozen=True)
class EventRuleToSNSTopicRel(CartographyRelSchema):
    """(:EventRule)-[:PUBLISHES_TO]->(:SNSTopic)
    Second most common target - SNS topics for notifications.
    """

    target_node_label: str = "SNSTopic"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("sns_topics_arns", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "PUBLISHES_TO"
    properties: _EventRuleRelProperties = _EventRuleRelProperties()


@dataclass(frozen=True)
class EventRuleToSQSQueueRel(CartographyRelSchema):
    """(:EventRule)-[:SENDS_TO]->(:SQSQueue)
    Third most common target - SQS queues for async processing.
    """

    target_node_label: str = "SQSQueue"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("sqs_queues_arns", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "SENDS_TO"
    properties: _EventRuleRelProperties = _EventRuleRelProperties()


@dataclass(frozen=True)
class EventRuleToKinesisStreamRel(CartographyRelSchema):
    """(:EventRule)-[:SENDS_TO]->(:KinesisStream)"""

    target_node_label: str = "KinesisStream"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("kinesis_streams_arns", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "SENDS_TO"
    properties: _EventRuleRelProperties = _EventRuleRelProperties()


@dataclass(frozen=True)
class EventRuleToECSClusterRel(CartographyRelSchema):
    """(:EventRule)-[:TARGETS]->(:ECSCluster)"""

    target_node_label: str = "ECSCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("ecs_clusters_arns", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "TARGETS"
    properties: _EventRuleRelProperties = _EventRuleRelProperties()


@dataclass(frozen=True)
class EventRuleToStepFunctionRel(CartographyRelSchema):
    """(:EventRule)-[:EXECUTES]->(:StepFunction)"""

    target_node_label: str = "StepFunction"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("step_functions_arns", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "EXECUTES"
    properties: _EventRuleRelProperties = _EventRuleRelProperties()


@dataclass(frozen=True)
class EventRuleToCloudWatchLogGroupRel(CartographyRelSchema):
    """(:EventRule)-[:LOGS_TO]->(:CloudWatchLogGroup)"""

    target_node_label: str = "CloudWatchLogGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("cloudwatch_log_groups_arns", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "LOGS_TO"
    properties: _EventRuleRelProperties = _EventRuleRelProperties()


@dataclass(frozen=True)
class EventRuleToBatchJobQueueRel(CartographyRelSchema):
    """(:EventRule)-[:SUBMITS_TO]->(:BatchJobQueue)"""

    target_node_label: str = "BatchJobQueue"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("batch_job_queues_arns", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "SUBMITS_TO"
    properties: _EventRuleRelProperties = _EventRuleRelProperties()


@dataclass(frozen=True)
class EventRuleToSageMakerPipelineRel(CartographyRelSchema):
    """(:EventRule)-[:STARTS_PIPELINE]->(:SageMakerPipeline)"""

    target_node_label: str = "SageMakerPipeline"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("sagemaker_pipelines_arns", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "STARTS_PIPELINE"
    properties: _EventRuleRelProperties = _EventRuleRelProperties()


@dataclass(frozen=True)
class EventRuleToFirehoseDeliveryStreamRel(CartographyRelSchema):
    """(:EventRule)-[:DELIVERS_TO]->(:FirehoseDeliveryStream)"""

    target_node_label: str = "FirehoseDeliveryStream"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("firehose_delivery_streams_arns", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "DELIVERS_TO"
    properties: _EventRuleRelProperties = _EventRuleRelProperties()


@dataclass(frozen=True)
class EventRuleToRedshiftClusterRel(CartographyRelSchema):
    """(:EventRule)-[:TARGETS]->(:RedshiftCluster)"""

    target_node_label: str = "RedshiftCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("redshift_clusters_arns", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "TARGETS"
    properties: _EventRuleRelProperties = _EventRuleRelProperties()


@dataclass(frozen=True)
class EventRuleToCodeBuildProjectRel(CartographyRelSchema):
    """(:EventRule)-[:TRIGGERS_BUILD]->(:CodeBuildProject)"""

    target_node_label: str = "CodeBuildProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("codebuild_projects_arns", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "TRIGGERS_BUILD"
    properties: _EventRuleRelProperties = _EventRuleRelProperties()


@dataclass(frozen=True)
class EventRuleToCodePipelineRel(CartographyRelSchema):
    """(:EventRule)-[:STARTS_PIPELINE]->(:CodePipeline)"""

    target_node_label: str = "CodePipeline"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("codepipelines_arns", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "STARTS_PIPELINE"
    properties: _EventRuleRelProperties = _EventRuleRelProperties()


@dataclass(frozen=True)
class EventRuleToAPIGatewayRel(CartographyRelSchema):
    """(:EventRule)-[:INVOKES_API]->(:APIGatewayRestAPI)"""

    target_node_label: str = "APIGatewayRestAPI"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("api_gateways_arns", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "INVOKES_API"
    properties: _EventRuleRelProperties = _EventRuleRelProperties()


@dataclass(frozen=True)
class EventRuleSchema(CartographyNodeSchema):
    """Schema for CloudWatch Event Rules.

    This schema includes relationships for all supported EventBridge target types.
    The sub_resource_relationship correctly points to AWSAccount (tenant-like object)
    as per Cartography best practices.
    """

    label: str = "EventRule"
    properties: EventRuleNodeProperties = EventRuleNodeProperties()
    sub_resource_relationship: EventRuleToAWSAccountRel = EventRuleToAWSAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [EventRuleToIAMRoleRel()]
    )
