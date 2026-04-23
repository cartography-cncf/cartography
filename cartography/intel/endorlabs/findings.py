import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.endorlabs.util import paginated_get
from cartography.models.endorlabs.finding import EndorLabsFindingSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


def get(bearer_token: str, namespace: str) -> list[dict[str, Any]]:
    return paginated_get(bearer_token, namespace, "findings")


def _extract_cve_id(finding_metadata: dict[str, Any]) -> str | None:
    vuln = finding_metadata.get("vulnerability", {})
    if not vuln:
        return None
    for alias in vuln.get("aliases", []):
        if alias.startswith("CVE-"):
            return alias
    return None


def transform(raw_findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    findings = []
    for finding in raw_findings:
        meta = finding.get("meta", {})
        spec = finding.get("spec", {})
        finding_metadata = spec.get("finding_metadata", {})

        findings.append(
            {
                "uuid": finding["uuid"],
                "name": meta.get("name"),
                "namespace": finding.get("tenant_meta", {}).get("namespace"),
                "summary": spec.get("summary"),
                "level": spec.get("level"),
                "finding_categories": spec.get("finding_categories"),
                "finding_tags": spec.get("finding_tags"),
                "target_dependency_name": spec.get("target_dependency_name"),
                "target_dependency_version": spec.get("target_dependency_version"),
                "target_dependency_package_name": spec.get(
                    "target_dependency_package_name",
                ),
                "proposed_version": spec.get("proposed_version"),
                "remediation": spec.get("remediation"),
                "remediation_action": spec.get("remediation_action"),
                "project_uuid": spec.get("project_uuid"),
                "cve_id": _extract_cve_id(finding_metadata),
                "create_time": meta.get("create_time"),
            },
        )
    return findings


@timeit
def load_findings(
    neo4j_session: neo4j.Session,
    findings: list[dict[str, Any]],
    namespace_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        EndorLabsFindingSchema(),
        findings,
        lastupdated=update_tag,
        NAMESPACE_ID=namespace_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(
        EndorLabsFindingSchema(),
        common_job_parameters,
    ).run(neo4j_session)


@timeit
def sync_findings(
    neo4j_session: neo4j.Session,
    bearer_token: str,
    namespace: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> list[dict[str, Any]]:
    logger.info("Starting Endor Labs findings sync")
    raw_findings = get(bearer_token, namespace)
    findings = transform(raw_findings)
    load_findings(neo4j_session, findings, namespace, update_tag)
    cleanup(neo4j_session, common_job_parameters)
    logger.info(
        "Completed Endor Labs findings sync (%d findings)",
        len(findings),
    )
    return findings
