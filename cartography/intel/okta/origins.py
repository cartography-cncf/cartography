# Okta intel module - Origin
import json
import logging
from typing import Dict
from typing import List

import neo4j
from okta.framework.ApiClient import ApiClient

from cartography.client.core.tx import run_write_query
from cartography.intel.okta.utils import create_api_client
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def _get_trusted_origins(api_client: ApiClient) -> str:
    """
    Get trusted origins from Okta
    :param api_client: api client
    :return: api response data
    """

    response = api_client.get_path("/")

    return response.text


@timeit
def transform_trusted_origins(data: str) -> List[Dict]:
    """
    Transform trusted origin data returned by Okta Server
    :param data: json response
    :return: Array of dictionary containing trusted origins properties
    """
    ret_list: List[Dict] = []

    json_data = json.loads(data)
    for origin_data in json_data:
        props = {}
        props["id"] = origin_data["id"]
        props["name"] = origin_data["name"]
        props["origin"] = origin_data["origin"]

        # https://developer.okta.com/docs/reference/api/trusted-origins/#scope-object
        scope_types = []
        for scope in origin_data.get("scopes", []):
            scope_types.append(scope["type"])

        props["scopes"] = scope_types
        props["status"] = origin_data["status"]
        props["created"] = origin_data.get("created", None)
        props["created_by"] = origin_data.get("createdBy", None)
        props["okta_last_updated"] = origin_data.get("lastUpdated", None)
        props["okta_last_updated_by"] = origin_data.get("lastUpdatedBy", None)

        ret_list.append(props)

    return ret_list


@timeit
def _load_trusted_origins(
    neo4j_session: neo4j.Session,
    okta_org_id: str,
    trusted_list: List[Dict],
    okta_update_tag: int,
) -> None:
    """
    Add trusted origins to the graph
    :param neo4j_session: session with the Neo4j server
    :param okta_org_id: okta organization id
    :param trusted_list: list of trusted origins
    :param okta_update_tag: The timestamp value to set our new Neo4j resources with
    :return: Nothing
    """

    ingest = """
    MATCH (org:OktaOrganization{id: $ORG_ID})
    WITH org
    UNWIND $TRUSTED_LIST as data
    MERGE (new:OktaTrustedOrigin{id: data.id})
    ON CREATE SET new.firstseen = timestamp()
    SET new.name = data.name,
    new.origin = data.origin,
    new.scopes = data.scoped,
    new.status = data.status,
    new.created = data.created,
    new.created_by = data.created_by,
    new.okta_last_updated = data.okta_last_updated,
    new.okta_last_updated_by = data.okta_last_updated_by,
    new.lastupdated = $okta_update_tag
    WITH org, new
    MERGE (org)-[r:RESOURCE]->(new)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $okta_update_tag
    """

    run_write_query(
        neo4j_session,
        ingest,
        ORG_ID=okta_org_id,
        TRUSTED_LIST=trusted_list,
        okta_update_tag=okta_update_tag,
    )


@timeit
def sync_trusted_origins(
    neo4j_session: neo4j.Session,
    okta_org_id: str,
    okta_update_tag: int,
    okta_api_key: str,
) -> None:
    """
    Sync trusted origins
    :param neo4j_session: session with the Neo4j server
    :param okta_org_id: okta organization id
    :param okta_update_tag: The timestamp value to set our new Neo4j resources with
    :param okta_api_key: okta api key
    :return: Nothing
    """

    logger.info("Syncing Okta Trusted Origins")

    api_client = create_api_client(okta_org_id, "/api/v1/trustedOrigins", okta_api_key)

    trusted_data = _get_trusted_origins(api_client)
    trusted_list = transform_trusted_origins(trusted_data)

    _load_trusted_origins(neo4j_session, okta_org_id, trusted_list, okta_update_tag)
