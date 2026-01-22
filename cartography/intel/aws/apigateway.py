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
from cartography.intel.aws.ec2.util import get_botocore_config
from cartography.models.aws.apigateway.apigateway import APIGatewayRestAPISchema
from cartography.models.aws.apigateway.apigatewaycertificate import (
    APIGatewayClientCertificateSchema,
)
from cartography.models.aws.apigateway.apigatewaydeployment import (
    APIGatewayDeploymentSchema,
)
from cartography.models.aws.apigateway.apigatewayintegration import (
    APIGatewayIntegrationSchema,
)
from cartography.models.aws.apigateway.apigatewaymethod import APIGatewayMethodSchema
from cartography.models.aws.apigateway.apigatewayresource import (
    APIGatewayResourceSchema,
)
from cartography.models.aws.apigateway.apigatewaystage import APIGatewayStageSchema
from cartography.util import aws_handle_regions
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_apigateway_rest_apis(
    boto3_session: boto3.session.Session,
    region: str,
) -> List[Dict]:
    client = boto3_session.client("apigateway", region_name=region)
    paginator = client.get_paginator("get_rest_apis")
    apis: List[Any] = []
    for page in paginator.paginate():
        apis.extend(page["items"])
    return apis


def get_rest_api_ids(
    rest_apis: List[Dict],
) -> List[str]:
    """
    Extracts the IDs of the REST APIs from the provided list.
    """
    return [api["id"] for api in rest_apis if "id" in api]


@timeit
@aws_handle_regions
def get_rest_api_deployments(
    boto3_session: boto3.session.Session,
    rest_api_ids: List[str],
    region: str,
) -> List[Dict[str, Any]]:
    """
    Retrieves the deployments for each REST API in the provided list.
    """
    client = boto3_session.client(
        "apigateway", region_name=region, config=get_botocore_config()
    )
    deployments: List[Dict[str, Any]] = []
    for api_id in rest_api_ids:
        paginator = client.get_paginator("get_deployments")
        for page in paginator.paginate(restApiId=api_id):
            for deployment in page.get("items", []):
                deployment["api_id"] = api_id
                deployments.append(deployment)
    return deployments


@timeit
@aws_handle_regions
def get_rest_api_details(
    boto3_session: boto3.session.Session,
    rest_apis: List[Dict],
    region: str,
) -> List[Tuple[Any, Any, Any, Any, Any, Any, Any]]:
    """
    Iterates over all API Gateway REST APIs.
    """
    client = boto3_session.client("apigateway", region_name=region)
    apis = []
    for api in rest_apis:
        stages = get_rest_api_stages(api, client)
        # clientcertificate id is given by the api stage
        certificate = get_rest_api_client_certificate(stages, client)
        resources, methods, integrations = get_rest_api_resources_methods_integrations(
            api,
            client,
        )
        policy = get_rest_api_policy(api, client)
        apis.append(
            (api["id"], stages, certificate, resources, methods, integrations, policy)
        )
    return apis


@timeit
@aws_handle_regions
def get_rest_api_stages(api: Dict, client: botocore.client.BaseClient) -> Any:
    """
    Gets the REST API Stage Resources.
    """
    try:
        stages = client.get_stages(restApiId=api["id"])
    except ClientError as e:
        logger.warning(f'Failed to retrieve Stages for Api Id - {api["id"]} - {e}')
        raise

    return stages["item"]


@timeit
def get_rest_api_client_certificate(
    stages: Dict,
    client: botocore.client.BaseClient,
) -> Optional[Any]:
    """
    Gets the current ClientCertificate resource if present, else returns None.
    """
    response = None
    for stage in stages:
        if "clientCertificateId" in stage:
            try:
                response = client.get_client_certificate(
                    clientCertificateId=stage["clientCertificateId"],
                )
                response["stageName"] = stage["stageName"]
            except ClientError as e:
                logger.warning(
                    f"Failed to retrieve Client Certificate for Stage {stage['stageName']} - {e}",
                )
                raise
        else:
            return []

    return response


@timeit
@aws_handle_regions
def get_rest_api_resources_methods_integrations(
    api: Dict, client: botocore.client.BaseClient
) -> Tuple[List[Any], List[Dict], List[Dict]]:
    """
    Gets the collection of Resource resources.
    """
    resources: List[Any] = []
    methods: List[Any] = []
    integrations: List[Any] = []

    paginator = client.get_paginator("get_resources")
    response_iterator = paginator.paginate(restApiId=api["id"])
    for page in response_iterator:
        page_resources = page["items"]
        resources.extend(page_resources)

        for resource in page_resources:
            resource_id = resource["id"]
            resource_methods = resource.get("resourceMethods", {})

            for http_method, method in resource_methods.items():
                method["resourceId"] = resource_id
                method["apiId"] = api["id"]
                method["httpMethod"] = http_method
                methods.append(method)
                try:
                    integration = client.get_integration(
                        restApiId=api["id"],
                        resourceId=resource_id,
                        httpMethod=http_method,
                    )
                except ClientError as e:
                    error_code = e.response.get("Error", {}).get("Code")
                    if error_code == "NotFoundException":
                        logger.warning(
                            "No integration found for API %s resource %s method %s: %s",
                            api["id"],
                            resource_id,
                            http_method,
                            e,
                        )
                        continue
                    raise
                integration["resourceId"] = resource_id
                integration["apiId"] = api["id"]
                integration["integrationHttpMethod"] = integration.get("httpMethod")
                integration["httpMethod"] = http_method
                integrations.append(integration)

    return resources, methods, integrations


