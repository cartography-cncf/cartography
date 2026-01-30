import json
import logging
from typing import Any

import neo4j
from kubernetes.client.models import V1Container
from kubernetes.client.models import V1Pod

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.kubernetes.util import get_epoch
from cartography.intel.kubernetes.util import k8s_paginate
from cartography.intel.kubernetes.util import K8sClient
from cartography.models.kubernetes.containers import KubernetesContainerSchema
from cartography.models.kubernetes.pods import KubernetesPodSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


def _extract_pod_containers(pod: V1Pod) -> dict[str, Any]:
    pod_containers: list[V1Container] = pod.spec.containers
    containers = dict()
    for container in pod_containers:
        containers[container.name] = {
            "uid": f"{pod.metadata.uid}-{container.name}",
            "name": container.name,
            "image": container.image,
            "namespace": pod.metadata.namespace,
            "pod_id": pod.metadata.uid,
            "imagePullPolicy": container.image_pull_policy,
        }

        # Extract resource requests and limits
        if container.resources:
            if container.resources.requests:
                containers[container.name]["memory_request"] = (
                    container.resources.requests.get("memory")
                )
                containers[container.name]["cpu_request"] = (
                    container.resources.requests.get("cpu")
                )
            else:
                containers[container.name]["memory_request"] = None
                containers[container.name]["cpu_request"] = None

            if container.resources.limits:
                containers[container.name]["memory_limit"] = (
                    container.resources.limits.get("memory")
                )
                containers[container.name]["cpu_limit"] = (
                    container.resources.limits.get("cpu")
                )
            else:
                containers[container.name]["memory_limit"] = None
                containers[container.name]["cpu_limit"] = None
        else:
            containers[container.name]["memory_request"] = None
            containers[container.name]["cpu_request"] = None
            containers[container.name]["memory_limit"] = None
            containers[container.name]["cpu_limit"] = None

        if pod.status and pod.status.container_statuses:
            for status in pod.status.container_statuses:
                if status.name in containers:
                    _state = "waiting"
                    if status.state.running:
                        _state = "running"
                    elif status.state.terminated:
                        _state = "terminated"
                    try:
                        image_sha = status.image_id.split("@")[1]
                    except IndexError:
                        image_sha = None

                    containers[status.name]["status_image_id"] = status.image_id
                    containers[status.name]["status_image_sha"] = image_sha
                    containers[status.name]["status_ready"] = status.ready
                    containers[status.name]["status_started"] = status.started
                    containers[status.name]["status_state"] = _state
    return containers


def _extract_pod_secrets(pod: V1Pod, cluster_name: str) -> tuple[list[str], list[str]]:
    """
    Extract all secret names referenced by a pod.
    Returns a tuple of (volume_secret_ids, env_secret_ids).
    Each list contains unique secret IDs in the format: {namespace}/{secret_name}
    """
    volume_secrets = set()
    env_secrets = set()
    namespace = pod.metadata.namespace

    # 1. Secrets mounted as volumes
    if pod.spec.volumes:
        for volume in pod.spec.volumes:
            if volume.secret and volume.secret.secret_name:
                volume_secrets.add(
                    f"{cluster_name}/{namespace}/{volume.secret.secret_name}"
                )

    # 2. Secrets from env / envFrom
    containers_to_scan = []
    if pod.spec.containers:
        containers_to_scan.extend(pod.spec.containers)
    if getattr(pod.spec, "init_containers", None):
        containers_to_scan.extend(pod.spec.init_containers)
    if getattr(pod.spec, "ephemeral_containers", None):
        containers_to_scan.extend(pod.spec.ephemeral_containers)

    for container in containers_to_scan:
        # env[].valueFrom.secretKeyRef
        if container.env:
            for env in container.env:
                if (
                    env.value_from
                    and env.value_from.secret_key_ref
                    and env.value_from.secret_key_ref.name
                ):
                    env_secrets.add(
                        f"{cluster_name}/{namespace}/{env.value_from.secret_key_ref.name}"
                    )

        # envFrom[].secretRef
        if container.env_from:
            for env_from in container.env_from:
                if env_from.secret_ref and env_from.secret_ref.name:
                    env_secrets.add(
                        f"{cluster_name}/{namespace}/{env_from.secret_ref.name}"
                    )

    # Return unique secret IDs for each type
    return list(volume_secrets), list(env_secrets)


