from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_source_node_matcher
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import SourceNodeMatcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class TerraformManagesRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)
    resource_type: PropertyRef = PropertyRef("resource_type")


def _make_manages_matchlink(target_label: str) -> type:
    @dataclass(frozen=True)
    class _MatchLink(CartographyRelSchema):
        source_node_label: str = "TerraformResourceInstance"
        source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
            {"id": PropertyRef("id")},
        )
        target_node_label: str = target_label
        target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
            {"id": PropertyRef("attributes_id")},
        )
        direction: LinkDirection = LinkDirection.OUTWARD
        rel_label: str = "MANAGES"
        properties: TerraformManagesRelProperties = TerraformManagesRelProperties()

    _MatchLink.__name__ = f"TerraformInstanceTo{target_label}MatchLink"
    _MatchLink.__qualname__ = _MatchLink.__name__
    return _MatchLink


TerraformInstanceToS3BucketMatchLink = _make_manages_matchlink("S3Bucket")
TerraformInstanceToEC2InstanceMatchLink = _make_manages_matchlink("EC2Instance")
TerraformInstanceToEKSClusterMatchLink = _make_manages_matchlink("EKSCluster")
TerraformInstanceToRDSInstanceMatchLink = _make_manages_matchlink("RDSInstance")
TerraformInstanceToRDSClusterMatchLink = _make_manages_matchlink("RDSCluster")
TerraformInstanceToAWSRoleMatchLink = _make_manages_matchlink("AWSRole")
TerraformInstanceToAWSUserMatchLink = _make_manages_matchlink("AWSUser")
TerraformInstanceToAWSGroupMatchLink = _make_manages_matchlink("AWSGroup")
TerraformInstanceToAWSManagedPolicyMatchLink = _make_manages_matchlink(
    "AWSManagedPolicy"
)
TerraformInstanceToEC2SecurityGroupMatchLink = _make_manages_matchlink(
    "EC2SecurityGroup"
)
TerraformInstanceToAWSVpcMatchLink = _make_manages_matchlink("AWSVpc")
TerraformInstanceToEC2SubnetMatchLink = _make_manages_matchlink("EC2Subnet")
TerraformInstanceToEBSVolumeMatchLink = _make_manages_matchlink("EBSVolume")
TerraformInstanceToAWSLambdaMatchLink = _make_manages_matchlink("AWSLambda")
TerraformInstanceToSQSQueueMatchLink = _make_manages_matchlink("SQSQueue")
TerraformInstanceToSNSTopicMatchLink = _make_manages_matchlink("SNSTopic")
TerraformInstanceToDynamoDBTableMatchLink = _make_manages_matchlink("DynamoDBTable")
TerraformInstanceToKMSKeyMatchLink = _make_manages_matchlink("KMSKey")
TerraformInstanceToSecretsManagerSecretMatchLink = _make_manages_matchlink(
    "SecretsManagerSecret"
)
TerraformInstanceToACMCertificateMatchLink = _make_manages_matchlink("ACMCertificate")
TerraformInstanceToECRRepositoryMatchLink = _make_manages_matchlink("ECRRepository")
TerraformInstanceToElasticacheClusterMatchLink = _make_manages_matchlink(
    "ElasticacheCluster"
)
TerraformInstanceToRedshiftClusterMatchLink = _make_manages_matchlink("RedshiftCluster")
TerraformInstanceToECSClusterMatchLink = _make_manages_matchlink("ECSCluster")
TerraformInstanceToAWSLoadBalancerV2MatchLink = _make_manages_matchlink(
    "AWSLoadBalancerV2"
)
TerraformInstanceToCloudWatchMetricAlarmMatchLink = _make_manages_matchlink(
    "CloudWatchMetricAlarm"
)

