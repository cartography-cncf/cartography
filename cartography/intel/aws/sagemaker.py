import logging
import time
from typing import Dict
from typing import List

import boto3
import neo4j

from cartography.intel.aws.ec2.util import get_botocore_config
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


def get_boto3_client(boto3_session: boto3.session.Session, service: str, region: str):
    client = boto3_session.client(service, region_name=region, config=get_botocore_config())
    return client


@timeit
def get_notebook_instances_list(boto3_session: boto3.session.Session, region: str) -> List[Dict]:
    instances: List[Dict] = []
    try:
        client = get_boto3_client(boto3_session, "sagemaker", region)

        paginator = client.get_paginator("list_notebook_instances")
        for page in paginator.paginate():
            instances.extend(page["NotebookInstances"])

        for instance in instances:
            instance["region"] = region

    except Exception as e:
        logger.warning(
            f"Could not list sagemaker notebook instances. skipping. - {e}",
        )
    return instances


@timeit
def load_notebook_instances(
    neo4j_session: neo4j.Session,
    instances: List[Dict],
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    neo4j_session.write_transaction(_load_notebook_instances_tx, instances, current_aws_account_id, aws_update_tag)


@timeit
def _load_notebook_instances_tx(
    tx: neo4j.Transaction,
    instances: List[Dict],
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    ingest_instances = """
    UNWIND $instances AS instance
    MERGE (i:AWSSagemakerNotebookInstance{arn:instance.NotebookInstanceArn})
    ON CREATE SET i.firstseen = timestamp(),
    i.arn = instance.NotebookInstanceArn,
    i.creationtime = instance.CreationTime
    SET i.lastmodifiedtime = instance.LastModifiedTime,
    i.name = instance.NotebookInstanceName,
    i.status = instance.NotebookInstanceStatus,
    i.url = instance.Url,
    i.instancetype = instance.InstanceType,
    i.defaultcoderepository = instance.DefaultCodeRepository,
    i.lastupdated =$aws_update_tag,
    i.region = instance.region
    WITH i
    MATCH (aa:AWSAccount{id: $AWS_ACCOUNT_ID})
    MERGE (aa)-[r:RESOURCE]->(i)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $aws_update_tag
    """

    tx.run(
        ingest_instances,
        instances=instances,
        AWS_ACCOUNT_ID=current_aws_account_id,
        aws_update_tag=aws_update_tag,
    )


@timeit
def get_endpoints_list(boto3_session: boto3.session.Session, region: str) -> List[Dict]:
    endpoints: List[Dict] = []
    try:
        client = get_boto3_client(boto3_session, "sagemaker", region)

        paginator = client.get_paginator("list_endpoints")
        for page in paginator.paginate():
            endpoints.extend(page["Endpoints"])

        for endpoint in endpoints:
            endpoint["region"] = region

    except Exception as e:
        logger.warning(
            f"Could not list sagemaker endpoints. skipping. - {e}",
        )
    return endpoints


@timeit
def load_endpoints(
    neo4j_session: neo4j.Session,
    endpoints: List[Dict],
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    neo4j_session.write_transaction(_load_endpoints_tx, endpoints, current_aws_account_id, aws_update_tag)


@timeit
def _load_endpoints_tx(
    tx: neo4j.Transaction,
    endpoints: List[Dict],
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    ingest_endpoints = """
    UNWIND $endpoints AS endpoint
    MERGE (e:AWSSagemakerEndpoint{arn:endpoint.EndpointArn})
    ON CREATE SET e.firstseen = timestamp(),
    e.arn = endpoint.EndpointArn,
    e.creationtime = endpoint.CreationTime
    SET e.lastmodifiedtime = endpoint.LastModifiedTime,
    e.name = endpoint.EndpointName,
    e.status = endpoint.EndpointStatus,
    e.lastupdated =$aws_update_tag,
    e.region = endpoint.region
    WITH e
    MATCH (aa:AWSAccount{id: $AWS_ACCOUNT_ID})
    MERGE (aa)-[r:RESOURCE]->(e)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $aws_update_tag
    """

    tx.run(
        ingest_endpoints,
        endpoints=endpoints,
        AWS_ACCOUNT_ID=current_aws_account_id,
        aws_update_tag=aws_update_tag,
    )


@timeit
def get_training_jobs_list(boto3_session: boto3.session.Session, region: str) -> List[Dict]:
    training_jobs: List[Dict] = []
    try:
        client = get_boto3_client(boto3_session, "sagemaker", region)

        paginator = client.get_paginator("list_training_jobs")
        for page in paginator.paginate():
            training_jobs.extend(page["TrainingJobSummaries"])

        for training_job in training_jobs:
            training_job["region"] = region

    except Exception as e:
        logger.warning(
            f"Could not list sagemaker training jobs. skipping. - {e}",
        )
    return training_jobs


@timeit
def load_training_jobs(
    neo4j_session: neo4j.Session,
    training_jobs: List[Dict],
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    neo4j_session.write_transaction(_load_training_jobs_tx, training_jobs, current_aws_account_id, aws_update_tag)


@timeit
def _load_training_jobs_tx(
    tx: neo4j.Transaction,
    training_jobs: List[Dict],
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    ingest_training_jobs = """
    UNWIND $training_jobs AS job
    MERGE (i:AWSSagemakerTrainingJob{arn:job.TrainingJobArn})
    ON CREATE SET i.firstseen = timestamp(),
    i.arn = job.TrainingJobArn,
    i.creationtime = job.CreationTime
    SET i.lastmodifiedtime = job.LastModifiedTime,
    i.name = job.TrainingJobName,
    i.status = job.TrainingJobStatus,
    i.trainingplanarn = job.TrainingPlanArn,
    i.lastupdated =$aws_update_tag,
    i.region = job.region
    WITH i
    MATCH (aa:AWSAccount{id: $AWS_ACCOUNT_ID})
    MERGE (aa)-[r:RESOURCE]->(i)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $aws_update_tag
    """

    tx.run(
        ingest_training_jobs,
        training_jobs=training_jobs,
        AWS_ACCOUNT_ID=current_aws_account_id,
        aws_update_tag=aws_update_tag,
    )


@timeit
def get_models_list(boto3_session: boto3.session.Session, region: str) -> List[Dict]:
    models: List[Dict] = []
    try:
        client = get_boto3_client(boto3_session, "sagemaker", region)

        paginator = client.get_paginator("list_models")
        for page in paginator.paginate():
            models.extend(page["Models"])

        for model in models:
            model["region"] = region

    except Exception as e:
        logger.warning(
            f"Could not list sagemaker models. skipping. - {e}",
        )
    return models


@timeit
def load_models(
    neo4j_session: neo4j.Session,
    models: List[Dict],
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    neo4j_session.write_transaction(_load_models_tx, models, current_aws_account_id, aws_update_tag)


@timeit
def _load_models_tx(
    tx: neo4j.Transaction,
    models: List[Dict],
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    ingest_models = """
    UNWIND $models AS model
    MERGE (e:AWSSagemakerModel{arn:model.ModelArn})
    ON CREATE SET e.firstseen = timestamp(),
    e.arn = model.ModelArn,
    e.creationtime = model.CreationTime
    SET e.name = model.ModelName,
    e.lastupdated =$aws_update_tag,
    e.region = model.region
    WITH e
    MATCH (aa:AWSAccount{id: $AWS_ACCOUNT_ID})
    MERGE (aa)-[r:RESOURCE]->(e)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $aws_update_tag
    """

    tx.run(
        ingest_models,
        models=models,
        AWS_ACCOUNT_ID=current_aws_account_id,
        aws_update_tag=aws_update_tag,
    )


@timeit
def get_domains_list(boto3_session: boto3.session.Session, region: str) -> List[Dict]:
    domains: List[Dict] = []
    try:
        client = get_boto3_client(boto3_session, "sagemaker", region)

        paginator = client.get_paginator("list_domains")
        for page in paginator.paginate():
            domains.extend(page["Domains"])

        for domain in domains:
            domain["region"] = region

    except Exception as e:
        logger.warning(
            f"Could not list sagemaker domains. skipping. - {e}",
        )
    return domains


@timeit
def load_domains(
    neo4j_session: neo4j.Session,
    domains: List[Dict],
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    neo4j_session.write_transaction(_load_domains_tx, domains, current_aws_account_id, aws_update_tag)


@timeit
def _load_domains_tx(
    tx: neo4j.Transaction,
    domains: List[Dict],
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    ingest_domains = """
    UNWIND $domains AS domain
    MERGE (i:AWSSagemakerDomain{arn:domain.DomainArn})
    ON CREATE SET i.firstseen = timestamp(),
    i.arn = domain.DomainArn,
    i.creationtime = domain.CreationTime
    SET i.lastmodifiedtime = domain.LastModifiedTime,
    i.name = domain.DomainName,
    i.status = domain.Status,
    i.url = domain.Url,
    i.id = domain.DomainId,
    i.lastupdated =$aws_update_tag,
    i.region = domain.region
    WITH i
    MATCH (aa:AWSAccount{id: $AWS_ACCOUNT_ID})
    MERGE (aa)-[r:RESOURCE]->(i)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $aws_update_tag
    """

    tx.run(
        ingest_domains,
        domains=domains,
        AWS_ACCOUNT_ID=current_aws_account_id,
        aws_update_tag=aws_update_tag,
    )


@timeit
def get_clusters_list(boto3_session: boto3.session.Session, region: str) -> List[Dict]:
    clusters: List[Dict] = []
    try:
        client = get_boto3_client(boto3_session, "sagemaker", region)

        paginator = client.get_paginator("list_clusters")
        for page in paginator.paginate():
            clusters.extend(page["ClusterSummaries"])

        for cluster in clusters:
            cluster["region"] = region

    except Exception as e:
        logger.warning(
            f"Could not list sagemaker clusters. skipping. - {e}",
        )
    return clusters


@timeit
def load_clusters(
    neo4j_session: neo4j.Session,
    clusters: List[Dict],
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    neo4j_session.write_transaction(_load_clusters_tx, clusters, current_aws_account_id, aws_update_tag)


@timeit
def _load_clusters_tx(
    tx: neo4j.Transaction,
    clusters: List[Dict],
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    ingest_clusters = """
    UNWIND $clusters AS cluster
    MERGE (i:AWSSagemakerCluster{arn:cluster.ClusterArn})
    ON CREATE SET i.firstseen = timestamp(),
    i.arn = cluster.ClusterArn,
    i.creationtime = cluster.CreationTime
    SET i.name = cluster.ClusterName,
    i.status = cluster.ClusterStatus,
    i.lastupdated =$aws_update_tag,
    i.region = cluster.region
    WITH i
    MATCH (aa:AWSAccount{id: $AWS_ACCOUNT_ID})
    MERGE (aa)-[r:RESOURCE]->(i)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $aws_update_tag
    """

    tx.run(
        ingest_clusters,
        clusters=clusters,
        AWS_ACCOUNT_ID=current_aws_account_id,
        aws_update_tag=aws_update_tag,
    )


@timeit
def cleanup_sagemaker(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('aws_import_sagemaker_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync_sagemaker(
    neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, regions: str, current_aws_account_id: str,
    aws_update_tag: int, common_job_parameters: Dict,
) -> None:
    notebook_instances_list = []
    for region in regions:
        notebook_instances_list.extend(get_notebook_instances_list(boto3_session, region))

    logger.info(f"Total notebook instances: {len(notebook_instances_list)}")

    load_notebook_instances(neo4j_session, notebook_instances_list, current_aws_account_id, aws_update_tag)

    endpoints_list = []
    for region in regions:
        endpoints_list.extend(get_endpoints_list(boto3_session, region))

    logger.info(f"Total endpoints: {len(endpoints_list)}")

    load_endpoints(neo4j_session, endpoints_list, current_aws_account_id, aws_update_tag)

    training_jobs_list = []
    for region in regions:
        training_jobs_list.extend(get_training_jobs_list(boto3_session, region))

    logger.info(f"Total training jobs: {len(training_jobs_list)}")

    load_training_jobs(neo4j_session, training_jobs_list, current_aws_account_id, aws_update_tag)

    models_list = []
    for region in regions:
        models_list.extend(get_models_list(boto3_session, region))

    logger.info(f"Total models: {len(models_list)}")

    load_models(neo4j_session, models_list, current_aws_account_id, aws_update_tag)

    domains_list = []
    for region in regions:
        domains_list.extend(get_domains_list(boto3_session, region))

    logger.info(f"Total domains: {len(domains_list)}")

    load_domains(neo4j_session, domains_list, current_aws_account_id, aws_update_tag)

    clusters_list = []
    for region in regions:
        clusters_list.extend(get_clusters_list(boto3_session, region))

    logger.info(f"Total clusters: {len(clusters_list)}")

    load_clusters(neo4j_session, clusters_list, current_aws_account_id, aws_update_tag)


@timeit
def sync(
    neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, regions: List[str], current_aws_account_id: str,
    update_tag: int, common_job_parameters: Dict,
) -> None:
    tic = time.perf_counter()

    logger.info("Syncing Sagemaker for account '%s', at %s.", current_aws_account_id, tic)
    sync_sagemaker(neo4j_session, boto3_session, regions, current_aws_account_id, update_tag, common_job_parameters)

    cleanup_sagemaker(neo4j_session, common_job_parameters)

    toc = time.perf_counter()
    logger.info(f"Time to process Sagemaker: {toc - tic:0.4f} seconds")
