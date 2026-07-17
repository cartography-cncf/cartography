import re
from dataclasses import dataclass

import neo4j

from cartography.client.core.tx import run_write_query

_LABEL_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")


@dataclass(frozen=True)
class AWSLabelMigration:
    old_label: str
    new_label: str

    def __post_init__(self) -> None:
        for label in (self.old_label, self.new_label):
            if not _LABEL_PATTERN.fullmatch(label):
                raise ValueError(f"Invalid Neo4j label: {label!r}")
        if self.new_label != f"AWS{self.old_label}":
            raise ValueError(
                f"AWS label migration must use the AWS prefix: "
                f"{self.old_label!r} -> {self.new_label!r}",
            )


def _migration(old_label: str) -> AWSLabelMigration:
    return AWSLabelMigration(old_label, f"AWS{old_label}")


# DEPRECATED: The old labels in this registry will be removed in v1.0.0.
AWS_LABEL_MIGRATIONS: tuple[AWSLabelMigration, ...] = tuple(
    _migration(label)
    for label in (
        "ACMCertificate",
        "APIGatewayClientCertificate",
        "APIGatewayDeployment",
        "APIGatewayIntegration",
        "APIGatewayMethod",
        "APIGatewayResource",
        "APIGatewayRestAPI",
        "APIGatewayStage",
        "APIGatewayV2API",
        "AccountAccessKey",
        "AutoScalingGroup",
        "DBSubnetGroup",
        "DynamoDBArchivalSummary",
        "DynamoDBBackup",
        "DynamoDBBillingModeSummary",
        "DynamoDBGlobalSecondaryIndex",
        "DynamoDBRestoreSummary",
        "DynamoDBSSEDescription",
        "DynamoDBStream",
        "DynamoDBTable",
        "EBSVolume",
        "EBSSnapshot",
        "EC2Image",
        "EC2Instance",
        "EC2Ipv6Address",
        "EC2KeyPair",
        "EC2NetworkAcl",
        "EC2NetworkAclRule",
        "EC2PrivateIp",
        "EC2Reservation",
        "EC2ReservedInstance",
        "EC2Route",
        "EC2RouteTable",
        "EC2RouteTableAssociation",
        "EC2SecurityGroup",
        "EC2Subnet",
        "ECRImage",
        "ECRImageLayer",
        "ECRPullThroughCacheRule",
        "ECRRepository",
        "ECRRepositoryImage",
        "ECSCluster",
        "ECSContainer",
        "ECSContainerDefinition",
        "ECSContainerInstance",
        "ECSService",
        "ECSTask",
        "ECSTaskDefinition",
        "EKSAccessEntry",
        "EKSCluster",
        "ELBListener",
        "ELBV2Listener",
        "ELBV2TargetGroup",
        "EMRCluster",
        "ESDomain",
        "EfsAccessPoint",
        "EfsFileSystem",
        "EfsMountTarget",
        "ElasticIPAddress",
        "ElasticacheCluster",
        "ElasticacheTopic",
        "EventBridgeRule",
        "EventBridgeTarget",
        "GlueConnection",
        "GlueJob",
        "GuardDutyDetector",
        "GuardDutyFinding",
        "KMSAlias",
        "KMSGrant",
        "KMSKey",
        "LaunchConfiguration",
        "LaunchTemplate",
        "LaunchTemplateVersion",
        "NameServer",
        "NetworkInterface",
        "RDSCluster",
        "RDSEventSubscription",
        "RDSInstance",
        "RDSSnapshot",
        "RedshiftCluster",
        "PublicSSMParameter",
        "S3AccountPublicAccessBlock",
        "S3Acl",
        "S3Bucket",
        "S3PolicyStatement",
        "SESEmailIdentity",
        "SNSTopic",
        "SNSTopicSubscription",
        "SQSQueue",
        "SSMInstanceInformation",
        "SSMInstancePatch",
        "SSMParameter",
        "SecretsManagerSecret",
        "SecretsManagerSecretVersion",
        "SecurityHub",
        "CloudFormationStack",
        "CloudFrontDistribution",
        "CloudTrailTrail",
        "CloudWatchLogGroup",
        "CloudWatchLogMetricFilter",
        "CloudWatchMetricAlarm",
        "CodeBuildProject",
        "CognitoIdentityPool",
        "CognitoUserPool",
    )
)


def build_aws_label_migration_query(
    migrations: tuple[AWSLabelMigration, ...] = AWS_LABEL_MIGRATIONS,
) -> str:
    migration_clauses = "\n".join(
        (
            "FOREACH (_ IN CASE "
            f"WHEN n:{migration.old_label} AND NOT n:{migration.new_label} "
            f"THEN [1] ELSE [] END | SET n:{migration.new_label})"
        )
        for migration in migrations
    )
    return f"""
    MATCH (:AWSAccount{{id: $AWS_ID}})-[:RESOURCE]->(n)
    WITH DISTINCT n
    {migration_clauses}
    """


def migrate_legacy_aws_labels(
    neo4j_session: neo4j.Session,
    current_aws_account_id: str,
) -> None:
    """Add provider-specific labels to legacy resources before ingestion."""
    run_write_query(
        neo4j_session,
        build_aws_label_migration_query(),
        AWS_ID=current_aws_account_id,
    )


# DEPRECATED: PublicSSMParameter compatibility support will be removed in v1.0.0.
def migrate_legacy_public_ssm_parameter_label(
    neo4j_session: neo4j.Session,
) -> None:
    """Migrate global AWS-managed SSM parameters, which have no account edge."""
    run_write_query(
        neo4j_session,
        """
        MATCH (parameter:PublicSSMParameter)
        WHERE NOT parameter:AWSPublicSSMParameter
        SET parameter:AWSPublicSSMParameter
        """,
    )
