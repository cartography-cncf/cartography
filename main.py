# Used by GCP Functions
# GCP Python API Docs - https://googleapis.github.io/google-api-python-client/docs/dyn/
import base64
import json
import logging
import os

import requests
from requests import Response
from requests.exceptions import RequestException

import cartography.cli
import utils.logger as lgr
from libraries.pubsublibrary import PubSubLibrary
from utils.errors import PubSubPublishError

# Used by GCP Functions


def gcp_cartography_worker(event, ctx):
    logging.getLogger("cartography").setLevel(os.environ.get("CDX_LOG_LEVEL"))
    logging.getLogger("cartography.graph").setLevel(os.environ.get("CDX_LOG_LEVEL"))
    logging.getLogger("cartography.intel").setLevel(os.environ.get("CDX_LOG_LEVEL"))
    logging.getLogger("cartography.sync").setLevel(os.environ.get("CDX_LOG_LEVEL"))
    logging.getLogger("cartography.cartography").setLevel(os.environ.get("CDX_LOG_LEVEL"))
    logging.getLogger("cloudconsolelink.clouds").setLevel(os.environ.get("CDX_LOG_LEVEL"))

    logger = lgr.get_logger("DEBUG")
    logger.info("inventory sync gcp worker request received via PubSub")

    if "data" in event:
        message = base64.b64decode(event["data"]).decode("utf-8")

    else:
        logger.info("invalid message format in PubSub")
        return {
            "status": "failure",
            "message": "unable to parse PubSub message",
        }

    logger.info(f"message from PubSub: {message}")

    try:
        params = json.loads(message)

    except Exception as e:
        logger.error(f"error while parsing request json: {e}")
        return {
            "status": "failure",
            "message": "unable to parse request",
        }

    neo4j_config = params.get("neo4j", {})

    neo4j_config.setdefault("uri", os.environ["CDX_APP_NEO4J_URI"])
    neo4j_config.setdefault("user", os.environ["CDX_APP_NEO4J_USER"])
    neo4j_config.setdefault("pwd", os.environ["CDX_APP_NEO4J_PWD"])
    neo4j_config.setdefault("connection_lifetime", 200)

    # Connect to Data Center Specific database
    request_data_center = params.get("dc", "US")
    if request_data_center == "US":
        neo4j_config["uri"] = os.environ["CDX_APP_NEO4J_URI"]
        neo4j_config["user"] = os.environ["CDX_APP_NEO4J_USER"]
        neo4j_config["pwd"] = os.environ["CDX_APP_NEO4J_PWD"]

    elif request_data_center == "IN":
        neo4j_config["uri"] = os.environ["CDX_IN_APP_NEO4J_URI"]
        neo4j_config["user"] = os.environ["CDX_IN_APP_NEO4J_USER"]
        neo4j_config["pwd"] = os.environ["CDX_IN_APP_NEO4J_PWD"]

    else:
        neo4j_config["uri"] = os.environ["CDX_APP_NEO4J_URI"]
        neo4j_config["user"] = os.environ["CDX_APP_NEO4J_USER"]
        neo4j_config["pwd"] = os.environ["CDX_APP_NEO4J_PWD"]

    params["neo4j"] = neo4j_config

    if params.get("templateType") == "GCPINVENTORYVIEWS":
        gcp_process_request(logger, params)
    elif params.get("templateType") == "GITHUBINVENTORYVIEWS":
        github_process_request(logger, params)
    elif params.get("templateType") == "BITBUCKETINVENTORYVIEWS":
        bitbucket_process_request(logger, params)
    elif params.get("templateType") == "GITLABINVENTORYVIEWS":
        gitlab_process_request(logger, params)
    elif params.get("templateType") == "AZUREDEVOPSINVENTORYVIEWS":
        azure_devops_process_request(logger, params)

    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "status": "success",
            },
        ),
    }


