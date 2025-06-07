import logging
from typing import Any
from typing import Dict
from typing import List
from typing import Tuple

import neo4j
from pdpyras import APISession

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.pagerduty.escalation_policy import (
    PagerDutyEscalationPolicySchema,
)
from cartography.models.pagerduty.escalation_policy_rule import (
    PagerDutyEscalationPolicyRuleSchema,
)
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync_escalation_policies(
    neo4j_session: neo4j.Session,
    update_tag: int,
    pd_session: APISession,
    common_job_parameters: dict[str, Any],
) -> None:
    data = get_escalation_policies(pd_session)
    escalation_policies, escalation_rules = transform(data)
    load_escalation_policy_data(neo4j_session, escalation_policies, update_tag)
    load_escalation_rule_data(neo4j_session, escalation_rules, update_tag)
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get_escalation_policies(pd_session: APISession) -> List[Dict[str, Any]]:
    all_escalation_policies: List[Dict[str, Any]] = []
    params = {"include[]": ["services", "teams", "targets"]}
    for escalation_policy in pd_session.iter_all("escalation_policies", params=params):
        all_escalation_policies.append(escalation_policy)
    return all_escalation_policies


def transform(
    data: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    policies: List[Dict[str, Any]] = []
    rules: List[Dict[str, Any]] = []
    for policy in data:
        if policy.get("escalation_rules"):
            i = 0
            for rule in policy["escalation_rules"]:
                rule["_escalation_policy_id"] = policy["id"]
                rule["_escalation_policy_order"] = i
                users_id: list[str] = []
                schedules_id: list[str] = []
                for target in rule["targets"]:
                    if target["type"] == "user_reference":
                        users_id.append(target["id"])
                    elif target["type"] == "schedule_reference":
                        schedules_id.append(target["id"])
                rule["users_id"] = users_id
                rule["schedules_id"] = schedules_id
                rules.append(rule)
                i = i + 1
        policy["services_id"] = [
            service["id"] for service in policy.get("services", [])
        ]
        policy["teams_id"] = [team["id"] for team in policy.get("teams", [])]
        policies.append(policy)

    return policies, rules


@timeit
def load_escalation_policy_data(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    update_tag: int,
) -> None:
    """
    Transform and load policies information
    """
    logger.info(f"Loading {len(data)} pagerduty policies.")
    load(
        neo4j_session,
        PagerDutyEscalationPolicySchema(),
        data,
        lastupdated=update_tag,
    )


@timeit
def load_escalation_rule_data(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    update_tag: int,
) -> None:
    """
    Transform and load escalation rules information
    """
    logger.info(f"Loading {len(data)} pagerduty escalation rules.")
    load(
        neo4j_session,
        PagerDutyEscalationPolicyRuleSchema(),
        data,
        lastupdated=update_tag,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(
        PagerDutyEscalationPolicyRuleSchema(), common_job_parameters
    ).run(
        neo4j_session,
    )
    GraphJob.from_node_schema(
        PagerDutyEscalationPolicySchema(), common_job_parameters
    ).run(
        neo4j_session,
    )
