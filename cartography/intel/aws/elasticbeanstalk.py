import logging
from pprint import pprint
from typing import Any
from typing import Dict
from typing import List

import boto3
import neo4j
from collections import namedtuple

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.aws.elasticbeanstalk.environment import ElasticBeanstalkEnvironmentSchema
from cartography.stats import get_stats_client
from cartography.util import aws_handle_regions
from cartography.util import merge_module_sync_metadata
from cartography.util import timeit

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)

@timeit
@aws_handle_regions
def get_elasticbeanstak_environments(
    boto3_session: boto3.session.Session,
    region: str,
) -> list[dict[str, Any]]:
    client = boto3_session.client("elasticbeanstalk", region_name=region)
    paginator = client.get_paginator("describe_environments")
    environments: list[dict[str, Any]] = []
    for page in paginator.paginate():
        # I'm not sure why describe_environments doesn't return resources as well,
        # the docs suggest it should. Instead, do a call for each environment 
        # and add the resources to them
        for environment in page.get("Environments",[]):
            resources = client.describe_environment_resources(EnvironmentId=environment["EnvironmentId"])
            environment["Resources"] = resources.get("EnvironmentResources")
            environments.append(environment)
    
    return environments


def transform_elasticbeanstalk_environments(
    environments: list[dict[str, Any]], region: str
) -> List[Dict[str, Any]]:
    
    environment_list = []

    for environment in environments:

        environment_id = environment["EnvironmentId"]

        environment_record = {
            "EnvironmentId": environment_id,
            "EnvironmentArn": environment["EnvironmentArn"],
            "EnvironmentName": environment.get("EnvironmentName"),
            "ApplicationName": environment.get("ApplicationName"),
            "VersionLabel": environment.get("VersionLabel"),
            "SolutionStackName": environment.get("SolutionStackName"),
            "PlatformArn": environment.get("PlatformArn"),
            "EndpointURL": environment.get("EndpointURL"),
            "CNAME": environment.get("CNAME"),
            "Status": environment.get("Status"),
            "AbortableOperationInProgress": environment.get("AbortableOperationInProgress"),
            "Health": environment.get("Health"),
            "HealthStatus": environment.get("HealthStatus"),
            "Region": region,
        }

        if environment.get("Resources"):
            resources = environment["Resources"]

            # These fields are set so that relationships can match on them (e.g. ElasticBeanstalkToInstanceRel)
            environment_record["ASG_NAMES"] = [str(res["Name"]) for res in resources.get("AutoScalingGroups", [])]
            environment_record["INSTANCE_IDS"] = [str(res["Id"]) for res in resources.get("Instances", [])]
            environment_record["LAUNCHCONFIG_NAMES"] =  [str(res["Name"]) for res in resources.get("LaunchConfigurations", [])]
            environment_record["LAUNCHTEMPLATE_IDS"] = [str(res["Id"]) for res in resources.get("LaunchTemplates", [])]
            environment_record["LOADBALANCER_NAMES"] = [str(res["Name"]) for res in resources.get("LoadBalancers", [])]
            environment_record["QUEUE_URLS"] = [str(res["URL"]) for res in resources.get("Queues", [])]
            environment_record["TRIGGER_NAMES"] =  [str(res["Name"]) for res in resources.get("Triggers", [])]

        environment_list.append(environment_record)

    return environment_list



@timeit
def load_environments(
    neo4j_session: neo4j.Session,
    data: list[dict],
    region: str,
    current_aws_account_id: str,
    update_tag: int,
) -> None:
    
    logger.info(
        f"Loading {len(data)} ElasticBeanstalk environments for region '{region}' into graph."
    )
    load(
        neo4j_session,
        ElasticBeanstalkEnvironmentSchema(),
        data,
        Region=region,
        AWS_ID=current_aws_account_id,
        lastupdated=update_tag,
    )

@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(ElasticBeanstalkEnvironmentSchema(), common_job_parameters).run(
        neo4j_session
    )

@timeit
def sync(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: list[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    for region in regions:
        logger.info(
            "Syncing ElasticBeanstalk environments for region '%s' in account '%s'.",
            region,
            current_aws_account_id,
        )
        raw_environments = get_elasticbeanstak_environments(boto3_session, region)
        elasticbeanstalk_data = transform_elasticbeanstalk_environments(raw_environments, region)
        load_environments(
            neo4j_session,
            elasticbeanstalk_data,
            region,
            current_aws_account_id,
            update_tag,
        )
    cleanup(neo4j_session, common_job_parameters)
    merge_module_sync_metadata(
        neo4j_session,
        group_type="AWSAccount",
        group_id=current_aws_account_id,
        synced_type="ElasticBeanstalkEnvironment",
        update_tag=update_tag,
        stat_handler=stat_handler,
    )
