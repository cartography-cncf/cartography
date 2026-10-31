import logging
from typing import Any

import neo4j
import scaleway
from scaleway.autoscaling.v1alpha1 import AutoscalingV1Alpha1API
from scaleway.autoscaling.v1alpha1 import InstanceGroup
from scaleway.autoscaling.v1alpha1 import InstancePolicy
from scaleway.autoscaling.v1alpha1 import InstanceTemplate
from scaleway_core.api import ScalewayException

from cartography.client.core.tx import load
from cartography.client.core.tx import load_matchlinks
from cartography.graph.job import GraphJob
from cartography.intel.scaleway.utils import list_all_zones
from cartography.intel.scaleway.utils import scaleway_obj_to_dict
from cartography.models.scaleway.instance.autoscaling import ScalewayInstanceGroupSchema
from cartography.models.scaleway.instance.autoscaling import (
    ScalewayInstanceTemplateSchema,
)
from cartography.models.scaleway.instance.autoscaling import ScalewayScalingPolicySchema
from cartography.models.scaleway.loadbalancer.loadbalancer import (
    ScalewayLoadBalancerToPrivateNetworkMatchLink,
)
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: scaleway.Client,
    common_job_parameters: dict[str, Any],
    org_id: str,
    projects_id: list[str],
    update_tag: int,
) -> None:
    result = get(client)
    if result is None:
        return
    templates, groups, policies = result
    (
        templates_by_project,
        groups_by_project,
        policies_by_project,
        lb_private_network_links_by_project,
    ) = transform(
        templates,
        groups,
        policies,
        projects_id,
    )
    load_autoscaling_resources(
        neo4j_session,
        templates_by_project,
        groups_by_project,
        policies_by_project,
        update_tag,
    )
    load_lb_private_network_links(
        neo4j_session,
        lb_private_network_links_by_project,
        update_tag,
    )
    cleanup(neo4j_session, projects_id, common_job_parameters)


@timeit
def get(
    client: scaleway.Client,
) -> tuple[list[InstanceTemplate], list[InstanceGroup], list[InstancePolicy]] | None:
    """Return org-wide Autoscaling templates, groups, and policies, or None if
    Autoscaling cannot be read. None signals the caller to skip load/cleanup
    entirely rather than treating the error as an authoritative empty set."""
    api = AutoscalingV1Alpha1API(client)
    try:
        templates = list_all_zones(api.list_instance_templates_all)
        groups = list_all_zones(api.list_instance_groups_all)
        policies: list[InstancePolicy] = []
        for group in groups:
            policies.extend(
                api.list_instance_policies_all(
                    instance_group_id=group.id,
                    zone=group.zone,
                )
            )
        return templates, groups, policies
    except ScalewayException as exc:
        # Autoscaling is a public beta product; accounts without access
        # answer 403 for the whole API. Skip rather than aborting the sync or
        # wiping existing inventory.
        if exc.status_code == 403:
            logger.info(
                "Scaleway Autoscaling not enabled for this account, skipping.",
            )
            return None
        raise


