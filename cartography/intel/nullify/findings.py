import logging
from collections.abc import Callable
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.nullify.util import paginate
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.nullify.container_finding import NullifyContainerFindingSchema
from cartography.models.nullify.cspm_finding import NullifyCSPMFindingSchema
from cartography.models.nullify.dependency_finding import NullifyDependencyFindingSchema
from cartography.models.nullify.sast_finding import NullifySASTFindingSchema
from cartography.models.nullify.secret_finding import NullifySecretFindingSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


def transform_container_findings(
    findings: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Flatten each container finding's nested ``imageMetadata`` object onto the finding
    dict so the affected image is queryable on the node. Container findings are keyed on
    a container image, not a package, so they carry ``imageMetadata`` rather than the
    ``package``/``version`` fields the dependency findings use.
    """
    for finding in findings:
        image = finding.get("imageMetadata") or {}
        finding["_image_reference"] = image.get("fullReference")
        finding["_image_short_name"] = image.get("shortName")
        finding["_image_tag"] = image.get("tag")
        finding["_image_digest"] = image.get("digest")
        finding["_image_registry_domain"] = image.get("registryDomain")
    return findings


def _sync_finding_type(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    base_url: str,
    path: str,
    schema: CartographyNodeSchema,
    tenant_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
    transform: Callable[[list[dict[str, Any]]], list[dict[str, Any]]] | None = None,
) -> list[dict[str, Any]]:
    """
    Fetch, load, and clean up one finding type. All finding endpoints share the same
    cursor-paginated ``findings`` envelope, so a single helper covers every type; a
    per-type ``transform`` reshapes the payload before load when needed.
    """
    findings = paginate(api_session, f"{base_url}{path}", "findings")
    if transform is not None:
        findings = transform(findings)
    load(
        neo4j_session,
        schema,
        findings,
        lastupdated=update_tag,
        TENANT_ID=tenant_id,
    )
    GraphJob.from_node_schema(schema, common_job_parameters).run(neo4j_session)
    return findings


@timeit
def sync_sast_findings(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    base_url: str,
    tenant_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> list[dict[str, Any]]:
    return _sync_finding_type(
        neo4j_session,
        api_session,
        base_url,
        "/sast/findings",
        NullifySASTFindingSchema(),
        tenant_id,
        update_tag,
        common_job_parameters,
    )


@timeit
def sync_dependency_findings(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    base_url: str,
    tenant_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> list[dict[str, Any]]:
    return _sync_finding_type(
        neo4j_session,
        api_session,
        base_url,
        "/sca/dependencies/findings",
        NullifyDependencyFindingSchema(),
        tenant_id,
        update_tag,
        common_job_parameters,
    )


@timeit
def sync_container_findings(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    base_url: str,
    tenant_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> list[dict[str, Any]]:
    return _sync_finding_type(
        neo4j_session,
        api_session,
        base_url,
        "/sca/containers/findings",
        NullifyContainerFindingSchema(),
        tenant_id,
        update_tag,
        common_job_parameters,
        transform=transform_container_findings,
    )


@timeit
def sync_secret_findings(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    base_url: str,
    tenant_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> list[dict[str, Any]]:
    return _sync_finding_type(
        neo4j_session,
        api_session,
        base_url,
        "/secrets/findings",
        NullifySecretFindingSchema(),
        tenant_id,
        update_tag,
        common_job_parameters,
    )


@timeit
def sync_cspm_findings(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    base_url: str,
    tenant_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> list[dict[str, Any]]:
    return _sync_finding_type(
        neo4j_session,
        api_session,
        base_url,
        "/cspm/findings",
        NullifyCSPMFindingSchema(),
        tenant_id,
        update_tag,
        common_job_parameters,
    )
