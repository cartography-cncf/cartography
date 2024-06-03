# Okta intel module - AWS SAML
import logging
import re
from collections import namedtuple
from typing import Dict
from typing import List
from typing import Optional

import neo4j

from cartography.client.core.tx import read_list_of_dicts_tx
from cartography.client.core.tx import read_single_value_tx
from cartography.util import timeit


AccountRole = namedtuple('AccountRole', ['account_id', 'role_name'])
OktaGroup = namedtuple('OktaGroup', ['group_id', 'group_name'])
GroupRole = namedtuple('GroupRole', ['okta_group_id', 'aws_role_arn'])

logger = logging.getLogger(__name__)


def _parse_regex(regex_string: str) -> str:
    return regex_string.replace("{{accountid}}", "P<accountid>").replace("{{role}}", "P<role>").strip()


def _parse_okta_group_name(okta_group_name: str, mapping_regex: str) -> AccountRole | None:
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


def transform_okta_group_to_aws_role(group_id: str, group_name: str, mapping_regex: str) -> Optional[Dict]:
    account_role = _parse_okta_group_name(group_name, mapping_regex)
    if account_role:
        role_arn = f"arn:aws:iam::{account_role.account_id}:role/{account_role.role_name}"
        return {"groupid": group_id, "role": role_arn}
    return None


@timeit
def query_for_okta_to_aws_role_mapping(neo4j_session: neo4j.Session, mapping_regex: str) -> List[Dict]:
    """
    Query the graph for all groups associated with the amazon_aws application and map them to AWSRoles
    :param neo4j_session: session from the Neo4j server
    :param mapping_regex: the regex used by the organization to map groups to aws roles
    """
    query = "MATCH (app:OktaApplication{name:'amazon_aws'})--(group:OktaGroup) return group.id, group.name"

    group_to_role_mapping: List[Dict] = []
    has_results = False
    results = neo4j_session.run(query)

    for res in results:
        has_results = True
        # input: okta group id, okta group name. output: aws role arn.
        mapping = transform_okta_group_to_aws_role(res["group.id"], res["group.name"], mapping_regex)
        if mapping:
            group_to_role_mapping.append(mapping)

    if has_results and not group_to_role_mapping:
        logger.warn(
            "AWS Okta Application present, but no mappings were found. "
            "Please verify the mapping regex is correct",
        )

    return group_to_role_mapping


@timeit
def _load_okta_group_to_aws_roles(
    neo4j_session: neo4j.Session, group_to_role: List[Dict],
    okta_update_tag: int,
) -> None:
    """
    Add the ALLOWED_BY relationship between OktaGroups and the AWSRoles they enable
    :param neo4j_session: session with the Neo4j server
    :param group_to_role: the mapping between OktaGroups and the AWSRoles they allow access to
    :param okta_update_tag: The timestamp value to set our new Neo4j resources with
    :return: Nothing
    """
    ingest_statement = """

    UNWIND $GROUP_TO_ROLE as app_data
    MATCH (role:AWSRole{arn: app_data.role})
    MATCH (group:OktaGroup{id: app_data.groupid})
    MERGE (role)<-[r:ALLOWED_BY]-(group)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $okta_update_tag
    """

    neo4j_session.run(
        ingest_statement,
        GROUP_TO_ROLE=group_to_role,
        okta_update_tag=okta_update_tag,
    )


@timeit
def _load_human_can_assume_role(neo4j_session: neo4j.Session, okta_update_tag: int) -> None:
    """
    Add the CAN_ASSUME_ROLE relationship between Humans and the AWSRoles they can assume
    :param neo4j_session: session with the Neo4j server
    :param okta_update_tag: The timestamp value to set our new Neo4j resources with
    :return: Nothing
    """
    ingest_statement = """
    MATCH (role:AWSRole)<-[:ALLOWED_BY]-(:OktaGroup)<-[:MEMBER_OF_OKTA_GROUP]-(:OktaUser)-[:IDENTITY_OKTA]-(human:Human)
    MERGE (human)-[r:CAN_ASSUME_ROLE]->(role)
    SET r.lastupdated = $okta_update_tag
    """

    neo4j_session.run(
        ingest_statement,
        okta_update_tag=okta_update_tag,
    )


def get_awssso_okta_groups(neo4j_session: neo4j.Session, okta_org_id: str) -> list[OktaGroup]:
    """
    Return list of all Okta group ids in the current Okta organization tied to Okta Applications with name
    "amazon_aws_sso".
    """
    query = """
    MATCH (g:OktaGroup)-[:APPLICATION]->(a:OktaApplication{name:"amazon_aws_sso"})
           <-[:RESOURCE]-(:OktaOrganization{id: $okta_org_id})
    RETURN g.id as group_id, g.name as group_name
    """
    result = neo4j_session.read_transaction(read_list_of_dicts_tx, query, okta_org_id=okta_org_id)
    return [OktaGroup(group_name=og['group_name'], group_id=og['group_id']) for og in result]


def get_awssso_role_arn(account_id: str, role_hint: str, neo4j_session: neo4j.Session) -> str | None:
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
    return neo4j_session.read_transaction(read_single_value_tx, query, account_id=account_id, role_hint=role_hint)


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

        role_arn = get_awssso_role_arn(account_role.account_id, account_role.role_name, neo4j_session)
        if role_arn:
            result.append(GroupRole(group.group_id, role_arn))
    return result


def _load_awssso_tx(tx: neo4j.Transaction, group_to_role: list[GroupRole], okta_update_tag: int) -> None:
    ingest_statement = """
    UNWIND $GROUP_TO_ROLE as app_data
        MATCH (role:AWSRole{arn: app_data.aws_role_arn})
        MATCH (group:OktaGroup{id: app_data.okta_group_id})
        MERGE (role)<-[r:ALLOWED_BY]-(group)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $okta_update_tag
    """
    tx.run(
        ingest_statement,
        GROUP_TO_ROLE=[g._asdict() for g in group_to_role],
        okta_update_tag=okta_update_tag,
    )


def _load_okta_group_to_awssso_roles(
        neo4j_session: neo4j.Session,
        group_to_role: list[GroupRole],
        okta_update_tag: int,
) -> None:
    neo4j_session.write_transaction(_load_awssso_tx, group_to_role, okta_update_tag)


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
    group_to_role_mapping = query_for_okta_to_aws_role_mapping(neo4j_session, mapping_regex)
    _load_okta_group_to_aws_roles(neo4j_session, group_to_role_mapping, okta_update_tag)
    _load_human_can_assume_role(neo4j_session, okta_update_tag)

    sso_okta_groups = get_awssso_okta_groups(neo4j_session, okta_org_id)
    group_to_ssorole_mapping = query_for_okta_to_awssso_role_mapping(neo4j_session, sso_okta_groups, mapping_regex)
    _load_okta_group_to_awssso_roles(neo4j_session, group_to_ssorole_mapping, okta_update_tag)
