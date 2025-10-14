import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j
from pdpyras import APISession

from cartography.client.core.tx import run_write_query
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync_escalation_policies(
    neo4j_session: neo4j.Session,
    update_tag: int,
    pd_session: APISession,
) -> None:
    escalation_policies = get_escalation_policies(pd_session)
    load_escalation_policy_data(neo4j_session, escalation_policies, update_tag)


@timeit
def get_escalation_policies(pd_session: APISession) -> List[Dict[str, Any]]:
    all_escalation_policies: List[Dict[str, Any]] = []
    params = {"include[]": ["services", "teams", "targets"]}
    for escalation_policy in pd_session.iter_all("escalation_policies", params=params):
        all_escalation_policies.append(escalation_policy)
    return all_escalation_policies


def load_escalation_policy_data(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    update_tag: int,
) -> None:
    """
    Transform and load escalation_policy information
    """
    ingestion_cypher_query = """
    UNWIND $EscalationPolicies AS policy
        MERGE (p:PagerDutyEscalationPolicy{id: policy.id})
        ON CREATE SET p.html_url = policy.html_url,
            p.firstseen = timestamp()
        SET p.type = policy.type,
            p.summary = policy.summary,
            p.on_call_handoff_notifications = policy.on_call_handoff_notifications,
            p.name = policy.name,
            p.num_loops = policy.num_loops,
            p.lastupdated = $update_tag
    """
    logger.info(f"Loading {len(data)} pagerduty escalation_policies.")

    rules: List[Dict[str, Any]] = []
    services: List[Dict[str, Any]] = []
    teams: List[Dict[str, Any]] = []
    for policy in data:
        if policy.get("escalation_rules"):
            i = 0
            for rule in policy["escalation_rules"]:
                rule["_escalation_policy_id"] = policy["id"]
                rule["_escalation_policy_order"] = i
                rules.append(rule)
                i = i + 1
        if policy.get("services"):
            for service in policy["services"]:
                services.append(
                    {"escalation_policy": policy["id"], "service": service["id"]},
                )
        if policy.get("teams"):
            for team in policy["teams"]:
                teams.append({"escalation_policy": policy["id"], "team": team["id"]})

    run_write_query(
        neo4j_session,
        ingestion_cypher_query,
        EscalationPolicies=data,
        update_tag=update_tag,
    )

    _attach_rules(neo4j_session, rules, update_tag)
    _attach_services(neo4j_session, services, update_tag)
    _attach_teams(neo4j_session, teams, update_tag)


def _attach_rules(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    update_tag: int,
) -> None:
    """
    Add escalation policy rules, and attach them to targets.
    """
    ingestion_cypher_query = """
    UNWIND $Rules AS rule
        MERGE (epr:PagerDutyEscalationPolicyRule{id: rule.id})
        ON CREATE SET epr.firstseen = timestamp()
        SET epr.escalation_delay_in_minutes = rule.escalation_delay_in_minutes,
            epr.lastupdated = $update_tag
        WITH epr, rule
        MATCH (ep:PagerDutyEscalationPolicy{id: rule._escalation_policy_id})
        MERGE (ep)-[r:HAS_RULE]->(epr)
        ON CREATE SET r.firstseen = timestamp()
        SET r.order = rule._escalation_policy_order
    """

    users: List[Dict[str, Any]] = []
    schedules: List[Dict[str, Any]] = []

    for rule in data:
        if rule.get("targets"):
            for target in rule["targets"]:
                if target["type"] == "user":
                    users.append({"rule": rule["id"], "user": target["id"]})
                elif target["type"] == "schedule":
                    schedules.append({"rule": rule["id"], "schedule": target["id"]})

    run_write_query(
        neo4j_session,
        ingestion_cypher_query,
        Rules=data,
        update_tag=update_tag,
    )

    _attach_user_targets(neo4j_session, users, update_tag)
    _attach_schedule_targets(neo4j_session, schedules, update_tag)


def _attach_user_targets(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    update_tag: int,
) -> None:
    """
    Add relationship between escalation policy and services.
    """
    ingestion_cypher_query = """
    UNWIND $Relations AS relation
        MATCH (p:PagerDutyEscalationPolicyRule{id: relation.rule}),
        (u:PagerDutyUser{id: relation.user})
        MERGE (p)-[r:ASSOCIATED_WITH]->(u)
        ON CREATE SET r.firstseen = timestamp()
    """
    run_write_query(
        neo4j_session,
        ingestion_cypher_query,
        Relations=data,
        update_tag=update_tag,
    )


def _attach_schedule_targets(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    update_tag: int,
) -> None:
    """
    Add relationship between escalation policy and services.
    """
    ingestion_cypher_query = """
    UNWIND $Relations AS relation
        MATCH (p:PagerDutyEscalationPolicyRule{id: relation.rule}),
        (s:PagerDutySchedule{id: relation.schedule})
        MERGE (p)-[r:ASSOCIATED_WITH]->(s)
        ON CREATE SET r.firstseen = timestamp()
    """
    run_write_query(
        neo4j_session,
        ingestion_cypher_query,
        Relations=data,
        update_tag=update_tag,
    )


def _attach_services(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    update_tag: int,
) -> None:
    """
    Add relationship between escalation policy and services.
    """
    ingestion_cypher_query = """
    UNWIND $Relations AS relation
        MATCH (p:PagerDutyEscalationPolicy{id: relation.escalation_policy}),
        (s:PagerDutyService{id: relation.service})
        MERGE (s)-[r:ASSOCIATED_WITH]->(p)
        ON CREATE SET r.firstseen = timestamp()
    """
    run_write_query(
        neo4j_session,
        ingestion_cypher_query,
        Relations=data,
        update_tag=update_tag,
    )


def _attach_teams(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    update_tag: int,
) -> None:
    """
    Add relationship between escalation policy and teams.
    """
    ingestion_cypher_query = """
    UNWIND $Relations AS relation
        MATCH (p:PagerDutyEscalationPolicy{id: relation.escalation_policy}),
        (t:PagerDutyTeam{id: relation.team})
        MERGE (t)-[r:ASSOCIATED_WITH]->(p)
        ON CREATE SET r.firstseen = timestamp()
    """
    run_write_query(
        neo4j_session,
        ingestion_cypher_query,
        Relations=data,
        update_tag=update_tag,
    )
