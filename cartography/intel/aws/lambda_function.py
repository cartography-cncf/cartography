import json
import logging
from typing import Any
from typing import Dict
from typing import List

import boto3
import botocore
import neo4j
from policyuniverse.policy import Policy

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.aws.util.botocore_config import create_boto3_client
from cartography.intel.container_arch import normalize_architecture
from cartography.intel.container_image import parse_image_uri
from cartography.models.aws.lambda_function.alias import AWSLambdaFunctionAliasSchema
from cartography.models.aws.lambda_function.event_source_mapping import (
    AWSLambdaEventSourceMappingSchema,
)
from cartography.models.aws.lambda_function.lambda_function import AWSLambdaSchema
from cartography.models.aws.lambda_function.layer import AWSLambdaLayerSchema
from cartography.util import aws_handle_regions
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_lambda_data(boto3_session: boto3.session.Session, region: str) -> List[Dict]:
    """
    Create an Lambda boto3 client and grab all the lambda functions.
    """
    client = create_boto3_client(boto3_session, "lambda", region_name=region)
    paginator = client.get_paginator("list_functions")
    lambda_functions = []
    for page in paginator.paginate():
        for each_function in page["Functions"]:
            lambda_functions.append(each_function)
    return lambda_functions


@timeit
@aws_handle_regions
def get_lambda_image_uris(
    boto3_session: boto3.session.Session,
    lambda_functions: List[Dict],
    region: str,
) -> Dict[str, Dict[str, str | None]]:
    """
    For each container-image Lambda (PackageType=Image), call get_function to
    resolve ImageUri / ResolvedImageUri. list_functions does not return the
    Code.ImageUri field, so this per-function call is required for image-based
    Lambdas only. Returns a map of function_arn -> {"ImageUri", "ResolvedImageUri"}.

    A failure on a single function is logged and skipped (matching the existing
    per-function pattern used by get_lambda_permission_policy) so one transient
    SDK error does not abort the whole region's Lambda sync.
    """
    client = create_boto3_client(boto3_session, "lambda", region_name=region)
    image_uris: Dict[str, Dict[str, str | None]] = {}
    for function_data in lambda_functions:
        if function_data.get("PackageType") != "Image":
            continue
        function_arn = function_data["FunctionArn"]
        try:
            response = client.get_function(FunctionName=function_arn)
        except Exception as e:
            logger.warning("Failed to get image URI for Lambda %s: %s", function_arn, e)
            continue
        code = response.get("Code") or {}
        image_uris[function_arn] = {
            "ImageUri": code.get("ImageUri"),
            "ResolvedImageUri": code.get("ResolvedImageUri"),
        }
    return image_uris


def transform_lambda_functions(
    lambda_functions: List[Dict],
    permissions_by_arn: Dict[str, Dict[str, Any]],
    image_uris_by_arn: Dict[str, Dict[str, str | None]],
    region: str,
) -> List[Dict]:
    transformed_functions = []

    for function_data in lambda_functions:
        transformed_function = function_data.copy()

        # In API response, TracingConfig is a nested object so flatten it for use in the data model
        tracing_config = function_data.get("TracingConfig", {})
        transformed_function["TracingConfigMode"] = tracing_config.get("Mode")

        transformed_function["Region"] = region

        function_arn = function_data["FunctionArn"]
        permission_data = permissions_by_arn[function_arn]
        transformed_function["AnonymousAccess"] = permission_data["AnonymousAccess"]
        transformed_function["AnonymousActions"] = permission_data["AnonymousActions"]

        # For PackageType=Image Lambdas, the resolved image URI is fetched via a
        # per-function GetFunction call (list_functions does not return Code).
        # Parsing both the URI and its digest allows RESOLVED_IMAGE to link Lambdas
        # to registry image nodes the same way Cloud Run / Azure Container workloads do.
        code = image_uris_by_arn.get(function_arn, {})
        image_uri, image_digest = parse_image_uri(
            code.get("ResolvedImageUri") or code.get("ImageUri")
        )
        transformed_function["image_uri"] = image_uri
        transformed_function["image_digest"] = image_digest

        architectures = function_data.get("Architectures") or []
        transformed_function["architecture_normalized"] = (
            normalize_architecture(architectures[0]) if architectures else None
        )

        transformed_functions.append(transformed_function)

    return transformed_functions


