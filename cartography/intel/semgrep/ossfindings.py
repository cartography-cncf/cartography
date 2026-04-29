from __future__ import annotations

import hashlib
import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.common.object_store import filter_report_refs
from cartography.intel.common.object_store import ObjectStoreError
from cartography.intel.common.object_store import read_json_report
from cartography.intel.common.object_store import ReportReader
from cartography.intel.common.object_store import ReportRef
from cartography.models.semgrep.deployment import SemgrepDeploymentSchema
from cartography.models.semgrep.ossfindings import OSSSemgrepSASTFindingSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

OSS_DEPLOYMENT_ID = "oss"


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

    required_keys = {"check_id", "path", "start", "end", "extra"}
    return required_keys.issubset(first.keys())


def get_semgrep_oss_reports(
    reader: ReportReader,
) -> list[tuple[ReportRef, dict[str, Any]]]:
    """
    Read Semgrep OSS JSON reports from a provider-agnostic report source.

    Returns:
        List of (ref, parsed_document) pairs for valid Semgrep OSS reports.
    """
    refs = filter_report_refs(
        reader.list_reports(),
        suffix=".json",
    )

    if not refs:
        logger.warning(
            "Semgrep OSS sync was configured, but no JSON reports were found in %s",
            reader.source_uri,
        )
        return []

    reports: list[tuple[ReportRef, dict[str, Any]]] = []

    for ref in refs:
        try:
            document = read_json_report(reader, ref)
        except ObjectStoreError as exc:
            logger.warning("Skipping unreadable Semgrep report %s: %s", ref.uri, exc)
            continue

        if not _looks_like_semgrep_oss_report(document):
            logger.debug("Skipping %s: not a Semgrep OSS JSON report", ref.uri)
            continue

        reports.append((ref, document))

    return reports


def _is_oss_sast_result(result: dict[str, Any]) -> bool:
    """
    Lightweight shape check for a Semgrep OSS code finding.
    """
    if not isinstance(result, dict):
        return False

    required_keys = {"check_id", "path", "start", "end", "extra"}
    if not required_keys.issubset(result.keys()):
        return False

    if not isinstance(result.get("start"), dict):
        return False
    if not isinstance(result.get("end"), dict):
        return False
    if not isinstance(result.get("extra"), dict):
        return False

    return True


def _build_oss_sast_finding_id(result: dict[str, Any]) -> str:
    """
    Build a stable synthetic ID for OSS findings since Semgrep OSS CLI output
    does not include the Semgrep Cloud finding ID.
    """
    raw_id = "|".join(
        [
            str(result.get("check_id", "")),
            str(result.get("path", "")),
            str(result.get("start", {}).get("line", "")),
            str(result.get("start", {}).get("col", "")),
            str(result.get("end", {}).get("line", "")),
            str(result.get("end", {}).get("col", "")),
        ],
    )
    digest = hashlib.sha256(raw_id.encode("utf-8")).hexdigest()
    return f"semgrep-oss-sast-{digest}"


def transform_oss_semgrep_sast_report(
    report: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Transform a Semgrep OSS CLI JSON report into rows loadable by
    OSSSemgrepSASTFindingSchema.
    """
    raw_results = report.get("results", [])
    if not isinstance(raw_results, list):
        raise ValueError("Semgrep OSS report must contain a top-level 'results' list.")

    repository = report.get("repository", {})
    repository_name = repository.get("name") if isinstance(repository, dict) else None
    repository_url = repository.get("url") if isinstance(repository, dict) else None
    branch = repository.get("branch") if isinstance(repository, dict) else None

    transformed: list[dict[str, Any]] = []

    for result in raw_results:
        if not _is_oss_sast_result(result):
            continue

        row = dict(result)
        row["id"] = _build_oss_sast_finding_id(result)

        # Inject repository context from the top-level report metadata.
        row["repositoryName"] = repository_name
        row["repositoryUrl"] = repository_url
        row["branch"] = branch

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
    common_job_parameters: dict[str, Any],
) -> None:
    logger.info("Running OSS SemgrepSASTFinding cleanup job.")
    GraphJob.from_node_schema(
        OSSSemgrepSASTFindingSchema(),
        common_job_parameters,
    ).run(neo4j_session)


@timeit
def sync_oss_semgrep_sast_findings(
    neo4j_session: neo4j.Session,
    reader: ReportReader,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    End-to-end sync for OSS Semgrep SAST findings: get, transform, load, cleanup.
    """
    reports = get_semgrep_oss_reports(reader)
    if not reports:
        return

    all_findings: list[dict[str, Any]] = []
    for ref, document in reports:
        logger.info("Transforming OSS Semgrep SAST findings from %s", ref.uri)
        all_findings.extend(transform_oss_semgrep_sast_report(document))

    logger.info("Transformed %d total OSS Semgrep SAST findings.", len(all_findings))

    load_oss_semgrep_sast_findings(neo4j_session, all_findings, update_tag)

    common_job_parameters["DEPLOYMENT_ID"] = OSS_DEPLOYMENT_ID
    cleanup_oss_semgrep_sast_findings(neo4j_session, common_job_parameters)
