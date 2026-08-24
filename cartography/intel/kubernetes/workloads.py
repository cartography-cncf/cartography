import json
import logging
from typing import Any

import neo4j
from kubernetes.client.exceptions import ApiException
from kubernetes.client.models import V1CronJob
from kubernetes.client.models import V1DaemonSet
from kubernetes.client.models import V1Deployment
from kubernetes.client.models import V1Job
from kubernetes.client.models import V1ReplicaSet
from kubernetes.client.models import V1StatefulSet

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.kubernetes.util import get_controller_owner_reference
from cartography.intel.kubernetes.util import get_epoch
from cartography.intel.kubernetes.util import k8s_paginate
from cartography.intel.kubernetes.util import K8sClient
from cartography.models.kubernetes.cronjobs import KubernetesCronJobSchema
from cartography.models.kubernetes.daemonsets import KubernetesDaemonSetSchema
from cartography.models.kubernetes.deployments import KubernetesDeploymentSchema
from cartography.models.kubernetes.jobs import KubernetesJobSchema
from cartography.models.kubernetes.replicasets import KubernetesReplicaSetSchema
from cartography.models.kubernetes.statefulsets import KubernetesStatefulSetSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


def _format_labels(labels: dict[str, str] | None) -> str:
    return json.dumps(labels or {})


# The workload list calls re-raise on ANY error (raise_on_error) so sync_workloads
# never mistakes a partial/empty result for a complete one: a missing controller
# would otherwise leave pods with unmatched WORKLOAD_PARENT edges and trigger a
# destructive cleanup. sync_workloads turns any failure into a skip (return None).
@timeit
def get_deployments(client: K8sClient) -> list[V1Deployment]:
    return k8s_paginate(
        client.apps.list_deployment_for_all_namespaces, raise_on_error=True
    )


@timeit
def get_replicasets(client: K8sClient) -> list[V1ReplicaSet]:
    return k8s_paginate(
        client.apps.list_replica_set_for_all_namespaces, raise_on_error=True
    )


@timeit
def get_statefulsets(client: K8sClient) -> list[V1StatefulSet]:
    return k8s_paginate(
        client.apps.list_stateful_set_for_all_namespaces, raise_on_error=True
    )


@timeit
def get_daemonsets(client: K8sClient) -> list[V1DaemonSet]:
    return k8s_paginate(
        client.apps.list_daemon_set_for_all_namespaces, raise_on_error=True
    )


@timeit
def get_jobs(client: K8sClient) -> list[V1Job]:
    return k8s_paginate(client.batch.list_job_for_all_namespaces, raise_on_error=True)


@timeit
def get_cronjobs(client: K8sClient) -> list[V1CronJob]:
    return k8s_paginate(
        client.batch.list_cron_job_for_all_namespaces, raise_on_error=True
    )


def transform_deployments(deployments: list[V1Deployment]) -> list[dict[str, Any]]:
    out = []
    for deployment in deployments:
        status = deployment.status
        out.append(
            {
                "uid": deployment.metadata.uid,
                "name": deployment.metadata.name,
                "namespace": deployment.metadata.namespace,
                "creation_timestamp": get_epoch(deployment.metadata.creation_timestamp),
                "deletion_timestamp": get_epoch(deployment.metadata.deletion_timestamp),
                "replicas": deployment.spec.replicas if deployment.spec else None,
                "ready_replicas": getattr(status, "ready_replicas", None),
                "available_replicas": getattr(status, "available_replicas", None),
                "labels": _format_labels(deployment.metadata.labels),
            }
        )
    return out


def transform_statefulsets(statefulsets: list[V1StatefulSet]) -> list[dict[str, Any]]:
    out = []
    for statefulset in statefulsets:
        spec = statefulset.spec
        status = statefulset.status
        out.append(
            {
                "uid": statefulset.metadata.uid,
                "name": statefulset.metadata.name,
                "namespace": statefulset.metadata.namespace,
                "creation_timestamp": get_epoch(
                    statefulset.metadata.creation_timestamp
                ),
                "deletion_timestamp": get_epoch(
                    statefulset.metadata.deletion_timestamp
                ),
                "replicas": getattr(spec, "replicas", None),
                "ready_replicas": getattr(status, "ready_replicas", None),
                "service_name": getattr(spec, "service_name", None),
                "labels": _format_labels(statefulset.metadata.labels),
            }
        )
    return out


