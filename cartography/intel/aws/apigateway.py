import json
import logging
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

import boto3
import botocore
import neo4j
from botocore.exceptions import ClientError
from policyuniverse.policy import Policy

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.aws.apigateway import APIGatewayRestAPISchema
from cartography.models.aws.apigatewaycertificate import APIGatewayClientCertificateSchema
from cartography.models.aws.apigatewayresource import APIGatewayResourceSchema
from cartography.models.aws.apigatewaystage import APIGatewayStageSchema
from cartography.util import aws_handle_regions
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_apigateway_rest_apis(boto3_session: boto3.session.Session, region: str) -> List[Dict]:
    client = boto3_session.client('apigateway', region_name=region)
    paginator = client.get_paginator('get_rest_apis')
    apis: List[Any] = []
    for page in paginator.paginate():
        apis.extend(page['items'])
    return apis


@timeit
@aws_handle_regions
def get_rest_api_details(
        boto3_session: boto3.session.Session, rest_apis: List[Dict], region: str,
) -> List[Tuple[Any, Any, Any, Any, Any]]:
    """
    Iterates over all API Gateway REST APIs.
    """
    client = boto3_session.client('apigateway', region_name=region)
    apis = []
    for api in rest_apis:
        stages = get_rest_api_stages(api, client)
        # clientcertificate id is given by the api stage
        certificate = get_rest_api_client_certificate(stages, client)
        resources = get_rest_api_resources(api, client)
        policy = get_rest_api_policy(api, client)
        apis.append((api['id'], stages, certificate, resources, policy))
    return apis


@timeit
def get_rest_api_stages(api: Dict, client: botocore.client.BaseClient) -> Any:
    """
    Gets the REST API Stage Resources.
    """
    try:
        stages = client.get_stages(restApiId=api['id'])
    except ClientError as e:
        logger.warning(f'Failed to retrieve Stages for Api Id - {api["id"]} - {e}')
        raise

    return stages['item']


@timeit
def get_rest_api_client_certificate(stages: Dict, client: botocore.client.BaseClient) -> Optional[Any]:
    """
    Gets the current ClientCertificate resource if present, else returns None.
    """
    response = None
    for stage in stages:
        if 'clientCertificateId' in stage:
            try:
                response = client.get_client_certificate(clientCertificateId=stage['clientCertificateId'])
                response['stageName'] = stage['stageName']
            except ClientError as e:
                logger.warning(f"Failed to retrive Client Certificate for Stage {stage['stageName']} - {e}")
                raise
        else:
            return []

    return response


@timeit
def get_rest_api_resources(api: Dict, client: botocore.client.BaseClient) -> List[Any]:
    """
    Gets the collection of Resource resources.
    """
    resources: List[Any] = []
    paginator = client.get_paginator('get_resources')
    response_iterator = paginator.paginate(restApiId=api['id'])
    for page in response_iterator:
        resources.extend(page['items'])

    return resources


@timeit
def get_rest_api_policy(api: Dict, client: botocore.client.BaseClient) -> Any:
    """
    Gets the REST API policy. Returns policy string or None if no policy is present.
    """
    policy = api['policy'] if 'policy' in api and api['policy'] else None
    return policy


def transform_apigateway_rest_apis(
    rest_apis: List[Dict], resource_policies: List[Dict], region: str, current_aws_account_id: str, aws_update_tag: int,
) -> List[Dict]:
    """
    Transform API Gateway REST API data for ingestion, including policy analysis
    """
    # Create a mapping of api_id to policy data for easier lookup
    policy_map = {
        policy['api_id']: policy
        for policy in resource_policies
    }

    transformed_apis = []
    for api in rest_apis:
        policy_data = policy_map.get(api['id'], {})
        transformed_api = {
            'id': api['id'],
            'createdDate': str(api['createdDate']) if 'createdDate' in api else None,
            'version': api.get('version'),
            'minimumCompressionSize': api.get('minimumCompressionSize'),
            'disableExecuteApiEndpoint': api.get('disableExecuteApiEndpoint'),
            # Set defaults in the transform function
            'anonymous_access': policy_data.get('internet_accessible', False),
            'anonymous_actions': policy_data.get('accessible_actions', []),
            # TODO Issue #1452: clarify internet exposure vs anonymous access
        }
        transformed_apis.append(transformed_api)

    return transformed_apis


