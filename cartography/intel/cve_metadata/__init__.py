import logging
from collections import Counter
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
from cartography.intel.cve_metadata import kev
from cartography.intel.cve_metadata import nvd
from cartography.intel.cve_metadata import vulnrichment
from cartography.intel.cve_metadata.effect_tags import derive_effect_tags
from cartography.intel.cve_metadata.effect_tags import unmapped_cwes
from cartography.models.cve_metadata.cve_metadata import CVEMetadataSchema
from cartography.models.cve_metadata.cve_metadata_feed import CVEMetadataFeedSchema
from cartography.stats import get_stats_client
from cartography.util import merge_module_sync_metadata
from cartography.util import run_analysis_job
from cartography.util import timeit

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)

CVE_METADATA_FEED_ID = "CVE_METADATA"
ALL_SOURCES = {"nvd", "epss", "kev", "vulnrichment"}

# Each CVEMetadata row fans out to every node carrying the :CVE label with the same cve_id
# (the deprecated CVE node plus AWSInspectorFinding / SemgrepSCAFinding / TrivyImageFinding /
# ...), and all of those ENRICHES MERGEs land in one transaction. Yearly batches alone stay
# under the 10000-row default, so without this a whole CVE year is one transaction: on a large
# container-scanning graph a ~2400-row transaction exhausted a 3.5 GiB
# dbms.memory.transaction.total.max pool.
CVE_METADATA_BATCH_SIZE = 500


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
      AND NOT (
        labels(c) = ['CVE']
        AND coalesce(c._module_name, '') = 'cartography:cve'
        AND NOT EXISTS {
          MATCH (c)-[r]-()
          WHERE NOT type(r) IN ['RESOURCE', 'ENRICHES']
        }
      )
    RETURN DISTINCT c.cve_id
    """
    return [str(cve_id) for cve_id in read_list_of_values_tx(neo4j_session, query)]


@timeit
def load_cve_metadata_feed(
    neo4j_session: neo4j.Session,
    update_tag: int,
    sources: set[str],
    kev_catalog: kev.KevCatalog | None = None,
    vulnrichment_snapshot: vulnrichment.VulnrichmentSnapshot | None = None,
) -> None:
    """Load the CVEMetadataFeed node."""
    feed_data = [
        {
            "FEED_ID": CVE_METADATA_FEED_ID,
            "source_nvd": "nvd" in sources,
            "source_epss": "epss" in sources,
            "source_kev": "kev" in sources,
            "source_vulnrichment": "vulnrichment" in sources,
            "kev_catalog_version": (
                kev_catalog.catalog_version if kev_catalog else None
            ),
            "kev_date_released": kev_catalog.date_released if kev_catalog else None,
            "vulnrichment_commit": (
                vulnrichment_snapshot.commit if vulnrichment_snapshot else None
            ),
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
        batch_size=CVE_METADATA_BATCH_SIZE,
        lastupdated=update_tag,
        FEED_ID=CVE_METADATA_FEED_ID,
    )


def _fetch_kev_catalog(http_session: Session) -> kev.KevCatalog | None:
    try:
        return kev.transform_kev_catalog(kev.get_kev_catalog(http_session))
    except (requests.exceptions.RequestException, ValueError, KeyError, TypeError):
        logger.warning(
            "Failed to fetch the CISA KEV catalog; is_kev falls back to NVD where available.",
            exc_info=True,
        )
        return None


def _fetch_vulnrichment(
    http_session: Session,
    cve_ids: set[str],
) -> vulnrichment.VulnrichmentSnapshot | None:
    try:
        return vulnrichment.get_vulnrichment_records(http_session, cve_ids)
    except vulnrichment.FETCH_ERRORS:
        logger.warning(
            "Failed to read the Vulnrichment archive, continuing without SSVC enrichment.",
            exc_info=True,
        )
        return None


@timeit
def start_cve_metadata_ingestion(
    neo4j_session: neo4j.Session,
    config: Config,
) -> None:
    """
    Enrich existing CVE nodes with metadata from NVD, EPSS, the CISA KEV catalog,
    and CISA Vulnrichment.
    :param neo4j_session: Neo4J session for database interface
    :param config: A cartography.config object
    """
    sources = set(config.cve_metadata_src) if config.cve_metadata_src else ALL_SOURCES
    invalid = sources - ALL_SOURCES
    if invalid:
        raise ValueError(
            f"Invalid CVE metadata sources: {invalid}. Valid sources: {ALL_SOURCES}",
        )

    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
        "FEED_ID": CVE_METADATA_FEED_ID,
    }

    # DEPRECATED: cleanup for plain CVE feed nodes from cartography:cve; remove in v1.0.0.
    run_analysis_job(
        "cve_deprecated_feed_cleanup.json",
        neo4j_session,
        common_job_parameters,
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

    if not yearly_batches:
        load_cve_metadata_feed(neo4j_session, config.update_tag, sources)
    else:
        session = Session()
        retry_policy = Retry(
            total=8,
            connect=1,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
        )
        session.mount("https://", HTTPAdapter(max_retries=retry_policy))

        # Count vulns per CWE we don't yet have in the effect_tags mapping table,
        # so the aggregated gap is logged once at the end of the sync.
        unmapped_cwe_counts: Counter[str] = Counter()

        with session as http_session:
            # KEV and Vulnrichment are single downloads, fetched once for all batches.
            kev_catalog = None
            if "kev" in sources:
                kev_catalog = _fetch_kev_catalog(http_session)
            vulnrichment_snapshot = None
            if "vulnrichment" in sources:
                vulnrichment_snapshot = _fetch_vulnrichment(http_session, set(cve_ids))

            # Load the feed node first so each batch can attach RESOURCE links to it.
            load_cve_metadata_feed(
                neo4j_session,
                config.update_tag,
                sources,
                kev_catalog,
                vulnrichment_snapshot,
            )

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

                # Runs without a catalog too, so that is_kev_source records the
                # NVD fallback.
                kev.merge_kev_into_cves(cves, kev_catalog)
                vulnrichment.merge_vulnrichment_into_cves(cves, vulnrichment_snapshot)
                logger.info(
                    "%d of %d CVEs in batch are known exploited (is_kev from %s); "
                    "%d have an SSVC decision.",
                    sum(1 for cve in cves if cve.get("is_kev")),
                    len(cves),
                    "the KEV catalog" if kev_catalog else "NVD, where available",
                    sum(1 for cve in cves if cve.get("ssvc_exploitation")),
                )

                # Derive effect_tags for every CVE (not just NVD-transformed ones),
                # so the ingest contract holds even for epss-only / NVD-absent nodes.
                for cve in cves:
                    cve["effect_tags"], cve["effect_tags_source"] = derive_effect_tags(
                        cve,
                    )
                    unmapped_cwe_counts.update(unmapped_cwes(cve.get("weaknesses", [])))

                load_cve_metadata(neo4j_session, cves, config.update_tag)

        if unmapped_cwe_counts:
            summary = ", ".join(
                f"{count} vuln(s) with {cwe}"
                for cwe, count in unmapped_cwe_counts.most_common()
            )
            logger.warning(
                "effect_tags: %d CWE(s) not in the mapping table: %s",
                len(unmapped_cwe_counts),
                summary,
            )

    # Step 4: Cleanup stale CVEMetadata nodes from previous syncs
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