def gcp_process_request(logger, params):
    logger.info(f"request - {params.get('templateType')} - {params.get('eventId')} - {params.get('workspace')}")

    svcs = []
    for svc in params.get("services", []):
        page = svc.get("pagination", {}).get("pageSize")
        if page:
            svc["pagination"]["pageSize"] = 10000

        svcs.append(svc)

    body = {
        "credentials": {
            "account_email": params["accountEmail"],
            "google_workspace_user_email": params.get("workspaceUser"),
            "token_uri": os.environ["CDX_TOKEN_URI"],
        },
        "neo4j": {
            "uri": params.get("neo4j", {}).get("uri", ""),
            "user": params.get("neo4j", {}).get("user", ""),
            "pwd": params.get("neo4j", {}).get("pwd", ""),
            "connection_lifetime": 200,
        },
        "logging": {
            "mode": "verbose",
        },
        "params": {
            "sessionString": params.get("sessionString"),
            "eventId": params.get("eventId"),
            "templateType": params.get("templateType"),
            "workspace": params.get("workspace"),
            "groups": params.get("groups", []),
            "actions": params.get("actions"),
            "resultTopic": params.get("resultTopic"),
            "requestTopic": params.get("requestTopic"),
            "partial": params.get("partial"),
            "services": params.get("services"),
            "iamEntitlementRequestTopic": params.get("iamEntitlementRequestTopic"),
            "externalIdp": params.get("externalIdp"),
        },
        "services": svcs,
        "updateTag": params.get("runTimestamp"),
    }

    resp = cartography.cli.run_gcp(body)

    if "status" in resp and resp["status"] == "success":
        if resp.get("pagination", None):
            services = []
            for service, pagination in resp.get("pagination", {}).items():
                if pagination.get("hasNextPage", False):
                    services.append(
                        {
                            "name": service,
                            "pagination": {
                                "pageSize": pagination.get("pageSize", 1),
                                "pageNo": pagination.get("pageNo", 0) + 1,
                            },
                        },
                    )
            if len(services) > 0:
                resp["services"] = services

            else:
                del resp["updateTag"]

            del resp["pagination"]

        logger.info(f"successfully processed cartography: {resp}")

    else:
        logger.info(f"failed to process cartography: {resp['message']}")

    publish_response(logger, body, resp, params)

    logger.info(f"inventory sync gcp response - {params.get('eventId')}: {json.dumps(resp)}")


def github_process_request(logger, params):
    logger.info(f"request - {params.get('templateType')} - {params.get('eventId')} - {params.get('workspace')}")

    svcs = []
    for svc in params.get("services", []):
        page = svc.get("pagination", {}).get("pageSize")
        if page:
            svc["pagination"]["pageSize"] = 10000

        svcs.append(svc)

    # github_config must be encoded
    # format={"organization":[{"token":"",url="","name":""}]}

    auth = {
        "organization": [
            {
                "token": params.get("token"),
                "url": "https://api.github.com/graphql",
                "name": params.get("workspace", {}).get("account_id"),
            },
        ],
    }

    auth_json = json.dumps(auth)
    github_config = base64.b64encode(auth_json.encode())

    body = {
        "credentials": {},
        "neo4j": {
            "uri": params.get("neo4j", {}).get("uri", ""),
            "user": params.get("neo4j", {}).get("user", ""),
            "pwd": params.get("neo4j", {}).get("pwd", ""),
            "connection_lifetime": 200,
        },
        "logging": {
            "mode": "verbose",
        },
        "github_config": github_config,
        "params": {
            "sessionString": params.get("sessionString"),
            "eventId": params.get("eventId"),
            "templateType": params.get("templateType"),
            "workspace": params.get("workspace"),
            "actions": params.get("actions"),
            "resultTopic": params.get("resultTopic"),
            "requestTopic": params.get("requestTopic"),
            "partial": params.get("partial"),
            "services": params.get("services"),
        },
        "services": svcs,
        "updateTag": params.get("runTimestamp"),
    }

    resp = cartography.cli.run_github(body)

    if "status" in resp and resp["status"] == "success":
        if resp.get("pagination", None):
            services = []
            for service, pagination in resp.get("pagination", {}).items():
                if pagination.get("hasNextPage", False):
                    services.append(
                        {
                            "name": service,
                            "pagination": {
                                "pageSize": pagination.get("pageSize", 1),
                                "pageNo": pagination.get("pageNo", 0) + 1,
                            },
                        },
                    )
            if len(services) > 0:
                resp["services"] = services

            else:
                del resp["updateTag"]

            del resp["pagination"]

        logger.info(f"successfully processed cartography: {resp}")

    else:
        logger.info(f"failed to process cartography: {resp['message']}")

    publish_response(logger, body, resp, params)

    logger.info(f"inventory sync gcp response - {params.get('eventId')}: {json.dumps(resp)}")

    return {"status": "success"}


