import logging
from typing import Any
from typing import Dict
from typing import List
from typing import Tuple

import boto3
import botocore
import neo4j

from cartography.util import aws_handle_regions
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_lambda_data(boto3_session: boto3.session.Session, region: str) -> List[Dict]:
    """
    Create an Lambda boto3 client and grab all the lambda functions.
    """
    client = boto3_session.client("lambda", region_name=region)
    paginator = client.get_paginator("list_functions")
    lambda_functions = []
    for page in paginator.paginate():
        for each_function in page["Functions"]:
            lambda_functions.append(each_function)
    return lambda_functions


@timeit
def load_lambda_functions(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    ingest_lambda_functions = """
    UNWIND $lambda_functions_list AS lf
        MERGE (lambda:AWSLambda{id: lf.FunctionArn})
        ON CREATE SET lambda.firstseen = timestamp()
        SET lambda.name = lf.FunctionName,
        lambda.modifieddate = lf.LastModified,
        lambda.runtime = lf.Runtime,
        lambda.description = lf.Description,
        lambda.timeout = lf.Timeout,
        lambda.memory = lf.MemorySize,
        lambda.codesize = lf.CodeSize,
        lambda.handler = lf.Handler,
        lambda.version = lf.Version,
        lambda.tracingconfigmode = lf.TracingConfig.Mode,
        lambda.revisionid = lf.RevisionId,
        lambda.state = lf.State,
        lambda.statereason = lf.StateReason,
        lambda.statereasoncode = lf.StateReasonCode,
        lambda.lastupdatestatus = lf.LastUpdateStatus,
        lambda.lastupdatestatusreason = lf.LastUpdateStatusReason,
        lambda.lastupdatestatusreasoncode = lf.LastUpdateStatusReasonCode,
        lambda.packagetype = lf.PackageType,
        lambda.signingprofileversionarn = lf.SigningProfileVersionArn,
        lambda.signingjobarn = lf.SigningJobArn,
        lambda.codesha256 = lf.CodeSha256,
        lambda.architectures = lf.Architectures,
        lambda.masterarn = lf.MasterArn,
        lambda.kmskeyarn = lf.KMSKeyArn,
        lambda.lastupdated = $aws_update_tag
        WITH lambda, lf
        MATCH (owner:AWSAccount{id: $AWS_ACCOUNT_ID})
        MERGE (owner)-[r:RESOURCE]->(lambda)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $aws_update_tag
        WITH lambda, lf
        MATCH (role:AWSPrincipal{arn: lf.Role})
        MERGE (lambda)-[r:STS_ASSUMEROLE_ALLOW]->(role)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $aws_update_tag
    """

    neo4j_session.run(
        ingest_lambda_functions,
        lambda_functions_list=data,
        Region=region,
        AWS_ACCOUNT_ID=current_aws_account_id,
        aws_update_tag=aws_update_tag,
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
def get_lambda_function_details(
    boto3_session: boto3.session.Session,
    data: List[Dict],
    region: str,
) -> List[Tuple[str, List[Any], List[Any], List[Any]]]:
    client = boto3_session.client("lambda", region_name=region)
    details = []
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
            ),
        )
    return details


@timeit
def load_lambda_function_details(
    neo4j_session: neo4j.Session,
    lambda_function_details: List[Tuple[str, List[Dict], List[Dict], List[Dict]]],
    update_tag: int,
) -> None:
    lambda_aliases: List[Dict] = []
    lambda_event_source_mappings: List[Dict] = []
    lambda_layers: List[Dict] = []
    for function_arn, aliases, event_source_mappings, layers in lambda_function_details:
        if len(aliases) > 0:
            for alias in aliases:
                alias["FunctionArn"] = function_arn
            lambda_aliases.extend(aliases)
        if len(event_source_mappings) > 0:
            lambda_event_source_mappings.extend(event_source_mappings)
        if len(layers) > 0:
            for layer in layers:
                layer["FunctionArn"] = function_arn
            lambda_layers.extend(layers)

    _load_lambda_function_aliases(neo4j_session, lambda_aliases, update_tag)
    _load_lambda_event_source_mappings(
        neo4j_session,
        lambda_event_source_mappings,
        update_tag,
    )
    _load_lambda_layers(neo4j_session, lambda_layers, update_tag)