RESOURCE_TYPE_MATCHLINKS: dict[str, CartographyRelSchema] = {
    "aws_s3_bucket": TerraformInstanceToS3BucketMatchLink(),
    "aws_instance": TerraformInstanceToEC2InstanceMatchLink(),
    "aws_eks_cluster": TerraformInstanceToEKSClusterMatchLink(),
    "aws_db_instance": TerraformInstanceToRDSInstanceMatchLink(),
    "aws_rds_cluster": TerraformInstanceToRDSClusterMatchLink(),
    "aws_iam_role": TerraformInstanceToAWSRoleMatchLink(),
    "aws_iam_user": TerraformInstanceToAWSUserMatchLink(),
    "aws_iam_group": TerraformInstanceToAWSGroupMatchLink(),
    "aws_iam_policy": TerraformInstanceToAWSManagedPolicyMatchLink(),
    "aws_security_group": TerraformInstanceToEC2SecurityGroupMatchLink(),
    "aws_vpc": TerraformInstanceToAWSVpcMatchLink(),
    "aws_subnet": TerraformInstanceToEC2SubnetMatchLink(),
    "aws_ebs_volume": TerraformInstanceToEBSVolumeMatchLink(),
    "aws_lambda_function": TerraformInstanceToAWSLambdaMatchLink(),
    "aws_sqs_queue": TerraformInstanceToSQSQueueMatchLink(),
    "aws_sns_topic": TerraformInstanceToSNSTopicMatchLink(),
    "aws_dynamodb_table": TerraformInstanceToDynamoDBTableMatchLink(),
    "aws_kms_key": TerraformInstanceToKMSKeyMatchLink(),
    "aws_secretsmanager_secret": TerraformInstanceToSecretsManagerSecretMatchLink(),
    "aws_acm_certificate": TerraformInstanceToACMCertificateMatchLink(),
    "aws_ecr_repository": TerraformInstanceToECRRepositoryMatchLink(),
    "aws_elasticache_cluster": TerraformInstanceToElasticacheClusterMatchLink(),
    "aws_redshift_cluster": TerraformInstanceToRedshiftClusterMatchLink(),
    "aws_ecs_cluster": TerraformInstanceToECSClusterMatchLink(),
    # Both aws_lb and aws_alb are aliases for the same resource type in Terraform
    "aws_lb": TerraformInstanceToAWSLoadBalancerV2MatchLink(),
    "aws_alb": TerraformInstanceToAWSLoadBalancerV2MatchLink(),
    "aws_cloudwatch_metric_alarm": TerraformInstanceToCloudWatchMetricAlarmMatchLink(),
}

# Maps Terraform resource types to the attributes key whose value matches
# the corresponding AWS graph node's `id` property.
# Defaults to `attrs.get("id") or attrs.get("arn")` when not listed here.
RESOURCE_TYPE_ID_ATTR: dict[str, str] = {
    # ARN-keyed nodes: Terraform attributes.id = name/identifier, not ARN
    "aws_eks_cluster": "arn",  # EKSCluster.id = ARN; tf id = cluster name
    "aws_db_instance": "arn",  # RDSInstance.id = DBInstanceArn; tf id = DB identifier
    "aws_rds_cluster": "arn",  # RDSCluster.id = DBClusterArn; tf id = cluster identifier
    "aws_lambda_function": "arn",  # AWSLambda.id = FunctionArn; tf id = function name
    "aws_sqs_queue": "arn",  # SQSQueue.id = QueueArn; tf id = queue URL
    "aws_sns_topic": "arn",  # SNSTopic.id = TopicArn; tf id = topic ARN (same)
    "aws_dynamodb_table": "arn",  # DynamoDBTable.id = Arn; tf id = table name
    "aws_secretsmanager_secret": "arn",  # SecretsManagerSecret.id = ARN; tf id = secret ARN (same)
    "aws_acm_certificate": "arn",  # ACMCertificate.id = Arn; tf id = cert ARN (same)
    "aws_ecr_repository": "arn",  # ECRRepository.id = repositoryArn; tf id = repo name
    "aws_elasticache_cluster": "arn",  # ElasticacheCluster.id = ARN; tf id = cluster id
    "aws_redshift_cluster": "arn",  # RedshiftCluster.id = arn; tf id = cluster identifier
    "aws_ecs_cluster": "arn",  # ECSCluster.id = clusterArn; tf id = cluster name
    "aws_lb": "arn",  # AWSLoadBalancerV2.id = DNSName... but arn is more reliable
    "aws_alb": "arn",  # same as aws_lb
    "aws_cloudwatch_metric_alarm": "arn",  # CloudWatchMetricAlarm.id = AlarmArn; tf id = alarm name
    # KMSKey.id = KeyId which matches tf attributes.key_id
    "aws_kms_key": "key_id",
    # IAM: AWSRole/AWSUser/AWSGroup.id = arn, tf attributes.arn matches directly
    "aws_iam_role": "arn",
    "aws_iam_user": "arn",
    "aws_iam_group": "arn",
    "aws_iam_policy": "arn",
    # VPC/Subnet/EBS: Cartography id = AWS resource ID, same as tf attributes.id — no override needed
    # aws_vpc -> AWSVpc.id = VpcId = tf attributes.id ✓
    # aws_subnet -> EC2Subnet.id = SubnetId = tf attributes.id ✓
    # aws_ebs_volume -> EBSVolume.id = VolumeId = tf attributes.id ✓
}
