import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j
from googleapiclient.discovery import HttpError
from googleapiclient.discovery import Resource

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.gcp.util import classify_gcp_http_error
from cartography.intel.gcp.util import gcp_api_execute_with_retry
from cartography.intel.gcp.util import is_permission_denied_error
from cartography.intel.gcp.util import summarize_gcp_http_error
from cartography.models.gcp.api_gateway import GCPApiGatewayApiConfigSchema
from cartography.models.gcp.api_gateway import GCPApiGatewayApiSchema
from cartography.models.gcp.api_gateway import GCPApiGatewayGatewaySchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


def _handle_project_scoped_error(
    e: HttpError, project_id: str, what: str
) -> tuple[List[Dict], bool]:
    """
    Shared error triage for the three API Gateway list calls. Returns an empty
    list plus an incomplete flag for the recoverable cases, and re-raises
    anything else. Callers must suppress cleanup when incomplete is True,
    otherwise a transient failure deletes inventory that still exists.
    """
    category = classify_gcp_http_error(e)
    if category == "invalid":
        logger.warning(
            "The project %s is invalid - returned a 400 invalid error. %s",
            project_id,
            summarize_gcp_http_error(e),
        )
    elif is_permission_denied_error(e):
        logger.warning(
            "You do not have apigateway %s list access to the project %s. %s",
            what,
            project_id,
            summarize_gcp_http_error(e),
        )
    elif category == "billing_disabled":
        logger.warning(
            "Billing is disabled for project %s. Skipping API Gateway %s sync. %s",
            project_id,
            what,
            summarize_gcp_http_error(e),
        )
    elif category == "api_disabled":
        logger.info(
            "API Gateway API appears disabled for project %s. Skipping %s sync. %s",
            project_id,
            what,
            summarize_gcp_http_error(e),
        )
    else:
        raise e
    return [], True


@timeit
def get_apis(apigateway: Resource, project_id: str) -> tuple[List[Dict], bool]:
    """
    Get all API Gateway Apis for a project. Apis are global, so they live under
    the "global" location.
    """
    try:
        apis: List[Dict] = []
        incomplete = False
        parent = f"projects/{project_id}/locations/global"
        req = apigateway.projects().locations().apis().list(parent=parent)
        while req is not None:
            res = gcp_api_execute_with_retry(req)
            apis.extend(res.get("apis", []))
            # A location the API could not reach means the listing is partial.
            incomplete = incomplete or bool(res.get("unreachableLocations"))
            req = (
                apigateway.projects()
                .locations()
                .apis()
                .list_next(previous_request=req, previous_response=res)
            )
        if incomplete:
            logger.warning(
                "GCP: apigateway apis.list for project %s reported unreachable "
                "locations; keeping partial data and suppressing cleanup.",
                project_id,
            )
        return apis, incomplete
    except HttpError as e:
        return _handle_project_scoped_error(e, project_id, "apis")


@timeit
def get_api_configs(
    apigateway: Resource, project_id: str, api_names: List[str]
) -> tuple[List[Dict], bool]:
    """
    Get all ApiConfigs for the given Apis.

    configs.list has no `view` parameter and never returns openapiDocuments, so
    each config is re-fetched with view=FULL to pick up the attached document.
    That makes this N+1 by design: one list per Api plus one get per config.
    """
    configs: List[Dict] = []
    incomplete = False
    for api_name in api_names:
        try:
            listed: List[Dict] = []
            req = (
                apigateway.projects().locations().apis().configs().list(parent=api_name)
            )
            while req is not None:
                res = gcp_api_execute_with_retry(req)
                listed.extend(res.get("apiConfigs", []))
                incomplete = incomplete or bool(res.get("unreachableLocations"))
                req = (
                    apigateway.projects()
                    .locations()
                    .apis()
                    .configs()
                    .list_next(previous_request=req, previous_response=res)
                )
        except HttpError as e:
            _handle_project_scoped_error(e, project_id, "api configs")
            # This Api's configs are missing from the result set, so cleanup
            # would delete config nodes that still exist upstream.
            incomplete = True
            continue

        for config in listed:
            try:
                full = gcp_api_execute_with_retry(
                    apigateway.projects()
                    .locations()
                    .apis()
                    .configs()
                    .get(name=config["name"], view="FULL")
                )
                configs.append(full)
            except HttpError as e:
                if is_permission_denied_error(e):
                    logger.warning(
                        "No apigateway.apiconfigs.get access to %s, "
                        "falling back to the list view without the OpenAPI document. %s",
                        config["name"],
                        summarize_gcp_http_error(e),
                    )
                    configs.append(config)
                else:
                    raise
    return configs, incomplete


@timeit
def get_gateways(apigateway: Resource, project_id: str) -> tuple[List[Dict], bool]:
    """
    Get all Gateways for a project. Gateways are regional; "-" enumerates every
    location in one call.
    """
    try:
        gateways: List[Dict] = []
        incomplete = False
        parent = f"projects/{project_id}/locations/-"
        req = apigateway.projects().locations().gateways().list(parent=parent)
        while req is not None:
            res = gcp_api_execute_with_retry(req)
            gateways.extend(res.get("gateways", []))
            incomplete = incomplete or bool(res.get("unreachableLocations"))
            req = (
                apigateway.projects()
                .locations()
                .gateways()
                .list_next(previous_request=req, previous_response=res)
            )
        if incomplete:
            logger.warning(
                "GCP: apigateway gateways.list for project %s reported unreachable "
                "locations; keeping partial data and suppressing cleanup.",
                project_id,
            )
        return gateways, incomplete
    except HttpError as e:
        return _handle_project_scoped_error(e, project_id, "gateways")


