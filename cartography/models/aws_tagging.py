from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AWSTaggableResource:
    """Runtime matching metadata for one AWS resource type supported by tagging."""

    resource_type: str
    label: str
    property: str
    id_parser: str | None = None
    region_property: str | None = None


AWS_TAGGABLE_RESOURCES = (
    AWSTaggableResource("autoscaling:autoScalingGroup", "AWSAutoScalingGroup", "arn"),
    AWSTaggableResource("dynamodb:table", "AWSDynamoDBTable", "id"),
    AWSTaggableResource("ec2:instance", "AWSEC2Instance", "id", "ec2_short_id"),
    AWSTaggableResource(
        "ec2:internet-gateway",
        "AWSInternetGateway",
        "id",
        "ec2_short_id",
    ),
    AWSTaggableResource("ec2:key-pair", "AWSEC2KeyPair", "id"),
    AWSTaggableResource(
        "ec2:network-interface",
        "AWSNetworkInterface",
        "id",
        "ec2_short_id",
    ),
    AWSTaggableResource("ecr:repository", "AWSECRRepository", "id"),
    AWSTaggableResource(
        "ec2:security-group",
        "AWSEC2SecurityGroup",
        "id",
        "ec2_short_id",
    ),
    AWSTaggableResource("ec2:subnet", "AWSEC2Subnet", "subnetid", "ec2_short_id"),
    AWSTaggableResource("ec2:transit-gateway", "AWSTransitGateway", "id"),
    AWSTaggableResource(
        "ec2:transit-gateway-attachment",
        "AWSTransitGatewayAttachment",
        "id",
    ),
    AWSTaggableResource("ec2:vpc", "AWSVpc", "id", "ec2_short_id"),
    AWSTaggableResource("ec2:volume", "AWSEBSVolume", "id", "ec2_short_id"),
    AWSTaggableResource(
        "ec2:elastic-ip-address",
        "AWSElasticIPAddress",
        "id",
        "ec2_short_id",
    ),
    AWSTaggableResource("ecs:cluster", "AWSECSCluster", "id"),
    AWSTaggableResource("ecs:container", "AWSECSContainer", "id"),
    AWSTaggableResource("ecs:container-instance", "AWSECSContainerInstance", "id"),
    AWSTaggableResource("ecs:task", "AWSECSTask", "id"),
    AWSTaggableResource("ecs:task-definition", "AWSECSTaskDefinition", "id"),
    AWSTaggableResource("eks:cluster", "AWSEKSCluster", "id"),
    AWSTaggableResource("elasticache:cluster", "AWSElasticacheCluster", "arn"),
    AWSTaggableResource(
        "elasticloadbalancing:loadbalancer",
        "AWSLoadBalancer",
        "name",
        "elb_short_id",
        "region",
    ),
    AWSTaggableResource(
        "elasticloadbalancing:loadbalancer/app",
        "AWSLoadBalancerV2",
        "name",
        "lb2_short_id",
        "region",
    ),
    AWSTaggableResource(
        "elasticloadbalancing:loadbalancer/net",
        "AWSLoadBalancerV2",
        "name",
        "lb2_short_id",
        "region",
    ),
    AWSTaggableResource("elasticmapreduce:cluster", "AWSEMRCluster", "arn"),
    AWSTaggableResource("es:domain", "AWSESDomain", "arn"),
    AWSTaggableResource("kms:key", "AWSKMSKey", "arn"),
    AWSTaggableResource("iam:role", "AWSRole", "arn"),
    AWSTaggableResource("iam:user", "AWSUser", "arn"),
    AWSTaggableResource("lambda:function", "AWSLambda", "id"),
    AWSTaggableResource("redshift:cluster", "AWSRedshiftCluster", "id"),
    AWSTaggableResource("rds:db", "AWSRDSInstance", "id"),
    AWSTaggableResource("rds:subgrp", "AWSDBSubnetGroup", "id"),
    AWSTaggableResource("rds:cluster", "AWSRDSCluster", "id"),
    AWSTaggableResource("rds:snapshot", "AWSRDSSnapshot", "id"),
    AWSTaggableResource("s3", "AWSS3Bucket", "id", "s3_bucket_name"),
    AWSTaggableResource(
        "secretsmanager:secret",
        "AWSSecretsManagerSecret",
        "id",
    ),
    AWSTaggableResource("sqs", "AWSSQSQueue", "id"),
)
