# Used by AWS Lambda & EKS
import json
import logging
import os
import threading
import time
import uuid
from threading import Thread

from neo4j.exceptions import Neo4jError

import cartography.cli
from libraries.authlibrary import AuthLibrary
from libraries.snslibrary import SNSLibrary
from libraries.sqslibrary import SQSLibrary
from utils.context import AppContext
from utils.logger import get_logger

app_init = None
context = None


def current_config(env):
    return "config/production.json" if env == "PRODUCTION" else "config/default.json"


def set_assume_role_keys(context):
    context.assume_role_access_key_key_id = context.assume_role_access_secret_key_id = (
        os.environ["CDX_APP_ASSUME_ROLE_KMS_KEY_ID"]
    )
    context.assume_role_access_key_cipher = os.environ["CDX_APP_ASSUME_ROLE_ACCESS_KEY"]
    context.assume_role_access_secret_cipher = os.environ[
        "CDX_APP_ASSUME_ROLE_ACCESS_SECRET"
    ]
    context.neo4j_uri = os.environ["CDX_APP_NEO4J_URI"]
    context.neo4j_user = os.environ["CDX_APP_NEO4J_USER"]
    context.neo4j_pwd = os.environ["CDX_APP_NEO4J_PWD"]
    context.neo4j_connection_lifetime = 200


def init_app(ctx):
    global app_init, context

    context = AppContext(
        region=os.environ["CDX_DEFAULT_REGION"],
        log_level=os.environ["CDX_LOG_LEVEL"],
        app_env=os.environ["CDX_APP_ENV"],
    )
    context.logger = get_logger(context.log_level)

    decrypted_value = ""

    # Read from config files in the project
    with open(current_config(context.app_env)) as f:
        decrypted_value = f.read()

    # Cloudanix AWS AccountID
    if ctx:
        context.aws_account_id = ctx.invoked_function_arn.split(":")[4]

    context.parse(decrypted_value)

    set_assume_role_keys(context)

    app_init = True


