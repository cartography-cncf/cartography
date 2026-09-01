from __future__ import annotations

# Okta intel module - AWS SAML
import logging
import re
from collections import namedtuple

import neo4j

from cartography.client.core.tx import load_matchlinks
from cartography.client.core.tx import read_list_of_dicts_tx
from cartography.client.core.tx import read_single_value_tx
from cartography.graph.job import GraphJob
from cartography.models.okta.awssaml import OktaGroupToAWSRoleAllowedByMatchLink
from cartography.models.okta.awssaml import OktaGroupToAWSRoleHasRoleMatchLink
from cartography.util import timeit

AccountRole = namedtuple("AccountRole", ["account_id", "role_name"])
OktaGroup = namedtuple("OktaGroup", ["group_id", "group_name"])
GroupRole = namedtuple("GroupRole", ["okta_group_id", "aws_role_arn"])

logger = logging.getLogger(__name__)


def _parse_regex(regex_string: str) -> str:
    return (
        regex_string.replace("{{accountid}}", "P<accountid>")
        .replace("{{role}}", "P<role>")
        .strip()
    )


def _parse_okta_group_name(
    okta_group_name: str,
    mapping_regex: str,
) -> AccountRole | None:
    """
    Extract AWS account id and AWS role name from the given Okta group name using the given mapping regex.
    """
    regex = _parse_regex(mapping_regex)
    matches = re.search(regex, okta_group_name)
    if matches:
        account_id = matches.group("accountid")
        role_name = matches.group("role")
        return AccountRole(account_id, role_name)
    return None


def transform_okta_group_to_aws_role(
    group_id: str,
    group_name: str,
    mapping_regex: str,
) -> dict | None:
    account_role = _parse_okta_group_name(group_name, mapping_regex)
    if account_role:
        role_arn = (
            f"arn:aws:iam::{account_role.account_id}:role/{account_role.role_name}"
        )
        return {"groupid": group_id, "role": role_arn}
    return None


@timeit
def query_for_okta_to_aws_role_mapping(
    neo4j_session: neo4j.Session,
    mapping_regex: str,
    okta_org_id: str,
) -> list[dict]:
    """
    Query the graph for all groups associated with the amazon_aws application and map them to AWSRoles
    :param neo4j_session: session from the Neo4j server
    :param mapping_regex: the regex used by the organization to map groups to aws roles
    :param okta_org_id: Okta organization that owns the groups and application
    """
    query = """
    MATCH (org:OktaOrganization {id: $okta_org_id})-[:RESOURCE]->
          (app:OktaApplication {name: 'amazon_aws'})
    MATCH (org)-[:RESOURCE]->(group:OktaGroup)-[:APPLICATION]->(app)
    RETURN group.id AS group_id, group.name AS group_name
    """

    group_to_role_mapping: list[dict] = []
    results = neo4j_session.execute_read(
        read_list_of_dicts_tx,
        query,
        okta_org_id=okta_org_id,
    )

    for res in results:
        # input: okta group id, okta group name. output: aws role arn.
        mapping = transform_okta_group_to_aws_role(
            res["group_id"],
            res["group_name"],
            mapping_regex,
        )
        if mapping:
            group_to_role_mapping.append(mapping)

    if results and not group_to_role_mapping:
        logger.warning(
            "AWS Okta Application present, but no mappings were found. "
            "Please verify the mapping regex is correct",
        )

    return group_to_role_mapping


@timeit
def _load_okta_group_to_aws_roles(
    neo4j_session: neo4j.Session,
    group_to_role: list[GroupRole],
    okta_update_tag: int,
    okta_org_id: str,
) -> None:
    """
    Add canonical HAS_ROLE and compatibility ALLOWED_BY relationships between
    OktaGroups and the AWSRoles they enable.
    :param neo4j_session: session with the Neo4j server
    :param group_to_role: the mapping between OktaGroups and the AWSRoles they allow access to
    :param okta_update_tag: The timestamp value to set our new Neo4j resources with
    :param okta_org_id: Okta organization that owns the relationships
    :return: Nothing
    """
    mappings = [mapping._asdict() for mapping in group_to_role]
    schemas = (
        OktaGroupToAWSRoleHasRoleMatchLink(),
        OktaGroupToAWSRoleAllowedByMatchLink(),
    )
    for schema in schemas:
        load_matchlinks(
            neo4j_session,
            schema,
            mappings,
            lastupdated=okta_update_tag,
            _sub_resource_label="OktaOrganization",
            _sub_resource_id=okta_org_id,
        )
        GraphJob.from_matchlink(
            schema,
            "OktaOrganization",
            okta_org_id,
            okta_update_tag,
        ).run(
            neo4j_session,
        )


