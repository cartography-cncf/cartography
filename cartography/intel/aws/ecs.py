import logging
from typing import Any
from typing import Dict
from typing import List

import boto3
import neo4j

from cartography.util import aws_handle_regions
from cartography.util import camel_to_snake
from cartography.util import dict_date_to_epoch
from cartography.util import run_cleanup_job
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


@timeit
def load_ecs_clusters(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    ingest_clusters = """
    UNWIND $Clusters AS cluster
        MERGE (c:ECSCluster{id: cluster.clusterArn})
        ON CREATE SET c.firstseen = timestamp()
        SET c.name = cluster.clusterName, c.region = $Region,
            c.arn = cluster.clusterArn,
            c.ecc_kms_key_id = cluster.configuration.executeCommandConfiguration.kmsKeyId,
            c.ecc_logging = cluster.configuration.executeCommandConfiguration.logging,
            c.ecc_log_configuration_cloud_watch_log_group_name = cluster.configuration.executeCommandConfiguration.logConfiguration.cloudWatchLogGroupName,
            c.ecc_log_configuration_cloud_watch_encryption_enabled = cluster.configuration.executeCommandConfiguration.logConfiguration.cloudWatchEncryptionEnabled,
            c.ecc_log_configuration_s3_bucket_name = cluster.configuration.executeCommandConfiguration.logConfiguration.s3BucketName,
            c.ecc_log_configuration_s3_encryption_enabled = cluster.configuration.executeCommandConfiguration.logConfiguration.s3EncryptionEnabled,
            c.ecc_log_configuration_s3_key_prefix = cluster.configuration.executeCommandConfiguration.logConfiguration.s3KeyPrefix,
            c.status = cluster.status,
            c.settings_container_insights = cluster.settings_container_insights,
            c.capacity_providers = cluster.capacityProviders,
            c.attachments_status = cluster.attachmentsStatus,
            c.lastupdated = $aws_update_tag
        WITH c
        MATCH (owner:AWSAccount{id: $AWS_ACCOUNT_ID})
        MERGE (owner)-[r:RESOURCE]->(c)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $aws_update_tag
    """  # noqa:E501
    clusters: List[Dict[str, Any]] = []
    for cluster in data:
        for setting in cluster.get("settings", []):
            setting_name = camel_to_snake(setting["name"])
            cluster[f"settings_{setting_name}"] = setting["value"]
        clusters.append(cluster)

    neo4j_session.run(
        ingest_clusters,
        Clusters=clusters,
        Region=region,
        AWS_ACCOUNT_ID=current_aws_account_id,
        aws_update_tag=aws_update_tag,
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
    ingest_instances = """
    UNWIND $Instances AS instance
        MERGE (i:ECSContainerInstance{id: instance.containerInstanceArn})
        ON CREATE SET i.firstseen = timestamp()
        SET i.ec2_instance_id = instance.ec2InstanceId, i.region = $Region,
            i.arn = instance.containerInstanceArn,
            i.capacity_provider_name = instance.capacityProviderName,
            i.version = instance.version,
            i.version_info_agent_version = instance.versionInfo.agentVersion,
            i.version_info_agent_hash = instance.versionInfo.agentHash,
            i.version_info_agent_docker_version = instance.versionInfo.dockerVersion,
            i.status = instance.status,
            i.status_reason = instance.statusReason,
            i.agent_connected = instance.agentConnected,
            i.agent_update_status = instance.agentUpdateStatus,
            i.registered_at = instance.registeredAt,
            i.lastupdated = $aws_update_tag
        WITH i
        MATCH (c:ECSCluster{id: $ClusterARN})
        MERGE (c)-[r:HAS_CONTAINER_INSTANCE]->(i)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $aws_update_tag
    """
    instances: List[Dict[str, Any]] = []
    for instance in data:
        instance["registeredAt"] = dict_date_to_epoch(instance, "registeredAt")
        instances.append(instance)

    neo4j_session.run(
        ingest_instances,
        ClusterARN=cluster_arn,
        Instances=instances,
        Region=region,
        AWS_ACCOUNT_ID=current_aws_account_id,
        aws_update_tag=aws_update_tag,
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
    ingest_services = """
    UNWIND $Services AS service
        MERGE (s:ECSService{id: service.serviceArn})
        ON CREATE SET s.firstseen = timestamp()
        SET s.name = service.serviceName, s.region = $Region,
            s.arn = service.serviceArn,
            s.cluster_arn = service.clusterArn,
            s.status = service.status,
            s.desired_count = service.desiredCount,
            s.running_count = service.runningCount,
            s.pending_count = service.pendingCount,
            s.launch_type = service.launchType,
            s.platform_version = service.platformVersion,
            s.platform_family = service.platformFamily,
            s.task_definition = service.taskDefinition,
            s.deployment_config_circuit_breaker_enable = service.deploymentConfiguration.deploymentCircuitBreaker.enable,
            s.deployment_config_circuit_breaker_rollback = service.deploymentConfiguration.deploymentCircuitBreaker.rollback,
            s.deployment_config_maximum_percent = service.deploymentConfiguration.maximumPercent,
            s.deployment_config_minimum_healthy_percent = service.deploymentConfiguration.minimumHealthyPercent,
            s.role_arn = service.roleArn,
            s.created_at = service.createdAt,
            s.health_check_grace_period_seconds = service.healthCheckGracePeriodSeconds,
            s.created_by = service.createdBy,
            s.enable_ecs_managed_tags = service.enableECSManagedTags,
            s.propagate_tags = service.propagateTags,
            s.enable_execute_command = service.enableExecuteCommand,
            s.lastupdated = $aws_update_tag
        WITH s
        MATCH (c:ECSCluster{id: $ClusterARN})
        MERGE (c)-[r:HAS_SERVICE]->(s)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $aws_update_tag
        WITH s
        MATCH (d:ECSTaskDefinition{id: s.task_definition})
        MERGE (s)-[r2:HAS_TASK_DEFINITION]->(d)
        ON CREATE SET r2.firstseen = timestamp()
        SET r2.lastupdated = $aws_update_tag
    """  # noqa:E501
    services: List[Dict[str, Any]] = []
    for service in data:
        service["createdAt"] = dict_date_to_epoch(service, "createdAt")
        services.append(service)

    neo4j_session.run(
        ingest_services,
        ClusterARN=cluster_arn,
        Services=services,
        Region=region,
        AWS_ACCOUNT_ID=current_aws_account_id,
        aws_update_tag=aws_update_tag,
    )


@timeit
def load_ecs_task_definitions(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    ingest_task_definitions = """
    UNWIND $Definitions AS def
        MERGE (d:ECSTaskDefinition{id: def.taskDefinitionArn})
        ON CREATE SET d.firstseen = timestamp()
        SET d.arn = def.taskDefinitionArn,
            d.region = $Region,
            d.family = def.family,
            d.task_role_arn = def.taskRoleArn,
            d.execution_role_arn = def.executionRoleArn,
            d.network_mode = def.networkMode,
            d.revision = def.revision,
            d.status = def.status,
            d.compatibilities = def.compatibilities,
            d.runtime_platform_cpu_architecture = def.runtimePlatform.cpuArchitecture,
            d.runtime_platform_operating_system_family = def.runtimePlatform.operatingSystemFamily,
            d.requires_compatibilities = def.requiresCompatibilities,
            d.cpu = def.cpu,
            d.memory = def.memory,
            d.pid_mode = def.pidMode,
            d.ipc_mode = def.ipcMode,
            d.proxy_configuration_type = def.proxyConfiguration.type,
            d.proxy_configuration_container_name = def.proxyConfiguration.containerName,
            d.registered_at = def.registeredAt,
            d.deregistered_at = def.deregisteredAt,
            d.registered_by = def.registeredBy,
            d.ephemeral_storage_size_in_gib = def.ephemeralStorage.sizeInGiB,
            d.lastupdated = $aws_update_tag
        WITH d
        MATCH (task:ECSTask{task_definition_arn: d.arn})
        MERGE (task)-[r:HAS_TASK_DEFINITION]->(d)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $aws_update_tag
        WITH d
        MATCH (owner:AWSAccount{id: $AWS_ACCOUNT_ID})
        MERGE (owner)-[r:RESOURCE]->(d)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $aws_update_tag
    """
    container_definitions: List[Dict[str, Any]] = []
    task_definitions: List[Dict[str, Any]] = []
    for task_definition in data:
        task_definition["registeredAt"] = dict_date_to_epoch(
            task_definition,
            "registeredAt",
        )
        task_definition["deregisteredAt"] = dict_date_to_epoch(
            task_definition,
            "deregisteredAt",
        )
        for container in task_definition.get("containerDefinitions", []):
            container["_taskDefinitionArn"] = task_definition["taskDefinitionArn"]
            container_definitions.append(container)
        task_definitions.append(task_definition)

    neo4j_session.run(
        ingest_task_definitions,
        Definitions=task_definitions,
        Region=region,
        AWS_ACCOUNT_ID=current_aws_account_id,
        aws_update_tag=aws_update_tag,
    )

    load_ecs_container_definitions(
        neo4j_session,
        container_definitions,
        region,
        current_aws_account_id,
        aws_update_tag,
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
    ingest_tasks = """
    UNWIND $Tasks AS task
        MERGE (t:ECSTask{id: task.taskArn})
        ON CREATE SET t.firstseen = timestamp()
        SET t.arn = task.taskArn, t.region = $Region,
            t.availability_zone = task.availabilityZone,
            t.capacity_provider_name = task.capacityProviderName,
            t.cluster_arn = task.clusterArn,
            t.connectivity = task.connectivity,
            t.connectivity_at = task.connectivityAt,
            t.container_instance_arn = task.containerInstanceArn,
            t.cpu = task.cpu,
            t.created_at = task.createdAt,
            t.desired_status = task.desiredStatus,
            t.enable_execute_command = task.enableExecuteCommand,
            t.execution_stopped_at = task.executionStoppedAt,
            t.group = task.group,
            t.health_status = task.healthStatus,
            t.last_status = task.lastStatus,
            t.launch_type = task.launchType,
            t.memory = task.memory,
            t.platform_version = task.platformVersion,
            t.platform_family = task.platformFamily,
            t.pull_started_at = task.pullStartedAt,
            t.pull_stopped_at = task.pullStoppedAt,
            t.started_at = task.startedAt,
            t.started_by = task.startedBy,
            t.stop_code = task.stopCode,
            t.stopped_at = task.stoppedAt,
            t.stopped_reason = task.stoppedReason,
            t.stopping_at = task.stoppingAt,
            t.task_definition_arn = task.taskDefinitionArn,
            t.version = task.version,
            t.ephemeral_storage_size_in_gib = task.ephemeralStorage.sizeInGiB,
            t.lastupdated = $aws_update_tag
        WITH t
        MATCH (c:ECSCluster{id: $ClusterARN})
        MERGE (c)-[r:HAS_TASK]->(t)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $aws_update_tag
        WITH t
        MATCH (td:ECSTaskDefinition{id: t.task_definition_arn})
        MERGE (t)-[r2:HAS_TASK_DEFINITION]->(td)
        ON CREATE SET r2.firstseen = timestamp()
        SET r2.lastupdated = $aws_update_tag
        WITH t
        MATCH (ci:ECSContainerInstance{id: t.container_instance_arn})
        MERGE (ci)-[r3:HAS_TASK]->(t)
        ON CREATE SET r3.firstseen = timestamp()
        SET r3.lastupdated = $aws_update_tag
    """
    containers: List[Dict[str, Any]] = []
    tasks: List[Dict[str, Any]] = []
    for task in data:
        task["connectivityAt"] = dict_date_to_epoch(task, "connectivityAt")
        task["createdAt"] = dict_date_to_epoch(task, "createdAt")
        task["executionStoppedAt"] = dict_date_to_epoch(task, "executionStoppedAt")
        task["pullStartedAt"] = dict_date_to_epoch(task, "pullStartedAt")
        task["pullStoppedAt"] = dict_date_to_epoch(task, "pullStoppedAt")
        task["startedAt"] = dict_date_to_epoch(task, "startedAt")
        task["stoppedAt"] = dict_date_to_epoch(task, "stoppedAt")
        task["stoppingAt"] = dict_date_to_epoch(task, "stoppingAt")
        containers.extend(task["containers"])
        tasks.append(task)

    neo4j_session.run(
        ingest_tasks,
        ClusterARN=cluster_arn,
        Tasks=tasks,
        Region=region,
        AWS_ACCOUNT_ID=current_aws_account_id,
        aws_update_tag=aws_update_tag,
    )

    load_ecs_containers(
        neo4j_session,
        containers,
        region,
        current_aws_account_id,
        aws_update_tag,
    )


@timeit
def load_ecs_container_definitions(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    ingest_definitions = """
    UNWIND $Definitions AS def
        MERGE (d:ECSContainerDefinition{id: def._taskDefinitionArn + "-" + def.name})
        ON CREATE SET d.firstseen = timestamp()
        SET d.task_definition_arn = def._taskDefinitionArn, d.region = $Region,
            d.name = def.name,
            d.image = def.image,
            d.cpu = def.cpu,
            d.memory = def.memory,
            d.memory_reservation = def.memoryReservation,
            d.links = def.links,
            d.essential = def.essential,
            d.entry_point = def.entryPoint,
            d.command = def.command,
            d.start_timeout = def.startTimeout,
            d.stop_timeout = def.stop_timeout,
            d.hostname = def.hostname,
            d.user = def.user,
            d.working_directory = def.workingDirectory,
            d.disable_networking = def.disableNetworking,
            d.privileged = def.privileged,
            d.readonly_root_filesystem = def.readonlyRootFilesystem,
            d.dns_servers = def.dnsServers,
            d.dns_search_domains = def.dnsSearchDomains,
            d.docker_security_options = def.dockerSecurityOptions,
            d.interactive = def.interactive,
            d.pseudo_terminal = def.pseudoTerminal,
            d.lastupdated = $aws_update_tag
        WITH d
        MATCH (td:ECSTaskDefinition{id: d.task_definition_arn})
        MERGE (td)-[r:HAS_CONTAINER_DEFINITION]->(d)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $aws_update_tag
    """
    neo4j_session.run(
        ingest_definitions,
        Definitions=data,
        Region=region,
        AWS_ACCOUNT_ID=current_aws_account_id,
        aws_update_tag=aws_update_tag,
    )


@timeit
def load_ecs_containers(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    ingest_containers = """
    UNWIND $Containers AS container
        MERGE (c:ECSContainer{id: container.containerArn})
        ON CREATE SET c.firstseen = timestamp()
        SET c.arn = container.containerArn, c.region = $Region,
            c.task_arn = container.taskArn,
            c.name = container.name,
            c.image = container.image,
            c.image_digest = container.imageDigest,
            c.runtime_id = container.runtimeId,
            c.last_status = container.lastStatus,
            c.exit_code = container.exitCode,
            c.reason = container.reason,
            c.health_status = container.healthStatus,
            c.cpu = container.cpu,
            c.memory = container.memory,
            c.memory_reservation = container.memoryReservation,
            c.gpu_ids = container.gpuIds,
            c.lastupdated = $aws_update_tag
        WITH c
        MATCH (t:ECSTask{id: c.task_arn})
        MERGE (t)-[r:HAS_CONTAINER]->(c)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $aws_update_tag
    """
    neo4j_session.run(
        ingest_containers,
        Containers=data,
        Region=region,
        AWS_ACCOUNT_ID=current_aws_account_id,
        aws_update_tag=aws_update_tag,
    )


@timeit
def cleanup_ecs(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job("aws_import_ecs_cleanup.json", neo4j_session, common_job_parameters)


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
            "Syncing ECS for region '%s' in account '%s'.",
            region,
            current_aws_account_id,
        )
        cluster_arns = get_ecs_cluster_arns(boto3_session, region)
        clusters = get_ecs_clusters(boto3_session, region, cluster_arns)
        if len(clusters) == 0:
            continue
        load_ecs_clusters(
            neo4j_session,
            clusters,
            region,
            current_aws_account_id,
            update_tag,
        )
        for cluster_arn in cluster_arns:
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
            tasks = get_ecs_tasks(
                cluster_arn,
                boto3_session,
                region,
            )
            load_ecs_tasks(
                neo4j_session,
                cluster_arn,
                tasks,
                region,
                current_aws_account_id,
                update_tag,
            )
            task_definitions = get_ecs_task_definitions(
                boto3_session,
                region,
                tasks,
            )
            load_ecs_task_definitions(
                neo4j_session,
                task_definitions,
                region,
                current_aws_account_id,
                update_tag,
            )
    cleanup_ecs(neo4j_session, common_job_parameters)
