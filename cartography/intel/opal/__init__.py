import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j
import opal_security as opal

from cartography.config import Config
from cartography.intel.opal.opal_aws import sync_opal_aws
from cartography.intel.opal.opal_okta import sync_opal_okta
from cartography.util import run_cleanup_job
from cartography.util import timeit

PAGE_SIZE = 200
logger = logging.getLogger(__name__)


def _resource_client(configuration: opal.Configuration) -> opal.api.ResourcesApi:
    api_client = opal.ApiClient(configuration)
    return opal.ResourcesApi(api_client)


def _group_client(configuration: opal.Configuration) -> opal.api.GroupsApi:
    api_client = opal.ApiClient(configuration)
    return opal.GroupsApi(api_client)


def _owners_client(configuration: opal.Configuration) -> opal.api.OwnersApi:
    api_client = opal.ApiClient(configuration)
    return opal.OwnersApi(api_client)


def parse_group(group: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse a group dict and add the resource_type field.
    """
    group["resource_id"] = group.get("group_id")
    group["resource_type"] = "OPAL_GROUP"
    group["remote_resource_name"] = group.get("remote_name")
    return group


def get_all_groups(client: opal.api.GroupsApi) -> List[Dict[str, Any]]:
    """
    Retrieve all groups from the Opal API.

    :param client: The Opal GroupsApi client.
    :return: A list of all groups.
    """
    logger.info("Getting all groups from Opal")
    try:
        response = client.get_groups(page_size=PAGE_SIZE)
        groups = [parse_group(g.to_dict()) for g in response.results]
        while response.next:
            response = client.get_groups(page_size=PAGE_SIZE, cursor=response.next)
            groups.extend([parse_group(g.to_dict()) for g in response.results])
    except opal.ApiException as e:
        logger.error(f"Error getting groups from Opal: {e}")
        raise
    return groups


def get_opal_groups_to_okta_groups_map(groups: List[Dict[str, Any]]) -> Dict[str, str]:
    """
    Create a map of Opal Groups to their Okta groups using the remote_info field.
    """
    logger.info("Mapping opal groups to okta groups")

    opal_to_okta_map = {}
    for group in groups:
        opal_group_id = group.get('group_id')
        okta_group_id = group.get('remote_id')
        if opal_group_id and okta_group_id:
            opal_to_okta_map[opal_group_id] = okta_group_id
    return opal_to_okta_map


def get_owner_ids_to_okta_groups_map(
    owners_client: opal.api.OwnersApi,
    opal_to_okta_map: Dict[str, str],
) -> Dict[str, str]:
    """
    Return a mapping of owner_ids to okta groups.
    The source_group_id property of an owner is the opal group that is the owner.
    From the opal group, you can determine the okta group by looking it up in opal_to_okta_map.
    """
    logger.info("Getting owner ids to okta groups map")
    owner_ids_to_okta_groups_map = {}
    response = owners_client.get_owners(page_size=PAGE_SIZE)
    owners = [o.to_dict() for o in response.results]
    while response.next:
        response = owners_client.get_owners(cursor=response.next)
        owners.extend([o.to_dict() for o in response.results])
    for owner in owners:
        owner_id = owner.get('owner_id')
        source_group_id = owner.get('source_group_id')
        if owner_id and source_group_id:
            okta_group_id = opal_to_okta_map.get(source_group_id)
            if okta_group_id:
                owner_ids_to_okta_groups_map[owner_id] = okta_group_id
    return owner_ids_to_okta_groups_map


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]) -> None:
    logger.info("Cleaning up opal aws")
    # GraphJob.from_node_schema(OpalResourceSchema(), common_job_parameters).run(neo4j_session)
    run_cleanup_job(
        'opal_aws_cleanup.json',
        neo4j_session,
        common_job_parameters,
    )


@timeit
def start_opal_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    if not config.opal_access_token or not config.opal_host:
        logger.warning("No valid Opal credentials could be found. Exiting Opal sync stage.")
        return

    configuration = opal.Configuration(
        host=f"{config.opal_host}/v1",
        access_token=config.opal_access_token,
    )
    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
    }
    resource_client = _resource_client(configuration)
    owners_client = _owners_client(configuration)
    group_client = _group_client(configuration)
    groups = get_all_groups(group_client)
    opal_to_okta_map = get_opal_groups_to_okta_groups_map(groups)
    owner_ids_to_okta_groups_map = get_owner_ids_to_okta_groups_map(owners_client, opal_to_okta_map)

    sync_opal_aws(
        neo4j_session,
        config.update_tag,
        resource_client,
        opal_to_okta_map,
        owner_ids_to_okta_groups_map,
    )
    sync_opal_okta(
        neo4j_session,
        config.update_tag,
        groups,
        opal_to_okta_map,
        owner_ids_to_okta_groups_map,
    )
    cleanup(neo4j_session, common_job_parameters)
