import logging
from typing import Any

import neo4j
import requests
from requests import Session
from requests.adapters import HTTPAdapter
from urllib3 import Retry

from cartography.client.core.tx import load
from cartography.config import Config
from cartography.intel.cve_metadata import epss
from cartography.intel.cve_metadata import nvd
from cartography.models.cve_metadata.cve_metadata import CVEMetadataSchema
from cartography.models.cve_metadata.cve_metadata_feed import CVEMetadataFeedSchema
from cartography.stats import get_stats_client
from cartography.util import merge_module_sync_metadata
from cartography.util import timeit

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)

CVE_METADATA_FEED_ID = "CVE_METADATA"
ALL_SOURCES = {"nvd", "epss"}


@timeit
def load_cve_metadata_feed(
    neo4j_session: neo4j.Session,
    update_tag: int,
) -> None:
    """Load the CVEMetadataFeed node."""
    feed_data = [{"FEED_ID": CVE_METADATA_FEED_ID}]
    load(
        neo4j_session,
        CVEMetadataFeedSchema(),
        feed_data,
        lastupdated=update_tag,
    )


@timeit
def load_cve_metadata(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    update_tag: int,
) -> None:
    """Load CVEMetadata nodes into the graph."""
    logger.info("Loading %d CVEMetadata nodes into the graph.", len(data))
    load(
        neo4j_session,
        CVEMetadataSchema(),
        data,
        lastupdated=update_tag,
        FEED_ID=CVE_METADATA_FEED_ID,
    )


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

    # Step 1: Get all CVE IDs from the graph — this is the authoritative list
    cve_ids = nvd.get_cve_ids_from_graph(neo4j_session)
    if not cve_ids:
        logger.info("No CVE nodes found in graph, skipping CVE metadata enrichment.")
        return
    logger.info("Found %d CVE nodes in graph to enrich.", len(cve_ids))

    # Build one entry per graph CVE; each source enriches these dicts
    cves: list[dict[str, Any]] = [
        {
            "id": cve_id,
            "source_nvd": "nvd" in sources,
            "source_epss": "epss" in sources,
        }
        for cve_id in cve_ids
    ]

    session = Session()
    retry_policy = Retry(
        total=8,
        connect=1,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    session.mount("https://", HTTPAdapter(max_retries=retry_policy))

    with session as http_session:
        # Step 2: Enrich with NVD data (failures propagate — NVD is the primary source)
        if "nvd" in sources:
            nvd_data = nvd.get_and_transform_nvd_cves(
                http_session,
                config.cve_metadata_nist_url,
                set(cve_ids),
            )
            nvd.merge_nvd_into_cves(cves, nvd_data)
            logger.info("NVD enriched %d CVEs.", len(nvd_data))

        # Step 3: Enrich with EPSS scores (non-fatal — optional enrichment)
        if "epss" in sources:
            try:
                epss_data = epss.get_epss_scores(http_session, cve_ids)
                epss.merge_epss_into_cves(cves, epss_data)
            except requests.exceptions.RequestException:
                logger.warning(
                    "Failed to fetch EPSS scores, continuing without EPSS enrichment.",
                    exc_info=True,
                )

        # Step 4: Load into graph
        load_cve_metadata_feed(neo4j_session, config.update_tag)
        load_cve_metadata(neo4j_session, cves, config.update_tag)

    merge_module_sync_metadata(
        neo4j_session,
        group_type="CVEMetadata",
        group_id=CVE_METADATA_FEED_ID,
        synced_type="CVEMetadata",
        update_tag=config.update_tag,
        stat_handler=stat_handler,
    )
