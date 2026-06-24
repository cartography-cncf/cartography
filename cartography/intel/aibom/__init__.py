import logging
from typing import Any

from neo4j import Session

from cartography.client.core.tx import read_single_value_tx
from cartography.config import Config
from cartography.intel.aibom.cleanup import cleanup_aibom
from cartography.intel.aibom.loader import load_aibom_components
from cartography.intel.aibom.loader import load_aibom_sources
from cartography.intel.aibom.transform import transform_aibom_component_payloads
from cartography.intel.aibom.transform import transform_aibom_source_payloads
from cartography.intel.common.object_store import filter_report_refs
from cartography.intel.common.object_store import ObjectStoreError
from cartography.intel.common.object_store import read_json_report
from cartography.intel.common.object_store import ReportReader
from cartography.intel.common.report_reader_builder import (
    build_report_reader_for_source,
)
from cartography.intel.common.report_source import parse_report_source
from cartography.stats import get_stats_client
from cartography.util import timeit

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)


def _extract_digest_from_source_key(source_key: str) -> str | None:
    _, sep, digest = source_key.partition("@")
    if not sep or not digest.startswith("sha256:"):
        return None
    return digest


def _image_digest_exists(neo4j_session: Session, digest: str) -> bool:
    result = neo4j_session.execute_read(
        read_single_value_tx,
        "MATCH (img:Image {_ont_digest: $digest}) RETURN img._ont_digest LIMIT 1",
        digest=digest,
    )
    return result is not None


def _code_repository_uri_exists(neo4j_session: Session, uri: str) -> bool:
    """
    Return True when the URI matches an existing GitHubRepository.url or
    GitLabProject.web_url node already present in the graph.
    """
    result = neo4j_session.execute_read(
        read_single_value_tx,
        """
        OPTIONAL MATCH (gh:GitHubRepository {url: $uri})
        WITH gh
        OPTIONAL MATCH (gl:GitLabProject {web_url: $uri})
        RETURN (gh IS NOT NULL OR gl IS NOT NULL) AS resolved
        LIMIT 1
        """,
        uri=uri,
    )
    return bool(result)


def prepare_aibom_report_for_ingestion(
    neo4j_session: Session,
    document: dict[str, Any],
    source: str,
) -> dict[str, Any]:
    """
    Perform the GET/preparation step for an AIBOM report:
    validate the raw document at a high level, extract source keys, and verify
    that every anchor resolves to an existing target node. Digest-qualified
    source keys must resolve to concrete :Image nodes; any other source key is
    treated as a code-repository URI and must resolve to an existing
    GitHubRepository or GitLabProject.
    """
    sources = document["aibom_analysis"]["sources"]
    source_keys = tuple(sources)
    if not source_keys:
        raise ValueError(
            f"AIBOM report at {source} did not contain any sources",
        )

    missing_digests: list[str] = []
    unresolved_repository_uris: list[str] = []
    for source_key in source_keys:
        digest = _extract_digest_from_source_key(source_key)
        if digest is not None:
            if not _image_digest_exists(neo4j_session, digest):
                missing_digests.append(digest)
        elif not _code_repository_uri_exists(neo4j_session, source_key):
            unresolved_repository_uris.append(source_key)

    if missing_digests:
        raise ValueError(
            "AIBOM report "
            f"{source} did not resolve to concrete :Image nodes for digests: "
            f"{', '.join(sorted(set(missing_digests)))}",
        )
    if unresolved_repository_uris:
        raise ValueError(
            "AIBOM report "
            f"{source} did not resolve to existing GitHubRepository or "
            "GitLabProject nodes for source keys: "
            f"{', '.join(sorted(set(unresolved_repository_uris)))}",
        )

    return document


@timeit
def sync_aibom_from_report_reader(
    neo4j_session: Session,
    reader: ReportReader,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    logger.info("Using AIBOM results from %s", reader.source_uri)

    json_files = filter_report_refs(
        reader.list_reports(),
        suffix=".json",
    )
    if not json_files:
        logger.warning(
            "AIBOM sync was configured, but no json files were found in %s",
            reader.source_uri,
        )
        return

    cleanup_blocking_report_count = 0
    processed_reports = 0
    for ref in json_files:
        source = ref.uri
        try:
            document = read_json_report(reader, ref)
        except ObjectStoreError as exc:
            logger.error("Failed to read AIBOM data from %s: %s", source, exc)
            cleanup_blocking_report_count += 1
            continue

        prepared_report = prepare_aibom_report_for_ingestion(
            neo4j_session,
            document,
            source,
        )

        source_payloads = transform_aibom_source_payloads(
            prepared_report,
            report_location=source,
        )
        component_payloads = transform_aibom_component_payloads(prepared_report)
        if not source_payloads:
            logger.info("AIBOM report %s had no source payloads to ingest", source)
            continue

        if component_payloads:
            load_aibom_components(neo4j_session, component_payloads, update_tag)
        load_aibom_sources(neo4j_session, source_payloads, update_tag)
        stat_handler.incr("aibom_reports_processed")
        processed_reports += 1

    # Skip cleanup if we did not fully observe every candidate report.
    # This matches the trivy modules all or nothing approach.
    if cleanup_blocking_report_count:
        logger.warning(
            "Skipping AIBOM cleanup because %d report(s) failed or were skipped during preparation.",
            cleanup_blocking_report_count,
        )
        return

    # Skip cleanup when nothing was ingested: AIBOM cleanup is unscoped and
    # would delete data from a successful prior run.
    if processed_reports == 0:
        logger.warning(
            "Skipping AIBOM cleanup because no reports were ingested.",
        )
        return

    cleanup_aibom(neo4j_session, common_job_parameters)


@timeit
def start_aibom_ingestion(neo4j_session: Session, config: Config) -> None:
    if not config.aibom_source:
        logger.info("AIBOM configuration not provided. Skipping AIBOM ingestion.")
        return

    source = parse_report_source(config.aibom_source)
    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
    }
    with build_report_reader_for_source(
        source,
        config=config,
    ) as reader:
        sync_aibom_from_report_reader(
            neo4j_session,
            reader,
            config.update_tag,
            common_job_parameters,
        )