def transform_lambda_aliases(aliases: List[Dict], function_arn: str) -> List[Dict]:
    """
    Transform lambda function aliases by adding the parent function ARN.
    """
    transformed_aliases = []
    for alias in aliases:
        transformed_alias = alias.copy()
        transformed_alias["FunctionArn"] = function_arn
        transformed_aliases.append(transformed_alias)
    return transformed_aliases


def transform_lambda_layers(layers: List[Dict], function_arn: str) -> List[Dict]:
    """
    Transform lambda layers by adding the parent function ARN.
    """
    transformed_layers = []
    for layer in layers:
        transformed_layer = layer.copy()
        transformed_layer["FunctionArn"] = function_arn
        transformed_layers.append(transformed_layer)
    return transformed_layers


@timeit
def load_lambda_functions(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    """
    Load AWS Lambda functions using the data model
    """
    load(
        neo4j_session,
        AWSLambdaSchema(),
        data,
        AWS_ID=current_aws_account_id,
        Region=region,
        lastupdated=aws_update_tag,
    )


@timeit
@aws_handle_regions
def get_function_aliases(
    lambda_function: Dict,
    client: botocore.client.BaseClient,
) -> List[Any]:
    aliases: List[Any] = []
    paginator = client.get_paginator("list_aliases")
    for page in paginator.paginate(FunctionName=lambda_function["FunctionName"]):
        aliases.extend(page["Aliases"])

    return aliases


@timeit
@aws_handle_regions
def get_event_source_mappings(
    lambda_function: Dict,
    client: botocore.client.BaseClient,
) -> List[Any]:
    event_source_mappings: List[Any] = []
    paginator = client.get_paginator("list_event_source_mappings")
    for page in paginator.paginate(FunctionName=lambda_function["FunctionName"]):
        event_source_mappings.extend(page["EventSourceMappings"])

    return event_source_mappings


@timeit
@aws_handle_regions
def get_lambda_permissions(
    lambda_functions: List[Dict],
    boto3_session: boto3.Session,
    region: str,
) -> Dict[str, Dict[str, Any]]:
    """
    Get Lambda permissions for the given functions in the specified region.
    """
    client = create_boto3_client(boto3_session, "lambda", region_name=region)
    all_permissions = {}
    for function in lambda_functions:
        function_name = function["FunctionName"]
        function_arn = function["FunctionArn"]

        all_permissions[function_arn] = {
            "AnonymousAccess": None,
            "AnonymousActions": None,
        }

        try:
            response = client.get_policy(FunctionName=function_name)
            policy = response.get("Policy")

            if policy:
                parsed_policy = parse_policy(function_arn, policy)
                all_permissions[function_arn] = {
                    "AnonymousAccess": parsed_policy.get("AnonymousAccess"),
                    "AnonymousActions": parsed_policy.get("AnonymousActions"),
                }
        except client.exceptions.ResourceNotFoundException:
            logger.debug(f"No policy found for Lambda function {function_name}")
            pass
        except Exception as e:
            logger.warning(
                f"Error getting policy for Lambda function {function_name}: {e}"
            )

    return all_permissions


def parse_policy(function_arn: str, policy: str) -> Dict[str, Any]:
    """
    Parse the Lambda permission policy to extract anonymous access and actions.
    """
    policy_obj = Policy(json.loads(policy))
    inet_actions = policy_obj.internet_accessible_actions()

    return {
        "AnonymousAccess": policy_obj.is_internet_accessible(),
        "AnonymousActions": list(inet_actions) if inet_actions else [],
    }


@timeit
def load_lambda_function_aliases(
    neo4j_session: neo4j.Session,
    lambda_aliases: List[Dict],
    region: str,
    current_aws_account_id: str,
    update_tag: int,
) -> None:
    """
    Load AWS Lambda function aliases using the data model
    """
    load(
        neo4j_session,
        AWSLambdaFunctionAliasSchema(),
        lambda_aliases,
        AWS_ID=current_aws_account_id,
        Region=region,
        lastupdated=update_tag,
    )


@timeit
def load_lambda_event_source_mappings(
    neo4j_session: neo4j.Session,
    lambda_event_source_mappings: List[Dict],
    current_aws_account_id: str,
    update_tag: int,
) -> None:
    """
    Load AWS Lambda event source mappings using the data model approach.
    """
    load(
        neo4j_session,
        AWSLambdaEventSourceMappingSchema(),
        lambda_event_source_mappings,
        AWS_ID=current_aws_account_id,
        lastupdated=update_tag,
    )


@timeit
def load_lambda_layers(
    neo4j_session: neo4j.Session,
    lambda_layers: List[Dict],
    current_aws_account_id: str,
    update_tag: int,
) -> None:
    """
    Load AWS Lambda layers using the data model approach.
    """
    load(
        neo4j_session,
        AWSLambdaLayerSchema(),
        lambda_layers,
        AWS_ID=current_aws_account_id,
        lastupdated=update_tag,
    )


@timeit
def cleanup_lambda(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    """
    Clean up Lambda resources
    """
    logger.info("Running Lambda cleanup")

    # Clean up child entities first
    GraphJob.from_node_schema(
        AWSLambdaFunctionAliasSchema(), common_job_parameters
    ).run(neo4j_session)
    GraphJob.from_node_schema(
        AWSLambdaEventSourceMappingSchema(), common_job_parameters
    ).run(neo4j_session)
    GraphJob.from_node_schema(AWSLambdaLayerSchema(), common_job_parameters).run(
        neo4j_session
    )

    # Clean up parent Lambda nodes last
    GraphJob.from_node_schema(AWSLambdaSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync_aliases(
    neo4j_session: neo4j.Session,
    lambda_functions: List[Dict],
    client: Any,
    region: str,
    current_aws_account_id: str,
    update_tag: int,
) -> None:
    """
    Sync Lambda function aliases for all functions in the region.
    """
    all_aliases = []

    for lambda_function in lambda_functions:
        function_arn = lambda_function["FunctionArn"]

        # Get, transform, and collect aliases
        aliases = get_function_aliases(lambda_function, client)
        if aliases:
            transformed_aliases = transform_lambda_aliases(aliases, function_arn)
            all_aliases.extend(transformed_aliases)

    # Load all aliases
    load_lambda_function_aliases(
        neo4j_session, all_aliases, region, current_aws_account_id, update_tag
    )


@timeit
def sync_event_source_mappings(
    neo4j_session: neo4j.Session,
    lambda_functions: List[Dict],
    client: Any,
    current_aws_account_id: str,
    update_tag: int,
) -> None:
    """
    Sync Lambda event source mappings for all functions in the region.
    """
    all_esms = []

    for lambda_function in lambda_functions:
        # Get and collect event source mappings (no transformation needed)
        esms = get_event_source_mappings(lambda_function, client)
        if esms:
            all_esms.extend(esms)

    # Load all event source mappings
    load_lambda_event_source_mappings(
        neo4j_session, all_esms, current_aws_account_id, update_tag
    )


@timeit
def sync_lambda_layers(
    neo4j_session: neo4j.Session,
    lambda_functions: List[Dict],
    current_aws_account_id: str,
    update_tag: int,
) -> None:
    """
    Sync Lambda layers for all functions in the region.
    """
    all_layers = []

    for lambda_function in lambda_functions:
        function_arn = lambda_function["FunctionArn"]

        # Get, transform, and collect layers (from function data)
        layers = lambda_function.get("Layers", [])
        if layers:
            transformed_layers = transform_lambda_layers(layers, function_arn)
            all_layers.extend(transformed_layers)

    # Load all layers
    load_lambda_layers(neo4j_session, all_layers, current_aws_account_id, update_tag)


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
            "Syncing Lambda for region in '%s' in account '%s'.",
            region,
            current_aws_account_id,
        )

        # Get and load core lambda functions
        data = get_lambda_data(boto3_session, region)
        permissions_by_arn = get_lambda_permissions(data, boto3_session, region)
        image_uris_by_arn = get_lambda_image_uris(boto3_session, data, region)
        transformed_data = transform_lambda_functions(
            data, permissions_by_arn, image_uris_by_arn, region
        )
        load_lambda_functions(
            neo4j_session,
            transformed_data,
            region,
            current_aws_account_id,
            update_tag,
        )

        # Create Lambda client for sub-entity requests
        client = create_boto3_client(boto3_session, "lambda", region_name=region)

        # Sync all sub-entities
        sync_aliases(
            neo4j_session,
            data,
            client,
            region,
            current_aws_account_id,
            update_tag,
        )

        sync_event_source_mappings(
            neo4j_session,
            data,
            client,
            current_aws_account_id,
            update_tag,
        )

        sync_lambda_layers(
            neo4j_session,
            data,
            current_aws_account_id,
            update_tag,
        )

    cleanup_lambda(neo4j_session, common_job_parameters)
