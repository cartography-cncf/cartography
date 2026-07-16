from cartography.models.core.nodes import ExtraNodeLabel
from cartography.models.core.nodes import LabelKind

AWS_IP_RULE = ExtraNodeLabel(
    label="AWSIpRule",
    description="A aws node participating in the shared AWSIpRule graph interface.",
)


AWS_IPV4_CIDR_BLOCK = ExtraNodeLabel(
    label="AWSIpv4CidrBlock",
    description="A aws node participating in the shared AWSIpv4CidrBlock graph interface.",
)


AWS_IPV6_CIDR_BLOCK = ExtraNodeLabel(
    label="AWSIpv6CidrBlock",
    description="A aws node participating in the shared AWSIpv6CidrBlock graph interface.",
)


AWS_POLICY = ExtraNodeLabel(
    label="AWSPolicy",
    description="A aws node participating in the shared AWSPolicy graph interface.",
)


AWS_PRINCIPAL = ExtraNodeLabel(
    label="AWSPrincipal",
    description="A aws node participating in the shared AWSPrincipal graph interface.",
)


ENDPOINT = ExtraNodeLabel(
    label="Endpoint",
    description="A aws node participating in the shared Endpoint graph interface.",
)


IP = ExtraNodeLabel(
    label="Ip",
    description="A aws node participating in the shared Ip graph interface.",
)


KEY_PAIR = ExtraNodeLabel(
    label="KeyPair",
    description="A aws node participating in the shared KeyPair graph interface.",
)


MFA_DEVICE = ExtraNodeLabel(
    label="MfaDevice",
    description="A aws node participating in the shared MfaDevice graph interface.",
)


SSM_PARAMETER = ExtraNodeLabel(
    label="SSMParameter",
    description="A aws node participating in the shared SSMParameter graph interface.",
)


LOAD_BALANCER_V2 = ExtraNodeLabel(
    label="LoadBalancerV2",
    description="A aws node participating in the shared LoadBalancerV2 graph interface.",
)


