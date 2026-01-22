import logging
from typing import Any
from typing import Dict
from typing import List

import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.aws.ecs.clusters import ECSClusterSchema
from cartography.models.aws.ecs.container_definitions import (
    ECSContainerDefinitionSchema,
)
from cartography.models.aws.ecs.container_instances import ECSContainerInstanceSchema
from cartography.models.aws.ecs.containers import ECSContainerSchema
from cartography.models.aws.ecs.services import ECSServiceSchema
from cartography.models.aws.ecs.task_definitions import ECSTaskDefinitionSchema
from cartography.models.aws.ecs.tasks import ECSTaskSchema
from cartography.util import aws_handle_regions
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_ecs_cluster_arns(
    boto3_session: boto3.session.Session,
    region: str,
) -> List[str]:
    client = boto3_session.client("ecs", region_name=region)
    paginator = client.get_paginator("list_clusters")
    cluster_arns: List[str] = []
    for page in paginator.paginate():
        cluster_arns.extend(page.get("clusterArns", []))
    return cluster_arns


@timeit
@aws_handle_regions
def get_ecs_clusters(
    boto3_session: boto3.session.Session,
    region: str,
    cluster_arns: List[str],
) -> List[Dict[str, Any]]:
    client = boto3_session.client("ecs", region_name=region)
    # TODO: also include attachment info, and make relationships between the attachements
    # and the cluster.
    includes = ["SETTINGS", "CONFIGURATIONS"]
    clusters: List[Dict[str, Any]] = []
    for i in range(0, len(cluster_arns), 100):
        cluster_arn_chunk = cluster_arns[i : i + 100]
        cluster_chunk = client.describe_clusters(
            clusters=cluster_arn_chunk,
            include=includes,
        )
        clusters.extend(cluster_chunk.get("clusters", []))
    return clusters


@timeit
@aws_handle_regions
def get_ecs_container_instances(
    cluster_arn: str,
    boto3_session: boto3.session.Session,
    region: str,
) -> List[Dict[str, Any]]:
    client = boto3_session.client("ecs", region_name=region)
    paginator = client.get_paginator("list_container_instances")
    container_instances: List[Dict[str, Any]] = []
    container_instance_arns: List[str] = []
    for page in paginator.paginate(cluster=cluster_arn):
        container_instance_arns.extend(page.get("containerInstanceArns", []))
    includes = ["CONTAINER_INSTANCE_HEALTH"]
    for i in range(0, len(container_instance_arns), 100):
        container_instance_arn_chunk = container_instance_arns[i : i + 100]
        container_instance_chunk = client.describe_container_instances(
            cluster=cluster_arn,
            containerInstances=container_instance_arn_chunk,
            include=includes,
        )
        container_instances.extend(
            container_instance_chunk.get("containerInstances", []),
        )
    return container_instances


@timeit
@aws_handle_regions
def get_ecs_services(
    cluster_arn: str,
    boto3_session: boto3.session.Session,
    region: str,
) -> List[Dict[str, Any]]:
    client = boto3_session.client("ecs", region_name=region)
    paginator = client.get_paginator("list_services")
    services: List[Dict[str, Any]] = []
    service_arns: List[str] = []
    for page in paginator.paginate(cluster=cluster_arn):
        service_arns.extend(page.get("serviceArns", []))
    for i in range(0, len(service_arns), 10):
        service_arn_chunk = service_arns[i : i + 10]
        service_chunk = client.describe_services(
            cluster=cluster_arn,
            services=service_arn_chunk,
        )
        services.extend(service_chunk.get("services", []))
    return services


