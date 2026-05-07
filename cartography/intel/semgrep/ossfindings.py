from __future__ import annotations

import hashlib
import logging
from typing import Any
from typing import TYPE_CHECKING

import neo4j
import yaml
from pydantic import BaseModel
from pydantic import Field
from pydantic import field_validator
from pydantic import ValidationError

from cartography.client.core.tx import load
from cartography.client.core.tx import run_write_query
from cartography.intel.common.object_store import filter_report_refs
from cartography.intel.common.object_store import ObjectStoreError
from cartography.intel.common.object_store import read_json_report
from cartography.intel.common.object_store import read_text_report
from cartography.intel.common.object_store import ReportReader
from cartography.intel.common.object_store import ReportRef
from cartography.intel.common.report_reader_builder import (
    build_report_reader_for_source,
)
from cartography.intel.common.report_source import parse_report_source
from cartography.models.semgrep.deployment import SemgrepDeploymentSchema
from cartography.models.semgrep.ossfindings import OSSSemgrepSASTFindingSchema
from cartography.util import timeit

if TYPE_CHECKING:
    from cartography.config import Config

logger = logging.getLogger(__name__)

OSS_DEPLOYMENT_ID = "oss"
_SEMGREP_OSS_RESULT_REQUIRED_KEYS = {"check_id", "path", "start", "end", "extra"}
_SEMGREP_OSS_UNUSABLE_FINGERPRINTS = {"requires login"}


