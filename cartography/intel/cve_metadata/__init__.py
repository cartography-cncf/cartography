import logging
from typing import Any

import neo4j
import requests
from requests import Session
from requests.adapters import HTTPAdapter
from urllib3 import Retry

from cartography.client.core.tx import load
from cartography.client.core.tx import read_list_of_values_tx
from cartography.config import Config
from cartography.graph.job import GraphJob
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


def _get_cve_feed_year(cve_id: str) -> str | None:
    parts = cve_id.split("-")
    if len(parts) < 2 or not parts[1].isdigit():
        return None
    return str(max(int(parts[1]), nvd.NVD_YEARLY_FEED_START_YEAR))


def _build_yearly_cve_batches(cve_ids: list[str]) -> list[list[str]]:
    by_year: dict[str, list[str]] = {}
    for cve_id in sorted(cve_ids):
        year_bucket = _get_cve_feed_year(cve_id)
        if year_bucket is None:
            continue
        by_year.setdefault(year_bucket, []).append(cve_id)
    return [by_year[year] for year in sorted(by_year)]


@timeit
def get_cve_ids_from_graph(neo4j_session: neo4j.Session) -> list[str]:
    """Query Neo4j for all CVE node IDs present in the graph."""
    query = """
    MATCH (c:CVE)
    WHERE c.cve_id STARTS WITH "CVE"
    RETURN DISTINCT c.cve_id
    """
    return [str(cve_id) for cve_id in read_list_of_values_tx(neo4j_session, query)]


@timeit
def load_cve_metadata_feed(
    neo4j_session: neo4j.Session,
    update_tag: int,
    sources: set[str],
) -> None:
    """Load the CVEMetadataFeed node."""
    feed_data = [
        {
            "FEED_ID": CVE_METADATA_FEED_ID,
            "source_nvd": "nvd" in sources,
            "source_epss": "epss" in sources,
        }
    ]
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
    cve_ids = get_cve_ids_from_graph(neo4j_session)
    logger.info("Found %d CVE nodes in graph to enrich.", len(cve_ids))
    yearly_batches = _build_yearly_cve_batches(cve_ids)
    skipped_cves = len(cve_ids) - sum(len(batch) for batch in yearly_batches)
    if skipped_cves:
        logger.warning(
            "Skipping %d CVE IDs with unexpected format during CVE metadata enrichment.",
            skipped_cves,
        )

    # Load the feed node first so each batch can attach RESOURCE links to it.
    load_cve_metadata_feed(neo4j_session, config.update_tag, sources)

    if yearly_batches:
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
            # Step 2: Enrich and load one CVE year at a time to keep memory bounded.
            for batch_cve_ids in yearly_batches:
                cves: list[dict[str, Any]] = [
                    {"id": cve_id} for cve_id in batch_cve_ids
                ]

                if "nvd" in sources:
                    nvd_data = nvd.get_and_transform_nvd_cves(
                        http_session,
                        set(batch_cve_ids),
                        api_key=config.cve_metadata_nist_api_key,
                    )
                    nvd.merge_nvd_into_cves(cves, nvd_data)
                    logger.info("NVD enriched %d CVEs in batch.", len(nvd_data))

                if "epss" in sources:
                    try:
                        epss_data = epss.get_epss_scores(http_session, batch_cve_ids)
                        epss.merge_epss_into_cves(cves, epss_data)
                    except requests.exceptions.RequestException:
                        logger.warning(
                            "Failed to fetch EPSS scores, continuing without EPSS enrichment.",
                            exc_info=True,
                        )

                load_cve_metadata(neo4j_session, cves, config.update_tag)

    # Step 4: Cleanup stale CVEMetadata nodes from previous syncs
    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
        "FEED_ID": CVE_METADATA_FEED_ID,
    }
    GraphJob.from_node_schema(CVEMetadataSchema(), common_job_parameters).run(
        neo4j_session,
    )

    merge_module_sync_metadata(
        neo4j_session,
        group_type="CVEMetadata",
        group_id=CVE_METADATA_FEED_ID,
        synced_type="CVEMetadata",
        update_tag=config.update_tag,
        stat_handler=stat_handler,
    )
