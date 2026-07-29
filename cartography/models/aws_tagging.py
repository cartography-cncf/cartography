from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AWSTaggableResource:
    """
    How to find the Cartography node that a Resource Groups Tagging API ARN refers to.

    - ``resource_type``: the resource type as reported by the tagging API.
    - ``label``: the node label used in Cartography for this resource type.
    - ``property``: the field of this node that uniquely identifies the resource.
    - ``id_parser``: [optional] key into the ARN parsers in
      cartography.intel.aws.resourcegroupstaggingapi. EC2 instances and S3 buckets
      currently use non-ARNs as their primary identifiers, so the ARN returned by the
      tagging API has to be translated to the form Cartography uses.
      TODO: make EC2 and S3 assets queryable by their full ARN so this can go away.
    - ``region_property``: [optional] the node property holding the resource's region.
      When present, the tag MATCH is scoped to the synced region so that same-named
      resources in different regions (load balancers are keyed by name) are not
      cross-tagged.
    """

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
    # Match on the classic ELB's own label (AWSLoadBalancer), not the shared
    # "LoadBalancer" ontology label, which is also attached to AWSLoadBalancerV2
    # nodes. Otherwise a classic ELB tag would bleed onto an ALB/NLB of the same
    # name in the same region.
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
    # Buckets are the only objects in the S3 service:
    # https://docs.aws.amazon.com/AmazonS3/latest/dev/s3-arn-format.html
    AWSTaggableResource("s3", "AWSS3Bucket", "id", "s3_bucket_name"),
    AWSTaggableResource(
        "secretsmanager:secret",
        "AWSSecretsManagerSecret",
        "id",
    ),
    AWSTaggableResource("sqs", "AWSSQSQueue", "id"),
)
