import logging
from typing import Any

from neo4j import Session

from cartography.config import Config
from cartography.intel.aibom.cleanup import cleanup_aibom
from cartography.intel.aibom.loader import load_aibom_components
from cartography.intel.aibom.loader import load_aibom_custom_relationships
from cartography.intel.aibom.loader import load_aibom_exposes_tool_relationships
from cartography.intel.aibom.loader import load_aibom_sources
from cartography.intel.aibom.loader import load_aibom_uses_model_relationships
from cartography.intel.aibom.loader import load_aibom_uses_tool_relationships
from cartography.intel.aibom.transform import (
    group_aibom_relationship_payloads_by_source_key,
)
from cartography.intel.aibom.transform import transform_aibom_component_payloads
from cartography.intel.aibom.transform import transform_aibom_relationship_payloads
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


def _extract_aibom_source_map(document: dict[str, Any]) -> dict[str, Any]:
    return document["aibom_analysis"]["sources"]


def _extract_digest_from_source_key(source_key: str) -> str | None:
    _, sep, digest = source_key.partition("@")
    if not sep or not digest.startswith("sha256:"):
        return None
    return digest


def _image_digest_exists(neo4j_session: Session, digest: str) -> bool:
    result = neo4j_session.run(
        "MATCH (img:Image {_ont_digest: $digest}) RETURN img._ont_digest LIMIT 1",
        digest=digest,
    ).single()
    return result is not None


def prepare_aibom_report_for_ingestion(
    neo4j_session: Session,
    document: dict[str, Any],
    source: str,
) -> dict[str, Any] | None:
    """
    Perform the GET/preparation step for an AIBOM report:
    validate the raw document at a high level, extract source keys, require
    digest-qualified anchors, and verify they resolve to concrete :Image nodes.
    """
    sources = _extract_aibom_source_map(document)
    source_keys = tuple(
        source_key for source_key in sources if isinstance(source_key, str)
    )
    if not source_keys:
        logger.warning(
            "Skipping AIBOM report %s: expected string source keys in sources map",
            source,
        )
        return None

    image_digests = tuple(
        digest
        for digest in (
            _extract_digest_from_source_key(source_key) for source_key in source_keys
        )
        if digest
    )
    if not image_digests:
        logger.warning(
            "Skipping AIBOM report %s: no digest-qualified source keys were found",
            source,
        )
        return None

    missing_digests = [
        digest
        for digest in image_digests
        if not _image_digest_exists(neo4j_session, digest)
    ]
    if missing_digests:
        logger.warning(
            "Skipping AIBOM report %s: source digests did not resolve to concrete :Image nodes: %s",
            source,
            ", ".join(sorted(set(missing_digests))),
        )
        return None

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

    failed_report_count = 0
    processed_reports = 0
    for ref in json_files:
        source = ref.uri
        try:
            document = read_json_report(reader, ref)
        except ObjectStoreError as exc:
            logger.error("Failed to read AIBOM data from %s: %s", source, exc)
            failed_report_count += 1
            continue

        prepared_report = prepare_aibom_report_for_ingestion(
            neo4j_session,
            document,
            source,
        )

        if prepared_report is None:
            continue

        source_payloads = transform_aibom_source_payloads(
            prepared_report,
            report_location=source,
        )
        component_payloads = transform_aibom_component_payloads(prepared_report)
        relationship_payloads = transform_aibom_relationship_payloads(
            prepared_report,
        )
        uses_model_relationship_payloads = (
            group_aibom_relationship_payloads_by_source_key(
                relationship_payloads,
                "USES_MODEL",
            )
        )
        uses_tool_relationship_payloads = (
            group_aibom_relationship_payloads_by_source_key(
                relationship_payloads,
                "USES_TOOL",
            )
        )
        exposes_tool_relationship_payloads = (
            group_aibom_relationship_payloads_by_source_key(
                relationship_payloads,
                "EXPOSES_TOOL",
            )
        )
        custom_relationship_payloads = group_aibom_relationship_payloads_by_source_key(
            relationship_payloads,
            "CUSTOM",
        )
        if not source_payloads:
            logger.info("AIBOM report %s had no source payloads to ingest", source)
            continue

        stat_handler.incr("aibom_reports_processed")
        load_aibom_components(neo4j_session, component_payloads, update_tag)
        load_aibom_sources(neo4j_session, source_payloads, update_tag)
        for source_key, source_payloads in uses_model_relationship_payloads.items():
            load_aibom_uses_model_relationships(
                neo4j_session,
                source_payloads,
                source_key,
                update_tag,
            )
        for source_key, source_payloads in uses_tool_relationship_payloads.items():
            load_aibom_uses_tool_relationships(
                neo4j_session,
                source_payloads,
                source_key,
                update_tag,
            )
        for source_key, source_payloads in exposes_tool_relationship_payloads.items():
            load_aibom_exposes_tool_relationships(
                neo4j_session,
                source_payloads,
                source_key,
                update_tag,
            )
        for source_key, source_payloads in custom_relationship_payloads.items():
            load_aibom_custom_relationships(
                neo4j_session,
                source_payloads,
                source_key,
                update_tag,
            )
        processed_reports += 1

    if failed_report_count:
        logger.warning(
            "Skipping AIBOM cleanup because %d report(s) failed to read or parse.",
            failed_report_count,
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
