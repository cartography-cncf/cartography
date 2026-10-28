import logging
from typing import Any

import neo4j
from kubernetes.client.exceptions import ApiException

from cartography.client.core.tx import load_matchlinks
from cartography.graph.job import GraphJob
from cartography.intel.kubernetes.util import get_qualified_resource_name
from cartography.intel.kubernetes.util import K8sClient
from cartography.intel.kubernetes.util import list_cluster_custom_objects
from cartography.models.kubernetes.target_group_bindings import (
    ELBV2TargetGroupToKubernetesServiceMatchLink,
)
from cartography.util import timeit

logger = logging.getLogger(__name__)

ELBV2_API_GROUP = "elbv2.k8s.aws"


@timeit
def get_target_group_bindings(client: K8sClient) -> list[dict[str, Any]]:
    return list_cluster_custom_objects(
        client,
        group=ELBV2_API_GROUP,
        version="v1beta1",
        plural="targetgroupbindings",
    )


def transform_target_group_bindings(
    bindings: list[dict[str, Any]],
    cluster_name: str,
) -> list[dict[str, Any]]:
    transformed = []
    for binding in bindings:
        metadata = binding["metadata"]
        spec = binding.get("spec") or {}
        service_ref = spec.get("serviceRef") or {}
        # Bindings that name the target group instead of giving its ARN cannot be
        # matched against AWSELBV2TargetGroup.id, so they are skipped.
        if not spec.get("targetGroupARN") or not service_ref.get("name"):
            continue
        port = service_ref.get("port")
        transformed.append(
            {
                "target_group_arn": spec["targetGroupARN"],
                "cluster_name": cluster_name,
                "service_qualified_name": get_qualified_resource_name(
                    metadata["namespace"], service_ref["name"]
                ),
                "binding_name": metadata["name"],
                "target_type": spec.get("targetType"),
                "service_port": str(port) if port is not None else None,
            }
        )
    return transformed


def load_target_group_bindings(
    neo4j_session: neo4j.Session,
    bindings: list[dict[str, Any]],
    update_tag: int,
    cluster_id: str,
) -> None:
    load_matchlinks(
        neo4j_session,
        ELBV2TargetGroupToKubernetesServiceMatchLink(),
        bindings,
        lastupdated=update_tag,
        _sub_resource_label="KubernetesCluster",
        _sub_resource_id=cluster_id,
    )


def cleanup(session: neo4j.Session, common_job_parameters: dict[str, Any]) -> None:
    logger.debug("Running cleanup job for TargetGroupBinding relationships")
    GraphJob.from_matchlink(
        ELBV2TargetGroupToKubernetesServiceMatchLink(),
        "KubernetesCluster",
        common_job_parameters["CLUSTER_ID"],
        common_job_parameters["UPDATE_TAG"],
    ).run(session)


@timeit
def sync_target_group_bindings(
    neo4j_session: neo4j.Session,
    client: K8sClient,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    try:
        bindings = get_target_group_bindings(client)
    except ApiException as err:
        if err.status in (401, 403):
            # Cleaning up after a denied list would delete edges that may still be accurate.
            logger.warning(
                "Cartography lacks permission to list targetgroupbindings on cluster %s "
                "(status %s). Skipping TargetGroupBinding sync and preserving previously "
                "synced data. Grant `list targetgroupbindings` in the elbv2.k8s.aws group "
                "to enable ingestion.",
                client.name,
                err.status,
            )
            return
        raise
    load_target_group_bindings(
        neo4j_session,
        transform_target_group_bindings(bindings, client.name),
        update_tag=update_tag,
        cluster_id=common_job_parameters["CLUSTER_ID"],
    )
    cleanup(neo4j_session, common_job_parameters)
