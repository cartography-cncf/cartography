from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.runpod.util import get_list
from cartography.intel.runpod.util import id_list
from cartography.intel.runpod.util import require_list_field
from cartography.intel.runpod.util import require_non_empty
from cartography.models.runpod.catalog import RunPodDataCenterSchema
from cartography.util import timeit


@timeit
def get(session: requests.Session, base_url: str) -> list[dict[str, Any]]:
    return get_list(session, base_url, "/catalog/datacenters", ("dataCenters", "data"))


def _gpu_type_ids(data_center: dict[str, Any]) -> list[str]:
    if "gpuTypes" in data_center:
        gpu_types = require_list_field(data_center, "gpuTypes")
    elif "gpuAvailability" in data_center:
        gpu_types = require_list_field(data_center, "gpuAvailability")
    else:
        gpu_types = []
    return id_list(gpu_types, "gpuTypes")


def transform(
    data_centers: list[dict[str, Any]], account_id: str
) -> list[dict[str, Any]]:
    transformed = []
    for data_center in data_centers:
        if "volumeTypes" in data_center:
            volume_types = require_list_field(data_center, "volumeTypes")
        elif "networkVolumeTypes" in data_center:
            volume_types = require_list_field(data_center, "networkVolumeTypes")
        else:
            volume_types = []
        if "globalNetworking" in data_center:
            global_networking = data_center["globalNetworking"]
        elif "globalNetwork" in data_center:
            global_networking = data_center["globalNetwork"]
        else:
            global_networking = None
        transformed.append(
            {
                "id": require_non_empty(data_center.get("id"), "data center id"),
                "account_id": account_id,
                "name": data_center.get("name"),
                "location": data_center.get("location") or data_center.get("region"),
                "country_code": data_center.get("countryCode"),
                "gpu_type_ids": _gpu_type_ids(data_center),
                "compliance": data_center.get("compliance") or [],
                "volume_types": volume_types,
                "global_networking": global_networking,
            }
        )
    return transformed


@timeit
def load_data_centers(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        RunPodDataCenterSchema(),
        data,
        lastupdated=update_tag,
        RUNPOD_ACCOUNT_ID=account_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(RunPodDataCenterSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    session: requests.Session,
    base_url: str,
    account_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    data_centers = get(session, base_url)
    transformed = transform(data_centers, account_id)
    load_data_centers(neo4j_session, transformed, account_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)
