import logging

import neo4j
from requests import Session
from requests.adapters import HTTPAdapter
from urllib3 import Retry

from cartography.client.core.tx import load
from cartography.config import Config
from cartography.intel.cve_metadata import epss
from cartography.intel.cve_metadata import nvd
from cartography.models.cve_metadata.cve_metadata import CVEMetadataFeedSchema
from cartography.models.cve_metadata.cve_metadata import CVEMetadataSchema
from cartography.stats import get_stats_client
from cartography.util import merge_module_sync_metadata
from cartography.util import timeit

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)

CVE_METADATA_FEED_ID = "CVE_METADATA"
ALL_SOURCES = {"nvd", "epss"}


def _retryable_session() -> Session:
    session = Session()
    retry_policy = Retry(
        total=8,
        connect=1,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    session.mount("https://", HTTPAdapter(max_retries=retry_policy))
    return session


@timeit
def start_cve_metadata_ingestion(
    neo4j_session: neo4j.Session,
    config: Config,
) -> None:
    """
    Enrich existing CVE nodes with metadata from NVD and EPSS.
    :param neo4j_session: Neo4J session for database interface
    :param config: A cartography.config object
    """
    sources = set(config.cve_metadata_src) if config.cve_metadata_src else ALL_SOURCES
    invalid = sources - ALL_SOURCES
    if invalid:
        raise ValueError(
            f"Invalid CVE metadata sources: {invalid}. Valid sources: {ALL_SOURCES}",
        )

    # Step 1: Get all CVE IDs from the graph
    cve_ids = nvd.get_cve_ids_from_graph(neo4j_session)
    if not cve_ids:
        logger.info("No CVE nodes found in graph, skipping CVE metadata enrichment.")
        return
    cve_ids_set = set(cve_ids)
    logger.info("Found %d CVE nodes in graph to enrich.", len(cve_ids_set))

    with _retryable_session() as http_session:
        # Step 2: Fetch NVD data (filtered to graph CVEs)
        if "nvd" in sources:
            cves = nvd.get_and_transform_nvd_cves(
                http_session,
                neo4j_session,
                config.cve_metadata_nist_url,
                cve_ids_set,
            )
            logger.info("NVD returned metadata for %d CVEs.", len(cves))
        else:
            # Create stub entries for CVEs so EPSS data can still be loaded
            cves = [{"id": cve_id} for cve_id in cve_ids]

        # Step 3: Fetch and merge EPSS scores
        if "epss" in sources:
            epss_data = epss.get_epss_scores(http_session, cve_ids)
            epss.merge_epss_into_cves(cves, epss_data)

        # Step 4: Load CVEMetadataFeed node
        feed_data = [{"FEED_ID": CVE_METADATA_FEED_ID}]
        load(
            neo4j_session,
            CVEMetadataFeedSchema(),
            feed_data,
            lastupdated=config.update_tag,
        )

        # Step 5: Load CVEMetadata nodes
        logger.info("Loading %d CVEMetadata nodes into the graph.", len(cves))
        load(
            neo4j_session,
            CVEMetadataSchema(),
            cves,
            lastupdated=config.update_tag,
            FEED_ID=CVE_METADATA_FEED_ID,
        )

    merge_module_sync_metadata(
        neo4j_session,
        group_type="CVEMetadata",
        group_id=CVE_METADATA_FEED_ID,
        synced_type="CVEMetadata",
        update_tag=config.update_tag,
        stat_handler=stat_handler,
    )
