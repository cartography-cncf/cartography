from typing import Any, Dict, List, Tuple
import logging

import boto3
import botocore
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.aws.awslambda.function import LambdaFunctionSchema
from cartography.models.aws.awslambda.alias import LambdaAliasSchema
from cartography.models.aws.awslambda.event_source_mapping import LambdaEventSourceMappingSchema
from cartography.models.aws.awslambda.layer import LambdaLayerSchema
from cartography.util import aws_handle_regions
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_lambda_data(boto3_session: boto3.session.Session, region: str) -> List[Dict]:
    """Create a Lambda boto3 client and grab all the lambda functions."""
    client = boto3_session.client("lambda", region_name=region)
    paginator = client.get_paginator("list_functions")
    lambda_functions: List[Dict[str, Any]] = []
    for page in paginator.paginate():
        lambda_functions.extend(page.get("Functions", []))
    return lambda_functions


@timeit
def transform_lambda_functions(raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Pass through data for now."""
    return raw_data


@timeit
def load_lambda_functions(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    load(
        neo4j_session,
        LambdaFunctionSchema(),
        data,
        Region=region,
        AWS_ID=current_aws_account_id,
        lastupdated=aws_update_tag,
    )


@timeit
@aws_handle_regions
def get_function_aliases(lambda_function: Dict, client: botocore.client.BaseClient) -> List[Any]:
    aliases: List[Any] = []
    paginator = client.get_paginator("list_aliases")
    for page in paginator.paginate(FunctionName=lambda_function["FunctionName"]):
        aliases.extend(page["Aliases"])
    return aliases


@timeit
@aws_handle_regions
def get_event_source_mappings(lambda_function: Dict, client: botocore.client.BaseClient) -> List[Any]:
    event_source_mappings: List[Any] = []
    paginator = client.get_paginator("list_event_source_mappings")
    for page in paginator.paginate(FunctionName=lambda_function["FunctionName"]):
        event_source_mappings.extend(page["EventSourceMappings"])
    return event_source_mappings


@timeit
@aws_handle_regions
def get_lambda_function_details(
    boto3_session: boto3.session.Session,
    data: List[Dict[str, Any]],
    region: str,
) -> List[Tuple[str, List[Any], List[Any], List[Any]]]:
    client = boto3_session.client("lambda", region_name=region)
    details: List[Tuple[str, List[Any], List[Any], List[Any]]] = []
    for lambda_function in data:
        function_aliases = get_function_aliases(lambda_function, client)
        event_source_mappings = get_event_source_mappings(lambda_function, client)
        layers = lambda_function.get("Layers", [])
        details.append(
            (
                lambda_function["FunctionArn"],
                function_aliases,
                event_source_mappings,
                layers,
            )
        )
    return details


@timeit
def load_lambda_function_aliases(
    neo4j_session: neo4j.Session,
    lambda_aliases: List[Dict[str, Any]],
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        LambdaAliasSchema(),
        lambda_aliases,
        lastupdated=update_tag,
    )


@timeit
def load_lambda_event_source_mappings(
    neo4j_session: neo4j.Session,
    lambda_event_source_mappings: List[Dict[str, Any]],
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        LambdaEventSourceMappingSchema(),
        lambda_event_source_mappings,
        lastupdated=update_tag,
    )


@timeit
def load_lambda_layers(
    neo4j_session: neo4j.Session,
    lambda_layers: List[Dict[str, Any]],
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        LambdaLayerSchema(),
        lambda_layers,
        lastupdated=update_tag,
    )


@timeit
def load_lambda_function_details(
    neo4j_session: neo4j.Session,
    lambda_function_details: List[Tuple[str, List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]],
    update_tag: int,
) -> None:
    lambda_aliases: List[Dict[str, Any]] = []
    lambda_event_source_mappings: List[Dict[str, Any]] = []
    lambda_layers: List[Dict[str, Any]] = []
    for function_arn, aliases, event_source_mappings, layers in lambda_function_details:
        for alias in aliases:
            alias["FunctionArn"] = function_arn
        lambda_aliases.extend(aliases)
        for esm in event_source_mappings:
            esm["FunctionArn"] = function_arn
        lambda_event_source_mappings.extend(event_source_mappings)
        for layer in layers:
            layer["FunctionArn"] = function_arn
        lambda_layers.extend(layers)

    load_lambda_function_aliases(neo4j_session, lambda_aliases, update_tag)
    load_lambda_event_source_mappings(neo4j_session, lambda_event_source_mappings, update_tag)
    load_lambda_layers(neo4j_session, lambda_layers, update_tag)


@timeit
def cleanup_lambda(neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]) -> None:
    GraphJob.from_node_schema(LambdaFunctionSchema(), common_job_parameters).run(neo4j_session)
    GraphJob.from_node_schema(LambdaAliasSchema(), common_job_parameters).run(neo4j_session)
    GraphJob.from_node_schema(LambdaEventSourceMappingSchema(), common_job_parameters).run(neo4j_session)
    GraphJob.from_node_schema(LambdaLayerSchema(), common_job_parameters).run(neo4j_session)


@timeit
def sync_lambda_functions(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: List[str],
    current_aws_account_id: str,
    aws_update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    for region in regions:
        logger.info(
            "Syncing Lambda for region in '%s' in account '%s'.",
            region,
            current_aws_account_id,
        )
        raw_data = get_lambda_data(boto3_session, region)
        transformed = transform_lambda_functions(raw_data)
        load_lambda_functions(
            neo4j_session,
            transformed,
            region,
            current_aws_account_id,
            aws_update_tag,
        )
        lambda_function_details = get_lambda_function_details(
            boto3_session,
            raw_data,
            region,
        )
        load_lambda_function_details(
            neo4j_session,
            lambda_function_details,
            aws_update_tag,
        )

    cleanup_lambda(neo4j_session, common_job_parameters)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: List[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    sync_lambda_functions(
        neo4j_session,
        boto3_session,
        regions,
        current_aws_account_id,
        update_tag,
        common_job_parameters,
    )