@timeit
@aws_handle_regions
def get_ecs_task_definitions(
    boto3_session: boto3.session.Session,
    region: str,
    tasks: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    client = boto3_session.client("ecs", region_name=region)
    task_definitions: List[Dict[str, Any]] = []
    for task in tasks:
        task_definition = client.describe_task_definition(
            taskDefinition=task["taskDefinitionArn"],
        )
        task_definitions.append(task_definition["taskDefinition"])
    return task_definitions


def _get_container_defs_from_task_definitions(
    definitions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    container_defs: list[dict[str, Any]] = []
    for td in definitions:
        for container in td.get("containerDefinitions", []):
            c = container.copy()
            c["_taskDefinitionArn"] = td["taskDefinitionArn"]
            c["id"] = f"{td['taskDefinitionArn']}-{c['name']}"
            container_defs.append(c)
    return container_defs


@timeit
@aws_handle_regions
def get_ecs_tasks(
    cluster_arn: str,
    boto3_session: boto3.session.Session,
    region: str,
) -> List[Dict[str, Any]]:
    client = boto3_session.client("ecs", region_name=region)
    paginator = client.get_paginator("list_tasks")
    tasks: List[Dict[str, Any]] = []
    task_arns: List[str] = []
    for page in paginator.paginate(cluster=cluster_arn):
        task_arns.extend(page.get("taskArns", []))
    for i in range(0, len(task_arns), 100):
        task_arn_chunk = task_arns[i : i + 100]
        task_chunk = client.describe_tasks(
            cluster=cluster_arn,
            tasks=task_arn_chunk,
        )
        tasks.extend(task_chunk.get("tasks", []))
    return tasks


def _get_containers_from_tasks(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    containers: list[dict[str, Any]] = []
    for task in tasks:
        containers.extend(task.get("containers", []))
    return containers


def transform_ecs_tasks(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Extract network interface ID from task attachments and service name from group.
    """
    for task in tasks:
        # Extract serviceName from group field
        group = task.get("group")
        if group and group.startswith("service:"):
            task["serviceName"] = group.split("service:", 1)[1]

        # Extract network interface ID from task attachments
        for attachment in task.get("attachments", []):
            if attachment.get("type") == "ElasticNetworkInterface":
                details = attachment.get("details", [])
                for detail in details:
                    if detail.get("name") == "networkInterfaceId":
                        task["networkInterfaceId"] = detail.get("value")
                        break
                break
    return tasks


@timeit
def load_ecs_clusters(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    load(
        neo4j_session,
        ECSClusterSchema(),
        data,
        Region=region,
        AWS_ID=current_aws_account_id,
        lastupdated=aws_update_tag,
    )


@timeit
def load_ecs_container_instances(
    neo4j_session: neo4j.Session,
    cluster_arn: str,
    data: List[Dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    load(
        neo4j_session,
        ECSContainerInstanceSchema(),
        data,
        ClusterArn=cluster_arn,
        Region=region,
        AWS_ID=current_aws_account_id,
        lastupdated=aws_update_tag,
    )


@timeit
def load_ecs_services(
    neo4j_session: neo4j.Session,
    cluster_arn: str,
    data: List[Dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    load(
        neo4j_session,
        ECSServiceSchema(),
        data,
        ClusterArn=cluster_arn,
        Region=region,
        AWS_ID=current_aws_account_id,
        lastupdated=aws_update_tag,
    )


@timeit
def load_ecs_task_definitions(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    load(
        neo4j_session,
        ECSTaskDefinitionSchema(),
        data,
        Region=region,
        AWS_ID=current_aws_account_id,
        lastupdated=aws_update_tag,
    )


@timeit
def load_ecs_tasks(
    neo4j_session: neo4j.Session,
    cluster_arn: str,
    data: List[Dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    load(
        neo4j_session,
        ECSTaskSchema(),
        data,
        ClusterArn=cluster_arn,
        Region=region,
        AWS_ID=current_aws_account_id,
        lastupdated=aws_update_tag,
    )


@timeit
def load_ecs_container_definitions(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    load(
        neo4j_session,
        ECSContainerDefinitionSchema(),
        data,
        Region=region,
        AWS_ID=current_aws_account_id,
        lastupdated=aws_update_tag,
    )


@timeit
def load_ecs_containers(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    load(
        neo4j_session,
        ECSContainerSchema(),
        data,
        Region=region,
        AWS_ID=current_aws_account_id,
        lastupdated=aws_update_tag,
    )


@timeit
def cleanup_ecs(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    GraphJob.from_node_schema(ECSContainerSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(ECSTaskSchema(), common_job_parameters).run(neo4j_session)
    GraphJob.from_node_schema(ECSContainerInstanceSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(ECSServiceSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(
        ECSContainerDefinitionSchema(), common_job_parameters
    ).run(neo4j_session)
    GraphJob.from_node_schema(ECSTaskDefinitionSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(ECSClusterSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def _sync_ecs_cluster_arns(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    cluster_arns: List[str],
    region: str,
    current_aws_account_id: str,
    update_tag: int,
) -> None:
    clusters = get_ecs_clusters(boto3_session, region, cluster_arns)
    if len(clusters) == 0:
        return
    load_ecs_clusters(
        neo4j_session,
        clusters,
        region,
        current_aws_account_id,
        update_tag,
    )


@timeit
def _sync_ecs_container_instances(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    cluster_arn: str,
    region: str,
    current_aws_account_id: str,
    update_tag: int,
) -> None:
    cluster_instances = get_ecs_container_instances(
        cluster_arn,
        boto3_session,
        region,
    )
    load_ecs_container_instances(
        neo4j_session,
        cluster_arn,
        cluster_instances,
        region,
        current_aws_account_id,
        update_tag,
    )


@timeit
def _sync_ecs_services(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    cluster_arn: str,
    region: str,
    current_aws_account_id: str,
    update_tag: int,
) -> None:
    services = get_ecs_services(
        cluster_arn,
        boto3_session,
        region,
    )
    load_ecs_services(
        neo4j_session,
        cluster_arn,
        services,
        region,
        current_aws_account_id,
        update_tag,
    )


@timeit
def _sync_ecs_task_and_container_defns(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    cluster_arn: str,
    region: str,
    current_aws_account_id: str,
    update_tag: int,
) -> None:
    tasks = get_ecs_tasks(
        cluster_arn,
        boto3_session,
        region,
    )
    tasks = transform_ecs_tasks(tasks)
    containers = _get_containers_from_tasks(tasks)
    load_ecs_tasks(
        neo4j_session,
        cluster_arn,
        tasks,
        region,
        current_aws_account_id,
        update_tag,
    )
    load_ecs_containers(
        neo4j_session,
        containers,
        region,
        current_aws_account_id,
        update_tag,
    )

    task_definitions = get_ecs_task_definitions(
        boto3_session,
        region,
        tasks,
    )
    container_defs = _get_container_defs_from_task_definitions(task_definitions)
    load_ecs_task_definitions(
        neo4j_session,
        task_definitions,
        region,
        current_aws_account_id,
        update_tag,
    )
    load_ecs_container_definitions(
        neo4j_session,
        container_defs,
        region,
        current_aws_account_id,
        update_tag,
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: List[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: Dict,
) -> None:
    for region in regions:
        logger.info(
            f"Syncing ECS for region '{region}' in account '{current_aws_account_id}'.",
        )
        cluster_arns = get_ecs_cluster_arns(boto3_session, region)
        _sync_ecs_cluster_arns(
            neo4j_session,
            boto3_session,
            cluster_arns,
            region,
            current_aws_account_id,
            update_tag,
        )
        for cluster_arn in cluster_arns:
            _sync_ecs_container_instances(
                neo4j_session,
                boto3_session,
                cluster_arn,
                region,
                current_aws_account_id,
                update_tag,
            )
            _sync_ecs_task_and_container_defns(
                neo4j_session,
                boto3_session,
                cluster_arn,
                region,
                current_aws_account_id,
                update_tag,
            )
            _sync_ecs_services(
                neo4j_session,
                boto3_session,
                cluster_arn,
                region,
                current_aws_account_id,
                update_tag,
            )
    cleanup_ecs(neo4j_session, common_job_parameters)
