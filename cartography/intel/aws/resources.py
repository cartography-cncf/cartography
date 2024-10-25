from typing import Dict

from cartography.intel.aws import apigateway
from cartography.intel.aws import config
from cartography.intel.aws import dynamodb
from cartography.intel.aws import ecr
from cartography.intel.aws import ecs
from cartography.intel.aws import eks
from cartography.intel.aws import elasticache
from cartography.intel.aws import elasticsearch
from cartography.intel.aws import emr
from cartography.intel.aws import iam
from cartography.intel.aws import inspector
from cartography.intel.aws import kms
from cartography.intel.aws import lambda_function
from cartography.intel.aws import permission_relationships
from cartography.intel.aws import rds
from cartography.intel.aws import redshift
from cartography.intel.aws import resourcegroupstaggingapi
from cartography.intel.aws import route53
from cartography.intel.aws import s3
from cartography.intel.aws import secretsmanager
from cartography.intel.aws import securityhub
from cartography.intel.aws import sqs
from cartography.intel.aws import ssm
from cartography.intel.aws.ec2.auto_scaling_groups import sync_ec2_auto_scaling_groups
from cartography.intel.aws.ec2.elastic_ip_addresses import sync_elastic_ip_addresses
from cartography.intel.aws.ec2.images import sync_ec2_images
from cartography.intel.aws.ec2.instances import sync_ec2_instances
from cartography.intel.aws.ec2.internet_gateways import sync_internet_gateways
from cartography.intel.aws.ec2.key_pairs import sync_ec2_key_pairs
from cartography.intel.aws.ec2.launch_templates import sync_ec2_launch_templates
from cartography.intel.aws.ec2.load_balancer_v2s import sync_load_balancer_v2s
from cartography.intel.aws.ec2.load_balancers import sync_load_balancers
from cartography.intel.aws.ec2.network_interfaces import sync_network_interfaces
from cartography.intel.aws.ec2.reserved_instances import sync_ec2_reserved_instances
from cartography.intel.aws.ec2.security_groups import sync_ec2_security_groupinfo
from cartography.intel.aws.ec2.snapshots import sync_ebs_snapshots
from cartography.intel.aws.ec2.subnets import sync_subnets
from cartography.intel.aws.ec2.tgw import sync_transit_gateways
from cartography.intel.aws.ec2.volumes import sync_ebs_volumes
from cartography.intel.aws.ec2.vpc import sync_vpc
from cartography.intel.aws.ec2.vpc_peerings import sync_vpc_peerings

RESOURCE_FUNCTIONS: Dict = {
    'iam': iam.sync,
    's3': s3.sync,
    'dynamodb': dynamodb.sync,
    'ec2:launch_templates': sync_ec2_launch_templates,
    'ec2:autoscalinggroup': sync_ec2_auto_scaling_groups,
    # `ec2:instance` must be included before `ssm` and `ec2:images`,
    # they rely on EC2Instance data provided by this module.
    'ec2:instance': sync_ec2_instances,
    'ec2:images': sync_ec2_images,
    'ec2:keypair': sync_ec2_key_pairs,
    'ec2:load_balancer': sync_load_balancers,
    'ec2:load_balancer_v2': sync_load_balancer_v2s,
    'ec2:network_interface': sync_network_interfaces,
    'ec2:security_group': sync_ec2_security_groupinfo,
    'ec2:subnet': sync_subnets,
    'ec2:tgw': sync_transit_gateways,
    'ec2:vpc': sync_vpc,
    'ec2:vpc_peering': sync_vpc_peerings,
    'ec2:internet_gateway': sync_internet_gateways,
    'ec2:reserved_instances': sync_ec2_reserved_instances,
    'ec2:volumes': sync_ebs_volumes,
    'ec2:snapshots': sync_ebs_snapshots,
    'ecr': ecr.sync,
    'ecs': ecs.sync,
    'eks': eks.sync,
    'elasticache': elasticache.sync,
    'elastic_ip_addresses': sync_elastic_ip_addresses,
    'emr': emr.sync,
    'lambda_function': lambda_function.sync,
    'kms': kms.sync,
    'rds': rds.sync,
    'redshift': redshift.sync,
    'route53': route53.sync,
    'elasticsearch': elasticsearch.sync,
    'permission_relationships': permission_relationships.sync,
    'resourcegroupstaggingapi': resourcegroupstaggingapi.sync,
    'apigateway': apigateway.sync,
    'secretsmanager': secretsmanager.sync,
    'securityhub': securityhub.sync,
    'sqs': sqs.sync,
    'ssm': ssm.sync,
    'inspector': inspector.sync,
    'config': config.sync,
}
