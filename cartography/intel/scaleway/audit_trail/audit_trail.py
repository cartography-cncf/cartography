import logging
from typing import Any

import neo4j
import scaleway
from scaleway.audit_trail.v1alpha1 import AlertRule
from scaleway.audit_trail.v1alpha1 import AuditTrailV1Alpha1API

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.scaleway.utils import scaleway_obj_to_dict
from cartography.models.scaleway.audit_trail.audit_trail import (
    ScalewayAuditTrailAlertRuleSchema,
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
    alert_rules = get(client, org_id)
    alert_rules_by_project = transform_alert_rules(alert_rules, projects_id)
    load_alert_rules(neo4j_session, alert_rules_by_project, update_tag)
    cleanup(neo4j_session, projects_id, common_job_parameters)


@timeit
def get(
    client: scaleway.Client,
    org_id: str,
) -> list[AlertRule]:
    api = AuditTrailV1Alpha1API(client)
    return api.list_alert_rules_all(organization_id=org_id)


def transform_alert_rules(
    alert_rules: list[AlertRule],
    projects_id: list[str],
) -> dict[str, list[dict[str, Any]]]:
    alert_rules_by_project: dict[str, list[dict[str, Any]]] = {}
    for alert_rule in alert_rules:
        formatted = scaleway_obj_to_dict(alert_rule)
        # Alert rules are org-scoped (no project_id field); attach to every
        # project in the organization so they surface under each project node.
        for project_id in projects_id:
            alert_rules_by_project.setdefault(project_id, []).append(formatted)
    return alert_rules_by_project


@timeit
def load_alert_rules(
    neo4j_session: neo4j.Session,
    alert_rules_by_project: dict[str, list[dict[str, Any]]],
    update_tag: int,
) -> None:
    for project_id, alert_rules in alert_rules_by_project.items():
        logger.info(
            "Loading %d Scaleway Audit Trail alert rules in project '%s' into Neo4j.",
            len(alert_rules),
            project_id,
        )
        load(
            neo4j_session,
            ScalewayAuditTrailAlertRuleSchema(),
            alert_rules,
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
            ScalewayAuditTrailAlertRuleSchema(), scoped_job_parameters
        ).run(neo4j_session)
