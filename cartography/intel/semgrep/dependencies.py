import logging
from typing import Any
from typing import Callable
from typing import Dict
from typing import List

import neo4j
import requests
from requests.exceptions import HTTPError
from requests.exceptions import ReadTimeout

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.semgrep.dependencies import SemgrepGoLibrarySchema
from cartography.models.semgrep.dependencies import SemgrepJavascriptLibrarySchema
from cartography.stats import get_stats_client
from cartography.util import merge_module_sync_metadata
from cartography.util import timeit

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)
_PAGE_SIZE = 10000
_TIMEOUT = (60, 60)
_MAX_RETRIES = 3


@timeit
def get_dependencies(semgrep_app_token: str, deployment_id: str, ecosystems: List[str]) -> List[Dict[str, Any]]:
    """
    Gets all dependencies for the given ecosystems within the given Semgrep deployment ID.
    param: semgrep_app_token: The Semgrep App token to use for authentication.
    param: deployment_id: The Semgrep deployment ID to use for retrieving dependencies.
    param: ecosystems: One or more ecosystems to import dependencies from, e.g. "gomod" or "pypi".
    The list of supported ecosystems is defined here:
    https://semgrep.dev/api/v1/docs/#tag/SupplyChainService/operation/semgrep_app.products.sca.handlers.dependency.list_dependencies_conexxion
    """
    all_deps = []
    deps_url = f"https://semgrep.dev/api/v1/deployments/{deployment_id}/dependencies"
    has_more = True
    page = 0
    retries = 0
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {semgrep_app_token}",
    }

    request_data: dict[str, Any] = {
        "pageSize": _PAGE_SIZE,
        "dependencyFilter": {
            "ecosystem": ecosystems,
        },
    }

    logger.info(f"Retrieving Semgrep dependencies for deployment '{deployment_id}'.")
    while has_more:
        try:
            response = requests.post(deps_url, json=request_data, headers=headers, timeout=_TIMEOUT)
            response.raise_for_status()
            data = response.json()
        except (ReadTimeout, HTTPError):
            logger.warning(f"Failed to retrieve Semgrep dependencies for page {page}. Retrying...")
            retries += 1
            if retries >= _MAX_RETRIES:
                raise
            continue
        deps = data.get("dependencies", [])
        has_more = data.get("hasMore", False)
        logger.info(f"Processed page {page} of Semgrep dependencies.")
        all_deps.extend(deps)
        retries = 0
        page += 1
        request_data["cursor"] = data.get("cursor")

    logger.info(f"Retrieved {len(all_deps)} Semgrep dependencies in {page} pages.")
    return all_deps


def transform_dependencies(raw_deps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Transforms the raw dependencies response from Semgrep API into a list of dicts
    that can be used to create the Dependency nodes.
    """

    """
    sample raw_dep as of November 2024:
    {
        "repositoryId": "123456",
        "definedAt": {
            "path": "go.mod",
            "startLine": "6",
            "endLine": "6",
            "url": "https://github.com/org/repo-name/blob/00000000000000000000000000000000/go.mod#L6",
            "committedAt": "1970-01-01T00:00:00Z",
            "startCol": "0",
            "endCol": "0"
        },
        "transitivity": "DIRECT",
        "package": {
            "name": "github.com/foo/bar",
            "versionSpecifier": "1.2.3"
        },
        "ecosystem": "gomod",
        "licenses": [],
        "pathToTransitivity": []
    },
    """
    deps = []
    for raw_dep in raw_deps:

        # We could call a different endpoint to get all repo IDs and store a mapping of repo ID to URL,
        # but it's much simpler to just extract the URL from the definedAt field.
        repo_url = raw_dep["definedAt"]["url"].split("/blob/", 1)[0]

        name = raw_dep["package"]["name"]
        version = raw_dep["package"]["versionSpecifier"]
        id = f"{name}|{version}"

        # As of November 2024, Semgrep does not import dependencies with version specifiers such as >, <, etc.
        # For now, hardcode the specifier to ==<version> to align with GitHub-sourced Python dependencies.
        # If Semgrep eventually supports version specifiers, update this line accordingly.
        specifier = f"=={version}"

        deps.append({
            # existing dependency properties:
            "id": id,
            "name": name,
            "specifier": specifier,
            "version": version,
            "repo_url": repo_url,

            # Semgrep-specific properties:
            "ecosystem": raw_dep["ecosystem"],
            "transitivity": raw_dep["transitivity"].lower(),
            "url": raw_dep["definedAt"]["url"],
        })

    return deps


@timeit
def load_dependencies(
    neo4j_session: neo4j.Session,
    dependency_schema: Callable,
    dependencies: List[Dict],
    deployment_id: str,
    update_tag: int,
) -> None:
    logger.info(f"Loading {len(dependencies)} {dependency_schema().label} objects into the graph.")
    load(
        neo4j_session,
        dependency_schema(),
        dependencies,
        lastupdated=update_tag,
        DEPLOYMENT_ID=deployment_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict[str, Any],
) -> None:
    logger.info("Running Semgrep Dependencies cleanup job.")
    GraphJob.from_node_schema(SemgrepGoLibrarySchema(), common_job_parameters).run(neo4j_session)
    GraphJob.from_node_schema(SemgrepJavascriptLibrarySchema(), common_job_parameters).run(neo4j_session)


@timeit
def sync_dependencies(
    neo4j_session: neo4j.Session,
    semgrep_app_token: str,
    update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:

    deployment_id = common_job_parameters.get("DEPLOYMENT_ID")
    if not deployment_id:
        logger.warning(
            "Missing Semgrep deployment ID, ensure that sync_deployment() has been called."
            "Skipping Semgrep dependencies sync job.",
        )
        return

    logger.info("Running Semgrep dependencies sync job.")

    # fetch and load dependencies for the Go ecosystem
    raw_go_deps = get_dependencies(semgrep_app_token, deployment_id, ecosystems=["gomod"])
    go_deps = transform_dependencies(raw_go_deps)
    load_dependencies(neo4j_session, SemgrepGoLibrarySchema, go_deps, deployment_id, update_tag)

    # fetch and load dependencies for the NPM ecosystem
    raw_js_deps = get_dependencies(semgrep_app_token, deployment_id, ecosystems=["npm"])
    js_deps = transform_dependencies(raw_js_deps)
    load_dependencies(neo4j_session, SemgrepJavascriptLibrarySchema, js_deps, deployment_id, update_tag)

    cleanup(neo4j_session, common_job_parameters)

    merge_module_sync_metadata(
        neo4j_session=neo4j_session,
        group_type='Semgrep',
        group_id=deployment_id,
        synced_type='SemgrepDependency',
        update_tag=update_tag,
        stat_handler=stat_handler,
    )
