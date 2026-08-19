from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.runpod.util import first_present
from cartography.intel.runpod.util import get_list
from cartography.intel.runpod.util import require_non_empty
from cartography.models.runpod.cluster import RunPodClusterSchema
from cartography.util import timeit


@timeit
def get(session: requests.Session, base_url: str) -> list[dict[str, Any]]:
    return get_list(session, base_url, "/clusters", ("clusters", "data"))


def _dict_or_empty(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _cluster_gpu_count(
    gpu: dict[str, Any],
    compute: dict[str, Any],
    pod_count: Any,
    cluster: dict[str, Any],
) -> Any:
    if "count" in gpu:
        return first_present(gpu, "count")
    if "gpuCount" in cluster:
        return cluster.get("gpuCount")
    if "gpuCountPerPod" in compute and isinstance(pod_count, int | float):
        return compute["gpuCountPerPod"] * pod_count
    return compute.get("gpuCountPerPod")


def _template_id(record: dict[str, Any]) -> Any:
    template = record.get("template")
    if isinstance(template, dict):
        return template.get("id")
    return record.get("templateId") or template


def transform(clusters: list[dict[str, Any]], account_id: str) -> list[dict[str, Any]]:
    transformed = []
    for cluster in clusters:
        compute = _dict_or_empty(cluster.get("compute"))
        gpu = _dict_or_empty(cluster.get("gpu"))
        pods = _dict_or_empty(cluster.get("pods"))
        by_status = _dict_or_empty(pods.get("byStatus"))
        primary_pod = _dict_or_empty(
            cluster.get("primaryPod") or cluster.get("primary")
        )
        pod_count = (
            first_present(pods, "count", "total")
            if any(key in pods for key in ("count", "total"))
            else cluster.get("podCount")
        )
        transformed.append(
            {
                "id": require_non_empty(cluster.get("id"), "cluster id"),
                "account_id": account_id,
                "name": cluster.get("name"),
                "status": cluster.get("status"),
                "data_center_id": cluster.get("dataCenterId"),
                "gpu_type_id": gpu.get("id")
                or compute.get("gpuTypeId")
                or cluster.get("gpuTypeId"),
                "gpu_count": _cluster_gpu_count(gpu, compute, pod_count, cluster),
                "pod_count": pod_count,
                "running_pod_count": (
                    first_present(pods, "running")
                    if "running" in pods
                    else by_status.get("RUNNING") or cluster.get("runningPodCount")
                ),
                "primary_pod_id": primary_pod.get("id")
                or primary_pod.get("podId")
                or cluster.get("primaryPodId"),
                "template_id": _template_id(cluster),
                "created_at": cluster.get("createdAt"),
            }
        )
    return transformed


@timeit
def load_clusters(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        RunPodClusterSchema(),
        data,
        lastupdated=update_tag,
        RUNPOD_ACCOUNT_ID=account_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(RunPodClusterSchema(), common_job_parameters).run(
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
    clusters = get(session, base_url)
    transformed = transform(clusters, account_id)
    load_clusters(neo4j_session, transformed, account_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)