LEGACY_ACM_CERTIFICATE = ExtraNodeLabel(
    label="ACMCertificate",
    description="Compatibility label for the deprecated `ACMCertificate` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_API_GATEWAY_CLIENT_CERTIFICATE = ExtraNodeLabel(
    label="APIGatewayClientCertificate",
    description="Compatibility label for the deprecated `APIGatewayClientCertificate` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_API_GATEWAY_DEPLOYMENT = ExtraNodeLabel(
    label="APIGatewayDeployment",
    description="Compatibility label for the deprecated `APIGatewayDeployment` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_API_GATEWAY_INTEGRATION = ExtraNodeLabel(
    label="APIGatewayIntegration",
    description="Compatibility label for the deprecated `APIGatewayIntegration` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_API_GATEWAY_METHOD = ExtraNodeLabel(
    label="APIGatewayMethod",
    description="Compatibility label for the deprecated `APIGatewayMethod` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_API_GATEWAY_RESOURCE = ExtraNodeLabel(
    label="APIGatewayResource",
    description="Compatibility label for the deprecated `APIGatewayResource` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_API_GATEWAY_REST_API = ExtraNodeLabel(
    label="APIGatewayRestAPI",
    description="Compatibility label for the deprecated `APIGatewayRestAPI` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_API_GATEWAY_STAGE = ExtraNodeLabel(
    label="APIGatewayStage",
    description="Compatibility label for the deprecated `APIGatewayStage` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_API_GATEWAY_V2_API = ExtraNodeLabel(
    label="APIGatewayV2API",
    description="Compatibility label for the deprecated `APIGatewayV2API` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_ACCOUNT_ACCESS_KEY = ExtraNodeLabel(
    label="AccountAccessKey",
    description="Compatibility label for the deprecated `AccountAccessKey` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_AUTO_SCALING_GROUP = ExtraNodeLabel(
    label="AutoScalingGroup",
    description="Compatibility label for the deprecated `AutoScalingGroup` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_CLOUD_FORMATION_STACK = ExtraNodeLabel(
    label="CloudFormationStack",
    description="Compatibility label for the deprecated `CloudFormationStack` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_CLOUD_FRONT_DISTRIBUTION = ExtraNodeLabel(
    label="CloudFrontDistribution",
    description="Compatibility label for the deprecated `CloudFrontDistribution` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_CLOUD_TRAIL_TRAIL = ExtraNodeLabel(
    label="CloudTrailTrail",
    description="Compatibility label for the deprecated `CloudTrailTrail` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_CLOUD_WATCH_LOG_GROUP = ExtraNodeLabel(
    label="CloudWatchLogGroup",
    description="Compatibility label for the deprecated `CloudWatchLogGroup` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_CLOUD_WATCH_LOG_METRIC_FILTER = ExtraNodeLabel(
    label="CloudWatchLogMetricFilter",
    description="Compatibility label for the deprecated `CloudWatchLogMetricFilter` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_CLOUD_WATCH_METRIC_ALARM = ExtraNodeLabel(
    label="CloudWatchMetricAlarm",
    description="Compatibility label for the deprecated `CloudWatchMetricAlarm` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_CODE_BUILD_PROJECT = ExtraNodeLabel(
    label="CodeBuildProject",
    description="Compatibility label for the deprecated `CodeBuildProject` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_COGNITO_IDENTITY_POOL = ExtraNodeLabel(
    label="CognitoIdentityPool",
    description="Compatibility label for the deprecated `CognitoIdentityPool` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_COGNITO_USER_POOL = ExtraNodeLabel(
    label="CognitoUserPool",
    description="Compatibility label for the deprecated `CognitoUserPool` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_DB_SUBNET_GROUP = ExtraNodeLabel(
    label="DBSubnetGroup",
    description="Compatibility label for the deprecated `DBSubnetGroup` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_DYNAMO_DB_ARCHIVAL_SUMMARY = ExtraNodeLabel(
    label="DynamoDBArchivalSummary",
    description="Compatibility label for the deprecated `DynamoDBArchivalSummary` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_DYNAMO_DB_BACKUP = ExtraNodeLabel(
    label="DynamoDBBackup",
    description="Compatibility label for the deprecated `DynamoDBBackup` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_DYNAMO_DB_BILLING_MODE_SUMMARY = ExtraNodeLabel(
    label="DynamoDBBillingModeSummary",
    description="Compatibility label for the deprecated `DynamoDBBillingModeSummary` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_DYNAMO_DB_GLOBAL_SECONDARY_INDEX = ExtraNodeLabel(
    label="DynamoDBGlobalSecondaryIndex",
    description="Compatibility label for the deprecated `DynamoDBGlobalSecondaryIndex` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_DYNAMO_DB_RESTORE_SUMMARY = ExtraNodeLabel(
    label="DynamoDBRestoreSummary",
    description="Compatibility label for the deprecated `DynamoDBRestoreSummary` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_DYNAMO_DBSSE_DESCRIPTION = ExtraNodeLabel(
    label="DynamoDBSSEDescription",
    description="Compatibility label for the deprecated `DynamoDBSSEDescription` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_DYNAMO_DB_STREAM = ExtraNodeLabel(
    label="DynamoDBStream",
    description="Compatibility label for the deprecated `DynamoDBStream` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_DYNAMO_DB_TABLE = ExtraNodeLabel(
    label="DynamoDBTable",
    description="Compatibility label for the deprecated `DynamoDBTable` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_EBS_SNAPSHOT = ExtraNodeLabel(
    label="EBSSnapshot",
    description="Compatibility label for the deprecated `EBSSnapshot` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_EBS_VOLUME = ExtraNodeLabel(
    label="EBSVolume",
    description="Compatibility label for the deprecated `EBSVolume` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_EC2_IMAGE = ExtraNodeLabel(
    label="EC2Image",
    description="Compatibility label for the deprecated `EC2Image` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_EC2_INSTANCE = ExtraNodeLabel(
    label="EC2Instance",
    description="Compatibility label for the deprecated `EC2Instance` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_EC2_IPV6_ADDRESS = ExtraNodeLabel(
    label="EC2Ipv6Address",
    description="Compatibility label for the deprecated `EC2Ipv6Address` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_EC2_KEY_PAIR = ExtraNodeLabel(
    label="EC2KeyPair",
    description="Compatibility label for the deprecated `EC2KeyPair` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_EC2_NETWORK_ACL = ExtraNodeLabel(
    label="EC2NetworkAcl",
    description="Compatibility label for the deprecated `EC2NetworkAcl` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_EC2_NETWORK_ACL_RULE = ExtraNodeLabel(
    label="EC2NetworkAclRule",
    description="Compatibility label for the deprecated `EC2NetworkAclRule` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_EC2_PRIVATE_IP = ExtraNodeLabel(
    label="EC2PrivateIp",
    description="Compatibility label for the deprecated `EC2PrivateIp` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_EC2_RESERVATION = ExtraNodeLabel(
    label="EC2Reservation",
    description="Compatibility label for the deprecated `EC2Reservation` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_EC2_RESERVED_INSTANCE = ExtraNodeLabel(
    label="EC2ReservedInstance",
    description="Compatibility label for the deprecated `EC2ReservedInstance` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_EC2_ROUTE = ExtraNodeLabel(
    label="EC2Route",
    description="Compatibility label for the deprecated `EC2Route` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_EC2_ROUTE_TABLE = ExtraNodeLabel(
    label="EC2RouteTable",
    description="Compatibility label for the deprecated `EC2RouteTable` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_EC2_ROUTE_TABLE_ASSOCIATION = ExtraNodeLabel(
    label="EC2RouteTableAssociation",
    description="Compatibility label for the deprecated `EC2RouteTableAssociation` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_EC2_SECURITY_GROUP = ExtraNodeLabel(
    label="EC2SecurityGroup",
    description="Compatibility label for the deprecated `EC2SecurityGroup` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_EC2_SUBNET = ExtraNodeLabel(
    label="EC2Subnet",
    description="Compatibility label for the deprecated `EC2Subnet` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_ECR_IMAGE = ExtraNodeLabel(
    label="ECRImage",
    description="Compatibility label for the deprecated `ECRImage` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_ECR_IMAGE_LAYER = ExtraNodeLabel(
    label="ECRImageLayer",
    description="Compatibility label for the deprecated `ECRImageLayer` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_ECR_PULL_THROUGH_CACHE_RULE = ExtraNodeLabel(
    label="ECRPullThroughCacheRule",
    description="Compatibility label for the deprecated `ECRPullThroughCacheRule` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_ECR_REPOSITORY = ExtraNodeLabel(
    label="ECRRepository",
    description="Compatibility label for the deprecated `ECRRepository` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_ECR_REPOSITORY_IMAGE = ExtraNodeLabel(
    label="ECRRepositoryImage",
    description="Compatibility label for the deprecated `ECRRepositoryImage` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_ECS_CLUSTER = ExtraNodeLabel(
    label="ECSCluster",
    description="Compatibility label for the deprecated `ECSCluster` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_ECS_CONTAINER = ExtraNodeLabel(
    label="ECSContainer",
    description="Compatibility label for the deprecated `ECSContainer` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_ECS_CONTAINER_DEFINITION = ExtraNodeLabel(
    label="ECSContainerDefinition",
    description="Compatibility label for the deprecated `ECSContainerDefinition` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_ECS_CONTAINER_INSTANCE = ExtraNodeLabel(
    label="ECSContainerInstance",
    description="Compatibility label for the deprecated `ECSContainerInstance` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_ECS_SERVICE = ExtraNodeLabel(
    label="ECSService",
    description="Compatibility label for the deprecated `ECSService` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_ECS_TASK = ExtraNodeLabel(
    label="ECSTask",
    description="Compatibility label for the deprecated `ECSTask` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_ECS_TASK_DEFINITION = ExtraNodeLabel(
    label="ECSTaskDefinition",
    description="Compatibility label for the deprecated `ECSTaskDefinition` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_EKS_CLUSTER = ExtraNodeLabel(
    label="EKSCluster",
    description="Compatibility label for the deprecated `EKSCluster` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_ELB_LISTENER = ExtraNodeLabel(
    label="ELBListener",
    description="Compatibility label for the deprecated `ELBListener` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_ELBV2_LISTENER = ExtraNodeLabel(
    label="ELBV2Listener",
    description="Compatibility label for the deprecated `ELBV2Listener` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_ELBV2_TARGET_GROUP = ExtraNodeLabel(
    label="ELBV2TargetGroup",
    description="Compatibility label for the deprecated `ELBV2TargetGroup` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_EMR_CLUSTER = ExtraNodeLabel(
    label="EMRCluster",
    description="Compatibility label for the deprecated `EMRCluster` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_ES_DOMAIN = ExtraNodeLabel(
    label="ESDomain",
    description="Compatibility label for the deprecated `ESDomain` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_EFS_ACCESS_POINT = ExtraNodeLabel(
    label="EfsAccessPoint",
    description="Compatibility label for the deprecated `EfsAccessPoint` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_EFS_FILE_SYSTEM = ExtraNodeLabel(
    label="EfsFileSystem",
    description="Compatibility label for the deprecated `EfsFileSystem` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_EFS_MOUNT_TARGET = ExtraNodeLabel(
    label="EfsMountTarget",
    description="Compatibility label for the deprecated `EfsMountTarget` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_ELASTIC_IP_ADDRESS = ExtraNodeLabel(
    label="ElasticIPAddress",
    description="Compatibility label for the deprecated `ElasticIPAddress` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_ELASTICACHE_CLUSTER = ExtraNodeLabel(
    label="ElasticacheCluster",
    description="Compatibility label for the deprecated `ElasticacheCluster` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_ELASTICACHE_TOPIC = ExtraNodeLabel(
    label="ElasticacheTopic",
    description="Compatibility label for the deprecated `ElasticacheTopic` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_EVENT_BRIDGE_RULE = ExtraNodeLabel(
    label="EventBridgeRule",
    description="Compatibility label for the deprecated `EventBridgeRule` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_EVENT_BRIDGE_TARGET = ExtraNodeLabel(
    label="EventBridgeTarget",
    description="Compatibility label for the deprecated `EventBridgeTarget` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_GLUE_CONNECTION = ExtraNodeLabel(
    label="GlueConnection",
    description="Compatibility label for the deprecated `GlueConnection` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_GLUE_JOB = ExtraNodeLabel(
    label="GlueJob",
    description="Compatibility label for the deprecated `GlueJob` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_GUARD_DUTY_DETECTOR = ExtraNodeLabel(
    label="GuardDutyDetector",
    description="Compatibility label for the deprecated `GuardDutyDetector` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_GUARD_DUTY_FINDING = ExtraNodeLabel(
    label="GuardDutyFinding",
    description="Compatibility label for the deprecated `GuardDutyFinding` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_KMS_ALIAS = ExtraNodeLabel(
    label="KMSAlias",
    description="Compatibility label for the deprecated `KMSAlias` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_KMS_GRANT = ExtraNodeLabel(
    label="KMSGrant",
    description="Compatibility label for the deprecated `KMSGrant` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_KMS_KEY = ExtraNodeLabel(
    label="KMSKey",
    description="Compatibility label for the deprecated `KMSKey` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_LAUNCH_CONFIGURATION = ExtraNodeLabel(
    label="LaunchConfiguration",
    description="Compatibility label for the deprecated `LaunchConfiguration` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_LAUNCH_TEMPLATE = ExtraNodeLabel(
    label="LaunchTemplate",
    description="Compatibility label for the deprecated `LaunchTemplate` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_LAUNCH_TEMPLATE_VERSION = ExtraNodeLabel(
    label="LaunchTemplateVersion",
    description="Compatibility label for the deprecated `LaunchTemplateVersion` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_NAME_SERVER = ExtraNodeLabel(
    label="NameServer",
    description="Compatibility label for the deprecated `NameServer` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_PUBLIC_SSM_PARAMETER = ExtraNodeLabel(
    label="PublicSSMParameter",
    description="Compatibility label for the deprecated `PublicSSMParameter` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_RDS_CLUSTER = ExtraNodeLabel(
    label="RDSCluster",
    description="Compatibility label for the deprecated `RDSCluster` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_RDS_EVENT_SUBSCRIPTION = ExtraNodeLabel(
    label="RDSEventSubscription",
    description="Compatibility label for the deprecated `RDSEventSubscription` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_RDS_INSTANCE = ExtraNodeLabel(
    label="RDSInstance",
    description="Compatibility label for the deprecated `RDSInstance` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_RDS_SNAPSHOT = ExtraNodeLabel(
    label="RDSSnapshot",
    description="Compatibility label for the deprecated `RDSSnapshot` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_REDSHIFT_CLUSTER = ExtraNodeLabel(
    label="RedshiftCluster",
    description="Compatibility label for the deprecated `RedshiftCluster` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_S3_ACCOUNT_PUBLIC_ACCESS_BLOCK = ExtraNodeLabel(
    label="S3AccountPublicAccessBlock",
    description="Compatibility label for the deprecated `S3AccountPublicAccessBlock` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_S3_ACL = ExtraNodeLabel(
    label="S3Acl",
    description="Compatibility label for the deprecated `S3Acl` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_S3_BUCKET = ExtraNodeLabel(
    label="S3Bucket",
    description="Compatibility label for the deprecated `S3Bucket` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_S3_POLICY_STATEMENT = ExtraNodeLabel(
    label="S3PolicyStatement",
    description="Compatibility label for the deprecated `S3PolicyStatement` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_SES_EMAIL_IDENTITY = ExtraNodeLabel(
    label="SESEmailIdentity",
    description="Compatibility label for the deprecated `SESEmailIdentity` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_SNS_TOPIC = ExtraNodeLabel(
    label="SNSTopic",
    description="Compatibility label for the deprecated `SNSTopic` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_SNS_TOPIC_SUBSCRIPTION = ExtraNodeLabel(
    label="SNSTopicSubscription",
    description="Compatibility label for the deprecated `SNSTopicSubscription` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_SQS_QUEUE = ExtraNodeLabel(
    label="SQSQueue",
    description="Compatibility label for the deprecated `SQSQueue` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_SSM_INSTANCE_INFORMATION = ExtraNodeLabel(
    label="SSMInstanceInformation",
    description="Compatibility label for the deprecated `SSMInstanceInformation` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_SSM_INSTANCE_PATCH = ExtraNodeLabel(
    label="SSMInstancePatch",
    description="Compatibility label for the deprecated `SSMInstancePatch` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_SECRETS_MANAGER_SECRET = ExtraNodeLabel(
    label="SecretsManagerSecret",
    description="Compatibility label for the deprecated `SecretsManagerSecret` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_SECRETS_MANAGER_SECRET_VERSION = ExtraNodeLabel(
    label="SecretsManagerSecretVersion",
    description="Compatibility label for the deprecated `SecretsManagerSecretVersion` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)


LEGACY_SECURITY_HUB = ExtraNodeLabel(
    label="SecurityHub",
    description="Compatibility label for the deprecated `SecurityHub` aws node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)
