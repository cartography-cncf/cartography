from __future__ import annotations

import logging
from typing import Any
from typing import TYPE_CHECKING

import neo4j
from pydantic import BaseModel

from cartography.client.core.tx import load
from cartography.client.core.tx import run_write_query
from cartography.intel.common.object_store import ObjectStoreError
from cartography.intel.common.object_store import read_json_report
from cartography.intel.common.object_store import ReportReader
from cartography.intel.common.object_store import ReportRef
from cartography.intel.common.report_reader_builder import (
    build_report_reader_for_source,
)
from cartography.intel.common.report_source import parse_report_source
from cartography.intel.zizmor.mapping import get_zizmor_repository_mappings
from cartography.intel.zizmor.mapping import ZizmorRepositoryMappingEntry
from cartography.intel.zizmor.transform import looks_like_zizmor_report
from cartography.intel.zizmor.transform import transform_zizmor_report
from cartography.models.zizmor.finding import ZizmorFindingSchema
from cartography.util import timeit

if TYPE_CHECKING:
    from cartography.config import Config

logger = logging.getLogger(__name__)


class ZizmorRepositoryReportCollection(BaseModel):
    """
    Aggregated report-read status for one repository mapping entry.

    Cleanup for a repository may only run when every report source listed for it
    was read successfully, so the per-source counts are tracked alongside the
    documents themselves.
    """

    repository_mapping: ZizmorRepositoryMappingEntry
    reports: list[tuple[ReportRef, list[dict[str, Any]]]]
    total_sources: int
    successful_sources: int

    @property
    def all_sources_succeeded(self) -> bool:
        return self.total_sources > 0 and self.successful_sources == self.total_sources


@timeit
def get_zizmor_report(reader: ReportReader) -> tuple[ReportRef, list[Any]] | None:
    """
    Read one zizmor JSON report from a provider-agnostic report source.

    Each report source listed in the repository mapping file is expected to
    resolve to exactly one artifact. If the source resolves to zero artifacts,
    multiple artifacts, a non-JSON artifact, or an invalid zizmor report, this
    returns None and the source is treated as failed.
    """
    refs = reader.list_reports()

    if len(refs) != 1:
        logger.warning(
            "Zizmor report source must resolve to exactly one artifact, but %s resolved to %d artifacts.",
            reader.source_uri,
            len(refs),
        )
        return None

    ref = refs[0]
    if not ref.name.endswith(".json"):
        logger.warning(
            "Zizmor report source %s must point to a single JSON artifact.",
            ref.uri,
        )
        return None

    try:
        document = read_json_report(reader, ref)
    except ObjectStoreError as exc:
        logger.warning("Skipping unreadable Zizmor report %s: %s", ref.uri, exc)
        return None

    if not looks_like_zizmor_report(document):
        logger.warning(
            "Skipping %s: report source did not contain a zizmor JSON v1 report. "
            "Zizmor reports must be produced with `--format=json-v1`.",
            ref.uri,
        )
        return None

    return ref, document


@timeit
def get_zizmor_reports_for_repository_mapping(
    repository_mapping: ZizmorRepositoryMappingEntry,
    *,
    config: Config | None = None,
) -> ZizmorRepositoryReportCollection:
    """
    Read the zizmor JSON reports listed for a single repository mapping entry.
    """
    reports: list[tuple[ReportRef, list[dict[str, Any]]]] = []
    successful_sources = 0

    for report_source in repository_mapping.reports:
        logger.info(
            "Reading Zizmor report source %s for repository %s.",
            report_source,
            repository_mapping.repository_name,
        )
        source = parse_report_source(report_source)
        with build_report_reader_for_source(source, config=config) as report_reader:
            source_report = get_zizmor_report(report_reader)

        if source_report is not None:
            reports.append(source_report)
            successful_sources += 1

    return ZizmorRepositoryReportCollection(
        repository_mapping=repository_mapping,
        reports=reports,
        total_sources=len(repository_mapping.reports),
        successful_sources=successful_sources,
    )


@timeit
def load_zizmor_findings(
    neo4j_session: neo4j.Session,
    findings: list[dict[str, Any]],
    update_tag: int,
) -> None:
    logger.info("Loading %d ZizmorFinding objects into the graph.", len(findings))
    load(
        neo4j_session,
        ZizmorFindingSchema(),
        findings,
        lastupdated=update_tag,
    )


# (rel_label, target_label) for every relationship on ZizmorFindingSchema.
_ZIZMOR_FINDING_RELATIONSHIPS = (
    ("AFFECTS", "GitHubWorkflow"),
    ("AFFECTS", "GitHubAction"),
    ("FOUND_IN", "GitHubRepository"),
)