def azure_devops_process_request(logger, params):
    logger.info(f"request - {params.get('templateType')} - {params.get('eventId')} - {params.get('workspace')}")

    svcs = []
    for svc in params.get("services", []):
        page = svc.get("pagination", {}).get("pageSize")
        if page:
            svc["pagination"]["pageSize"] = 10000

        svcs.append(svc)

    azure_devops_config = {
        "organization": [
            {
                "tenant_id": params.get("workspace", {}).get("tenantId"),
                "client_id": os.environ.get("CDX_AZURE_CLIENT_ID"),
                "client_secret": os.environ.get("CDX_AZURE_CLIENT_SECRET"),
                "url": "https://dev.azure.com",
                "name": params.get("workspace", {}).get("account_id"),
            },
        ],
    }

    body = {
        "neo4j": {
            "uri": params.get("neo4j", {}).get("uri", ""),
            "user": params.get("neo4j", {}).get("user", ""),
            "pwd": params.get("neo4j", {}).get("pwd", ""),
            "connection_lifetime": 200,
        },
        "logging": {
            "mode": "verbose",
        },
        "azure_devops_config": azure_devops_config,
        "params": {
            "sessionString": params.get("sessionString"),
            "eventId": params.get("eventId"),
            "templateType": params.get("templateType"),
            "workspace": params.get("workspace"),
            "actions": params.get("actions"),
            "resultTopic": params.get("resultTopic"),
            "requestTopic": params.get("requestTopic"),
            "partial": params.get("partial"),
            "services": params.get("services"),
        },
        "services": svcs,
        "updateTag": params.get("runTimestamp"),
    }

    resp = cartography.cli.run_azure_devops(body)

    if "status" in resp and resp["status"] == "success":
        if resp.get("pagination", None):
            services = []
            for service, pagination in resp.get("pagination", {}).items():
                if pagination.get("hasNextPage", False):
                    services.append(
                        {
                            "name": service,
                            "pagination": {
                                "pageSize": pagination.get("pageSize", 1),
                                "pageNo": pagination.get("pageNo", 0) + 1,
                            },
                        },
                    )
            if len(services) > 0:
                resp["services"] = services

            else:
                del resp["updateTag"]

            del resp["pagination"]

        logger.info(f"successfully processed cartography: {resp}")

    else:
        logger.info(f"failed to process cartography: {resp['message']}")

    publish_response(logger, body, resp, params)

    logger.info(f"inventory sync gcp response - {params.get('eventId')}: {json.dumps(resp)}")

    return {"status": "success"}