@timeit
def _load_lambda_function_aliases(
    neo4j_session: neo4j.Session,
    lambda_aliases: List[Dict],
    update_tag: int,
) -> None:
    ingest_aliases = """
    UNWIND $aliases_list AS alias
        MERGE (a:AWSLambdaFunctionAlias{id: alias.AliasArn})
        ON CREATE SET a.firstseen = timestamp()
        SET a.aliasname = alias.Name,
        a.functionversion = alias.FunctionVersion,
        a.description = alias.Description,
        a.revisionid = alias.RevisionId,
        a.lastupdated = $aws_update_tag
        WITH a, alias
        MATCH (lambda:AWSLambda{id: alias.FunctionArn})
        MERGE (lambda)-[r:KNOWN_AS]->(a)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $aws_update_tag
    """

    neo4j_session.run(
        ingest_aliases,
        aliases_list=lambda_aliases,
        aws_update_tag=update_tag,
    )


@timeit
def _load_lambda_event_source_mappings(
    neo4j_session: neo4j.Session,
    lambda_event_source_mappings: List[Dict],
    update_tag: int,
) -> None:
    ingest_esms = """
    UNWIND $esm_list AS esm
        MERGE (e:AWSLambdaEventSourceMapping{id: esm.UUID})
        ON CREATE SET e.firstseen = timestamp()
        SET e.batchsize = esm.BatchSize,
        e.startingposition = esm.StartingPosition,
        e.startingpositiontimestamp = esm.StartingPositionTimestamp,
        e.parallelizationfactor = esm.ParallelizationFactor,
        e.maximumbatchingwindowinseconds = esm.MaximumBatchingWindowInSeconds,
        e.eventsourcearn = esm.EventSourceArn,
        e.lastmodified = esm.LastModified,
        e.lastprocessingresult = esm.LastProcessingResult,
        e.state = esm.State,
        e.maximumrecordage = esm.MaximumRecordAgeInSeconds,
        e.bisectbatchonfunctionerror = esm.BisectBatchOnFunctionError,
        e.maximumretryattempts = esm.MaximumRetryAttempts,
        e.tumblingwindowinseconds = esm.TumblingWindowInSeconds,
        e.lastupdated = $aws_update_tag
        WITH e, esm
        MATCH (lambda:AWSLambda{id: esm.FunctionArn})
        MERGE (lambda)-[r:RESOURCE]->(e)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $aws_update_tag
    """

    neo4j_session.run(
        ingest_esms,
        esm_list=lambda_event_source_mappings,
        aws_update_tag=update_tag,
    )


@timeit
def _load_lambda_layers(
    neo4j_session: neo4j.Session,
    lambda_layers: List[Dict],
    update_tag: int,
) -> None:
    ingest_layers = """
    UNWIND $layers_list AS layer
        MERGE (l:AWSLambdaLayer{id: layer.Arn})
        ON CREATE SET l.firstseen = timestamp()
        SET l.codesize = layer.CodeSize,
        l.signingprofileversionarn  = layer.SigningProfileVersionArn,
        l.signingjobarn = layer.SigningJobArn,
        l.lastupdated = $aws_update_tag
        WITH l, layer
        MATCH (lambda:AWSLambda{id: layer.FunctionArn})
        MERGE (lambda)-[r:HAS]->(l)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $aws_update_tag
    """

    neo4j_session.run(
        ingest_layers,
        layers_list=lambda_layers,
        aws_update_tag=update_tag,
    )


@timeit
def cleanup_lambda(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job(
        "aws_import_lambda_cleanup.json",
        neo4j_session,
        common_job_parameters,
    )


@timeit
def sync_lambda_functions(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: List[str],
    current_aws_account_id: str,
    aws_update_tag: int,
    common_job_parameters: Dict,
) -> None:
    for region in regions:
        logger.info(
            "Syncing Lambda for region in '%s' in account '%s'.",
            region,
            current_aws_account_id,
        )
        data = get_lambda_data(boto3_session, region)
        load_lambda_functions(
            neo4j_session,
            data,
            region,
            current_aws_account_id,
            aws_update_tag,
        )
        lambda_function_details = get_lambda_function_details(
            boto3_session,
            data,
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
    common_job_parameters: Dict,
) -> None:
    sync_lambda_functions(
        neo4j_session,
        boto3_session,
        regions,
        current_aws_account_id,
        update_tag,
        common_job_parameters,
    )