def get_awssso_okta_groups(
    neo4j_session: neo4j.Session,
    okta_org_id: str,
) -> list[OktaGroup]:
    """
    Return list of all Okta group ids in the current Okta organization tied to Okta Applications with name
    "amazon_aws_sso".
    """
    query = """
    MATCH (org:OktaOrganization {id: $okta_org_id})-[:RESOURCE]->
          (a:OktaApplication {name: "amazon_aws_sso"})
    MATCH (org)-[:RESOURCE]->(g:OktaGroup)-[:APPLICATION]->(a)
    RETURN g.id as group_id, g.name as group_name
    """
    result = neo4j_session.execute_read(
        read_list_of_dicts_tx,
        query,
        okta_org_id=okta_org_id,
    )
    return [
        OktaGroup(group_name=og["group_name"], group_id=og["group_id"]) for og in result
    ]


def get_awssso_role_arn(
    account_id: str,
    role_hint: str,
    neo4j_session: neo4j.Session,
) -> str | None:
    """
    Attempt to return the AWS role ARN for the given AWS account ID and role hint string.
    This function exists to handle that AWS SSO roles have a 'AWSReservedSSO' prefix and a hashed suffix
    Input:
    - account_id: AWS account ID
    - role_hint (str): The `AccountRole.role_name` returned by _parse_okta_group_name(). This is the part of the Okta
    group name that refers to the AWS role name.
    Output:
    - If we are able to find it, returns the matching AWS role ARN.
    """
    query = """
    MATCH (:AWSAccount{id:$account_id})-[:RESOURCE]->(role:AWSRole{path:"/aws-reserved/sso.amazonaws.com/"})
    WHERE SPLIT(role.name, '_')[1..-1][0] = $role_hint
    RETURN role.arn AS role_arn
    """
    return neo4j_session.execute_read(
        read_single_value_tx,
        query,
        account_id=account_id,
        role_hint=role_hint,
    )


def query_for_okta_to_awssso_role_mapping(
    neo4j_session: neo4j.Session,
    awssso_okta_groups: list[OktaGroup],
    mapping_regex: str,
) -> list[GroupRole]:
    """
    Input:
    - neo4j session
    - str list of Okta group names
    - str regex that tells us how to find the AWS role name and account when given an Okta group name
    Output:
    - list of OktaGroup id to AWSRole arn pairs.
    """
    result = []
    for group in awssso_okta_groups:
        account_role = _parse_okta_group_name(group.group_name, mapping_regex)
        if not account_role:
            logger.info(f"Okta group {group.group_name} has no associated AWS SSO role")
            continue

        role_arn = get_awssso_role_arn(
            account_role.account_id,
            account_role.role_name,
            neo4j_session,
        )
        if role_arn:
            result.append(GroupRole(group.group_id, role_arn))
    return result


@timeit
def sync_okta_aws_saml(
    neo4j_session: neo4j.Session,
    mapping_regex: str,
    okta_update_tag: int,
    okta_org_id: str,
) -> None:
    """
    Sync okta integration with saml. This will link OktaGroups to the AWSRoles they enable.
    This is for people who use the okta saml provider for AWS
    https://saml-doc.okta.com/SAML_Docs/How-to-Configure-SAML-2.0-for-Amazon-Web-Service#scenarioC
    If an organization does not use okta as a SAML provider for AWS the query will not return any results
    and nothing will be added to the graph
    :param mapping_regex: session from the Neo4j server
    :param okta_org_id: okta organization id
    :param okta_update_tag: The timestamp value to set our new Neo4j resources with
    :param okta_api_key: Okta api key
    :return: Nothing
    """
    logger.info("Syncing Okta SAML Integration")

    # Query for the aws application and its associated groups
    group_to_role_mapping = query_for_okta_to_aws_role_mapping(
        neo4j_session,
        mapping_regex,
        okta_org_id,
    )
    combined_group_to_role_mapping = [
        GroupRole(
            okta_group_id=mapping["groupid"],
            aws_role_arn=mapping["role"],
        )
        for mapping in group_to_role_mapping
    ]

    sso_okta_groups = get_awssso_okta_groups(neo4j_session, okta_org_id)
    group_to_ssorole_mapping = query_for_okta_to_awssso_role_mapping(
        neo4j_session,
        sso_okta_groups,
        mapping_regex,
    )
    combined_group_to_role_mapping.extend(group_to_ssorole_mapping)
    _load_okta_group_to_aws_roles(
        neo4j_session,
        combined_group_to_role_mapping,
        okta_update_tag,
        okta_org_id,
    )