def bitbucket_process_request(logger, params):
    logger.info(f"request - {params.get('templateType')} - {params.get('eventId')} - {params.get('workspace')}")

    svcs = []
    for svc in params.get("services", []):
        page = svc.get("pagination", {}).get("pageSize")
        if page:
            svc["pagination"]["pageSize"] = 10000

        svcs.append(svc)

    body = {
        "credentials": {},
        "neo4j": {
            "uri": params.get("neo4j", {}).get("uri", ""),
            "user": params.get("neo4j", {}).get("user", ""),
            "pwd": params.get("neo4j", {}).get("pwd", ""),
            "connection_lifetime": 200,
        },
        "logging": {
            "mode": "verbose",
        },
        "bitbucket": {
            "client_id": os.environ["CDX_BITBUCKET_CLIENT_ID"],
            "client_secret": os.environ["CDX_BITBUCKET_CLIENT_SECRET"],
            "refresh_token": params.get("refreshToken"),
            # Prefer workspace access token (no OAuth refresh needed).
            # Falls back to OAuth refresh token flow for legacy sources.
            "access_token": params.get("workspaceAccessToken") or get_bitbucket_access_token(
                logger,
                os.environ["CDX_BITBUCKET_CLIENT_ID"],
                os.environ["CDX_BITBUCKET_CLIENT_SECRET"],
                params.get("refreshToken"),
            ),
        },
        "params": {
            "sessionString": params.get("sessionString"),
            "eventId": params.get("eventId"),
            "templateType": params.get("templateType"),
            "workspace": params.get("workspace"),
            "actions": params.get("actions"),
            "resultTopic": params.get("resultTopic"),
            "requestTopic": params.get("requestTopic"),
            "partial": params.get("partial"),
            "services": params.get("services"),
        },
        "services": svcs,
        "updateTag": params.get("runTimestamp"),
    }

    resp = cartography.cli.run_bitbucket(body)

    if "status" in resp and resp["status"] == "success":
        if resp.get("pagination", None):
            services = []
            for service, pagination in resp.get("pagination", {}).items():
                if pagination.get("hasNextPage", False):
                    services.append(
                        {
                            "name": service,
                            "pagination": {
                                "pageSize": pagination.get("pageSize", 1),
                                "pageNo": pagination.get("pageNo", 0) + 1,
                            },
                        },
                    )
            if len(services) > 0:
                resp["services"] = services

            else:
                del resp["updateTag"]

            del resp["pagination"]

        logger.info(f"successfully processed cartography: {resp}")

    else:
        logger.info(f"failed to process cartography: {resp['message']}")

    publish_response(logger, body, resp, params)

    logger.info(f"inventory sync gcp response - {params.get('eventId')}: {json.dumps(resp)}")

    return {"status": "success"}


def gitlab_process_request(logger, params):
    logger.info(
        "gitlab request received",
        extra={
            "template_type": params.get("templateType"),
            "event_id": params.get("eventId"),
            "workspace": params.get("workspace"),
        },
    )

    svcs = []
    for svc in params.get("services", []):
        page = svc.get("pagination", {}).get("pageSize")
        if page:
            svc["pagination"]["pageSize"] = 10000

        svcs.append(svc)

    GITLAB_CLOUD_DOMAIN = "https://gitlab.com"

    body = {
        "credentials": {},
        "neo4j": {
            "uri": params.get("neo4j", {}).get("uri", ""),
            "user": params.get("neo4j", {}).get("user", ""),
            "pwd": params.get("neo4j", {}).get("pwd", ""),
            "connection_lifetime": 200,
        },
        "logging": {
            "mode": "verbose",
        },
        "gitlab": {
            "access_token": params.get("accessToken"),
            "hosted_domain": params.get("headers", {}).get("X-Cloudanix-Gitlab-Hosted-Domain", GITLAB_CLOUD_DOMAIN),
        },
        "params": {
            "sessionString": params.get("sessionString"),
            "eventId": params.get("eventId"),
            "templateType": params.get("templateType"),
            "workspace": params.get("workspace"),
            "actions": params.get("actions"),
            "resultTopic": params.get("resultTopic"),
            "requestTopic": params.get("requestTopic"),
            "partial": params.get("partial"),
            "services": params.get("services"),
        },
        "services": svcs,
        "updateTag": params.get("runTimestamp"),
    }

    resp = cartography.cli.run_gitlab(body)

    if "status" in resp and resp["status"] == "success":
        if resp.get("pagination", None):
            services = []
            for service, pagination in resp.get("pagination", {}).items():
                if pagination.get("hasNextPage", False):
                    services.append(
                        {
                            "name": service,
                            "pagination": {
                                "pageSize": pagination.get("pageSize", 1),
                                "pageNo": pagination.get("pageNo", 0) + 1,
                            },
                        },
                    )
            if len(services) > 0:
                resp["services"] = services
            else:
                del resp["updateTag"]
            del resp["pagination"]

        logger.info(f"successfully processed cartography: {resp}")

    else:
        logger.info(f"failed to process cartography: {resp['message']}")

    publish_response(logger, body, resp, params)

    logger.info(f"inventory sync gcp response - {params.get('eventId')}: {json.dumps(resp)}")

    return {"status": "success"}


