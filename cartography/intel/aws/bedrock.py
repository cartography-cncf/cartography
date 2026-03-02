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
def get_bedrock_agents_list(boto3_session: boto3.session.Session, current_aws_account_id: str, region: str) -> List[Dict]:
    bedrock_agents: List[Dict] = []
    try:
        client = get_boto3_client(boto3_session, "bedrock-agent", region)

        paginator = client.get_paginator("list_agents")
        for page in paginator.paginate():
            bedrock_agents.extend(page["agentSummaries"])

        for bedrock_agent in bedrock_agents:
            bedrock_agent["region"] = region
            bedrock_agent["arn"] = f"arn:aws:bedrock:{region}:{current_aws_account_id}:agent/{bedrock_agent['agentId']}"

    except Exception as e:
        logger.warning(
            f"Could not list bedrock agents. skipping. - {e}",
        )
    return bedrock_agents


@timeit
def load_bedrock_agents(
    neo4j_session: neo4j.Session,
    bedrock_agents: List[Dict],
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    neo4j_session.write_transaction(_load_bedrock_agents_tx, bedrock_agents, current_aws_account_id, aws_update_tag)


@timeit
def _load_bedrock_agents_tx(
    tx: neo4j.Transaction,
    bedrock_agents: List[Dict],
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    ingest_bedrock_agents = """
    UNWIND $bedrock_agents AS agent
    MERGE (i:AWSBedrockAgent{arn:agent.arn})
    ON CREATE SET i.firstseen = timestamp(),
    i.arn = agent.arn,
    i.agentid = agent.agentId
    SET i.updatedat = agent.updatedAt,
    i.name = agent.agentName,
    i.status = agent.agentStatus,
    i.latestagentversion = agent.latestAgentVersion,
    i.lastupdated =$aws_update_tag,
    i.region = agent.region
    WITH i
    MATCH (aa:AWSAccount{id: $AWS_ACCOUNT_ID})
    MERGE (aa)-[r:RESOURCE]->(i)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $aws_update_tag
    """

    tx.run(
        ingest_bedrock_agents,
        bedrock_agents=bedrock_agents,
        AWS_ACCOUNT_ID=current_aws_account_id,
        aws_update_tag=aws_update_tag,
    )


@timeit
def get_model_customisation_jobs_list(boto3_session: boto3.session.Session, region: str) -> List[Dict]:
    model_customisation_jobs: List[Dict] = []
    try:
        client = get_boto3_client(boto3_session, "bedrock", region)

        paginator = client.get_paginator("list_model_customization_jobs")
        for page in paginator.paginate():
            model_customisation_jobs.extend(page["modelCustomizationJobSummaries"])

        for model_customisation_job in model_customisation_jobs:
            model_customisation_job["region"] = region

    except Exception as e:
        logger.warning(
            f"Could not list bedrock model customisation jobs. skipping. - {e}",
        )
    return model_customisation_jobs


@timeit
def load_model_customisation_jobs(
    neo4j_session: neo4j.Session,
    model_customisation_jobs: List[Dict],
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    neo4j_session.write_transaction(_load_model_customisation_jobs_tx, model_customisation_jobs, current_aws_account_id, aws_update_tag)


@timeit
def _load_model_customisation_jobs_tx(
    tx: neo4j.Transaction,
    model_customisation_jobs: List[Dict],
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    ingest_model_customisation_jobs = """
    UNWIND $model_customisation_jobs AS job
    MERGE (e:AWSBedrockCustomisationJob{arn:job.jobArn})
    ON CREATE SET e.firstseen = timestamp(),
    e.arn = job.jobArn,
    e.creationtime = job.creationTime
    SET e.lastmodifiedtime = job.lastModifiedTime,
    e.name = job.jobName,
    e.status = job.status,
    e.lastupdated =$aws_update_tag,
    e.region = job.region
    WITH e
    MATCH (aa:AWSAccount{id: $AWS_ACCOUNT_ID})
    MERGE (aa)-[r:RESOURCE]->(e)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $aws_update_tag
    """

    tx.run(
        ingest_model_customisation_jobs,
        model_customisation_jobs=model_customisation_jobs,
        AWS_ACCOUNT_ID=current_aws_account_id,
        aws_update_tag=aws_update_tag,
    )


@timeit
def get_bedrock_guardrails_list(boto3_session: boto3.session.Session, region: str) -> List[Dict]:
    bedrock_guardrails: List[Dict] = []
    try:
        client = get_boto3_client(boto3_session, "bedrock", region)

        paginator = client.get_paginator("list_guardrails")
        for page in paginator.paginate():
            bedrock_guardrails.extend(page["guardrails"])

        for bedrock_guardrail in bedrock_guardrails:
            bedrock_guardrail["region"] = region

    except Exception as e:
        logger.warning(
            f"Could not list bedrock guardrails. skipping. - {e}",
        )
    return bedrock_guardrails


@timeit
def load_bedrock_guardrails(
    neo4j_session: neo4j.Session,
    bedrock_guardrails: List[Dict],
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    neo4j_session.write_transaction(_load_bedrock_guardrails_tx, bedrock_guardrails, current_aws_account_id, aws_update_tag)


@timeit
def _load_bedrock_guardrails_tx(
    tx: neo4j.Transaction,
    bedrock_guardrails: List[Dict],
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    ingest_bedrock_guardrails = """
    UNWIND $bedrock_guardrails AS rail
    MERGE (i:AWSBedrockGuardRail{arn:rail.arn})
    ON CREATE SET i.firstseen = timestamp(),
    i.arn = rail.arn,
    i.createdat = rail.createdAt
    SET i.updatedat = rail.updatedAt,
    i.name = rail.name,
    i.status = rail.status,
    i.version = rail.version,
    i.lastupdated =$aws_update_tag,
    i.region = rail.region
    WITH i
    MATCH (aa:AWSAccount{id: $AWS_ACCOUNT_ID})
    MERGE (aa)-[r:RESOURCE]->(i)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $aws_update_tag
    """

    tx.run(
        ingest_bedrock_guardrails,
        bedrock_guardrails=bedrock_guardrails,
        AWS_ACCOUNT_ID=current_aws_account_id,
        aws_update_tag=aws_update_tag,
    )


@timeit
def get_custom_models(boto3_session: boto3.session.Session, region: str) -> List[Dict]:
    custom_models: List[Dict] = []
    try:
        client = get_boto3_client(boto3_session, "bedrock", region)

        paginator = client.get_paginator("list_custom_models")
        for page in paginator.paginate():
            custom_models.extend(page["modelSummaries"])

        for custom_model in custom_models:
            custom_model["region"] = region

    except Exception as e:
        logger.warning(
            f"Could not list bedrock custom models. skipping. - {e}",
        )
    return custom_models


@timeit
def load_custom_models(
    neo4j_session: neo4j.Session,
    custom_models: List[Dict],
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    neo4j_session.write_transaction(_load_custom_models_tx, custom_models, current_aws_account_id, aws_update_tag)


@timeit
def _load_custom_models_tx(
    tx: neo4j.Transaction,
    custom_models: List[Dict],
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    ingest_custom_models = """
    UNWIND $custom_models AS model
    MERGE (e:AWSBedrockCustomModel{arn:model.modelArn})
    ON CREATE SET e.firstseen = timestamp(),
    e.arn = model.modelArn,
    e.creationtime = model.CreationTime
    SET e.name = model.modelName,
    e.lastupdated =$aws_update_tag,
    e.region = model.region
    WITH e
    MATCH (aa:AWSAccount{id: $AWS_ACCOUNT_ID})
    MERGE (aa)-[r:RESOURCE]->(e)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $aws_update_tag
    """

    tx.run(
        ingest_custom_models,
        custom_models=custom_models,
        AWS_ACCOUNT_ID=current_aws_account_id,
        aws_update_tag=aws_update_tag,
    )


@timeit
def cleanup_bedrock(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('aws_import_bedrock_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync_bedrock(
    neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, regions: str, current_aws_account_id: str,
    aws_update_tag: int, common_job_parameters: Dict,
) -> None:
    bedrock_agents = []
    for region in regions:
        bedrock_agents.extend(get_bedrock_agents_list(boto3_session, current_aws_account_id, region))

    logger.info(f"Total bedrock agents: {len(bedrock_agents)}")

    load_bedrock_agents(neo4j_session, bedrock_agents, current_aws_account_id, aws_update_tag)

    model_customisation_jobs_list = []
    for region in regions:
        model_customisation_jobs_list.extend(get_model_customisation_jobs_list(boto3_session, region))

    logger.info(f"Total Bedrock model customisation jobs list: {len(model_customisation_jobs_list)}")

    load_model_customisation_jobs(neo4j_session, model_customisation_jobs_list, current_aws_account_id, aws_update_tag)

    bedrock_guardrails_list = []
    for region in regions:
        bedrock_guardrails_list.extend(get_bedrock_guardrails_list(boto3_session, region))

    logger.info(f"Total bedrock guardrails: {len(bedrock_guardrails_list)}")

    load_bedrock_guardrails(neo4j_session, bedrock_guardrails_list, current_aws_account_id, aws_update_tag)

    custom_models_list = []
    for region in regions:
        custom_models_list.extend(get_custom_models(boto3_session, region))

    logger.info(f"Total bedrock custom models: {len(custom_models_list)}")

    load_custom_models(neo4j_session, custom_models_list, current_aws_account_id, aws_update_tag)


@timeit
def sync(
    neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, regions: List[str], current_aws_account_id: str,
    update_tag: int, common_job_parameters: Dict,
) -> None:
    tic = time.perf_counter()

    logger.info("Syncing Bedrock for account '%s', at %s.", current_aws_account_id, tic)
    sync_bedrock(neo4j_session, boto3_session, regions, current_aws_account_id, update_tag, common_job_parameters)

    cleanup_bedrock(neo4j_session, common_job_parameters)

    toc = time.perf_counter()
    logger.info(f"Time to process Bedrock: {toc - tic:0.4f} seconds")
