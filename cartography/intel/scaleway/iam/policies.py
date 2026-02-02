import logging
from typing import Any

import neo4j
import scaleway
from scaleway.iam.v1alpha1 import IamV1Alpha1API
from scaleway.iam.v1alpha1 import Policy
from scaleway.iam.v1alpha1 import Rule

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.scaleway.utils import scaleway_obj_to_dict
from cartography.models.scaleway.iam.policy import ScalewayPolicySchema
from cartography.models.scaleway.iam.rule import ScalewayRuleSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: scaleway.Client,
    common_job_parameters: dict[str, Any],
    org_id: str,
    update_tag: int,
) -> None:
    api = IamV1Alpha1API(client)

    # Get and load policies
    policies = get_policies(api, org_id)
    formatted_policies = transform_policies(policies)
    load_policies(neo4j_session, formatted_policies, org_id, update_tag)

    # Get and load rules for all policies
    all_formatted_rules: list[dict[str, Any]] = []
    for policy in policies:
        rules = get_rules(api, policy.id)
        all_formatted_rules.extend(transform_rules(rules, policy.id))
    load_rules(neo4j_session, all_formatted_rules, org_id, update_tag)

    cleanup(neo4j_session, common_job_parameters)


@timeit
def get_policies(
    api: IamV1Alpha1API,
    org_id: str,
) -> list[Policy]:
    return api.list_policies_all(organization_id=org_id)


@timeit
def get_rules(
    api: IamV1Alpha1API,
    policy_id: str,
) -> list[Rule]:
    return api.list_rules_all(policy_id=policy_id)


def transform_policies(policies: list[Policy]) -> list[dict[str, Any]]:
    formatted_policies = []
    for policy in policies:
        formatted_policy = scaleway_obj_to_dict(policy)
        formatted_policies.append(formatted_policy)
    return formatted_policies


def transform_rules(rules: list[Rule], policy_id: str) -> list[dict[str, Any]]:
    formatted_rules = []
    for rule in rules:
        formatted_rule = scaleway_obj_to_dict(rule)
        formatted_rule["policy_id"] = policy_id
        formatted_rules.append(formatted_rule)
    return formatted_rules


@timeit
def load_policies(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    org_id: str,
    update_tag: int,
) -> None:
    logger.info("Loading %d Scaleway Policies into Neo4j.", len(data))
    load(
        neo4j_session,
        ScalewayPolicySchema(),
        data,
        lastupdated=update_tag,
        ORG_ID=org_id,
    )


@timeit
def load_rules(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    org_id: str,
    update_tag: int,
) -> None:
    if not data:
        return
    logger.info(
        "Loading %d Scaleway Rules into Neo4j.",
        len(data),
    )
    load(
        neo4j_session,
        ScalewayRuleSchema(),
        data,
        lastupdated=update_tag,
        ORG_ID=org_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(ScalewayPolicySchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(ScalewayRuleSchema(), common_job_parameters).run(
        neo4j_session
    )