def process_request(context, args, retry=0):
    try:
        context.logger.info(
            f"request - {args.get('templateType')} - {args.get('sessionString')} - {args.get('eventId')} - {args.get('workspace')}",
        )

        svcs = []
        for svc in args.get("services", []):
            page = svc.get("pagination", {}).get("pageSize")
            if page:
                svc["pagination"]["pageSize"] = 10000

            svcs.append(svc)

        # Connect to Data Center Specific database
        request_data_center = args.get("dc", "US")
        if request_data_center == "US":
            context.neo4j_uri = os.environ["CDX_APP_NEO4J_URI"]
            context.neo4j_user = os.environ["CDX_APP_NEO4J_USER"]
            context.neo4j_pwd = os.environ["CDX_APP_NEO4J_PWD"]

        elif request_data_center == "IN":
            context.neo4j_uri = os.environ["CDX_IN_APP_NEO4J_URI"]
            context.neo4j_user = os.environ["CDX_IN_APP_NEO4J_USER"]
            context.neo4j_pwd = os.environ["CDX_IN_APP_NEO4J_PWD"]

        else:
            context.neo4j_uri = os.environ["CDX_APP_NEO4J_URI"]
            context.neo4j_user = os.environ["CDX_APP_NEO4J_USER"]
            context.neo4j_pwd = os.environ["CDX_APP_NEO4J_PWD"]

        if args.get("templateType") == "AWSINVENTORYVIEWS":
            creds = None
            try:
                creds = get_auth_creds(context, args)

            except Exception as e:
                context.logger.error(
                    f"error while getting auth creds: {e}",
                    exc_info=True,
                    stack_info=True,
                    extra={"context": args},
                )

                sns_helper = SNSLibrary(context)
                if args.get("params", {}).get("resultTopic"):
                    payload = {
                        "status": "failure",
                        "params": args.get("params"),
                        "sessionString": args.get("sessionString"),
                        "eventId": args.get("eventId"),
                        "templateType": args.get("templateType"),
                        "workspace": args.get("workspace"),
                        "actions": args.get("actions"),
                        "resultTopic": args.get("resultTopic"),
                        "requestTopic": args.get("requestTopic"),
                        "identityStoreIdentifier": args.get("identityStoreIdentifier"),
                        "partial": args.get("partial", False),
                        "manualRun": args.get("manualRun", False),
                        "inventoryReturn": args.get("inventoryReturn", False),
                        "services": args.get("services"),
                        "dc": args.get("dc"),
                        "error": str(e),
                    }
                    status = sns_helper.publish(
                        json.dumps(payload), args["params"]["resultTopic"],
                    )
                    context.logger.debug(
                        f"result published to SNS with status: {status}",
                    )

                return

            body = {
                "credentials": creds,
                "neo4j": {
                    "uri": context.neo4j_uri,
                    "user": context.neo4j_user,
                    "pwd": context.neo4j_pwd,
                    "connection_lifetime": int(context.neo4j_connection_lifetime),
                },
                "logging": {
                    "mode": "verbose",
                },
                "params": {
                    "sessionString": args.get("sessionString"),
                    "eventId": args.get("eventId"),
                    "templateType": args.get("templateType"),
                    "regions": args.get("regions"),
                    "workspace": args.get("workspace"),
                    "actions": args.get("actions"),
                    "resultTopic": args.get("resultTopic"),
                    "requestTopic": args.get("requestTopic"),
                    "iamEntitlementRequestTopic": args.get(
                        "iamEntitlementRequestTopic",
                    ),
                    "identityStoreIdentifier": args.get("identityStoreIdentifier"),
                    "partial": args.get("partial", False),
                    "manualRun": args.get("manualRun", False),
                    "inventoryReturn": args.get("inventoryReturn", False),
                    "services": args.get("services"),
                    "dc": args.get("dc"),
                    "defaultRegion": args.get("primaryRegion", None),
                },
                "services": svcs,
                "updateTag": args.get("runTimestamp"),
                "refreshEntitlements": args.get("refreshEntitlements"),
                "identityStoreRegion": args.get("identityStoreRegion"),
                "awsInternalAccounts": args.get("awsInternalAccounts"),
            }

            resp = cartography.cli.run_aws(body)

        elif args.get("templateType") == "AZUREINVENTORYVIEWS":
            body = {
                "azure": {
                    "client_id": os.environ.get("CDX_AZURE_CLIENT_ID"),
                    "client_secret": os.environ.get("CDX_AZURE_CLIENT_SECRET"),
                    "redirect_uri": os.environ.get("CDX_AZURE_REDIRECT_URI"),
                    "subscription_id": args.get("workspace", {}).get("account_id"),
                    "tenant_id": args.get("tenantId"),
                    "refresh_token": args.get("refreshToken"),
                    "graph_scope": os.environ.get("CDX_AZURE_GRAPH_SCOPE"),
                    "azure_scope": os.environ.get("CDX_AZURE_AZURE_SCOPE"),
                    "default_graph_scope": os.environ.get(
                        "CDX_AZURE_DEFAULT_GRAPH_SCOPE",
                    ),
                    "vault_scope": os.environ.get("CDX_AZURE_KEY_VAULT_SCOPE"),
                },
                "neo4j": {
                    "uri": context.neo4j_uri,
                    "user": context.neo4j_user,
                    "pwd": context.neo4j_pwd,
                    "connection_lifetime": 200,
                },
                "logging": {
                    "mode": "verbose",
                },
                "params": {
                    "sessionString": args.get("sessionString"),
                    "eventId": args.get("eventId"),
                    "templateType": args.get("templateType"),
                    "workspace": args.get("workspace"),
                    "groups": args.get("groups"),
                    "subscriptions": args.get("subscriptions"),
                    "actions": args.get("actions"),
                    "resultTopic": args.get("resultTopic"),
                    "requestTopic": args.get("requestTopic"),
                    "partial": args.get("partial"),
                    "manualRun": args.get("manualRun"),
                    "services": args.get("services"),
                    "defaultSubscription": args.get("defaultSubscription"),
                    "authMode": args.get("headers", {}).get(
                        "x-cloudanix-azure-auth-mode", "user_impersonation",
                    ),
                },
                "services": svcs,
                "updateTag": args.get("runTimestamp"),
            }

            resp = cartography.cli.run_azure(body)

        if resp.get("status", "") == "success":
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

            context.logger.debug(f"successfully processed cartography: {resp}")

        else:
            context.logger.info(f"failed to process cartography: {resp['message']}")

        publish_response(context, body, resp, args)

        context.logger.debug(
            f"inventory sync aws response - {args['eventId']}: {json.dumps(resp)}",
        )
    except Neo4jError as e:
        context.logger.error(
            f"Neo4j Error. Retry - {retry} ",
            extra={
                "error": str(e),
                "message": args,
            },
        )
        retry += 1
        if retry < 2:
            time.sleep(60)
            process_request(context, args, retry)


