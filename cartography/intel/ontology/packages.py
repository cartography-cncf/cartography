import logging
from typing import Any

import neo4j

from cartography.analysis.ontology.analysis import PACKAGE_LINKING_JOBS
from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.ontology.utils import get_source_nodes_from_graph
from cartography.intel.trivy.util import make_normalized_package_name_id
from cartography.intel.trivy.util import parse_purl
from cartography.models.ontology.package import PackageSchema
from cartography.models.ontology.package_version import PackageVersionSchema
from cartography.util import run_typed_analysis_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    data = get_source_nodes_from_graph(neo4j_session, [], "packages")
    load_package_versions(
        neo4j_session,
        data,
        update_tag,
    )
    load_packages(
        neo4j_session,
        transform_packages(data),
        update_tag,
    )
    for job in PACKAGE_LINKING_JOBS:
        run_typed_analysis_job(job, neo4j_session, common_job_parameters)
    cleanup(neo4j_session, common_job_parameters)


@timeit
def load_package_versions(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        PackageVersionSchema(),
        data,
        lastupdated=update_tag,
    )


def transform_packages(data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Group PackageVersion rows into version-independent Package nodes.

    Rows whose components do not yield a versionless key (no name, or no type to
    normalize the name with) are skipped, mirroring how rows without a normalized_id
    never reach the PackageVersion node.

    Only rows carrying a PURL expose a namespace, so a non-None namespace found on any
    row of the group wins. This keeps the result independent of the order in which the
    source rows come back from the graph, the same way get_source_nodes_from_graph
    prefers non-None values when merging rows.
    """
    packages: dict[str, dict[str, Any]] = {}
    for row in data:
        package_id = make_normalized_package_name_id(
            purl=row.get("purl"),
            name=row.get("name"),
            pkg_type=row.get("type"),
        )
        if package_id is None:
            logger.debug(
                "Skipping package version '%s': no versionless key could be derived.",
                row.get("normalized_id"),
            )
            continue
        pkg_type, _, name = package_id.partition("|")
        package = packages.setdefault(
            package_id,
            {
                "id": package_id,
                "name": name,
                "namespace": None,
                "type": pkg_type,
                "version_ids": set(),
            },
        )
        if package["namespace"] is None:
            parsed_purl = parse_purl(row.get("purl"))
            if parsed_purl:
                package["namespace"] = parsed_purl["namespace"]
        package["version_ids"].add(row["normalized_id"])

    result = []
    for package in packages.values():
        package["version_ids"] = sorted(package["version_ids"])
        result.append(package)
    return result


@timeit
def load_packages(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        PackageSchema(),
        data,
        lastupdated=update_tag,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(PackageVersionSchema(), common_job_parameters).run(
        neo4j_session,
    )
    GraphJob.from_node_schema(PackageSchema(), common_job_parameters).run(
        neo4j_session,
    )
