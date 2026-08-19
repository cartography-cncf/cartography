from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.runpod.pods import _port_summaries
from cartography.intel.runpod.util import first_present
from cartography.intel.runpod.util import first_present_list
from cartography.intel.runpod.util import get_list
from cartography.intel.runpod.util import id_list
from cartography.intel.runpod.util import require_non_empty
from cartography.models.runpod.serverless import RunPodServerlessEndpointSchema
from cartography.util import timeit


@timeit
def get(session: requests.Session, base_url: str) -> list[dict[str, Any]]:
    return get_list(session, base_url, "/serverless", ("endpoints", "data"))


def _gpu_type_ids(endpoint: dict[str, Any]) -> list[str]:
    gpu_ids = first_present_list(endpoint, "gpuTypeIds", "gpuIds")
    if gpu_ids:
        return id_list(gpu_ids, "gpuTypeIds")
    gpu = endpoint.get("gpu") or {}
    gpu_pools = gpu.get("pools") if isinstance(gpu, dict) else None
    if gpu_pools:
        return id_list(gpu_pools, "gpu.pools")
    gpu_type_id = endpoint.get("gpuTypeId")
    return [str(gpu_type_id)] if gpu_type_id else []


def _network_volume_ids(endpoint: dict[str, Any]) -> list[str]:
    return id_list(
        first_present_list(endpoint, "networkVolumeIds", "networkVolumes"),
        "networkVolumeIds",
    )


def transform(endpoints: list[dict[str, Any]], account_id: str) -> list[dict[str, Any]]:
    transformed = []
    for endpoint in endpoints:
        workers = endpoint.get("workers") or {}
        scaler = endpoint.get("scaler") or endpoint.get("scaling") or {}
        transformed.append(
            {
                "id": require_non_empty(endpoint.get("id"), "serverless endpoint id"),
                "account_id": account_id,
                "name": endpoint.get("name"),
                "endpoint_type": endpoint.get("type"),
                "image_name": endpoint.get("imageName") or endpoint.get("image"),
                "gpu_type_ids": _gpu_type_ids(endpoint),
                "data_center_ids": endpoint.get("dataCenterIds") or [],
                "network_volume_ids": _network_volume_ids(endpoint),
                "workers_min": (
                    first_present(workers, "min")
                    if "min" in workers
                    else endpoint.get("workersMin")
                ),
                "workers_max": (
                    first_present(workers, "max")
                    if "max" in workers
                    else endpoint.get("workersMax")
                ),
                "idle_timeout": (
                    first_present(workers, "idleTimeout")
                    if "idleTimeout" in workers
                    else endpoint.get("idleTimeout")
                ),
                "scaler_type": (
                    first_present(scaler, "type")
                    if "type" in scaler
                    else endpoint.get("scalerType")
                ),
                "scaler_value": (
                    first_present(scaler, "value", "queueDelay", "requestCount")
                    if any(
                        key in scaler for key in ("value", "queueDelay", "requestCount")
                    )
                    else endpoint.get("scalerValue")
                ),
                "timeout": endpoint.get("timeout"),
                "created_at": endpoint.get("createdAt"),
                "ports": _port_summaries(endpoint.get("ports")),
            }
        )
    return transformed


@timeit
def load_serverless(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        RunPodServerlessEndpointSchema(),
        data,
        lastupdated=update_tag,
        RUNPOD_ACCOUNT_ID=account_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(
        RunPodServerlessEndpointSchema(), common_job_parameters
    ).run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    session: requests.Session,
    base_url: str,
    account_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    endpoints = get(session, base_url)
    transformed = transform(endpoints, account_id)
    load_serverless(neo4j_session, transformed, account_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)