def publish_response(context, body, resp, args):
    if context.app_env != "PRODUCTION":
        try:
            with open("response.json", "w") as outfile:
                json.dump(resp, outfile, indent=2)

        except Exception as e:
            context.logger.error(f"Failed to write to file: {e}")

    else:
        template_type = body.get("params", {}).get("templateType", "")

        if template_type == "AWSINVENTORYVIEWS":
            # AWS-specific payload
            payload = {
                "status": resp["status"],
                "params": body["params"],
                "sessionString": body.get("params", {}).get("sessionString"),
                "eventId": body.get("params", {}).get("eventId"),
                "templateType": body.get("params", {}).get("templateType"),
                "workspace": body.get("params", {}).get("workspace"),
                "actions": body.get("params", {}).get("actions"),
                "resultTopic": body.get("params", {}).get("resultTopic"),
                "requestTopic": body.get("params", {}).get("requestTopic"),
                "identityStoreIdentifier": body.get("params", {}).get(
                    "identityStoreIdentifier",
                ),
                "partial": body.get("params", {}).get("partial"),
                "manualRun": body.get("params", {}).get("manualRun"),
                "externalRoleArn": body.get("externalRoleArn"),
                "externalId": body.get("externalId"),
                "response": resp,
                "services": body.get("params", {}).get("services"),
                "runTimestamp": resp.get("updateTag", None),
                "iamEntitlementRequestTopic": body.get("params", {}).get(
                    "iamEntitlementRequestTopic",
                ),
                "dc": args.get("dc"),
            }

        elif template_type == "AZUREINVENTORYVIEWS":
            payload = {
                "status": resp["status"],
                "params": body["params"],
                "sessionString": body.get("params", {}).get("sessionString"),
                "eventId": body.get("params", {}).get("eventId"),
                "templateType": body.get("params", {}).get("templateType"),
                "workspace": body.get("params", {}).get("workspace"),
                "actions": body.get("params", {}).get("actions"),
                "resultTopic": body.get("params", {}).get("resultTopic"),
                "requestTopic": body.get("params", {}).get("requestTopic"),
                "subscriptions": body.get("params", {}).get("subscriptions"),
                "partial": body.get("params", {}).get("partial"),
                "manualRun": body.get("params", {}).get("manualRun"),
                "response": resp,
                "services": body.get("params", {}).get("services"),
                "runTimestamp": resp.get("updateTag", None),
                "tenantId": body.get("azure", {}).get("tenant_id"),
                "dc": args.get("dc"),
            }

        sns_helper = SNSLibrary(context)
        # If cartography processing response object contains `services` object that means pagination is in progress. push the message back to the same queue for continuation.
        if resp.get("services", None):
            if body.get("params", {}).get("requestTopic"):
                status = sns_helper.publish(
                    json.dumps(payload), body["params"]["requestTopic"],
                )

        elif body.get("params", {}).get("resultTopic"):
            if body.get("params", {}).get("partial") or body.get("params", {}).get(
                "inventoryReturn",
            ):
                # In case of a partial request processing, result should be pushed to "resultTopic" passed in the request
                status = sns_helper.publish(
                    json.dumps(payload), body["params"]["resultTopic"],
                )

            else:
                context.logger.info(
                    "Result not published anywhere. since we want to avoid query when inventory is refreshed",
                )

            status = True
            if template_type == "AWSINVENTORYVIEWS":
                publish_request_iam_entitlement(context, args, body)

        else:
            context.logger.debug("publishing results to CDX_CARTOGRAPHY_RESULT_TOPIC")
            status = sns_helper.publish(
                json.dumps(payload), context.aws_inventory_sync_response_topic,
            )
            if template_type == "AWSINVENTORYVIEWS":
                publish_request_iam_entitlement(context, args, body)

        context.logger.debug(f"result published to SNS with status: {status}")


def publish_request_iam_entitlement(context, req, body):
    if req.get("iamEntitlementRequestTopic"):
        sns_helper = SNSLibrary(context)

        # remove expiration (datetime field) attribute from resp
        if body.get("credentials", {}).get("expiration"):
            del body["credentials"]["expiration"]

        req["credentials"] = get_auth_creds(context, req)

        # remove expiration (datetime field) attribute from resp
        if req.get("credentials", {}).get("expiration"):
            del req["credentials"]["expiration"]

        if req.get("loggingAccount"):
            req["loggingAccount"] = get_logging_account_auth_creds(context, req)

            # remove expiration (datetime field) attribute from loggingAccount creds
            if req.get("loggingAccount", {}).get("creds", {}).get("expiration"):
                del req["loggingAccount"]["creds"]["expiration"]

        context.logger.debug("publishing results to IAM_ENTITLEMENT_REQUEST_TOPIC")
        status = sns_helper.publish(json.dumps(req), req["iamEntitlementRequestTopic"])
        context.logger.debug(f"result published to SNS with status: {status}")


