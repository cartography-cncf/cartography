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
from cartography.models.semgrep.dependencies import SemgrepNpmLibrarySchema
from cartography.stats import get_stats_client
from cartography.util import merge_module_sync_metadata
from cartography.util import timeit

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)
_PAGE_SIZE = 10000
_TIMEOUT = (60, 60)
_MAX_RETRIES = 3

# The keys in this dictionary must be in Semgrep's list of supported ecosystems, defined here:
# https://semgrep.dev/api/v1/docs/#tag/SupplyChainService/operation/semgrep_app.products.sca.handlers.dependency.list_dependencies_conexxion
ECOSYSTEM_TO_SCHEMA: Dict = {
    'gomod': SemgrepGoLibrarySchema,
    'npm': SemgrepNpmLibrarySchema,
}


def parse_and_validate_semgrep_ecosystems(ecosystems: str) -> List[str]:
    validated_ecosystems: List[str] = []
    for ecosystem in ecosystems.split(','):
        ecosystem = ecosystem.strip().lower()

        if ecosystem in ECOSYSTEM_TO_SCHEMA:
            validated_ecosystems.append(ecosystem)
        else:
            valid_ecosystems: str = ','.join(ECOSYSTEM_TO_SCHEMA.keys())
            raise ValueError(
                f'Error parsing `semgrep-dependency-ecosystems`. You specified "{ecosystems}". '
                f'Please check that your input is formatted as comma-separated values, e.g. "gomod,npm". '
                f'Full list of supported ecosystems: {valid_ecosystems}.',
            )
    return validated_ecosystems


@timeit
def get_dependencies(semgrep_app_token: str, deployment_id: str, ecosystem: str) -> List[Dict[str, Any]]:
    """
    Gets all dependencies for the given ecosystem within the given Semgrep deployment ID.
    param: semgrep_app_token: The Semgrep App token to use for authentication.
    param: deployment_id: The Semgrep deployment ID to use for retrieving dependencies.
    param: ecosystem: The ecosystem to import dependencies from, e.g. "gomod" or "npm".
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
            "ecosystem": [ecosystem],
        },
    }

    logger.info(f"Retrieving Semgrep {ecosystem} dependencies for deployment '{deployment_id}'.")
    while has_more:
        try:
            response = requests.post(deps_url, json=request_data, headers=headers, timeout=_TIMEOUT)
            response.raise_for_status()
            data = response.json()
        except (ReadTimeout, HTTPError):
            logger.warning(f"Failed to retrieve Semgrep {ecosystem} dependencies for page {page}. Retrying...")
            retries += 1
            if retries >= _MAX_RETRIES:
                raise
            continue
        deps = data.get("dependencies", [])
        has_more = data.get("hasMore", False)
        logger.info(f"Processed page {page} of Semgrep {ecosystem} dependencies.")
        all_deps.extend(deps)
        retries = 0
        page += 1
        request_data["cursor"] = data.get("cursor")

    logger.info(f"Retrieved {len(all_deps)} Semgrep {ecosystem} dependencies in {page} pages.")
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
    dependency_schema: Callable,
    common_job_parameters: Dict[str, Any],
) -> None:
    logger.info(f"Running Semgrep Dependencies cleanup job for {dependency_schema().label}.")
    GraphJob.from_node_schema(dependency_schema(), common_job_parameters).run(neo4j_session)


@timeit
def sync_dependencies(
    neo4j_session: neo4j.Session,
    semgrep_app_token: str,
    ecosystems_str: str,
    update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:

    deployment_id = common_job_parameters.get("DEPLOYMENT_ID")
    if not deployment_id:
        logger.warning(
            "Missing Semgrep deployment ID, ensure that sync_deployment() has been called. "
            "Skipping Semgrep dependencies sync job.",
        )
        return

    if not ecosystems_str:
        logger.warning(
            "Semgrep is not configured to import dependencies for any ecosystems, see docs to configure. "
            "Skipping Semgrep dependencies sync job.",
        )
        return

    # We don't expect an error here since we've already validated the input in cli.py
    ecosystems = parse_and_validate_semgrep_ecosystems(ecosystems_str)

    logger.info("Running Semgrep dependencies sync job.")

    for ecosystem in ecosystems:
        schema = ECOSYSTEM_TO_SCHEMA[ecosystem]
        raw_deps = get_dependencies(semgrep_app_token, deployment_id, ecosystem)
        deps = transform_dependencies(raw_deps)
        load_dependencies(neo4j_session, schema, deps, deployment_id, update_tag)
        cleanup(neo4j_session, schema, common_job_parameters)

    merge_module_sync_metadata(
        neo4j_session=neo4j_session,
        group_type='Semgrep',
        group_id=deployment_id,
        synced_type='SemgrepDependency',
        update_tag=update_tag,
        stat_handler=stat_handler,
    )