def transform_apis(apis: List[Dict]) -> List[Dict[str, Any]]:
    return [
        {
            "id": api["name"],
            "name": api["name"],
            "displayName": api.get("displayName"),
            "managedService": api.get("managedService"),
            "state": api.get("state"),
            "createTime": api.get("createTime"),
            "updateTime": api.get("updateTime"),
        }
        for api in apis
    ]


def transform_api_configs(configs: List[Dict]) -> List[Dict[str, Any]]:
    transformed = []
    for config in configs:
        docs = config.get("openapiDocuments") or []
        first_doc = docs[0].get("document", {}) if docs else {}
        transformed.append(
            {
                "id": config["name"],
                "name": config["name"],
                # projects/*/locations/global/apis/<api>/configs/<config>
                "apiId": config["name"].rsplit("/configs/", 1)[0],
                "displayName": config.get("displayName"),
                "state": config.get("state"),
                "serviceConfigId": config.get("serviceConfigId"),
                "gatewayServiceAccount": config.get("gatewayServiceAccount"),
                "hasOpenapiDocument": bool(docs),
                "openapiDocumentPath": first_doc.get("path"),
                "createTime": config.get("createTime"),
                "updateTime": config.get("updateTime"),
            }
        )
    return transformed


def transform_gateways(gateways: List[Dict]) -> List[Dict[str, Any]]:
    return [
        {
            "id": gw["name"],
            "name": gw["name"],
            # projects/<p>/locations/<region>/gateways/<gw>
            "region": gw["name"].split("/")[3],
            "displayName": gw.get("displayName"),
            "state": gw.get("state"),
            "defaultHostname": gw.get("defaultHostname"),
            "apiConfig": gw.get("apiConfig"),
            "createTime": gw.get("createTime"),
            "updateTime": gw.get("updateTime"),
        }
        for gw in gateways
    ]


@timeit
def load_apis(
    neo4j_session: neo4j.Session,
    apis: List[Dict],
    project_id: str,
    gcp_update_tag: int,
) -> None:
    load(
        neo4j_session,
        GCPApiGatewayApiSchema(),
        apis,
        lastupdated=gcp_update_tag,
        PROJECT_ID=project_id,
    )


@timeit
def load_api_configs(
    neo4j_session: neo4j.Session,
    configs: List[Dict],
    project_id: str,
    gcp_update_tag: int,
) -> None:
    load(
        neo4j_session,
        GCPApiGatewayApiConfigSchema(),
        configs,
        lastupdated=gcp_update_tag,
        PROJECT_ID=project_id,
    )


@timeit
def load_gateways(
    neo4j_session: neo4j.Session,
    gateways: List[Dict],
    project_id: str,
    gcp_update_tag: int,
) -> None:
    load(
        neo4j_session,
        GCPApiGatewayGatewaySchema(),
        gateways,
        lastupdated=gcp_update_tag,
        PROJECT_ID=project_id,
    )


@timeit
def cleanup_api_gateway(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict,
) -> None:
    logger.debug("Running GCP API Gateway cleanup job.")
    # Gateways first, then configs, then apis: cleanup follows the reverse of the
    # dependency order so relationships are removed before their targets.
    for schema in (
        GCPApiGatewayGatewaySchema(),
        GCPApiGatewayApiConfigSchema(),
        GCPApiGatewayApiSchema(),
    ):
        GraphJob.from_node_schema(schema, common_job_parameters).run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    apigateway: Resource,
    project_id: str,
    gcp_update_tag: int,
    common_job_parameters: Dict,
) -> None:
    """
    Sync GCP API Gateway (apigateway.googleapis.com) for a project.
    """
    logger.info("Syncing API Gateway for project %s.", project_id)

    apis, apis_incomplete = get_apis(apigateway, project_id)
    load_apis(neo4j_session, transform_apis(apis), project_id, gcp_update_tag)

    configs, configs_incomplete = get_api_configs(
        apigateway, project_id, [api["name"] for api in apis]
    )
    load_api_configs(
        neo4j_session, transform_api_configs(configs), project_id, gcp_update_tag
    )

    gateways, gateways_incomplete = get_gateways(apigateway, project_id)
    load_gateways(
        neo4j_session, transform_gateways(gateways), project_id, gcp_update_tag
    )

    # Cleanup deletes anything not touched by this run, so it is only safe when
    # every listing was complete. A partial result plus cleanup silently removes
    # inventory that still exists.
    if apis_incomplete or configs_incomplete or gateways_incomplete:
        logger.warning(
            "Skipping GCP API Gateway cleanup for project %s: at least one "
            "listing was incomplete.",
            project_id,
        )
        return
    cleanup_api_gateway(neo4j_session, common_job_parameters)