def get_auth_creds(context, args):
    auth_helper = AuthLibrary(context)

    if context.app_env == "PRODUCTION" or context.app_env == "DEBUG":
        auth_params = {
            "aws_access_key_id": auth_helper.get_assume_role_access_key(),
            "aws_secret_access_key": auth_helper.get_assume_role_access_secret(),
            "role_session_name": args.get("sessionString"),
            "role_arn": args.get("externalRoleArn"),
            "external_id": args.get("externalId"),
        }

        auth_creds = auth_helper.assume_role(auth_params)
        auth_creds["type"] = "assumerole"
        auth_creds["primary_region"] = args.get("primaryRegion", "us-east-1")

    else:
        auth_creds = {
            "type": "self",
            "aws_access_key_id": args.get("credentials", {}).get("awsAccessKeyID")
            if "credentials" in args
            else None,
            "aws_secret_access_key": args.get("credentials", {}).get(
                "awsSecretAccessKey",
            )
            if "credentials" in args
            else None,
        }

    return auth_creds


def get_logging_account_auth_creds(context, args):
    auth_helper = AuthLibrary(context)
    aws_access_key_id = auth_helper.get_assume_role_access_key()
    aws_secret_access_key = auth_helper.get_assume_role_access_secret()
    logging_account = args.get("loggingAccount", {})

    if context.app_env == "PRODUCTION" or context.app_env == "DEBUG":
        auth_params = {
            "aws_access_key_id": aws_access_key_id,
            "aws_secret_access_key": aws_secret_access_key,
            "role_session_name": str(uuid.uuid4()),
            "role_arn": logging_account.get("externalRoleArn"),
            "external_id": logging_account.get("externalId"),
        }

        auth_creds = auth_helper.assume_role(auth_params)
        auth_creds["type"] = "assumerole"
        auth_creds["primary_region"] = args.get("primaryRegion", "us-east-1")

    else:
        auth_creds = {
            "type": "self",
            "aws_access_key_id": args.get("credentials", {}).get("awsAccessKeyID")
            if "credentials" in args
            else None,
            "aws_secret_access_key": args.get("credentials", {}).get(
                "awsSecretAccessKey",
            )
            if "credentials" in args
            else None,
        }

    args["loggingAccount"]["creds"] = auth_creds

    return args.get("loggingAccount", {})


def aws_process_cartography(event, ctx):
    global app_init, context
    if not app_init:
        init_app(ctx)

    logging.getLogger("cartography").setLevel(os.environ.get("CDX_LOG_LEVEL"))
    logging.getLogger("cartography.graph").setLevel(os.environ.get("CDX_LOG_LEVEL"))
    logging.getLogger("cartography.intel").setLevel(os.environ.get("CDX_LOG_LEVEL"))
    logging.getLogger("cartography.sync").setLevel(os.environ.get("CDX_LOG_LEVEL"))
    logging.getLogger("cartography.cartography").setLevel(
        os.environ.get("CDX_LOG_LEVEL"),
    )
    logging.getLogger("cloudconsolelink.clouds").setLevel(
        os.environ.get("CDX_LOG_LEVEL"),
    )

    record = event["Records"][0]
    message = record["Sns"]["Message"]

    try:
        params = json.loads(message)

    except Exception as e:
        context.logger.error(
            f"error while parsing inventory sync aws request json: {e}",
            exc_info=True,
            stack_info=True,
        )

        response = {
            "status": "failure",
            "message": "unable to parse request",
        }

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
            },
            "body": json.dumps(response),
        }

    context.logger.debug(f"message: {json.dumps(params)}")

    process_request(context, params)

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
        },
        "body": json.dumps(
            {
                "status": "success",
            },
        ),
    }


