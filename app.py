# Used by AWS Lambda

import json
import os
import logging

import cartography.cli
from libraries.authlibrary import AuthLibrary
from libraries.kmslibrary import KMSLibrary
from libraries.snslibrary import SNSLibrary
from utils.context import AppContext
from utils.logger import get_logger


lambda_init = None
context = None

def current_config(env):
    return "config/production.json" if env=="PRODUCTION" else "config/default.json"

def set_assume_role_keys(context):
    context.assume_role_access_key_key_id = context.assume_role_access_secret_key_id = os.environ['CDX_APP_ASSUME_ROLE_KMS_KEY_ID']
    context.assume_role_access_key_cipher = os.environ['CDX_APP_ASSUME_ROLE_ACCESS_KEY']
    context.assume_role_access_secret_cipher = os.environ['CDX_APP_ASSUME_ROLE_ACCESS_SECRET']
    context.neo4j_uri = os.environ['CDX_APP_NEO4J_URI']
    context.neo4j_user = os.environ['CDX_APP_NEO4J_USER']
    context.neo4j_pwd = os.environ['CDX_APP_NEO4J_PWD']

def init_lambda(ctx):
    global lambda_init, context

    logging.getLogger('cartography').setLevel(os.environ.get('CDX_DEFAULT_LOG_LEVEL'))
    # logging.getLogger('cartography.intel').setLevel(os.environ.get('CDX_DEFAULT_LOG_LEVEL'))
    logging.getLogger('cartography.sync').setLevel(os.environ.get('CDX_DEFAULT_LOG_LEVEL'))
    logging.getLogger('cartography.graph').setLevel(os.environ.get('CDX_DEFAULT_LOG_LEVEL'))
    logging.getLogger('cartography.cartography').setLevel(os.environ.get('CDX_DEFAULT_LOG_LEVEL'))

    context = AppContext(
        region=os.environ['CDX_DEFAULT_REGION'],
        log_level=os.environ['CDX_DEFAULT_LOG_LEVEL'],
        app_env=os.environ['CDX_APP_ENV'],
    )
    context.logger = get_logger(context.log_level)

    decrypted_value = ''
    
    # Read from config files in the project
    with open(current_config(context.app_env), 'r') as f:
        decrypted_value = f.read()

    # Cloudanix AWS AccountID
    context.aws_account_id = ctx.invoked_function_arn.split(":")[4]
    context.parse(decrypted_value)
    
    set_assume_role_keys(context)

    lambda_init = True


def process_request(context, args):
    context.logger.info(f'{args["templateType"]} request received - {args["eventId"]}')
    context.logger.info(f'workspace - {args["workspace"]}')

    creds = get_auth_creds(context, args)

    body = {
        "credentials": creds,
        "neo4j": {
            "uri": context.neo4j_uri,
            "user": context.neo4j_user,
            "pwd": context.neo4j_pwd,
            "connection_lifetime": 3600,
        },
        "logging": {
            "mode": "verbose",
        },
        "params": {
            "sessionString": args['sessionString'],
            "eventId": args['eventId'],
            "templateType": args['templateType'],
            "workspace": args['workspace'],
            "actions": args['actions'],
            "resultTopic": args['resultTopic'],
        },
    }

    resp = cartography.cli.run_aws(body)

    if 'status' in resp and resp['status'] == 'success':
        context.logger.info(f'successfully processed cartography: {resp}')

    else:
        context.logger.info(f'failed to process cartography: {resp["message"]}')

    publish_response(context, body, resp)

    context.logger.info(f'inventory sync aws response - {args["eventId"]}: {json.dumps(resp)}')


def publish_response(context, req, resp):
    if context.app_env != 'PRODUCTION':
        try:
            with open('response.json', 'w') as outfile:
                json.dump(resp, outfile, indent=2)

        except Exception as e:
            context.logger.error(f'Failed to write to file: {e}')

    else:
        body = {
            "status": resp['status'],
            "params": req['params'],
            "sessionString": req['params']['sessionString'],
            "eventId": req['params']['eventId'],
            "templateType": req['params']['templateType'],
            "workspace": req['params']['workspace'],
            "actions": req['params']['actions'],
            "response": resp,
        }

        sns_helper = SNSLibrary(context)

        if 'resultTopic' in req['params']:
            # Result should be pushed to "resultTopic" passed in the request
            # status = sns_helper.publish(json.dumps(body), req['params']['resultTopic'])
            context.logger.info(f'Result not published anywhere. since we want to avoid query when inventory is refreshed')
            status = True

        else:
            status = sns_helper.publish(json.dumps(body), context.aws_inventory_sync_response_topic)

        context.logger.info(f'result published to SNS with status: {status}')


def get_auth_creds(context, args):
    auth_helper = AuthLibrary(context)

    if context.app_env == 'PRODUCTION' or context.app_env == 'DEBUG':
        auth_params = {
            'aws_access_key_id': auth_helper.get_assume_role_access_key(),
            'aws_secret_access_key': auth_helper.get_assume_role_access_secret(),
            'role_session_name': args['sessionString'],
            'role_arn': args['externalRoleArn'],
            'external_id': args['externalId'],
        }

        auth_creds = auth_helper.assume_role(auth_params)
        auth_creds['type'] = 'assumerole'

    else:
        auth_creds = {
            'type': 'self',
            'aws_access_key_id': args['credentials']['awsAccessKeyID'] if 'credentials' in args else None,
            'aws_secret_access_key': args['credentials']['awsSecretAccessKey'] if 'credentials' in args else None,
        }

    return auth_creds

def load_cartography(event, ctx):
    global lambda_init, context
    if not lambda_init:
        init_lambda(ctx)

    context.logger.info('inventory sync aws worker request received via SNS')

    record = event['Records'][0]
    message = record['Sns']['Message']

    try:
        params = json.loads(message)

    except Exception as e:
        context.logger.error(f'error while parsing inventory sync aws request json: {e}')

        return {
            "status": 'failure',
            "message": 'unable to parse request',
        }

    process_request(context, params)

    return {
        'statusCode': 200,
        'body': json.dumps({
            "status": 'success',
        }),
    }