import logging

import neo4j
import opal_security as opal

from cartography.client.core.tx import load
from cartography.intel.opal.opal_common import load_auto_approved_access
from cartography.intel.opal.opal_common import load_manual_approvers
from cartography.intel.opal.opal_common import parse_opal_resource_access_configuration
from cartography.models.opal.opalresource import OpalResourceSchema

logger = logging.getLogger(__name__)

PAGE_SIZE = 200


def parse_resource(resource: dict) -> dict:
    """
    Parse a resource dict and if the "remote_info" has an "aws_permission_set" in it,
    add the permission_set_arn and the account_id to the original dict.
    """
    remote_info = resource.get("remote_info", {})
    aws_permission_set = remote_info.get("aws_permission_set", {})

    if aws_permission_set:
        resource["remote_id"] = aws_permission_set.get("arn")
        resource["remote_account_id"] = aws_permission_set.get("account_id")

    return resource


def get_all_resources(client: opal.ResourcesApi, resource_type: opal.ResourceTypeEnum) -> list[dict]:
    logger.info(f"Getting all opal aws resources for {resource_type}")
    response = client.get_resources(page_size=PAGE_SIZE, resource_type_filter=resource_type)
    resources = [parse_resource(r.to_dict()) for r in response.results]
    while response.next:
        response = client.get_resources(page_size=PAGE_SIZE, resource_type_filter=resource_type, cursor=response.next)
        resources.extend([parse_resource(r.to_dict()) for r in response.results])

    return resources


def load_opal_resources(neo4j_session: neo4j.Session, resources: list[dict], update_tag: int) -> None:
    """
    Load Opal resources into the Neo4j database.

    :param neo4j_session: The Neo4j session to use for loading data.
    :param resources: The resources to load.
    :param update_tag: The update tag to use for the load operation.
    """
    logger.info(f"Loaded {len(resources)} opal aws resources")
    load(neo4j_session, OpalResourceSchema(), resources, lastupdated=update_tag)


def map_opal_resources_to_aws_roles(
        neo4j_session: neo4j.Session, update_tag: int,
        aws_permission_set_resources: list[dict],
) -> None:
    """
    Map OpalResource nodes to the AWSRoles they provide access to based on the provided list of resources.
    """
    logger.info(f"Mapping {len(aws_permission_set_resources)} opal resources to aws roles")
    neo4j_session.run(
        """
        UNWIND $aws_permission_set_resources AS resource
        MATCH (aws_account:AWSAccount {id: resource.remote_account_id})-[:RESOURCE]->
        (aws_role:AWSRole)<-[:ASSIGNED_TO_ROLE]-
        (aws_permset:AWSPermissionSet {arn: resource.remote_id})
        MATCH (opal_resource:OpalResource {id: resource.resource_id})
        MERGE (opal_resource)-[r:PROVIDES_ACCESS_TO]->(aws_role)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $update_tag
        """,
        aws_permission_set_resources=aws_permission_set_resources,
        update_tag=update_tag,
    )


def sync_opal_aws(
    neo4j_session: neo4j.Session,
    update_tag: int,
    resource_client: opal.ResourcesApi,
    opal_to_okta_map: dict,
    owner_ids_to_okta_groups_map: dict,
) -> None:
    """
    Sync Opal resources into Cartography.
    """
    resources = get_all_resources(resource_client, opal.ResourceTypeEnum.AWS_SSO_PERMISSION_SET)

    # Use the load function to execute the query
    load_opal_resources(neo4j_session, resources, update_tag)
    map_opal_resources_to_aws_roles(neo4j_session, update_tag, resources)

    auto_approved_access, manual_approved_access = parse_opal_resource_access_configuration(
        resources, opal_to_okta_map, owner_ids_to_okta_groups_map,
    )

    load_auto_approved_access(neo4j_session, update_tag, auto_approved_access)
    load_manual_approvers(neo4j_session, update_tag, manual_approved_access)
