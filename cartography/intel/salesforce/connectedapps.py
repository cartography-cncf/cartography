from collections import defaultdict
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.salesforce.util import parse_sf_datetime
from cartography.intel.salesforce.util import SalesforceClient
from cartography.models.salesforce.connectedapp import SalesforceConnectedAppSchema
from cartography.util import timeit

_APP_FIELDS = (
    "Id, Name, OptionsAllowAdminApprovedUsersOnly, CreatedDate, LastModifiedDate"
)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: SalesforceClient,
    common_job_parameters: dict[str, Any],
) -> None:
    apps = get_apps(client)
    tokens = get_oauth_tokens(client)
    apps = transform(apps, tokens)
    load_connected_apps(
        neo4j_session,
        apps,
        common_job_parameters["ORG_ID"],
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get_apps(client: SalesforceClient) -> list[dict[str, Any]]:
    return client.query_all(f"SELECT {_APP_FIELDS} FROM ConnectedApplication")


@timeit
def get_oauth_tokens(client: SalesforceClient) -> list[dict[str, Any]]:
    return client.query_all("SELECT Id, AppName, UserId FROM OAuthToken")


def transform(
    apps: list[dict[str, Any]],
    tokens: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    # ponytail: OAuthToken has no ConnectedApplication FK, so join on app name.
    # Rename the connected app or its tokens and the link is lost; acceptable
    # until Salesforce exposes a proper key.
    users_by_app_name: dict[str, set[str]] = defaultdict(set)
    for token in tokens:
        users_by_app_name[token["AppName"]].add(token["UserId"])
    for app in apps:
        app["CreatedDate"] = parse_sf_datetime(app.get("CreatedDate"))
        app["LastModifiedDate"] = parse_sf_datetime(app.get("LastModifiedDate"))
        app["_authorized_user_ids"] = list(users_by_app_name.get(app["Name"], set()))
    return apps


@timeit
def load_connected_apps(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    org_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SalesforceConnectedAppSchema(),
        data,
        lastupdated=update_tag,
        ORG_ID=org_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(
        SalesforceConnectedAppSchema(), common_job_parameters
    ).run(neo4j_session)
