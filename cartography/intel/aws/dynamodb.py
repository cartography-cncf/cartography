import logging
from typing import Any

import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.aws.ec2.util import get_botocore_config
from cartography.models.aws.dynamodb.archival import DynamoDBArchivalSummarySchema
from cartography.models.aws.dynamodb.backups import DynamoDBBackupSchema
from cartography.models.aws.dynamodb.billing import DynamoDBBillingModeSummarySchema
from cartography.models.aws.dynamodb.gsi import DynamoDBGSISchema
from cartography.models.aws.dynamodb.restore import DynamoDBRestoreSummarySchema
from cartography.models.aws.dynamodb.sse import DynamoDBSSEDescriptionSchema
from cartography.models.aws.dynamodb.streams import DynamoDBStreamSchema
from cartography.models.aws.dynamodb.tables import DynamoDBTableSchema
from cartography.stats import get_stats_client
from cartography.util import aws_handle_regions
from cartography.util import merge_module_sync_metadata
from cartography.util import timeit

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)


@timeit
@aws_handle_regions
def get_dynamodb_tables(
    boto3_session: boto3.session.Session,
    region: str,
) -> list[dict]:
    client = boto3_session.client(
        "dynamodb",
        region_name=region,
        config=get_botocore_config(),
    )
    paginator = client.get_paginator("list_tables")
    dynamodb_tables = []
    for page in paginator.paginate():
        for table_name in page["TableNames"]:
            dynamodb_tables.append(client.describe_table(TableName=table_name))
    return dynamodb_tables


@timeit
def transform_dynamodb_tables(
    dynamodb_tables: list[dict],
    region: str,
) -> tuple[
    list[dict[str, Any]],  # table_nodes
    list[dict[str, Any]],  # gsi_nodes
    list[dict[str, Any]],  # billing_nodes
    list[dict[str, Any]],  # stream_nodes
    list[dict[str, Any]],  # sse_nodes
    list[dict[str, Any]],  # archival_nodes
    list[dict[str, Any]],  # restore_nodes
    list[dict[str, Any]],  # backup_nodes (stubs)
]:
    """
    Transform DynamoDB table data for Neo4j ingestion.
    Extracts nested objects into separate entity data lists.
    """
    table_nodes: list[dict[str, Any]] = []
    gsi_nodes: list[dict[str, Any]] = []
    billing_nodes: list[dict[str, Any]] = []
    stream_nodes: list[dict[str, Any]] = []
    sse_nodes: list[dict[str, Any]] = []
    archival_nodes: list[dict[str, Any]] = []
    restore_nodes: list[dict[str, Any]] = []
    backup_arns: set = set()  # Collect unique backup ARNs

    for entry in dynamodb_tables:
        table_data = entry["Table"]
        table_arn = table_data["TableArn"]

        # Core table properties
        table_nodes.append(
            {
                "Arn": table_arn,
                "TableName": table_data["TableName"],
                "Region": region,
                "Rows": table_data.get("ItemCount"),
                "Size": table_data.get("TableSizeBytes"),
                "TableStatus": table_data.get("TableStatus"),
                "CreationDateTime": table_data.get("CreationDateTime"),
                "ProvisionedThroughputReadCapacityUnits": table_data[
                    "ProvisionedThroughput"
                ]["ReadCapacityUnits"],
                "ProvisionedThroughputWriteCapacityUnits": table_data[
                    "ProvisionedThroughput"
                ]["WriteCapacityUnits"],
            }
        )

        # Transform GSIs
        for gsi in table_data.get("GlobalSecondaryIndexes", []):
            gsi_nodes.append(
                {
                    "Arn": gsi["IndexArn"],
                    "TableArn": table_arn,
                    "Region": region,
                    "GSIName": gsi["IndexName"],
                    "ProvisionedThroughputReadCapacityUnits": gsi[
                        "ProvisionedThroughput"
                    ]["ReadCapacityUnits"],
                    "ProvisionedThroughputWriteCapacityUnits": gsi[
                        "ProvisionedThroughput"
                    ]["WriteCapacityUnits"],
                }
            )

        billing = table_data.get("BillingModeSummary", {})
        if billing:
            billing_nodes.append(
                {
                    "Id": f"{table_arn}/billing",
                    "TableArn": table_arn,
                    "BillingMode": billing.get("BillingMode"),
                    "LastUpdateToPayPerRequestDateTime": billing.get(
                        "LastUpdateToPayPerRequestDateTime"
                    ),
                }
            )

        # Transform Stream
        stream_arn = table_data.get("LatestStreamArn")
        stream_spec = table_data.get("StreamSpecification", {})
        if stream_arn and stream_spec:
            stream_nodes.append(
                {
                    "Arn": stream_arn,
                    "TableArn": table_arn,
                    "StreamLabel": table_data.get("LatestStreamLabel"),
                    "StreamEnabled": stream_spec.get("StreamEnabled"),
                    "StreamViewType": stream_spec.get("StreamViewType"),
                }
            )

        # Transform SSEDescription
        sse = table_data.get("SSEDescription", {})
        if sse:
            sse_nodes.append(
                {
                    "Id": f"{table_arn}/sse",
                    "TableArn": table_arn,
                    "SSEStatus": sse.get("Status"),
                    "SSEType": sse.get("SSEType"),
                    "KMSMasterKeyArn": sse.get("KMSMasterKeyArn"),
                }
            )

        # Transform ArchivalSummary
        archival = table_data.get("ArchivalSummary", {})
        if archival:
            archival_backup_arn = archival.get("ArchivalBackupArn")
            archival_nodes.append(
                {
                    "Id": f"{table_arn}/archival",
                    "TableArn": table_arn,
                    "ArchivalDateTime": archival.get("ArchivalDateTime"),
                    "ArchivalReason": archival.get("ArchivalReason"),
                    "ArchivalBackupArn": archival_backup_arn,
                }
            )
            if archival_backup_arn:
                backup_arns.add(archival_backup_arn)

        # Transform RestoreSummary
        restore = table_data.get("RestoreSummary", {})
        if restore:
            source_backup_arn = restore.get("SourceBackupArn")
            restore_nodes.append(
                {
                    "Id": f"{table_arn}/restore",
                    "TableArn": table_arn,
                    "RestoreDateTime": restore.get("RestoreDateTime"),
                    "RestoreInProgress": restore.get("RestoreInProgress"),
                    "SourceBackupArn": source_backup_arn,
                    "SourceTableArn": restore.get("SourceTableArn"),
                }
            )
            if source_backup_arn:
                backup_arns.add(source_backup_arn)

    # Create backup stub nodes from collected ARNs
    backup_nodes = [{"Arn": arn} for arn in backup_arns]

    return (
        table_nodes,
        gsi_nodes,
        billing_nodes,
        stream_nodes,
        sse_nodes,
        archival_nodes,
        restore_nodes,
        backup_nodes,
    )