@timeit
def load_apigateway_rest_apis(
    neo4j_session: neo4j.Session, data: List[Dict], region: str, current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    """
    Ingest API Gateway REST API data into neo4j.
    """
    load(
        neo4j_session,
        APIGatewayRestAPISchema(),
        data,
        region=region,
        lastupdated=aws_update_tag,
        AWS_ID=current_aws_account_id,
    )


def transform_apigateway_stages(stages: List[Dict], update_tag: int) -> List[Dict]:
    """
    Transform API Gateway Stage data for ingestion
    """
    stage_data = []
    for stage in stages:
        stage['createdDate'] = str(stage['createdDate'])
        stage['arn'] = f"arn:aws:apigateway:::{stage['apiId']}/{stage['stageName']}"
        stage_data.append(stage)
    return stage_data


def transform_apigateway_certificates(certificates: List[Dict], update_tag: int) -> List[Dict]:
    """
    Transform API Gateway Client Certificate data for ingestion
    """
    cert_data = []
    for certificate in certificates:
        certificate['createdDate'] = str(certificate['createdDate'])
        certificate['expirationDate'] = str(certificate.get('expirationDate'))
        certificate['stageArn'] = f"arn:aws:apigateway:::{certificate['apiId']}/{certificate['stageName']}"
        cert_data.append(certificate)
    return cert_data


def transform_rest_api_details(
    stages_certificate_resources: List[Tuple[Any, Any, Any, Any, Any]],
) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """
    Transform Stage, Client Certificate, and Resource data for ingestion
    """
    stages: List[Dict] = []
    certificates: List[Dict] = []
    resources: List[Dict] = []

    for api_id, stage, certificate, resource, _ in stages_certificate_resources:
        if len(stage) > 0:
            for s in stage:
                s['apiId'] = api_id
                s['createdDate'] = str(s['createdDate'])
                s['arn'] = f"arn:aws:apigateway:::{api_id}/{s['stageName']}"
            stages.extend(stage)

        if certificate:
            certificate['apiId'] = api_id
            certificate['createdDate'] = str(certificate['createdDate'])
            certificate['expirationDate'] = str(certificate.get('expirationDate'))
            certificate['stageArn'] = f"arn:aws:apigateway:::{api_id}/{certificate['stageName']}"
            certificates.append(certificate)

        if len(resource) > 0:
            for r in resource:
                r['apiId'] = api_id
            resources.extend(resource)

    return stages, certificates, resources


@timeit
def load_rest_api_details(
    neo4j_session: neo4j.Session, stages_certificate_resources: List[Tuple[Any, Any, Any, Any, Any]],
    aws_account_id: str, update_tag: int,
) -> None:
    """
    Transform and load Stage, Client Certificate, and Resource data
    """
    stages, certificates, resources = transform_rest_api_details(stages_certificate_resources)

    load(
        neo4j_session,
        APIGatewayStageSchema(),
        stages,
        lastupdated=update_tag,
        AWS_ID=aws_account_id,
    )

    load(
        neo4j_session,
        APIGatewayClientCertificateSchema(),
        certificates,
        lastupdated=update_tag,
        AWS_ID=aws_account_id,
    )

    load(
        neo4j_session,
        APIGatewayResourceSchema(),
        resources,
        lastupdated=update_tag,
        AWS_ID=aws_account_id,
    )


@timeit
def parse_policy(api_id: str, policy: Policy) -> Optional[Dict[Any, Any]]:
    """
    Uses PolicyUniverse to parse API Gateway REST API policy and returns the internet accessibility results
    """

    if policy is not None:
        # unescape doubly escapped JSON
        policy = policy.replace("\\", "")
        try:
            policy = Policy(json.loads(policy))
            if policy.is_internet_accessible():
                return {
                    "api_id": api_id,
                    "internet_accessible": True,
                    "accessible_actions": list(policy.internet_accessible_actions()),
                }
            else:
                return None
        except json.JSONDecodeError:
            logger.warn(f"failed to decode policy json : {policy}")
            return None
    else:
        return None


@timeit
def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    """
    Delete out-of-date API Gateway resources and relationships.
    Order matters - clean up certificates, stages, and resources before cleaning up the REST APIs they connect to.
    """
    logger.info("Running API Gateway cleanup job.")

    # Clean up certificates first
    cleanup_job = GraphJob.from_node_schema(APIGatewayClientCertificateSchema(), common_job_parameters)
    cleanup_job.run(neo4j_session)

    # Then stages
    cleanup_job = GraphJob.from_node_schema(APIGatewayStageSchema(), common_job_parameters)
    cleanup_job.run(neo4j_session)

    # Then resources
    cleanup_job = GraphJob.from_node_schema(APIGatewayResourceSchema(), common_job_parameters)
    cleanup_job.run(neo4j_session)

    # Finally REST APIs
    cleanup_job = GraphJob.from_node_schema(APIGatewayRestAPISchema(), common_job_parameters)
    cleanup_job.run(neo4j_session)


@timeit
def sync_apigateway_rest_apis(
    neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, region: str, current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    rest_apis = get_apigateway_rest_apis(boto3_session, region)
    stages_certificate_resources = get_rest_api_details(boto3_session, rest_apis, region)

    # Extract policies and transform the data
    policies = []
    for api_id, _, _, _, policy in stages_certificate_resources:
        parsed_policy = parse_policy(api_id, policy)
        if parsed_policy is not None:
            policies.append(parsed_policy)

    transformed_apis = transform_apigateway_rest_apis(
        rest_apis,
        policies,
        region,
        current_aws_account_id,
        aws_update_tag,
    )
    load_apigateway_rest_apis(neo4j_session, transformed_apis, region, current_aws_account_id, aws_update_tag)
    load_rest_api_details(neo4j_session, stages_certificate_resources, current_aws_account_id, aws_update_tag)


@timeit
def sync(
    neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, regions: List[str], current_aws_account_id: str,
    update_tag: int, common_job_parameters: Dict,
) -> None:
    for region in regions:
        logger.info(f"Syncing AWS APIGateway Rest APIs for region '{region}' in account '{current_aws_account_id}'.")
        sync_apigateway_rest_apis(neo4j_session, boto3_session, region, current_aws_account_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)
