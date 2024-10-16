import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j
import requests
from requests.exceptions import HTTPError
from requests.exceptions import ReadTimeout

from cartography.stats import get_stats_client
from cartography.util import timeit

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)
_PAGE_SIZE = 10000
_TIMEOUT = (60, 60)
_MAX_RETRIES = 3


@timeit
def get_dependencies(semgrep_app_token: str, deployment_id: str) -> List[Dict[str, Any]]:
    """
    Gets the list of dependencies associated with the passed Semgrep App token and deployment id.
    param: semgrep_app_token: The Semgrep App token to use for authentication.
    param: deployment_id: The Semgrep deployment ID to use for retrieving SCA deps.
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
            "ecosystem": ["gomod"],
            "repositoryId": [135415],
            # "transitivity": ["DIRECT"]
        },
    }

    logger.info(f"Retrieving Semgrep dependencies for deployment '{deployment_id}'.")
    while has_more:

        try:
            response = requests.post(deps_url, json=request_data, headers=headers, timeout=_TIMEOUT)
            response.raise_for_status()
            data = response.json()
        except (ReadTimeout, HTTPError) as e:
            logger.warning(f"Failed to retrieve Semgrep dependencies for page {page}. Retrying...")
            retries += 1
            if retries >= _MAX_RETRIES:
                raise e
            continue
        deps = data.get("dependencies", [])
        has_more = data.get("hasMore", False)
        # if page % 10 == 0:
        #     logger.info(f"Processed page {page} of Semgrep dependencies.")
        print(f"Processed page {page} of Semgrep dependencies.")
        all_deps.extend(deps)
        retries = 0
        page += 1
        request_data["cursor"] = data.get("cursor")

    logger.info(f"Retrieved {len(all_deps)} Semgrep dependencies in {page} pages.")
    print(f"Retrieved {len(all_deps)} Semgrep dependencies in {page} pages.")
    return all_deps


def transform_dependencies(raw_deps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Transforms the raw dependencies response from Semgrep API into a list of dicts
    that can be used to create the Dependency nodes.
    """

    """
    sample raw_dep:
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
        # Mandatory fields

        # repo_name = raw_dep["definedAt"]["url"].split("/")[4]
        repo_url = raw_dep["definedAt"]["url"].split("/blob/", 1)[0]  # TODO: less hacky way to do this?

        dep_name = raw_dep["package"]["name"]
        dep_version = raw_dep["package"]["versionSpecifier"]

        # this ID format matches the existing python deps
        # TODO: consider only using the name?
        dep_id = f"{dep_name}|{dep_version}"

        deps.append({
            # existing fields:
            "id": dep_id,
            "name": dep_name,
            # "specifier": spec, # TODO: consider hardcoding "=="?
            "version": dep_version,
            "repo_url": repo_url,

            # new fields:
            "defined_at": raw_dep["definedAt"]["url"],
            "ecosystem": raw_dep["ecosystem"],  # TODO: format this?
            "transitivity": raw_dep["transitivity"],  # TODO: format this?
        })

    print(f"Transformed {len(deps)} dependencies")
    return deps


@timeit
def load_dependencies(
    neo4j_session: neo4j.Session,
    dependencies: List[Dict],
    deployment_id: str,  # TODO
    update_tag: int,
) -> None:

    # for now, follow the query pattern used by cartography/intel/github/repos.py
    # TODO: consider using a schema to match existing semgrep functionality
    # TODO: support more than just Go dependencies
    query = """
    UNWIND $Dependencies AS dep
        MERGE (lib:GoLibrary:Dependency{id: dep.id})
        ON CREATE SET lib.firstseen = timestamp(),
        lib.name = dep.name
        SET lib.lastupdated = $UpdateTag,
        lib.version = dep.version

        WITH lib, dep
        MATCH (repo:GitHubRepository{id: dep.repo_url})
        MERGE (repo)-[r:REQUIRES]->(lib)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $UpdateTag,
        r.definedat = dep.defined_at,
        r.specifier = dep.specifier,
        r.transitivity = dep.transitivity
    """
    print(f"Loading {len(dependencies)} dependencies into the graph...")
    neo4j_session.run(
        query,
        Dependencies=dependencies,
        UpdateTag=update_tag,
    )
    print(f"Loaded {len(dependencies)} dependencies into the graph")