@timeit
def load_dynamodb_tables(
    neo4j_session: neo4j.Session,
    tables_data: list[dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    logger.info(
        f"Loading DynamoDB tables ({len(tables_data)}) for region '{region}' into graph.",
    )
    load(
        neo4j_session,
        DynamoDBTableSchema(),
        tables_data,
        lastupdated=aws_update_tag,
        Region=region,
        AWS_ID=current_aws_account_id,
    )


@timeit
def load_dynamodb_gsi(
    neo4j_session: neo4j.Session,
    gsi_data: list[dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    logger.info(
        f"Loading DynamoDB GSIs ({len(gsi_data)}) for region '{region}' into graph.",
    )
    load(
        neo4j_session,
        DynamoDBGSISchema(),
        gsi_data,
        lastupdated=aws_update_tag,
        Region=region,
        AWS_ID=current_aws_account_id,
    )


@timeit
def load_dynamodb_billing(
    neo4j_session: neo4j.Session,
    billing_data: list[dict[str, Any]],
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    logger.info(
        f"Loading DynamoDB billing summaries ({len(billing_data)}) into graph.",
    )
    load(
        neo4j_session,
        DynamoDBBillingModeSummarySchema(),
        billing_data,
        lastupdated=aws_update_tag,
        AWS_ID=current_aws_account_id,
    )


@timeit
def load_dynamodb_streams(
    neo4j_session: neo4j.Session,
    stream_data: list[dict[str, Any]],
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    logger.info(
        f"Loading DynamoDB streams ({len(stream_data)}) into graph.",
    )
    load(
        neo4j_session,
        DynamoDBStreamSchema(),
        stream_data,
        lastupdated=aws_update_tag,
        AWS_ID=current_aws_account_id,
    )


@timeit
def load_dynamodb_sse(
    neo4j_session: neo4j.Session,
    sse_data: list[dict[str, Any]],
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    logger.info(
        f"Loading DynamoDB SSE descriptions ({len(sse_data)}) into graph.",
    )
    load(
        neo4j_session,
        DynamoDBSSEDescriptionSchema(),
        sse_data,
        lastupdated=aws_update_tag,
        AWS_ID=current_aws_account_id,
    )


@timeit
def load_dynamodb_archival(
    neo4j_session: neo4j.Session,
    archival_data: list[dict[str, Any]],
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    logger.info(
        f"Loading DynamoDB archival summaries ({len(archival_data)}) into graph.",
    )
    load(
        neo4j_session,
        DynamoDBArchivalSummarySchema(),
        archival_data,
        lastupdated=aws_update_tag,
        AWS_ID=current_aws_account_id,
    )


@timeit
def load_dynamodb_restore(
    neo4j_session: neo4j.Session,
    restore_data: list[dict[str, Any]],
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    logger.info(
        f"Loading DynamoDB restore summaries ({len(restore_data)}) into graph.",
    )
    load(
        neo4j_session,
        DynamoDBRestoreSummarySchema(),
        restore_data,
        lastupdated=aws_update_tag,
        AWS_ID=current_aws_account_id,
    )


@timeit
def load_dynamodb_backups(
    neo4j_session: neo4j.Session,
    backup_data: list[dict[str, Any]],
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    logger.info(
        f"Loading DynamoDB backup stubs ({len(backup_data)}) into graph.",
    )
    load(
        neo4j_session,
        DynamoDBBackupSchema(),
        backup_data,
        lastupdated=aws_update_tag,
        AWS_ID=current_aws_account_id,
    )


@timeit
def cleanup_dynamodb(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict,
) -> None:
    """Clean up all DynamoDB entities."""
    GraphJob.from_node_schema(DynamoDBTableSchema(), common_job_parameters).run(
        neo4j_session,
    )
    GraphJob.from_node_schema(DynamoDBGSISchema(), common_job_parameters).run(
        neo4j_session,
    )
    GraphJob.from_node_schema(
        DynamoDBBillingModeSummarySchema(), common_job_parameters
    ).run(neo4j_session)
    GraphJob.from_node_schema(DynamoDBStreamSchema(), common_job_parameters).run(
        neo4j_session,
    )
    GraphJob.from_node_schema(
        DynamoDBSSEDescriptionSchema(), common_job_parameters
    ).run(
        neo4j_session,
    )
    GraphJob.from_node_schema(
        DynamoDBArchivalSummarySchema(), common_job_parameters
    ).run(neo4j_session)
    GraphJob.from_node_schema(
        DynamoDBRestoreSummarySchema(), common_job_parameters
    ).run(
        neo4j_session,
    )
    GraphJob.from_node_schema(DynamoDBBackupSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync_dynamodb_tables(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: list[str],
    current_aws_account_id: str,
    aws_update_tag: int,
    common_job_parameters: dict,
) -> None:
    for region in regions:
        logger.info(
            "Syncing DynamoDB for region '%s' in account '%s'.",
            region,
            current_aws_account_id,
        )
        dynamodb_tables = get_dynamodb_tables(boto3_session, region)
        (
            table_data,
            gsi_data,
            billing_data,
            stream_data,
            sse_data,
            archival_data,
            restore_data,
            backup_data,
        ) = transform_dynamodb_tables(dynamodb_tables, region)

        # Load tables first (they are the parent for child entities)
        load_dynamodb_tables(
            neo4j_session,
            table_data,
            region,
            current_aws_account_id,
            aws_update_tag,
        )
        load_dynamodb_gsi(
            neo4j_session,
            gsi_data,
            region,
            current_aws_account_id,
            aws_update_tag,
        )

        # Load backup stubs before archival/restore (they reference backups)
        load_dynamodb_backups(
            neo4j_session,
            backup_data,
            current_aws_account_id,
            aws_update_tag,
        )

        # Load child entities
        load_dynamodb_billing(
            neo4j_session, billing_data, current_aws_account_id, aws_update_tag
        )
        load_dynamodb_streams(
            neo4j_session, stream_data, current_aws_account_id, aws_update_tag
        )
        load_dynamodb_sse(
            neo4j_session, sse_data, current_aws_account_id, aws_update_tag
        )
        load_dynamodb_archival(
            neo4j_session, archival_data, current_aws_account_id, aws_update_tag
        )
        load_dynamodb_restore(
            neo4j_session, restore_data, current_aws_account_id, aws_update_tag
        )

    cleanup_dynamodb(neo4j_session, common_job_parameters)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: list[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: dict,
) -> None:
    sync_dynamodb_tables(
        neo4j_session,
        boto3_session,
        regions,
        current_aws_account_id,
        update_tag,
        common_job_parameters,
    )
    merge_module_sync_metadata(
        neo4j_session,
        group_type="AWSAccount",
        group_id=current_aws_account_id,
        synced_type="DynamoDBTable",
        update_tag=update_tag,
        stat_handler=stat_handler,
    )