@timeit
def get_rest_api_policy(api: Dict, client: botocore.client.BaseClient) -> Any:
    """
    Gets the REST API policy. Returns policy string or None if no policy is present.
    """
    policy = api["policy"] if "policy" in api and api["policy"] else None
    return policy


def transform_apigateway_rest_apis(
    rest_apis: List[Dict],
    resource_policies: List[Dict],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> List[Dict]:
    """
    Transform API Gateway REST API data for ingestion, including policy analysis
    """
    # Create a mapping of api_id to policy data for easier lookup
    policy_map = {policy["api_id"]: policy for policy in resource_policies}

    transformed_apis = []
    for api in rest_apis:
        policy_data = policy_map.get(api["id"], {})
        transformed_api = {
            "id": api["id"],
            "createdDate": str(api["createdDate"]) if "createdDate" in api else None,
            "version": api.get("version"),
            "minimumCompressionSize": api.get("minimumCompressionSize"),
            "disableExecuteApiEndpoint": api.get("disableExecuteApiEndpoint"),
            # Set defaults in the transform function
            "anonymous_access": policy_data.get("internet_accessible", False),
            "anonymous_actions": policy_data.get("accessible_actions", []),
            # TODO Issue #1452: clarify internet exposure vs anonymous access
        }
        transformed_apis.append(transformed_api)

    return transformed_apis


@timeit
def load_apigateway_rest_apis(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    region: str,
    current_aws_account_id: str,
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
        stage["createdDate"] = str(stage["createdDate"])
        stage["arn"] = f"arn:aws:apigateway:::{stage['apiId']}/{stage['stageName']}"
        stage_data.append(stage)
    return stage_data


def transform_apigateway_certificates(
    certificates: List[Dict],
    update_tag: int,
) -> List[Dict]:
    """
    Transform API Gateway Client Certificate data for ingestion
    """
    cert_data = []
    for certificate in certificates:
        certificate["createdDate"] = str(certificate["createdDate"])
        certificate["expirationDate"] = str(certificate.get("expirationDate"))
        certificate["stageArn"] = (
            f"arn:aws:apigateway:::{certificate['apiId']}/{certificate['stageName']}"
        )
        cert_data.append(certificate)
    return cert_data


def transform_rest_api_details(
    stages_certificate_resources: List[Tuple[Any, Any, Any, Any, Any, Any, Any]],
) -> Tuple[List[Dict], List[Dict], List[Dict], List[Dict], List[Dict]]:
    """
    Transform Stage, Client Certificate, Resource, Method and Integration data for ingestion
    """
    stages: List[Dict] = []
    certificates: List[Dict] = []
    resources: List[Dict] = []
    methods: List[Dict] = []
    integrations: List[Dict] = []

    for (
        api_id,
        stage,
        certificate,
        resource,
        method_list,
        integration_list,
        _,
    ) in stages_certificate_resources:

        if len(stage) > 0:
            for s in stage:
                s["apiId"] = api_id
                s["createdDate"] = str(s["createdDate"])
                s["arn"] = f"arn:aws:apigateway:::{api_id}/{s['stageName']}"
            stages.extend(stage)

        if certificate:
            certificate["apiId"] = api_id
            certificate["createdDate"] = str(certificate["createdDate"])
            certificate["expirationDate"] = str(certificate.get("expirationDate"))
            certificate["stageArn"] = (
                f"arn:aws:apigateway:::{api_id}/{certificate['stageName']}"
            )
            certificates.append(certificate)

        if len(resource) > 0:
            for r in resource:
                r["apiId"] = api_id
            resources.extend(resource)

        if len(method_list) > 0:
            for method in method_list:
                method["id"] = (
                    f"{method['apiId']}/{method['resourceId']}/{method['httpMethod']}"
                )
                method["authorizationType"] = method.get("authorizationType")
                method["authorizerId"] = method.get("authorizerId")
                method["requestValidatorId"] = method.get("requestValidatorId")
                method["operationName"] = method.get("operationName")
                method["apiKeyRequired"] = method.get("apiKeyRequired", False)
            methods.extend(method_list)

        if len(integration_list) > 0:
            for integration in integration_list:
                if not integration.get("id"):
                    integration["id"] = (
                        f"{integration['apiId']}/{integration['resourceId']}/{integration['httpMethod']}"
                    )
                integration["type"] = integration.get("type")
                integration["uri"] = integration.get("uri")
                integration["connectionType"] = integration.get("connectionType")
                integration["connectionId"] = integration.get("connectionId")
                integration["credentials"] = integration.get("credentials")
            integrations.extend(integration_list)

    return stages, certificates, resources, methods, integrations


def transform_apigateway_deployments(
    deployments: List[Dict[str, Any]],
    region: str,
) -> List[Dict[str, Any]]:
    """
    Transform API Gateway Deployment data for ingestion
    """
    transformed_deployments = []
    for deployment in deployments:
        transformed_deployment = {
            "id": f"{deployment['api_id']}/{deployment['id']}",
            "api_id": deployment["api_id"],
            "description": deployment.get("description"),
            "region": region,
        }
        transformed_deployments.append(transformed_deployment)
    return transformed_deployments


@timeit
def load_rest_api_details(
    neo4j_session: neo4j.Session,
    stages_certificate_resources_methods_integrations: List[
        Tuple[Any, Any, Any, Any, Any, Any, Any]
    ],
    aws_account_id: str,
    update_tag: int,
) -> None:
    """
    Transform and load Stage, Client Certificate, and Resource data
    """
    stages, certificates, resources, methods, integrations = transform_rest_api_details(
        stages_certificate_resources_methods_integrations,
    )

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

    load(
        neo4j_session,
        APIGatewayMethodSchema(),
        methods,
        lastupdated=update_tag,
        AWS_ID=aws_account_id,
    )

    load(
        neo4j_session,
        APIGatewayIntegrationSchema(),
        integrations,
        lastupdated=update_tag,
        AWS_ID=aws_account_id,
    )


@timeit
def load_apigateway_deployments(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    """
    Load API Gateway Deployment data into neo4j.
    """
    logger.info(
        f"Loading API Gateway {len(data)} deployments for region '{region}' into graph.",
    )
    load(
        neo4j_session,
        APIGatewayDeploymentSchema(),
        data,
        region=region,
        lastupdated=aws_update_tag,
        AWS_ID=current_aws_account_id,
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
            logger.warning(f"failed to decode policy json : {policy}")
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
    cleanup_job = GraphJob.from_node_schema(
        APIGatewayClientCertificateSchema(),
        common_job_parameters,
    )
    cleanup_job.run(neo4j_session)

    # Then stages
    cleanup_job = GraphJob.from_node_schema(
        APIGatewayStageSchema(),
        common_job_parameters,
    )
    cleanup_job.run(neo4j_session)

    # Then resources
    cleanup_job = GraphJob.from_node_schema(
        APIGatewayResourceSchema(),
        common_job_parameters,
    )
    cleanup_job.run(neo4j_session)

    # Finally REST APIs
    cleanup_job = GraphJob.from_node_schema(
        APIGatewayRestAPISchema(),
        common_job_parameters,
    )
    cleanup_job.run(neo4j_session)

    cleanup_job = GraphJob.from_node_schema(
        APIGatewayDeploymentSchema(),
        common_job_parameters,
    )
    cleanup_job.run(neo4j_session)

    cleanup_job = GraphJob.from_node_schema(
        APIGatewayMethodSchema(),
        common_job_parameters,
    )
    cleanup_job.run(neo4j_session)

    cleanup_job = GraphJob.from_node_schema(
        APIGatewayIntegrationSchema(),
        common_job_parameters,
    )
    cleanup_job.run(neo4j_session)


@timeit
def sync_apigateway_rest_apis(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    rest_apis = get_apigateway_rest_apis(boto3_session, region)
    stages_certificate_resources_methods_integrations = get_rest_api_details(
        boto3_session,
        rest_apis,
        region,
    )

    # Extract policies and transform the data
    policies = []
    for (
        api_id,
        _,
        _,
        _,
        _,
        _,
        policy,
    ) in stages_certificate_resources_methods_integrations:
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

    api_ids = get_rest_api_ids(rest_apis)
    deployments = get_rest_api_deployments(
        boto3_session,
        api_ids,
        region,
    )

    transformed_deployments = transform_apigateway_deployments(
        deployments,
        region,
    )

    load_apigateway_rest_apis(
        neo4j_session,
        transformed_apis,
        region,
        current_aws_account_id,
        aws_update_tag,
    )
    load_rest_api_details(
        neo4j_session,
        stages_certificate_resources_methods_integrations,
        current_aws_account_id,
        aws_update_tag,
    )
    load_apigateway_deployments(
        neo4j_session,
        transformed_deployments,
        region,
        current_aws_account_id,
        aws_update_tag,
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: List[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: Dict,
) -> None:
    for region in regions:
        logger.info(
            f"Syncing AWS APIGateway Rest APIs for region '{region}' in account '{current_aws_account_id}'.",
        )
        sync_apigateway_rest_apis(
            neo4j_session,
            boto3_session,
            region,
            current_aws_account_id,
            update_tag,
        )
    cleanup(neo4j_session, common_job_parameters)
