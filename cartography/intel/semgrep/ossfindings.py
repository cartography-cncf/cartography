from __future__ import annotations

import hashlib
import logging
from typing import Any

import neo4j
import yaml

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.common.object_store import filter_report_refs
from cartography.intel.common.object_store import ObjectStoreError
from cartography.intel.common.object_store import read_json_report
from cartography.intel.common.object_store import read_text_report
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


@timeit
def get_semgrep_oss_reports(
    reader: ReportReader,
) -> tuple[list[tuple[ReportRef, dict[str, Any]]], bool]:
    """
    Read Semgrep OSS JSON reports from a provider-agnostic report source.

    Returns:
        A tuple of:
        - List of (ref, parsed_document) pairs for valid Semgrep OSS reports.
        - Whether at least one valid Semgrep OSS report was successfully read.
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
        return [], False

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

    return reports, bool(reports)


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


def _build_oss_sast_finding_id(
    check_id: str,
    path: str,
    start_line: str,
    start_col: str,
    end_line: str,
    end_col: str,
    repository_url: str,
) -> str:
    """
    Build a stable synthetic ID for OSS findings since Semgrep OSS CLI output
    does not include the Semgrep Cloud finding ID. Include repository URL
    so identical findings in different repositories do not collide.
    """
    raw_id = "|".join(
        [
            check_id,
            path,
            start_line,
            start_col,
            end_line,
            end_col,
            repository_url,
        ],
    )
    digest = hashlib.sha256(raw_id.encode("utf-8")).hexdigest()
    return f"semgrep-oss-sast-{digest}"


def _get_semgrep_oss_repo_context(reader: ReportReader) -> dict[str, str]:
    """
    Load repository metadata from the single YAML file stored alongside
    Semgrep OSS reports in the configured report source.
    """
    metadata_refs = filter_report_refs(reader.list_reports(), suffix=".yaml")
    metadata_refs.extend(filter_report_refs(reader.list_reports(), suffix=".yml"))

    if not metadata_refs:
        raise ValueError(
            "Semgrep OSS source must contain exactly one YAML metadata file with "
            "provider, owner, repo, url, and branch fields."
        )
    if len(metadata_refs) > 1:
        raise ValueError(
            "Semgrep OSS source must contain exactly one YAML metadata file; "
            f"found {len(metadata_refs)}: {[ref.uri for ref in metadata_refs]}"
        )

    metadata_ref = metadata_refs[0]
    try:
        metadata_document = yaml.safe_load(read_text_report(reader, metadata_ref))
    except yaml.YAMLError as exc:
        raise ValueError(
            f"Semgrep OSS metadata file must be valid YAML: {metadata_ref.uri}"
        ) from exc

    if not isinstance(metadata_document, dict):
        raise ValueError(
            "Semgrep OSS metadata file must contain a YAML mapping with provider, "
            f"owner, repo, url, and branch fields: {metadata_ref.uri}"
        )

    required_fields = ("provider", "owner", "repo", "url", "branch")
    missing_fields = [
        field for field in required_fields if not metadata_document.get(field)
    ]
    if missing_fields:
        raise ValueError(
            "Semgrep OSS metadata file is missing required fields "
            f"{missing_fields}: {metadata_ref.uri}"
        )

    return {
        "repositoryName": f"{metadata_document['owner']}/{metadata_document['repo']}",
        "repositoryUrl": str(metadata_document["url"]),
        "branch": str(metadata_document["branch"]),
    }


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

        row = dict(result)
        row["id"] = _build_oss_sast_finding_id(
            check_id,
            path,
            start_line,
            start_col,
            end_line,
            end_col,
            repo_context["repositoryUrl"],
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
    repo_context = _get_semgrep_oss_repo_context(reader)
    reports, processed_reports = get_semgrep_oss_reports(reader)

    all_findings: list[dict[str, Any]] = []

    for ref, document in reports:
        logger.info("Transforming OSS Semgrep SAST findings from %s", ref.uri)
        all_findings.extend(transform_oss_semgrep_sast_report(document, repo_context))

    if all_findings:
        logger.info(
            "Transformed %d total OSS Semgrep SAST findings.", len(all_findings)
        )
        load_oss_semgrep_sast_findings(neo4j_session, all_findings, update_tag)

    if processed_reports:
        common_job_parameters["DEPLOYMENT_ID"] = OSS_DEPLOYMENT_ID
        cleanup_oss_semgrep_sast_findings(neo4j_session, common_job_parameters)
    else:
        logger.warning(
            "Skipping OSS Semgrep cleanup because no valid reports were processed from %s.",
            reader.source_uri,
        )
