import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.trivy.util import make_normalized_package_id
from cartography.models.endorlabs.package_version import EndorLabsPackageVersionSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)
_TIMEOUT = (60, 60)
_BASE_URL = "https://api.endorlabs.com"
_PAGE_SIZE = 100


@timeit
def get(bearer_token: str, namespace: str) -> list[dict[str, Any]]:
    all_package_versions: list[dict[str, Any]] = []
    page_token: str | None = None
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/jsoncompact",
    }

    while True:
        params: dict[str, Any] = {
            "list_parameters.page_size": _PAGE_SIZE,
        }
        if page_token:
            params["list_parameters.page_token"] = page_token

        response = requests.get(
            f"{_BASE_URL}/v1/namespaces/{namespace}/package-versions",
            headers=headers,
            params=params,
            timeout=_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()

        objects = data.get("list", {}).get("objects", [])
        all_package_versions.extend(objects)

        next_token = data.get("list", {}).get("response", {}).get("next_page_token")
        if not next_token or not objects:
            break
        page_token = next_token

    logger.debug("Fetched %d Endor Labs package versions", len(all_package_versions))
    return all_package_versions


_ECOSYSTEM_TO_PURL_TYPE: dict[str, str] = {
    "ECOSYSTEM_NPM": "npm",
    "ECOSYSTEM_PYPI": "pypi",
    "ECOSYSTEM_MAVEN": "maven",
    "ECOSYSTEM_GO": "golang",
    "ECOSYSTEM_RUBYGEMS": "gem",
    "ECOSYSTEM_NUGET": "nuget",
    "ECOSYSTEM_CRATES_IO": "cargo",
    "ECOSYSTEM_PACKAGIST": "composer",
    "ECOSYSTEM_PUB": "pub",
    "ECOSYSTEM_COCOAPODS": "cocoapods",
    "ECOSYSTEM_SWIFT": "swift",
    "ECOSYSTEM_CARGO": "cargo",
    "ECOSYSTEM_HACKAGE": "hackage",
    "ECOSYSTEM_HEX": "hex",
}


def _parse_package_name(name: str) -> tuple[str | None, str | None]:
    """Parse 'ecosystem://package@version' into (package, version)."""
    if "://" in name:
        name = name.split("://", 1)[1]
    if "@" in name:
        parts = name.rsplit("@", 1)
        return parts[0], parts[1]
    return name, None


def _make_purl(
    ecosystem: str | None,
    package_name: str | None,
    version: str | None,
) -> str | None:
    if not package_name or not version:
        return None
    purl_type = _ECOSYSTEM_TO_PURL_TYPE.get(ecosystem or "")
    if not purl_type:
        return None
    return f"pkg:{purl_type}/{package_name}@{version}"


def transform(
    raw_package_versions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    package_versions = []
    for pv in raw_package_versions:
        meta = pv.get("meta", {})
        spec = pv.get("spec", {})
        pv_name = meta.get("name")
        package_name, version = _parse_package_name(pv_name or "")
        ecosystem = spec.get("ecosystem")
        purl = _make_purl(ecosystem, package_name, version)
        normalized_id = make_normalized_package_id(purl=purl)

        package_versions.append(
            {
                "uuid": pv["uuid"],
                "name": pv_name,
                "namespace": pv.get("tenant_meta", {}).get("namespace"),
                "ecosystem": ecosystem,
                "package_name": package_name,
                "version": version,
                "purl": purl,
                "normalized_id": normalized_id,
                "release_timestamp": spec.get("release_timestamp"),
                "call_graph_available": spec.get("call_graph_available"),
                "project_uuid": spec.get("project_uuid"),
            },
        )
    return package_versions


@timeit
def load_package_versions(
    neo4j_session: neo4j.Session,
    package_versions: list[dict[str, Any]],
    namespace_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        EndorLabsPackageVersionSchema(),
        package_versions,
        lastupdated=update_tag,
        NAMESPACE_ID=namespace_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(
        EndorLabsPackageVersionSchema(),
        common_job_parameters,
    ).run(neo4j_session)


@timeit
def sync_package_versions(
    neo4j_session: neo4j.Session,
    bearer_token: str,
    namespace: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> list[dict[str, Any]]:
    logger.info("Starting Endor Labs package versions sync")
    raw_package_versions = get(bearer_token, namespace)
    package_versions = transform(raw_package_versions)
    load_package_versions(neo4j_session, package_versions, namespace, update_tag)
    cleanup(neo4j_session, common_job_parameters)
    logger.info(
        "Completed Endor Labs package versions sync (%d package versions)",
        len(package_versions),
    )
    return package_versions