def transform_daemonsets(daemonsets: list[V1DaemonSet]) -> list[dict[str, Any]]:
    out = []
    for daemonset in daemonsets:
        status = daemonset.status
        out.append(
            {
                "uid": daemonset.metadata.uid,
                "name": daemonset.metadata.name,
                "namespace": daemonset.metadata.namespace,
                "creation_timestamp": get_epoch(daemonset.metadata.creation_timestamp),
                "deletion_timestamp": get_epoch(daemonset.metadata.deletion_timestamp),
                "desired_number_scheduled": getattr(
                    status, "desired_number_scheduled", None
                ),
                "number_ready": getattr(status, "number_ready", None),
                "labels": _format_labels(daemonset.metadata.labels),
            }
        )
    return out


def transform_cronjobs(cronjobs: list[V1CronJob]) -> list[dict[str, Any]]:
    out = []
    for cronjob in cronjobs:
        spec = cronjob.spec
        out.append(
            {
                "uid": cronjob.metadata.uid,
                "name": cronjob.metadata.name,
                "namespace": cronjob.metadata.namespace,
                "creation_timestamp": get_epoch(cronjob.metadata.creation_timestamp),
                "deletion_timestamp": get_epoch(cronjob.metadata.deletion_timestamp),
                "schedule": getattr(spec, "schedule", None),
                "suspend": getattr(spec, "suspend", None),
                "labels": _format_labels(cronjob.metadata.labels),
            }
        )
    return out


def transform_replicasets(
    replicasets: list[V1ReplicaSet],
) -> tuple[list[dict[str, Any]], dict[str, str]]:
    """Transform ReplicaSets and build the ``replicaset_uid -> deployment_uid`` map.

    The map lets the pod transform collapse ``Pod -> ReplicaSet -> Deployment``
    into a single ``Pod -[:WORKLOAD_PARENT]-> Deployment`` edge.
    """
    out = []
    replicaset_to_deployment: dict[str, str] = {}
    for replicaset in replicasets:
        status = replicaset.status
        owner = get_controller_owner_reference(replicaset.metadata)
        owner_deployment_id = None
        if owner and owner[0] == "Deployment":
            owner_deployment_id = owner[1]
            replicaset_to_deployment[replicaset.metadata.uid] = owner_deployment_id
        out.append(
            {
                "uid": replicaset.metadata.uid,
                "name": replicaset.metadata.name,
                "namespace": replicaset.metadata.namespace,
                "creation_timestamp": get_epoch(replicaset.metadata.creation_timestamp),
                "deletion_timestamp": get_epoch(replicaset.metadata.deletion_timestamp),
                "replicas": replicaset.spec.replicas if replicaset.spec else None,
                "ready_replicas": getattr(status, "ready_replicas", None),
                "labels": _format_labels(replicaset.metadata.labels),
                "_owner_deployment_id": owner_deployment_id,
            }
        )
    return out, replicaset_to_deployment


def transform_jobs(jobs: list[V1Job]) -> list[dict[str, Any]]:
    out = []
    for job in jobs:
        spec = job.spec
        status = job.status
        owner = get_controller_owner_reference(job.metadata)
        cronjob_id = owner[1] if owner and owner[0] == "CronJob" else None
        out.append(
            {
                "uid": job.metadata.uid,
                "name": job.metadata.name,
                "namespace": job.metadata.namespace,
                "creation_timestamp": get_epoch(job.metadata.creation_timestamp),
                "deletion_timestamp": get_epoch(job.metadata.deletion_timestamp),
                "completions": getattr(spec, "completions", None),
                "parallelism": getattr(spec, "parallelism", None),
                "active": getattr(status, "active", None),
                "succeeded": getattr(status, "succeeded", None),
                "failed": getattr(status, "failed", None),
                "labels": _format_labels(job.metadata.labels),
                "_workload_parent_cronjob_id": cronjob_id,
                # Standalone Jobs (no owning CronJob) anchor to their namespace.
                "_workload_parent_namespace_name": (
                    None if cronjob_id else job.metadata.namespace
                ),
            }
        )
    return out


