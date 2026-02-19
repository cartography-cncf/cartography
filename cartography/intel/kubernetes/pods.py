import json
import logging
from typing import Any

import neo4j
from kubernetes.client.models import V1Container
from kubernetes.client.models import V1Pod

from cartography.client.core.tx import load
from cartography.client.core.tx import read_list_of_dicts_tx
from cartography.client.core.tx import run_write_query
from cartography.graph.job import GraphJob
from cartography.intel.container_arch import ARCH_SOURCE_CLUSTER_HINT
from cartography.intel.container_arch import ARCH_SOURCE_IMAGE_DIGEST_EXACT
from cartography.intel.container_arch import normalize_architecture_with_raw
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
    region: str | None = None,
) -> None:
    logger.info(f"Loading {len(containers)} kubernetes containers.")
    load(
        session,
        KubernetesContainerSchema(),
        containers,
        lastupdated=update_tag,
        CLUSTER_ID=cluster_id,
        CLUSTER_NAME=cluster_name,
        REGION=region,
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
def enrich_container_architecture(
    session: neo4j.Session,
    cluster_id: str,
    update_tag: int,
) -> None:
    # Cluster scoping is the authoritative boundary for Kubernetes runtime data,
    # so additional region filtering is unnecessary here.
    exact_rows = session.execute_read(
        read_list_of_dicts_tx,
        """
        MATCH (:KubernetesCluster {id: $CLUSTER_ID})-[:RESOURCE]->(c:KubernetesContainer {lastupdated: $UPDATE_TAG})
        MATCH (c)-[:HAS_IMAGE]->(img:Image)
        WHERE c.status_image_sha IS NOT NULL AND img.architecture IS NOT NULL
        RETURN c.id AS container_id, img.id AS image_id, img.architecture AS architecture_raw
        ORDER BY image_id ASC
        """,
        CLUSTER_ID=cluster_id,
        UPDATE_TAG=update_tag,
    )
    exact_updates_by_container = {}
    for row in exact_rows:
        container_id = row["container_id"]
        if container_id in exact_updates_by_container:
            continue
        normalized, _ = normalize_architecture_with_raw(row.get("architecture_raw"))
        if normalized == "unknown":
            continue
        exact_updates_by_container[container_id] = {
            "id": container_id,
            "architecture": row.get("architecture_raw"),
            "architecture_normalized": normalized,
            "architecture_source": ARCH_SOURCE_IMAGE_DIGEST_EXACT,
        }
    exact_updates = list(exact_updates_by_container.values())
    if exact_updates:
        run_write_query(
            session,
            """
            UNWIND $updates AS row
            MATCH (c:KubernetesContainer {id: row.id})
            SET c.architecture = row.architecture,
                c.architecture_normalized = row.architecture_normalized,
                c.architecture_source = row.architecture_source
            """,
            updates=exact_updates,
        )

    node_hint_rows = session.execute_read(
        read_list_of_dicts_tx,
        """
        MATCH (cluster:KubernetesCluster {id: $CLUSTER_ID})-[:RESOURCE]->(
            c:KubernetesContainer {lastupdated: $UPDATE_TAG}
        )
        WHERE c.architecture_normalized IS NULL OR c.architecture_normalized = 'unknown'
        MATCH (cluster)-[:RESOURCE]->(p:KubernetesPod)-[:CONTAINS]->(c)
        MATCH (p)-[:RUNS_ON]->(n:KubernetesNode)
        WHERE n.architecture IS NOT NULL
        RETURN c.id AS container_id, n.id AS node_id, n.architecture AS architecture_raw
        ORDER BY node_id ASC
        """,
        CLUSTER_ID=cluster_id,
        UPDATE_TAG=update_tag,
    )
    node_hint_updates_by_container = {}
    for row in node_hint_rows:
        container_id = row["container_id"]
        if container_id in node_hint_updates_by_container:
            continue
        normalized, _ = normalize_architecture_with_raw(row.get("architecture_raw"))
        if normalized == "unknown":
            continue
        node_hint_updates_by_container[container_id] = {
            "id": container_id,
            "architecture": row.get("architecture_raw"),
            "architecture_normalized": normalized,
            "architecture_source": ARCH_SOURCE_CLUSTER_HINT,
        }
    node_hint_updates = list(node_hint_updates_by_container.values())
    if node_hint_updates:
        run_write_query(
            session,
            """
            UNWIND $updates AS row
            MATCH (c:KubernetesContainer {id: row.id})
            SET c.architecture = row.architecture,
                c.architecture_normalized = row.architecture_normalized,
                c.architecture_source = row.architecture_source
            """,
            updates=node_hint_updates,
        )

    fallback_rows = session.execute_read(
        read_list_of_dicts_tx,
        """
        MATCH (cluster:KubernetesCluster {id: $CLUSTER_ID})-[:RESOURCE]->(
            c:KubernetesContainer {lastupdated: $UPDATE_TAG}
        )
        WHERE c.architecture_normalized IS NULL OR c.architecture_normalized = 'unknown'
        RETURN c.id AS container_id, cluster.platform AS platform
        """,
        CLUSTER_ID=cluster_id,
        UPDATE_TAG=update_tag,
    )
    cluster_hint_updates = []
    for row in fallback_rows:
        platform = row.get("platform")
        arch_hint = None
        if isinstance(platform, str) and "/" in platform:
            arch_hint = platform.split("/", 1)[1]
        elif isinstance(platform, str):
            arch_hint = platform
        normalized, _ = normalize_architecture_with_raw(arch_hint)
        if normalized == "unknown":
            continue
        cluster_hint_updates.append(
            {
                "id": row["container_id"],
                "architecture": arch_hint,
                "architecture_normalized": normalized,
                "architecture_source": ARCH_SOURCE_CLUSTER_HINT,
            }
        )
    if cluster_hint_updates:
        run_write_query(
            session,
            """
            UNWIND $updates AS row
            MATCH (c:KubernetesContainer {id: row.id})
            SET c.architecture = row.architecture,
                c.architecture_normalized = row.architecture_normalized,
                c.architecture_source = row.architecture_source
            """,
            updates=cluster_hint_updates,
        )


@timeit
def sync_pods(
    session: neo4j.Session,
    client: K8sClient,
    update_tag: int,
    common_job_parameters: dict[str, Any],
    region: str | None = None,
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
        region=region,
    )
    enrich_container_architecture(
        session=session,
        cluster_id=common_job_parameters["CLUSTER_ID"],
        update_tag=update_tag,
    )

    cleanup(session, common_job_parameters)
    return transformed_pods