def get_bitbucket_access_token(logger, client_id: str, client_secret: str, refresh_token: str):
    try:
        TOKEN_URL = "https://bitbucket.org/site/oauth2/access_token"
        token_req_payload = {"grant_type": "refresh_token", "refresh_token": refresh_token}
        response: Response = requests.post(
            TOKEN_URL,
            data=token_req_payload,
            allow_redirects=False,
            auth=(client_id, client_secret),
        )
        if response.status_code == requests.codes["ok"]:
            output: dict = response.json()
            return output.get("access_token")

        return None

    except RequestException as e:
        logger.info(f"getting error access token{e}")
        return None


def publish_response(logger, body, resp, params):
    payload = {
        "status": resp["status"],
        "params": body["params"],
        "accountEmail": body.get("credentials", {}).get("account_email"),
        "sessionString": body.get("params", {}).get("sessionString"),
        "eventId": body.get("params", {}).get("eventId"),
        "templateType": body.get("params", {}).get("templateType"),
        "workspace": body.get("params", {}).get("workspace"),
        "actions": body.get("params", {}).get("actions"),
        "resultTopic": body.get("params", {}).get("resultTopic"),
        "requestTopic": body.get("params", {}).get("requestTopic"),
        "partial": body.get("params", {}).get("partial"),
        "iamEntitlementRequestTopic": body.get("params", {}).get("iamEntitlementRequestTopic"),
        "response": resp,
        "services": body.get("params", {}).get("services", []),
        "runTimestamp": resp.get("updateTag", None),
    }

    pubsub_helper = PubSubLibrary()

    status = None
    try:
        # If cartography processing response object contains `services` object that means pagination is in progress. push the message back to the same queue for continuation.
        if resp.get("services", None):
            if body.get("params", {}).get("requestTopic"):
                # Result should be pushed to "requestTopic" passed in the request
                status = pubsub_helper.publish(
                    os.environ["CDX_PROJECT_ID"],
                    json.dumps(payload),
                    body.get("params", {}).get("requestTopic"),
                )

        elif body.get("params", {}).get("resultTopic"):
            if body.get("params", {}).get("partial"):
                # In case of a partial request processing, result should be pushed to "resultTopic" passed in the request
                status = pubsub_helper.publish(
                    os.environ["CDX_PROJECT_ID"],
                    json.dumps(payload),
                    body.get("params", {}).get("resultTopic"),
                )

            else:
                logger.info("Result not published anywhere. since we want to avoid query when inventory is refreshed")

            status = True

            if body.get("params", {}).get("iamEntitlementRequestTopic"):
                status = pubsub_helper.publish(
                    os.environ["CDX_PROJECT_ID"],
                    json.dumps(params),
                    body.get("params", {}).get("iamEntitlementRequestTopic"),
                )

        else:
            logger.info("publishing results to CDX_CARTOGRAPHY_RESULT_TOPIC")
            status = pubsub_helper.publish(
                os.environ["CDX_PROJECT_ID"],
                json.dumps(payload),
                os.environ["CDX_CARTOGRAPHY_RESULT_TOPIC"],
            )

            if body.get("params", {}).get("iamEntitlementRequestTopic"):
                status = pubsub_helper.publish(
                    os.environ["CDX_PROJECT_ID"],
                    json.dumps(params),
                    body.get("params", {}).get("iamEntitlementRequestTopic"),
                )

        logger.info(f"result published to PubSub with status: {status}")

    except PubSubPublishError as e:
        logger.error(f"Failed while publishing response to PubSub: {str(e)}")
