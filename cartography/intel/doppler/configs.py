from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.doppler.util import paginated_get
from cartography.models.doppler.config import DopplerConfigSchema
from cartography.util import timeit


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    project_slugs: list[str],
    common_job_parameters: dict[str, Any],
) -> list[dict[str, Any]]:
    """Returns a list of {"project", "config", "config_id"} dicts for the per-config
    fan-out syncs (secrets, service tokens, trusted IPs)."""
    configs = get(api_session, common_job_parameters["BASE_URL"], project_slugs)
    load_configs(
        neo4j_session,
        configs,
        common_job_parameters["WORKPLACE_ID"],
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)
    return [
        {"project": c["project"], "config": c["name"], "config_id": c["id"]}
        for c in configs
    ]


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
    project_slugs: list[str],
) -> list[dict[str, Any]]:
    configs: list[dict[str, Any]] = []
    for project in project_slugs:
        for config in paginated_get(
            api_session,
            f"{base_url}/configs",
            "configs",
            params={"project": project},
        ):
            name = config["name"]
            environment = config.get("environment")
            config["project"] = project
            config["id"] = f"{project}/{name}"
            config["environment_id"] = f"{project}/{environment}"
            configs.append(config)
    return configs


@timeit
def load_configs(
    neo4j_session: neo4j.Session,
    configs: list[dict[str, Any]],
    workplace_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        DopplerConfigSchema(),
        configs,
        lastupdated=update_tag,
        WORKPLACE_ID=workplace_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(DopplerConfigSchema(), common_job_parameters).run(
        neo4j_session
    )