def transform(
    templates: list[InstanceTemplate],
    groups: list[InstanceGroup],
    policies: list[InstancePolicy],
    projects_id: list[str],
) -> tuple[
    dict[str, list[dict[str, Any]]],
    dict[str, list[dict[str, Any]]],
    dict[str, list[dict[str, Any]]],
    dict[str, list[dict[str, Any]]],
]:
    templates_by_project: dict[str, list[dict[str, Any]]] = {}
    groups_by_project: dict[str, list[dict[str, Any]]] = {}
    policies_by_project: dict[str, list[dict[str, Any]]] = {}
    lb_private_network_links_by_project: dict[str, list[dict[str, Any]]] = {}

    allowed_projects = set(projects_id)
    project_by_group_id = {group.id: group.project_id for group in groups}

    for template in templates:
        if template.project_id not in allowed_projects:
            continue
        templates_by_project.setdefault(template.project_id, []).append(
            scaleway_obj_to_dict(template)
        )

    for group in groups:
        if group.project_id not in allowed_projects:
            continue
        formatted_group = scaleway_obj_to_dict(group)
        loadbalancer = formatted_group.get("loadbalancer") or {}
        loadbalancer_id = loadbalancer.get("id")
        private_network_id = loadbalancer.get("private_network_id")
        formatted_group["loadbalancer_id"] = loadbalancer_id
        formatted_group["loadbalancer_backend_ids"] = loadbalancer.get("backend_ids")
        formatted_group["loadbalancer_private_network_id"] = private_network_id
        groups_by_project.setdefault(group.project_id, []).append(formatted_group)

        # The private network attachment is a fact about the LoadBalancer
        # itself, not the InstanceGroup, so it's linked via a MatchLink onto
        # the already-existing ScalewayLoadBalancer node (loadbalancers.py
        # owns that node's properties; this module must not overwrite them).
        if loadbalancer_id and private_network_id:
            lb_private_network_links_by_project.setdefault(group.project_id, []).append(
                {
                    "loadbalancer_id": loadbalancer_id,
                    "private_network_id": private_network_id,
                }
            )

    for policy in policies:
        project_id = project_by_group_id.get(policy.instance_group_id)
        if project_id not in allowed_projects:
            continue
        policies_by_project.setdefault(project_id, []).append(
            scaleway_obj_to_dict(policy)
        )

    return (
        templates_by_project,
        groups_by_project,
        policies_by_project,
        lb_private_network_links_by_project,
    )


@timeit
def load_autoscaling_resources(
    neo4j_session: neo4j.Session,
    templates_by_project: dict[str, list[dict[str, Any]]],
    groups_by_project: dict[str, list[dict[str, Any]]],
    policies_by_project: dict[str, list[dict[str, Any]]],
    update_tag: int,
) -> None:
    for project_id, templates in templates_by_project.items():
        logger.info(
            "Loading %d Scaleway Instance Templates in project '%s' into Neo4j.",
            len(templates),
            project_id,
        )
        load(
            neo4j_session,
            ScalewayInstanceTemplateSchema(),
            templates,
            lastupdated=update_tag,
            PROJECT_ID=project_id,
        )

    for project_id, groups in groups_by_project.items():
        logger.info(
            "Loading %d Scaleway Instance Groups in project '%s' into Neo4j.",
            len(groups),
            project_id,
        )
        load(
            neo4j_session,
            ScalewayInstanceGroupSchema(),
            groups,
            lastupdated=update_tag,
            PROJECT_ID=project_id,
        )

    for project_id, policies in policies_by_project.items():
        logger.info(
            "Loading %d Scaleway Scaling Policies in project '%s' into Neo4j.",
            len(policies),
            project_id,
        )
        load(
            neo4j_session,
            ScalewayScalingPolicySchema(),
            policies,
            lastupdated=update_tag,
            PROJECT_ID=project_id,
        )


@timeit
def load_lb_private_network_links(
    neo4j_session: neo4j.Session,
    lb_private_network_links_by_project: dict[str, list[dict[str, Any]]],
    update_tag: int,
) -> None:
    for project_id, links in lb_private_network_links_by_project.items():
        logger.info(
            "Loading %d Scaleway LoadBalancer -> PrivateNetwork links in project '%s' into Neo4j.",
            len(links),
            project_id,
        )
        load_matchlinks(
            neo4j_session,
            ScalewayLoadBalancerToPrivateNetworkMatchLink(),
            links,
            lastupdated=update_tag,
            _sub_resource_label="ScalewayProject",
            _sub_resource_id=project_id,
        )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    projects_id: list[str],
    common_job_parameters: dict[str, Any],
) -> None:
    for project_id in projects_id:
        scoped_job_parameters = common_job_parameters.copy()
        scoped_job_parameters["PROJECT_ID"] = project_id
        GraphJob.from_node_schema(
            ScalewayScalingPolicySchema(), scoped_job_parameters
        ).run(neo4j_session)
        GraphJob.from_node_schema(
            ScalewayInstanceGroupSchema(), scoped_job_parameters
        ).run(neo4j_session)
        GraphJob.from_node_schema(
            ScalewayInstanceTemplateSchema(), scoped_job_parameters
        ).run(neo4j_session)
        GraphJob.from_matchlink(
            ScalewayLoadBalancerToPrivateNetworkMatchLink(),
            "ScalewayProject",
            project_id,
            common_job_parameters["UPDATE_TAG"],
        ).run(neo4j_session)