def extend_visibility_timeout(message, receipt_handle, timeout_duration, stop_event):
    max_runtime_minutes = 295
    start_time = time.time()
    max_runtime_seconds = max_runtime_minutes * 60
    try:
        sqs_library = SQSLibrary(context)
        while not stop_event.is_set():
            # Wait until 10 seconds before the visibility timeout expires, or until stop_event is set
            stop_event.wait(timeout_duration - 10)

            # Check if maximum runtime has been reached
            elapsed_time = time.time() - start_time
            if elapsed_time >= max_runtime_seconds:
                status = sqs_library.delete_message(receipt_handle)
                if status:
                    context.logger.warning(
                        f"Maximum runtime has been reached. Deleted message from queue - {json.loads(message['Body'])}",
                        extra={
                            "message": message["Body"],
                            "handle": receipt_handle,
                            "status": status,
                        },
                    )
                break

            if stop_event.is_set():
                break

            logging.debug(f"Extending visibilityTimeout for message: {receipt_handle}")

            status = sqs_library.change_message_visibility(
                receipt_handle, timeout_duration,
            )
            if status:
                context.logger.debug(
                    "Successfully Extended message visibility",
                    extra={
                        "message_handle": receipt_handle,
                        "duration": timeout_duration,
                    },
                )
            else:
                context.logger.debug(
                    "Failed to Extend message visibility",
                    extra={
                        "message_handle": receipt_handle,
                        "duration": timeout_duration,
                    },
                )

    except Exception as e:
        logging.error(f"Error extending visibilityTimeout: {str(e)}")


def process_message(context: AppContext, message: dict):
    context.logger.debug("Processing message", extra={"message": message["Body"]})

    is_success = False
    try:
        receipt_handle = message["ReceiptHandle"]

        stop_event = threading.Event()

        # Extend Visibility Timeout by 5 mins each time
        visibility_extension_thread = Thread(
            target=extend_visibility_timeout,
            args=(message, receipt_handle, 120, stop_event),
            daemon=True,
        )

        visibility_extension_thread.start()

        params = json.loads(message["Body"])
        context.logger.debug(
            "Received", extra={"message": params, "handle": receipt_handle},
        )

        process_request(context, params)

        is_success = True

        context.logger.debug(
            "Message processed successfully",
            extra={
                "message": message["Body"],
                "handle": receipt_handle,
                "success": is_success,
            },
        )

    except Exception as e:
        context.logger.error(
            "Error processing message",
            extra={
                "error": str(e),
                "message": message["Body"],
                "handle": message["ReceiptHandle"],
                "success": is_success,
            },
        )
        is_success = False

    finally:
        stop_event.set()

        # Delete the message from the queue
        sqs_library = SQSLibrary(context)

        # After processing, delete the message
        status = sqs_library.delete_message(message["ReceiptHandle"])
        if status:
            context.logger.debug(
                "Successfully deleted message from queue",
                extra={
                    "message": message["Body"],
                    "handle": receipt_handle,
                    "status": status,
                },
            )
            is_success = True
        else:
            context.logger.debug(
                "Failed to delete message from queue",
                extra={
                    "message": message["Body"],
                    "handle": receipt_handle,
                    "status": status,
                },
            )
            is_success = False

        visibility_extension_thread.join()

        stop_event = None
        visibility_extension_thread = None


def poll_messages(context: AppContext):
    context.logger.debug("Polling for messages from the queue...")

    start_time = time.time()
    # INFO: poll messages from sqs, fetch one message, process it and die
    processed_count: int = 0
    while True:
        context.logger.debug("fetching messages")

        try:
            sqs_library = SQSLibrary(context)

            # Pull messages from SQS
            messages = sqs_library.fetch_messages()
            context.logger.debug(
                "Messages fetched from Queue", extra={"count": len(messages)},
            )

            if len(messages) > 0:
                for message in messages:
                    process_message(context, message)
                    processed_count += 1
                    break

                if processed_count >= 1:
                    context.logger.debug(f"Processed {processed_count} messages.")
                    break

            else:
                # Log when no messages are available
                context.logger.debug("No messages available in the queue.")

            time.sleep(30)

            if time.time() - start_time > 60:
                context.logger.debug("Exiting after 1 minute of polling")
                break

        except Exception as e:
            context.logger.error(f"Error polling messages from SQS: {str(e)}")

    context.logger.debug("Process Exiting...")
    return


def init_app_context() -> AppContext:
    context = AppContext(
        region=os.environ["CDX_DEFAULT_REGION"],
        log_level=os.environ["CDX_LOG_LEVEL"],
        app_env=os.environ["CDX_APP_ENV"],
    )
    context.logger = get_logger(context.log_level)

    decrypted_value = ""

    # Read from config files in the project
    with open(current_config(context.app_env)) as f:
        decrypted_value = f.read()

    context.parse(decrypted_value)

    set_assume_role_keys(context)

    return context


if __name__ == "__main__":
    print("Service started...")

    if os.environ.get("CDX_RUN_AS") == "EKS":
        context = init_app_context()
        poll_messages(context)
