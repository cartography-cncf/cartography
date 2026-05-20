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
def get_logging_metrics(logging: Resource, project_id: str) -> List[Dict]:
    metrics = []
    try:
        req = logging.projects().metrics().list(parent=f"projects/{project_id}")
        while req is not None:
            res = req.execute()
            if res.get('metrics'):
                for metric in res['metrics']:
                    metric['region'] = 'global'
                    metric['id'] = metric['name']
                    metric['metric_name'] = metric.get('name').split('/')[-1]
                    metric['consolelink'] = gcp_console_link.get_console_link(project_id=project_id, resource_name="cloud_logging_metric")
                    metrics.append(metric)
            req = logging.projects().metrics().list_next(previous_request=req, previous_response=res)

        return metrics
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err.get('status', '') == 'PERMISSION_DENIED' or err.get('message', '') == 'Forbidden':
            logger.warning(
                (
                    "Could not retrieve logging metrics on project %s due to permissions issues. Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return []
        else:
            raise


@timeit
def load_logging_metrics(session: neo4j.Session, data_list: List[Dict], project_id: str, update_tag: int) -> None:
    session.execute_write(load_logging_metrics_tx, data_list, project_id, update_tag)


@timeit
def load_logging_metrics_tx(
    tx: neo4j.Transaction, data: List[Dict],
    project_id: str, gcp_update_tag: int,
) -> None:

    query = """
    UNWIND $Records as record
    MERGE (metric:GCPLoggingMetric{id:record.id})
    ON CREATE SET
        metric.firstseen = timestamp()
    SET
        metric.lastupdated = $gcp_update_tag,
        metric.region = record.region,
        metric.name = record.metric_name,
        metric.description = record.description,
        metric.filter = record.filter,
        metric.bucket_name = record.bucketName,
        metric.disabled = record.disabled,
        metric.consolelink = record.consolelink,
        metric.value_extractor = record.valueExtractor,
        metric.create_time = record.createTime,
        metric.update_time = record.updateTime
    WITH metric
    MATCH (owner:GCPProject{id: $ProjectId})
    MERGE (owner)-[r:RESOURCE]->(metric)
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
def cleanup_logging_metrics(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('gcp_logging_metrics_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync_logging_metrics(
    neo4j_session: neo4j.Session, logging: Resource, project_id: str,
    gcp_update_tag: int, common_job_parameters: Dict,
) -> None:

    metrics = get_logging_metrics(logging, project_id)

    load_logging_metrics(neo4j_session, metrics, project_id, gcp_update_tag)
    cleanup_logging_metrics(neo4j_session, common_job_parameters)


@timeit
def get_logging_sinks(logging: Resource, project_id: str) -> List[Dict]:
    sinks = []
    try:
        req = logging.sinks().list(parent=f"projects/{project_id}")
        while req is not None:
            res = req.execute()
            if res.get('sinks'):
                for sink in res['sinks']:
                    sink['region'] = 'global'
                    sink['id'] = f"projects/{project_id}/sinks/{sink['name']}"
                    sink['consolelink'] = gcp_console_link.get_console_link(project_id=project_id, resource_name='cloud_logging_sink')
                    sinks.append(sink)
            req = logging.projects().sinks().list_next(previous_request=req, previous_response=res)

        return sinks
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err.get('status', '') == 'PERMISSION_DENIED' or err.get('message', '') == 'Forbidden':
            logger.warning(
                (
                    "Could not retrieve logging sinks on project %s due to permissions issues. Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return []
        else:
            raise


@timeit
def load_logging_sinks(session: neo4j.Session, data_list: List[Dict], project_id: str, update_tag: int) -> None:
    session.execute_write(load_logging_sinks_tx, data_list, project_id, update_tag)


@timeit
def load_logging_sinks_tx(
    tx: neo4j.Transaction, data: List[Dict],
    project_id: str, gcp_update_tag: int,
) -> None:

    query = """
    UNWIND $Records as record
    MERGE (sink:GCPLoggingSink{id:record.id})
    ON CREATE SET
        sink.firstseen = timestamp()
    SET
        sink.lastupdated = $gcp_update_tag,
        sink.region = record.region,
        sink.name = record.name,
        sink.description = record.description,
        sink.filter = record.filter,
        sink.destination = record.destination,
        sink.disabled = record.disabled,
        sink.consolelink = record.consolelink,
        sink.writerIdentity = record.writerIdentity,
        sink.create_time = record.createTime,
        sink.update_time = record.updateTime
    WITH sink
    MATCH (owner:GCPProject{id: $ProjectId})
    MERGE (owner)-[r:RESOURCE]->(sink)
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
def cleanup_logging_sinks(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('gcp_logging_sinks_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync_logging_sinks(
    neo4j_session: neo4j.Session, logging: Resource, project_id: str,
    gcp_update_tag: int, common_job_parameters: Dict,
) -> None:

    sinks = get_logging_sinks(logging, project_id)

    load_logging_sinks(neo4j_session, sinks, project_id, gcp_update_tag)
    cleanup_logging_sinks(neo4j_session, common_job_parameters)


def sync(
    neo4j_session: neo4j.Session, logging: Resource, project_id: str, gcp_update_tag: int,
    common_job_parameters: dict, regions: list,
) -> None:

    tic = time.perf_counter()

    logger.info(f"Syncing logging for project {project_id}, at {tic}")

    sync_logging_metrics(
        neo4j_session, logging, project_id,
        gcp_update_tag, common_job_parameters,
    )
    sync_logging_sinks(
        neo4j_session, logging, project_id,
        gcp_update_tag, common_job_parameters,
    )

    toc = time.perf_counter()
    logger.info(f"Time to process logging: {toc - tic:0.4f} seconds")