@timeit
def cleanup_zizmor_findings(
    neo4j_session: neo4j.Session,
    repository_url: str,
    update_tag: int,
) -> None:
    """
    Delete stale zizmor findings and finding relationships for one repository.

    ZizmorFinding has no sub-resource to scope a generated cleanup job to, and an
    unscoped `GraphJob.from_node_schema()` would delete every stale finding
    globally. That would force us to skip cleanup entirely whenever a single
    report in the mapping file is unreadable, leaving stale findings behind for
    every other repository. Scoping on `repository_url` instead keeps a failure
    contained to the repository it affects, following the precedent set by
    `cleanup_oss_semgrep_sast_findings`.

    Relationships are cleaned separately from nodes because a finding's id does
    not cover its relationship targets. A step whose `uses` reference is bumped
    keeps the same audit, file path and YAML route, so the finding node survives
    the sync while its `AFFECTS` edge should move to the new action. Deleting
    only stale nodes would leave the edge to the old action attached.
    """
    logger.info("Running ZizmorFinding cleanup job for repository %s.", repository_url)

    for rel_label, target_label in _ZIZMOR_FINDING_RELATIONSHIPS:
        run_write_query(
            neo4j_session,
            f"""
            MATCH (n:ZizmorFinding)-[r:{rel_label}]->(:{target_label})
            WHERE n.repository_url = $REPOSITORY_URL
              AND r.lastupdated <> $UPDATE_TAG
            DELETE r
            """,
            REPOSITORY_URL=repository_url,
            UPDATE_TAG=update_tag,
        )

    run_write_query(
        neo4j_session,
        """
        MATCH (n:ZizmorFinding)
        WHERE n.repository_url = $REPOSITORY_URL
          AND n.lastupdated <> $UPDATE_TAG
        WITH n
        DETACH DELETE n
        """,
        REPOSITORY_URL=repository_url,
        UPDATE_TAG=update_tag,
    )


@timeit
def sync_zizmor_findings(
    neo4j_session: neo4j.Session,
    mapping_source: str,
    update_tag: int,
    *,
    config: Config | None = None,
) -> None:
    """
    End-to-end sync for zizmor findings: get, transform, load, cleanup.
    """
    cleanup_repository_urls: list[str] = []

    mapping = parse_report_source(mapping_source)
    with build_report_reader_for_source(mapping, config=config) as mapping_reader:
        repository_mappings = get_zizmor_repository_mappings(mapping_reader)

    for repository_mapping in repository_mappings:
        logger.info(
            "Processing Zizmor repository mapping for %s.",
            repository_mapping.repository_name,
        )
        report_collection = get_zizmor_reports_for_repository_mapping(
            repository_mapping,
            config=config,
        )
        repo_findings: list[dict[str, Any]] = []
        skipped_findings = 0

        for ref, document in report_collection.reports:
            logger.info("Transforming zizmor findings from %s", ref.uri)
            result = transform_zizmor_report(
                document,
                repository_mapping.repository_context,
            )
            repo_findings.extend(result.rows)
            skipped_findings += result.skipped

        logger.info(
            "Zizmor repository %s processed %d/%d report sources successfully.",
            repository_mapping.repository_name,
            report_collection.successful_sources,
            report_collection.total_sources,
        )
        if not report_collection.all_sources_succeeded:
            logger.warning(
                "Skipping cleanup for repository %s because only %d/%d report sources succeeded.",
                repository_mapping.repository_name,
                report_collection.successful_sources,
                report_collection.total_sources,
            )
        elif skipped_findings:
            # Skipped findings are still open; the graph just cannot represent
            # them. Cleaning up now would delete them as though they were fixed.
            logger.warning(
                "Skipping cleanup for repository %s because %d finding(s) could not be "
                "joined to the graph.",
                repository_mapping.repository_name,
                skipped_findings,
            )
        else:
            cleanup_repository_urls.append(repository_mapping.url)

        if repo_findings:
            logger.info(
                "Transformed %d zizmor findings for repository %s.",
                len(repo_findings),
                repository_mapping.repository_name,
            )
            load_zizmor_findings(neo4j_session, repo_findings, update_tag)

    if cleanup_repository_urls:
        for repository_url in cleanup_repository_urls:
            cleanup_zizmor_findings(neo4j_session, repository_url, update_tag)
    else:
        logger.warning(
            "Skipping Zizmor cleanup because no repository entries were fully observed from %s.",
            mapping_source,
        )


@timeit
def start_zizmor_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    if not config.zizmor_source:
        logger.info("Zizmor configuration not provided. Skipping Zizmor ingestion.")
        return

    sync_zizmor_findings(
        neo4j_session,
        config.zizmor_source,
        config.update_tag,
        config=config,
    )