class SemgrepOSSRepositoryMappingEntry(BaseModel):
    provider: str
    owner: str
    repo: str
    url: str
    branch: str
    reports: list[str] = Field(min_length=1)

    @field_validator("provider", "owner", "repo", "url", "branch")  # type: ignore[misc]
    @classmethod
    def _validate_required_string(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Value cannot be empty.")
        return normalized

    @field_validator("reports")  # type: ignore[misc]
    @classmethod
    def _validate_reports(cls, reports: list[str]) -> list[str]:
        normalized_reports: list[str] = []
        for raw_report in reports:
            report_source = raw_report.strip()
            if not report_source:
                raise ValueError("Report source cannot be empty.")
            normalized_reports.append(report_source)
        return normalized_reports

    @property
    def repository_name(self) -> str:
        return f"{self.owner}/{self.repo}"

    @property
    def repository_context(self) -> dict[str, str]:
        return {
            "repositoryName": self.repository_name,
            "repositoryUrl": self.url,
            "branch": self.branch,
        }


class SemgrepOSSRepositoryMappingFile(BaseModel):
    repositories: list[SemgrepOSSRepositoryMappingEntry] = Field(min_length=1)


class SemgrepOSSRepositoryReportCollection(BaseModel):
    """
    Aggregated report-read status for one repository mapping entry.

    This captures both the valid Semgrep OSS report documents collected for a
    repository and the per-source success counts needed to reason about whether
    the repository was fully observed during the current sync.
    """

    repository_mapping: SemgrepOSSRepositoryMappingEntry
    reports: list[tuple[ReportRef, dict[str, Any]]]
    total_sources: int
    successful_sources: int

    @property
    def failed_sources(self) -> int:
        return self.total_sources - self.successful_sources

    @property
    def all_sources_succeeded(self) -> bool:
        return self.total_sources > 0 and self.successful_sources == self.total_sources

    @property
    def any_reports_processed(self) -> bool:
        return self.successful_sources > 0


def get_semgrep_oss_repository_mappings(
    reader: ReportReader,
) -> list[SemgrepOSSRepositoryMappingEntry]:
    """
    Read and validate a Semgrep OSS repository mapping file.
    """
    mapping_refs = filter_report_refs(reader.list_reports(), suffix=".yaml")
    mapping_refs.extend(filter_report_refs(reader.list_reports(), suffix=".yml"))

    if len(mapping_refs) != 1:
        raise ValueError(
            "Semgrep OSS repository mapping source must contain exactly one YAML file."
        )
    mapping_ref = mapping_refs[0]

    try:
        mapping_document = yaml.safe_load(read_text_report(reader, mapping_ref))
    except yaml.YAMLError as exc:
        raise ValueError(
            f"Semgrep OSS repository mapping file must be valid YAML: {mapping_ref.uri}"
        ) from exc

    try:
        mapping_file = SemgrepOSSRepositoryMappingFile.model_validate(mapping_document)
    except ValidationError as exc:
        raise ValueError(
            "Semgrep OSS repository mapping file is invalid " f"{mapping_ref.uri}"
        ) from exc

    return mapping_file.repositories


def _looks_like_semgrep_oss_report(document: Any) -> bool:
    if not isinstance(document, dict):
        return False

    results = document.get("results")
    if not isinstance(results, list):
        return False

    # Empty results is still a valid Semgrep OSS report.
    if not results:
        return True

    first = results[0]
    if not isinstance(first, dict):
        return False

    return _SEMGREP_OSS_RESULT_REQUIRED_KEYS.issubset(first.keys())


@timeit
def get_semgrep_oss_report(
    reader: ReportReader,
) -> tuple[ReportRef, dict[str, Any]] | None:
    """
    Read one Semgrep OSS JSON report from a provider-agnostic report source.

    Each explicit report source listed in the repository mapping file is
    expected to resolve to exactly one artifact. If the source resolves to
    zero artifacts, multiple artifacts, a non-JSON artifact, or an invalid
    Semgrep OSS report, this returns None and the source is treated as failed.
    """
    refs = reader.list_reports()

    if len(refs) != 1:
        logger.warning(
            "Semgrep OSS report source must resolve to exactly one artifact, but %s resolved to %d artifacts.",
            reader.source_uri,
            len(refs),
        )
        return None

    ref = refs[0]
    if not ref.name.endswith(".json"):
        logger.warning(
            "Semgrep OSS report source %s must point to a single JSON artifact.",
            ref.uri,
        )
        return None

    try:
        document = read_json_report(reader, ref)
    except ObjectStoreError as exc:
        logger.warning("Skipping unreadable Semgrep report %s: %s", ref.uri, exc)
        return None

    if not _looks_like_semgrep_oss_report(document):
        logger.warning(
            "Skipping %s: explicit Semgrep OSS report source did not contain a Semgrep OSS JSON report.",
            ref.uri,
        )
        return None

    return ref, document


@timeit
def get_semgrep_oss_reports_for_repository_mapping(
    repository_mapping: SemgrepOSSRepositoryMappingEntry,
    *,
    config: Config | None = None,
) -> SemgrepOSSRepositoryReportCollection:
    """
    Read Semgrep OSS JSON reports for a single repository mapping entry.

    Iterates all explicit report sources listed under one repository entry,
    opens each source using the provider-agnostic report-source helpers, and
    aggregates the valid Semgrep OSS JSON documents that were successfully read.

    Returns:
        A repo-level collection object containing:
        - All valid Semgrep OSS report documents aggregated across the listed sources.
        - Counts describing how many listed sources succeeded or failed.
        - Convenience properties for repo-level success tracking.
    """
    reports: list[tuple[ReportRef, dict[str, Any]]] = []
    successful_sources = 0

    for report_source in repository_mapping.reports:
        logger.info(
            "Reading Semgrep OSS report source %s for repository %s.",
            report_source,
            repository_mapping.repository_name,
        )
        source = parse_report_source(report_source)
        with build_report_reader_for_source(source, config=config) as report_reader:
            source_report = get_semgrep_oss_report(report_reader)

        if source_report is not None:
            reports.append(source_report)
            successful_sources += 1

    return SemgrepOSSRepositoryReportCollection(
        repository_mapping=repository_mapping,
        reports=reports,
        total_sources=len(repository_mapping.reports),
        successful_sources=successful_sources,
    )


def _is_oss_sast_result(result: dict[str, Any]) -> bool:
    """
    Lightweight shape check for a Semgrep OSS code finding.
    """
    if not isinstance(result, dict):
        return False

    if not _SEMGREP_OSS_RESULT_REQUIRED_KEYS.issubset(result.keys()):
        return False

    if not isinstance(result.get("start"), dict):
        return False
    if not isinstance(result.get("end"), dict):
        return False
    if not isinstance(result.get("extra"), dict):
        return False

    return True


def _build_oss_sast_finding_id(
    check_id: str,
    path: str,
    start_line: str,
    start_col: str,
    end_line: str,
    end_col: str,
    repository_url: str,
    fingerprint: str | None = None,
) -> str:
    """
    Build a stable synthetic ID for OSS findings since Semgrep OSS CLI output
    does not include the Semgrep Cloud finding ID. Prefer Semgrep's
    fingerprint when present for stability across location-only churn, and
    fall back to a location hash otherwise. Include repository URL so
    identical findings in different repositories do not collide.
    """
    normalized_fingerprint = fingerprint.strip() if fingerprint is not None else None
    use_fingerprint = (
        normalized_fingerprint is not None
        and normalized_fingerprint
        and normalized_fingerprint.lower() not in _SEMGREP_OSS_UNUSABLE_FINGERPRINTS
    )

    raw_id_parts = [check_id]
    if use_fingerprint and normalized_fingerprint is not None:
        raw_id_parts.append(normalized_fingerprint)
    else:
        raw_id_parts.extend(
            [
                path,
                start_line,
                start_col,
                end_line,
                end_col,
            ]
        )
    raw_id_parts.append(repository_url)
    raw_id = "|".join(raw_id_parts)
    digest = hashlib.sha256(raw_id.encode("utf-8")).hexdigest()
    return f"semgrep-oss-sast-{digest}"


def transform_oss_semgrep_sast_report(
    report: dict[str, Any],
    repo_context: dict[str, str],
) -> list[dict[str, Any]]:
    """
    Transform a Semgrep OSS CLI JSON report into rows loadable by
    OSSSemgrepSASTFindingSchema.
    """
    raw_results = report.get("results", [])
    if not isinstance(raw_results, list):
        raise ValueError("Semgrep OSS report must contain a top-level 'results' list.")

    transformed: list[dict[str, Any]] = []

    for result in raw_results:
        if not _is_oss_sast_result(result):
            continue

        check_id = str(result.get("check_id", ""))
        path = str(result.get("path", ""))
        start = result.get("start", {})
        end = result.get("end", {})
        start_line = str(start.get("line", ""))
        start_col = str(start.get("col", ""))
        end_line = str(end.get("line", ""))
        end_col = str(end.get("col", ""))
        fingerprint = result.get("extra", {}).get("fingerprint")
        fingerprint_str = str(fingerprint).strip() if fingerprint is not None else None

        row = dict(result)
        row["id"] = _build_oss_sast_finding_id(
            check_id,
            path,
            start_line,
            start_col,
            end_line,
            end_col,
            repo_context["repositoryUrl"],
            fingerprint_str or None,
        )

        row.update(repo_context)
        category = result.get("extra", {}).get("metadata", {}).get("category")
        row["categories"] = [category] if category is not None else []

        transformed.append(row)

    return transformed


@timeit
def load_oss_semgrep_sast_findings(
    neo4j_session: neo4j.Session,
    findings: list[dict[str, Any]],
    update_tag: int,
) -> None:
    """
    Load OSS Semgrep SAST findings into the graph.

    OSS Semgrep reports don't come from a real Semgrep Cloud deployment, but
    the data model uses SemgrepDeployment as the sub-resource parent for scoped
    cleanup. We create a synthetic SemgrepDeployment node with id="oss" first
    so that the RESOURCE relationship has a valid target.
    """
    logger.info(
        "Loading %d OSS SemgrepSASTFinding objects into the graph.", len(findings)
    )
    load(
        neo4j_session,
        SemgrepDeploymentSchema(),
        [{"id": OSS_DEPLOYMENT_ID, "name": "OSS Semgrep", "slug": "oss"}],
        lastupdated=update_tag,
    )
    load(
        neo4j_session,
        OSSSemgrepSASTFindingSchema(),
        findings,
        lastupdated=update_tag,
        DEPLOYMENT_ID=OSS_DEPLOYMENT_ID,
    )


@timeit
def cleanup_oss_semgrep_sast_findings(
    neo4j_session: neo4j.Session,
    repository_url: str,
    update_tag: int,
) -> None:
    """
    Clean up stale OSS Semgrep SAST findings for one repository URL.

    This is intentionally scoped by both the synthetic OSS deployment and
    repository_url so we only delete stale OSS findings for repository entries
    that were fully observed in the current sync.
    """
    logger.info(
        "Running OSS SemgrepSASTFinding cleanup job for repository %s.",
        repository_url,
    )
    run_write_query(
        neo4j_session,
        """
        MATCH (n:SemgrepSASTFinding)<-[:RESOURCE]-(d:SemgrepDeployment {id: $DEPLOYMENT_ID})
        WHERE n.repository_url = $REPOSITORY_URL
          AND n.lastupdated <> $UPDATE_TAG
        WITH n
        DETACH DELETE n
        """,
        DEPLOYMENT_ID=OSS_DEPLOYMENT_ID,
        REPOSITORY_URL=repository_url,
        UPDATE_TAG=update_tag,
    )


@timeit
def sync_oss_semgrep_sast_findings(
    neo4j_session: neo4j.Session,
    mapping_source: str,
    update_tag: int,
    *,
    config: Config | None = None,
) -> None:
    """
    End-to-end sync for OSS Semgrep SAST findings: get, transform, load, cleanup.
    """
    cleanup_repository_urls: list[str] = []

    mapping = parse_report_source(mapping_source)
    with build_report_reader_for_source(mapping, config=config) as mapping_reader:
        repository_mappings = get_semgrep_oss_repository_mappings(mapping_reader)

    for repository_mapping in repository_mappings:
        logger.info(
            "Processing Semgrep OSS repository mapping for %s.",
            repository_mapping.repository_name,
        )
        report_collection = get_semgrep_oss_reports_for_repository_mapping(
            repository_mapping,
            config=config,
        )
        repo_findings: list[dict[str, Any]] = []

        for ref, document in report_collection.reports:
            logger.info("Transforming OSS Semgrep SAST findings from %s", ref.uri)
            repo_findings.extend(
                transform_oss_semgrep_sast_report(
                    document,
                    repository_mapping.repository_context,
                )
            )

        logger.info(
            "Semgrep OSS repository %s processed %d/%d report sources successfully.",
            repository_mapping.repository_name,
            report_collection.successful_sources,
            report_collection.total_sources,
        )
        if report_collection.all_sources_succeeded:
            cleanup_repository_urls.append(repository_mapping.url)
        else:
            logger.warning(
                "Skipping cleanup for repository %s because only %d/%d report sources succeeded.",
                repository_mapping.repository_name,
                report_collection.successful_sources,
                report_collection.total_sources,
            )

        if repo_findings:
            logger.info(
                "Transformed %d OSS Semgrep SAST findings for repository %s.",
                len(repo_findings),
                repository_mapping.repository_name,
            )
            load_oss_semgrep_sast_findings(neo4j_session, repo_findings, update_tag)

    if cleanup_repository_urls:
        for repository_url in cleanup_repository_urls:
            cleanup_oss_semgrep_sast_findings(
                neo4j_session,
                repository_url,
                update_tag,
            )
    else:
        logger.warning(
            "Skipping OSS Semgrep cleanup because no repository entries were fully observed from %s.",
            mapping_source,
        )
