import json
import logging
import time
from typing import Dict
from typing import List

import neo4j
from cloudconsolelink.clouds.gcp import GCPLinker
from googleapiclient.discovery import HttpError
from googleapiclient.discovery import Resource

from . import label
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)
gcp_console_link = GCPLinker()


@timeit
def get_dataflow_jobs(dataflow: Resource, project_id: str, regions: list, common_job_parameters) -> List[Dict]:
    jobs = []
    try:
        req = dataflow.projects().jobs().aggregated(projectId=project_id)
        while req is not None:
            res = req.execute()
            if res.get('jobs'):
                jobs.extend(res.get('jobs', []))
            req = dataflow.projects().jobs().aggregated_next(previous_request=req, previous_response=res)
        return jobs
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err.get('status', '') == 'PERMISSION_DENIED' or err.get('message', '') == 'Forbidden':
            logger.warning(
                (
                    "Could not retrieve dataflow jobs on project %s due to permissions issues. Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return []
        else:
            raise


@timeit
def transform_jobs(jobs: List[Dict], project_id: str) -> List[Dict]:
    transformed_jobs = []
    for job in jobs:
        job['consolelink'] = ''  # TODO

        big_table_details = job.get('jobMetadata', {}).get('bigTableDetails', [])
        big_tables = []
        for big_table in big_table_details:
            big_table_id = f"projects/{big_table.get('projectId')}/instances/{big_table.get('instanceId')}/tables/{big_table.get('tableId')}"
            big_tables.append(big_table_id)
        job['bigTables'] = big_tables

        big_query_details = job.get('jobMetadata', {}).get('bigqueryDetails', [])
        big_queries = []
        for big_query in big_query_details:
            big_query_id = f"projects/{big_query.get('projectId')}/datasets/{big_query.get('dataset')}/tables/{big_query.get('table')}"
            big_queries.append(big_query_id)
        job['bigQueries'] = big_queries

        pubsub_details = job.get('jobMetadata', {}).get('pubsubDetails', [])
        pubsub_all = []
        for pubsub in pubsub_details:
            topic_id = f"projects/{job.get('projectId')}/topics/{pubsub.get('topic')}"
            subscription_id = f"projects/{job.get('projectId')}/subscriptions/{pubsub.get('subscription')}"
            pubsub_all.append({'topicId': topic_id, 'subscriptionId': subscription_id})
        job['pubSub'] = pubsub_all

        spanner_details = job.get('jobMetadata', {}).get('spannerDetails', [])
        spanner_databases = []
        for spanner in spanner_details:
            spanner_database_id = f"projects/{spanner.get('projectId')}/instances/{spanner.get('instanceId')}/databases/{spanner.get('databaseId')}"
            spanner_databases.append(spanner_database_id)
        job['spannerDatabases'] = spanner_databases

        transformed_jobs.append(job)
    return transformed_jobs


@timeit
def load_dataflow_jobs(session: neo4j.Session, data_list: List[Dict], project_id: str, update_tag: int) -> None:
    session.execute_write(load_dataflow_jobs_tx, data_list, project_id, update_tag)


@timeit
def load_dataflow_jobs_tx(
    tx: neo4j.Transaction, data: List[Dict],
    project_id: str, gcp_update_tag: int,
) -> None:

    query = """
    UNWIND $Records as record
    MERGE (job:GCPDataFlowJob{id:record.id})
    ON CREATE SET
        job.firstseen = timestamp()
    SET
        job.lastupdated = $gcp_update_tag,
        job.create_time = record.createTime,
        job.region = record.location,
        job.name = record.name,
        job.type = record.type,
        job.cluster_manager_api_service = record.environment.clusterManagerApiService,
        job.dataset = record.environment.dataset,
        job.service_account_email = record.environment.serviceAccountEmail,
        job.service_kms_key_name = record.environment.serviceKmsKeyName,
        job.shuffle_mode = record.environment.shuffleMode,
        job.worker_region = record.environment.workerRegion,
        job.worker_zone = record.environment.workerZone,
        job.start_time = record.startTime,
        job.current_state = record.currentState,
        job.requested_state = record.requestedState,
        job.consolelink = record.consolelink,
        job.satisfies_pzs = record.satisfiesPzs
    WITH job, record
    UNWIND record.bigTables as big_table_id
    MATCH (big_table:GCPBigtableTable{id: big_table_id})
    MERGE (job)-[rjbt:REFERENCES]->(big_table)
    ON CREATE SET
        rjbt.firstseen = timestamp()
    WITH job, record
    UNWIND record.bigQueries as big_query_id
    MATCH (big_query:GCPBigqueryTable{id: big_query_id})
    MERGE (job)-[rjbq:REFERENCES]->(big_query)
    ON CREATE SET
        rjbq.firstseen = timestamp()
    WITH job, record
    UNWIND record.pubSub as pubsub
    MATCH (topic:GCPPubsubTopic{id: pubsub.topicId})
    MERGE (job)-[rt:REFERENCES]->(topic)
    ON CREATE SET
        rt.firstseen = timestamp()
    WITH job, pubsub, record
    MATCH (subscription:GCPPubsubSubscription{id: pubsub.subscriptionId})
    MERGE (job)-[rs:REFERENCES]->(subscription)
    ON CREATE SET
        rs.firstseen = timestamp()
    WITH job, record
    UNWIND record.spannerDatabases as spanner_database_id
    MATCH (database:GCPSpannerInstanceDatabase{id: spanner_database_id})
    MERGE (job)-[rd:REFERENCES]->(database)
    ON CREATE SET
        rd.firstseen = timestamp()
    WITH job
    MATCH (owner:GCPProject{id: $ProjectId})
    MERGE (owner)-[r:RESOURCE]->(job)
    ON CREATE SET
        r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag
    """
    tx.run(
        query,
        Records=data,
        ProjectId=project_id,
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def cleanup_dataflow_jobs(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('gcp_dataflow_jobs_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync(
    neo4j_session: neo4j.Session, dataflow: Resource, project_id: str, gcp_update_tag: int,
    common_job_parameters: Dict, regions: List,
) -> None:

    tic = time.perf_counter()
    logger.info("Syncing Dataflow for project '%s', at %s.", project_id, tic)

    jobs = get_dataflow_jobs(dataflow, project_id, regions, common_job_parameters)
    transformed_jobs = transform_jobs(jobs, project_id)
    load_dataflow_jobs(neo4j_session, transformed_jobs, project_id, gcp_update_tag)

    label.sync_labels(
        neo4j_session, transformed_jobs, gcp_update_tag,
        common_job_parameters, 'dataflow_jobs', 'GCPDataFlowJob',
    )
    cleanup_dataflow_jobs(neo4j_session, common_job_parameters)

    toc = time.perf_counter()
    logger.info(f"Time to process dataflow: {toc - tic:0.4f} seconds")