@timeit
def load_workloads(
    session: neo4j.Session,
    deployments: list[dict[str, Any]],
    statefulsets: list[dict[str, Any]],
    daemonsets: list[dict[str, Any]],
    cronjobs: list[dict[str, Any]],
    replicasets: list[dict[str, Any]],
    jobs: list[dict[str, Any]],
    update_tag: int,
    cluster_id: str,
    cluster_name: str,
) -> None:
    # Load top-level controllers first so the child edges (ReplicaSet ->
    # Deployment, Job -> CronJob) can match their targets.
    for schema, data in (
        (KubernetesDeploymentSchema(), deployments),
        (KubernetesStatefulSetSchema(), statefulsets),
        (KubernetesDaemonSetSchema(), daemonsets),
        (KubernetesCronJobSchema(), cronjobs),
        (KubernetesReplicaSetSchema(), replicasets),
        (KubernetesJobSchema(), jobs),
    ):
        load(
            session,
            schema,
            data,
            lastupdated=update_tag,
            CLUSTER_ID=cluster_id,
            CLUSTER_NAME=cluster_name,
        )


@timeit
def cleanup(session: neo4j.Session, common_job_parameters: dict[str, Any]) -> None:
    for schema in (
        KubernetesJobSchema(),
        KubernetesReplicaSetSchema(),
        KubernetesCronJobSchema(),
        KubernetesDaemonSetSchema(),
        KubernetesStatefulSetSchema(),
        KubernetesDeploymentSchema(),
    ):
        logger.debug("Running cleanup job for %s", schema.label)
        GraphJob.from_node_schema(schema, common_job_parameters).run(session)


@timeit
def sync_workloads(
    session: neo4j.Session,
    client: K8sClient,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> dict[str, str] | None:
    """Sync Kubernetes workload controllers and return the ReplicaSet -> Deployment map.

    The map is consumed by the pod sync so a pod owned by a ReplicaSet resolves
    its WORKLOAD_PARENT straight to the owning Deployment (the ReplicaSet is
    collapsed out of the ontology chain). Returns ``None`` (not ``{}``) whenever
    the workload sync could not complete every controller list, so the pod sync
    can tell "controllers ingested, none map to a Deployment" apart from
    "controllers not fully ingested" and fall back to a namespace WORKLOAD_PARENT
    for every controller-owned pod (avoiding unmatched edges to missing nodes).

    Any list failure skips load and cleanup so existing nodes are preserved. The
    apps/batch list verbs are required (see the Kubernetes config docs); the
    401/403 grace period below is a temporary migration aid, not an opt-out.
    """
    try:
        deployments = transform_deployments(get_deployments(client))
        statefulsets = transform_statefulsets(get_statefulsets(client))
        daemonsets = transform_daemonsets(get_daemonsets(client))
        cronjobs = transform_cronjobs(get_cronjobs(client))
        replicasets, replicaset_to_deployment = transform_replicasets(
            get_replicasets(client)
        )
        jobs = transform_jobs(get_jobs(client))
    except ApiException as e:
        if e.status in (401, 403):
            # DEPRECATED: transitional grace period. The apps/batch `list` verbs
            # are required; until v1.0.0 a missing verb is tolerated here (warn +
            # skip load and cleanup) so existing deployments are not broken or
            # wiped on upgrade. This branch will be removed in v1.0.0, after which
            # a 401/403 will fail loudly like any other required sync.
            logger.warning(
                "Cartography lacks permission to list workload controllers on "
                "cluster %s (status %s). Skipping workload sync and preserving "
                "previously synced Deployment/StatefulSet/DaemonSet/ReplicaSet/"
                "Job/CronJob nodes for now. Grant `list` on apps/v1 (deployments, "
                "replicasets, statefulsets, daemonsets) and batch/v1 (jobs, "
                "cronjobs): this is required and will become a hard failure in "
                "v1.0.0.",
                client.name,
                e.status,
            )
            return None
        # Any other API error (transient 5xx, timeout surfaced as ApiException,
        # etc.): skip load + cleanup and signal unavailability. Loading a partial
        # result would delete controllers absent from it and leave pods pointing
        # at controller ids that were never ingested.
        logger.error(
            "Kubernetes API error listing workload controllers on cluster %s "
            "(status %s). Skipping workload sync for this run and preserving "
            "previously synced nodes; pods fall back to a namespace WORKLOAD_PARENT.",
            client.name,
            e.status,
        )
        return None

    load_workloads(
        session=session,
        deployments=deployments,
        statefulsets=statefulsets,
        daemonsets=daemonsets,
        cronjobs=cronjobs,
        replicasets=replicasets,
        jobs=jobs,
        update_tag=update_tag,
        cluster_id=common_job_parameters["CLUSTER_ID"],
        cluster_name=client.name,
    )
    cleanup(session, common_job_parameters)
    return replicaset_to_deployment