@timeit
def get_pods(client: K8sClient) -> list[V1Pod]:
    items = k8s_paginate(client.core.list_pod_for_all_namespaces)
    return items


def _format_pod_labels(labels: dict[str, str]) -> str:
    return json.dumps(labels)


def transform_pods(pods: list[V1Pod], cluster_name: str) -> list[dict[str, Any]]:
    transformed_pods = []

    for pod in pods:
        containers = _extract_pod_containers(pod)
        volume_secrets, env_secrets = _extract_pod_secrets(pod, cluster_name)
        transformed_pods.append(
            {
                "uid": pod.metadata.uid,
                "name": pod.metadata.name,
                "status_phase": pod.status.phase,
                "creation_timestamp": get_epoch(pod.metadata.creation_timestamp),
                "deletion_timestamp": get_epoch(pod.metadata.deletion_timestamp),
                "namespace": pod.metadata.namespace,
                "node": pod.spec.node_name,
                "labels": _format_pod_labels(pod.metadata.labels),
                "containers": list(containers.values()),
                "secret_volume_ids": volume_secrets,
                "secret_env_ids": env_secrets,
            },
        )
    return transformed_pods


@timeit
def load_pods(
    session: neo4j.Session,
    pods: list[dict[str, Any]],
    update_tag: int,
    cluster_id: str,
    cluster_name: str,
) -> None:
    logger.info(f"Loading {len(pods)} kubernetes pods.")
    load(
        session,
        KubernetesPodSchema(),
        pods,
        lastupdated=update_tag,
        CLUSTER_ID=cluster_id,
        CLUSTER_NAME=cluster_name,
    )


def transform_containers(pods: list[dict[str, Any]]) -> list[dict[str, Any]]:
    containers = []
    for pod in pods:
        containers.extend(pod.get("containers", []))
    return containers


@timeit
def load_containers(
    session: neo4j.Session,
    containers: list[dict[str, Any]],
    update_tag: int,
    cluster_id: str,
    cluster_name: str,
) -> None:
    logger.info(f"Loading {len(containers)} kubernetes containers.")
    load(
        session,
        KubernetesContainerSchema(),
        containers,
        lastupdated=update_tag,
        CLUSTER_ID=cluster_id,
        CLUSTER_NAME=cluster_name,
    )


@timeit
def cleanup(session: neo4j.Session, common_job_parameters: dict[str, Any]) -> None:
    logger.debug("Running cleanup job for KubernetesContainer")
    cleanup_job = GraphJob.from_node_schema(
        KubernetesContainerSchema(), common_job_parameters
    )
    cleanup_job.run(session)

    logger.debug("Running cleanup job for KubernetesPod")
    cleanup_job = GraphJob.from_node_schema(
        KubernetesPodSchema(), common_job_parameters
    )
    cleanup_job.run(session)


@timeit
def sync_pods(
    session: neo4j.Session,
    client: K8sClient,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> list[dict[str, Any]]:
    pods = get_pods(client)

    transformed_pods = transform_pods(pods, client.name)
    load_pods(
        session=session,
        pods=transformed_pods,
        update_tag=update_tag,
        cluster_id=common_job_parameters["CLUSTER_ID"],
        cluster_name=client.name,
    )

    transformed_containers = transform_containers(transformed_pods)
    load_containers(
        session=session,
        containers=transformed_containers,
        update_tag=update_tag,
        cluster_id=common_job_parameters["CLUSTER_ID"],
        cluster_name=client.name,
    )

    cleanup(session, common_job_parameters)
    return transformed_pods
