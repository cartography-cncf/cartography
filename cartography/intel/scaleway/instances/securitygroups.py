import logging
from typing import Any

import neo4j
import scaleway
from scaleway.instance.v1 import InstanceV1API
from scaleway.instance.v1 import SecurityGroup
from scaleway.instance.v1 import SecurityGroupRule

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.scaleway.utils import DEFAULT_ZONE
from cartography.intel.scaleway.utils import scaleway_obj_to_dict
from cartography.models.scaleway.instance.securitygroup import (
    ScalewayInboundSecurityGroupRuleSchema,
)
from cartography.models.scaleway.instance.securitygroup import (
    ScalewayOutboundSecurityGroupRuleSchema,
)
from cartography.models.scaleway.instance.securitygroup import (
    ScalewaySecurityGroupSchema,
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
    groups, rules_by_group = get(client, org_id)
    groups_by_project, rules_by_project = transform_security_groups(
        groups, rules_by_group
    )
    load_security_groups(neo4j_session, groups_by_project, rules_by_project, update_tag)
    cleanup(neo4j_session, projects_id, common_job_parameters)


@timeit
def get(
    client: scaleway.Client,
    org_id: str,
) -> tuple[list[SecurityGroup], dict[str, list[SecurityGroupRule]]]:
    api = InstanceV1API(client)
    groups = api.list_security_groups_all(organization=org_id, zone=DEFAULT_ZONE)
    # ponytail: single page (per_page=100). The SDK's list_security_group_rules_all
    # helper recurses without terminating against the live API (same pagination bug
    # class as flexibleips / SDK #1040); a security group never has >100 rules.
    rules_by_group = {
        group.id: api.list_security_group_rules(
            security_group_id=group.id, zone=DEFAULT_ZONE, per_page=100
        ).rules
        for group in groups
    }
    return groups, rules_by_group


def transform_security_groups(
    groups: list[SecurityGroup],
    rules_by_group: dict[str, list[SecurityGroupRule]],
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, list[dict[str, Any]]]]:
    groups_by_project: dict[str, list[dict[str, Any]]] = {}
    rules_by_project: dict[str, list[dict[str, Any]]] = {}
    for group in groups:
        project_id = group.project
        formatted_group = scaleway_obj_to_dict(group)
        formatted_group["servers_id"] = [
            server["id"] for server in (formatted_group.get("servers") or [])
        ]
        groups_by_project.setdefault(project_id, []).append(formatted_group)

        for rule in rules_by_group.get(group.id, []):
            formatted_rule = scaleway_obj_to_dict(rule)
            formatted_rule["security_group_id"] = group.id
            rules_by_project.setdefault(project_id, []).append(formatted_rule)
    return groups_by_project, rules_by_project


@timeit
def load_security_groups(
    neo4j_session: neo4j.Session,
    groups_by_project: dict[str, list[dict[str, Any]]],
    rules_by_project: dict[str, list[dict[str, Any]]],
    update_tag: int,
) -> None:
    for project_id, groups in groups_by_project.items():
        logger.info(
            "Loading %d Scaleway SecurityGroups in project '%s' into Neo4j.",
            len(groups),
            project_id,
        )
        load(
            neo4j_session,
            ScalewaySecurityGroupSchema(),
            groups,
            lastupdated=update_tag,
            PROJECT_ID=project_id,
        )

    for project_id, rules in rules_by_project.items():
        inbound = [r for r in rules if r.get("direction") == "inbound"]
        outbound = [r for r in rules if r.get("direction") == "outbound"]
        load(
            neo4j_session,
            ScalewayInboundSecurityGroupRuleSchema(),
            inbound,
            lastupdated=update_tag,
            PROJECT_ID=project_id,
        )
        load(
            neo4j_session,
            ScalewayOutboundSecurityGroupRuleSchema(),
            outbound,
            lastupdated=update_tag,
            PROJECT_ID=project_id,
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
            ScalewaySecurityGroupSchema(), scoped_job_parameters
        ).run(neo4j_session)
        GraphJob.from_node_schema(
            ScalewayInboundSecurityGroupRuleSchema(), scoped_job_parameters
        ).run(neo4j_session)
        GraphJob.from_node_schema(
            ScalewayOutboundSecurityGroupRuleSchema(), scoped_job_parameters
        ).run(neo4j_session)
