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
def get_dataproc_clusters(dataproc: Resource, project_id: str, regions: list) -> List[Dict]:
    clusters = []
    try:
        if regions:
            for region in regions:
                req = dataproc.projects().regions().clusters().list(projectId=project_id, region=region)
                while req is not None:
                    res = req.execute()
                    if res.get('clusters'):
                        for cluster in res['clusters']:
                            cluster['region'] = region
                            cluster['id'] = f"projects/{project_id}/clusters/{cluster['clusterName']}"
                            cluster['consolelink'] = gcp_console_link.get_console_link(
                                project_id=project_id,
                                dataproc_cluster_name=cluster['clusterName'], region=cluster['region'], resource_name='dataproc_cluster',
                            )
                            clusters.append(cluster)
                    req = dataproc.projects().regions().clusters().list_next(previous_request=req, previous_response=res)

        return clusters
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err.get('status', '') == 'PERMISSION_DENIED' or err.get('message', '') == 'Forbidden':
            logger.warning(
                (
                    "Could not retrieve dataproc clusters on project %s due to permissions issues. Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return []
        else:
            raise


@timeit
def load_dataproc_clusters(session: neo4j.Session, data_list: List[Dict], project_id: str, update_tag: int) -> None:
    session.execute_write(load_dataproc_clusters_tx, data_list, project_id, update_tag)


@timeit
def load_dataproc_clusters_tx(
    tx: neo4j.Transaction, data: List[Dict],
    project_id: str, gcp_update_tag: int,
) -> None:

    query = """
    UNWIND $Records as record
    MERGE (cluster:GCPDataprocCluster{id:record.id})
    ON CREATE SET
        cluster.firstseen = timestamp()
    SET
        cluster.lastupdated = $gcp_update_tag,
        cluster.region = record.region,
        cluster.name = record.clusterName,
        cluster.state = record.status.state,
        cluster.consolelink = record.consolelink,
        cluster.cluster_uuid = record.clusterUuid
    WITH cluster
    MATCH (owner:GCPProject{id: $ProjectId})
    MERGE (owner)-[r:RESOURCE]->(cluster)
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
def cleanup_dataproc_clusters(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('gcp_dataproc_clusters_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync_dataproc_clusters(
    neo4j_session: neo4j.Session, dataproc: Resource, project_id: str, regions: List,
    gcp_update_tag: int, common_job_parameters: Dict,
) -> None:

    clusters = get_dataproc_clusters(dataproc, project_id, regions)

    load_dataproc_clusters(neo4j_session, clusters, project_id, gcp_update_tag)
    cleanup_dataproc_clusters(neo4j_session, common_job_parameters)
    label.sync_labels(neo4j_session, clusters, gcp_update_tag, common_job_parameters, 'dataproc_cluster', 'GCPDataprocCluster')


def sync(
    neo4j_session: neo4j.Session, dataproc: Resource, project_id: str, gcp_update_tag: int,
    common_job_parameters: dict, regions: list,
) -> None:

    tic = time.perf_counter()

    logger.info(f"Syncing Dataproc for project {project_id}, at {tic}")

    sync_dataproc_clusters(
        neo4j_session, dataproc, project_id, regions,
        gcp_update_tag, common_job_parameters,
    )

    toc = time.perf_counter()
    logger.info(f"Time to process dataproc: {toc - tic:0.4f} seconds")
