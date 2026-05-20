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
def get_cloudtasks_locations(cloudtasks: Resource, project_id: str) -> List[Dict]:
    locations = []
    try:
        request = cloudtasks.projects().locations().list(name=f"projects/{project_id}")
        while request is not None:
            response = request.execute()
            if response.get('locations'):
                locations.extend(response.get('locations', []))
            request = cloudtasks.projects().locations().list_next(previous_request=request, previous_response=response)
        return locations
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err.get('status', '') == 'PERMISSION_DENIED' or err.get('message', '') == 'Forbidden':
            logger.warning(
                (
                    "Could not retrieve cloudtasks jobs on project %s due to permissions issues. Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return []
        else:
            raise


@timeit
def transform_cloudtasks_locations(locations: List[Dict]) -> List[str]:
    transformed_locations = []
    for location in locations:
        transformed_locations.append(location.get('locationId'))
    return transformed_locations


@timeit
def get_cloudtasks_queues(cloudtasks: Resource, locations: List[str], project_id: str, common_job_parameters) -> List[Dict]:
    queues = []
    try:
        for location in locations:
            request = cloudtasks.projects().locations().queues().list(parent=f"projects/{project_id}/locations/{location}")
            while request is not None:
                response = request.execute()
                if response.get('queues'):
                    queues.extend(response.get('queues', []))
                request = cloudtasks.projects().locations().queues().list_next(previous_request=request, previous_response=response)
        return queues
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err.get('status', '') == 'PERMISSION_DENIED' or err.get('message', '') == 'Forbidden':
            logger.warning(
                (
                    "Could not retrieve cloudtasks queues on project %s due to permissions issues. Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return []
        else:
            raise


@timeit
def transform_cloudtasks_queues(queues: List[Dict], project_id: str) -> List[Dict]:
    transformed_queues = []
    for queue in queues:
        queue['consolelink'] = ''  # TODO
        queue['project_id'] = project_id
        queue['region'] = queue['name'].split('/')[-3]
        queue['id'] = queue['name']
        queue['queue_name'] = queue['name'].split('/')[-1]
        transformed_queues.append(queue)
    return transformed_queues


@timeit
def load_cloudtasks_queues(session: neo4j.Session, data_list: List[Dict], project_id: str, update_tag: int) -> None:
    session.execute_write(load_cloudtasks_queues_tx, data_list, project_id, update_tag)


@timeit
def load_cloudtasks_queues_tx(tx: neo4j.Session, data: List[Dict], project_id: str, gcp_update_tag: int) -> None:
    query = """
    UNWIND $Records as record
    MERGE (queue:GCPCloudTasksQueue{id: record.id})
    ON CREATE SET
        queue.firstseen = timestamp()
    SET
        queue.lastupdated = $gcp_update_tag,
        queue.region = record.region,
        queue.name = record.queue_name,
        queue.consolelink = record.consolelink,
        queue.state = record.state,
        queue.max_burst_size = record.rateLimits.maxBurstSize,
        queue.max_concurrent_dispatches = record.rateLimits.maxConcurrentDispatches,
        queue.max_dispatches_per_second = record.rateLimits.maxDispatchesPerSecond,
        queue.purge_time = record.purgeTime,
        queue.max_attempts = record.retryConfig.maxAttempts,
        queue.max_backoff = record.retryConfig.maxBackoff,
        queue.max_doublings = record.retryConfig.maxDoublings,
        queue.max_retry_duration = record.retryConfig.maxRetryDuration,
        queue.min_backoff = record.retryConfig.minBackoff,
        queue.host = record.appEngineRoutingOverride.host,
        queue.instance = record.appEngineRoutingOverride.instance,
        queue.service = record.appEngineRoutingOverride.service,
        queue.version = record.appEngineRoutingOverride.version
    WITH queue
    MATCH (owner:GCPProject{id: $ProjectId})
    MERGE (owner)-[r:RESOURCE]->(queue)
    ON CREATE SET
        r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag
    """
    tx.run(query, Records=data, ProjectId=project_id, gcp_update_tag=gcp_update_tag)


@timeit
def cleanup_cloudtasks_queues(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('gcp_cloudtasks_queues_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync(
    neo4j_session: neo4j.Session, cloudtasks: Resource, project_id: str, gcp_update_tag: int,
    common_job_parameters: Dict, regions: list,
) -> None:
    tic = time.perf_counter()
    logger.info("Syncing cloudtasks for project '%s', at %s.", project_id, tic)
    locations = get_cloudtasks_locations(cloudtasks, project_id)
    transformed_locations = transform_cloudtasks_locations(locations)

    queues = get_cloudtasks_queues(cloudtasks, transformed_locations, project_id, common_job_parameters)
    transformed_queues = transform_cloudtasks_queues(queues, project_id)
    load_cloudtasks_queues(neo4j_session, transformed_queues, project_id, gcp_update_tag)

    cleanup_cloudtasks_queues(neo4j_session, common_job_parameters)

    toc = time.perf_counter()
    logger.info(f"Time to process cloudtasks: {toc - tic:0.4f} seconds")
