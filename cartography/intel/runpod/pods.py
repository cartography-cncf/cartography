from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.runpod.util import first_not_none
from cartography.intel.runpod.util import first_present
from cartography.intel.runpod.util import get_list
from cartography.intel.runpod.util import require_non_empty
from cartography.models.runpod.pod import RunPodPodSchema
from cartography.util import timeit


def _port_summaries(ports: Any) -> list[str]:
    if not isinstance(ports, list):
        return []
    summaries = []
    for port in ports:
        if isinstance(port, dict):
            private_port = (
                port.get("privatePort") or port.get("private") or port.get("port")
            )
            public_port = port.get("publicPort") or port.get("public")
            protocol = port.get("protocol") or port.get("type")
            summary = ":".join(
                str(part)
                for part in (protocol, private_port, public_port)
                if part is not None
            )
            if summary:
                summaries.append(summary)
        elif port is not None:
            summaries.append(str(port))
    return summaries


def _persistent_mount(pod: dict[str, Any]) -> dict[str, Any]:
    mounts = pod.get("mounts") or {}
    persistent = mounts.get("persistent") if isinstance(mounts, dict) else {}
    return persistent if isinstance(persistent, dict) else {}


def _network_mounts(pod: dict[str, Any]) -> list[dict[str, Any]]:
    mounts = pod.get("mounts") or {}
    network_mounts = mounts.get("network") if isinstance(mounts, dict) else []
    if not isinstance(network_mounts, list):
        return []
    return [mount for mount in network_mounts if isinstance(mount, dict)]


def _network_volume_id(pod: dict[str, Any]) -> Any:
    for mount in _network_mounts(pod):
        volume_id = mount.get("volumeId")
        if volume_id:
            return volume_id
    network_volume = pod.get("networkVolume")
    if isinstance(network_volume, dict):
        return network_volume.get("id")
    return pod.get("networkVolumeId")


def _registry_id(pod: dict[str, Any]) -> Any:
    registry = pod.get("registry")
    if isinstance(registry, dict):
        return registry.get("id")
    return pod.get("containerRegistryId") or pod.get("registryId") or registry


def _template_id(record: dict[str, Any]) -> Any:
    template = record.get("template")
    if isinstance(template, dict):
        return template.get("id")
    return record.get("templateId") or template


def _cpu_value(pod: dict[str, Any], *keys: str) -> Any:
    cpu = pod.get("cpu")
    if isinstance(cpu, dict):
        value = first_not_none(cpu, *keys)
        if value is not None:
            return value
    return first_not_none(pod, *keys)


@timeit
def get(
    session: requests.Session,
    base_url: str,
) -> list[dict[str, Any]]:
    return get_list(
        session,
        base_url,
        "/pods",
        ("pods", "data"),
        params={"includeClusterPods": "true"},
    )


def transform(pods: list[dict[str, Any]], account_id: str) -> list[dict[str, Any]]:
    transformed = []
    for pod in pods:
        gpu = pod.get("gpu") or {}
        runtime = pod.get("runtime") or {}
        global_networking = pod.get("globalNetworking") or {}
        persistent_mount = _persistent_mount(pod)
        volume_in_gb = first_not_none(pod, "volumeInGb", "volume")
        if volume_in_gb is None:
            volume_in_gb = persistent_mount.get("size")
        transformed.append(
            {
                "id": require_non_empty(pod.get("id"), "pod id"),
                "account_id": account_id,
                "name": pod.get("name"),
                "status": pod.get("status"),
                "image_name": pod.get("imageName") or pod.get("image"),
                "machine_id": pod.get("machineId"),
                "data_center_id": pod.get("dataCenterId"),
                "gpu_type_id": gpu.get("id") or pod.get("gpuTypeId"),
                "gpu_count": (
                    first_present(gpu, "count")
                    if "count" in gpu
                    else pod.get("gpuCount")
                ),
                "vcpu_count": _cpu_value(pod, "vcpuCount", "vcpu"),
                "memory_in_gb": _cpu_value(pod, "memoryInGb", "memory"),
                "container_disk_in_gb": first_not_none(
                    pod, "containerDiskInGb", "containerDisk", "disk"
                ),
                "volume_in_gb": volume_in_gb,
                "volume_mount_path": pod.get("volumeMountPath")
                or persistent_mount.get("path"),
                "network_volume_id": _network_volume_id(pod),
                "template_id": _template_id(pod),
                "registry_id": _registry_id(pod),
                "global_networking_enabled": global_networking.get("enabled"),
                "public_ip": pod.get("publicIp") or runtime.get("publicIp"),
                "exposed_ports": _port_summaries(pod.get("ports")),
                "runtime_ports": _port_summaries(runtime.get("ports")),
                "created_at": pod.get("createdAt"),
                "started_at": pod.get("startedAt"),
            }
        )
    return transformed


@timeit
def load_pods(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        RunPodPodSchema(),
        data,
        lastupdated=update_tag,
        RUNPOD_ACCOUNT_ID=account_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(RunPodPodSchema(), common_job_parameters).run(
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
    pods = get(session, base_url)
    transformed = transform(pods, account_id)
    load_pods(neo4j_session, transformed, account_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)
