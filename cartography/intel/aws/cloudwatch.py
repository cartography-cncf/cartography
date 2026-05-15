import logging
import time
from typing import Dict
from typing import List

import boto3
import neo4j
from botocore.exceptions import ClientError
from cloudconsolelink.clouds.aws import AWSLinker

from cartography.intel.aws.ec2.util import get_botocore_config
from cartography.util import aws_handle_regions
from cartography.util import batch
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)
aws_console_link = AWSLinker()


@timeit
@aws_handle_regions
def get_event_buses(boto3_session: boto3.session.Session, region):
    response = {}
    try:
        client = boto3_session.client("events", region_name=region, config=get_botocore_config())
        response = client.list_event_buses()

    except ClientError as e:
        logger.error(f"Failed to call EventBridge list_event_buses for region: {region} - {e}")

    event_buses = response.get("EventBuses", [])
    while "NextToken" in response:
        try:
            response = client.list_event_buses(NextToken=response["NextToken"])
            event_buses.extend(response.get("EventBuses", []))

        except ClientError as e:
            logger.error(f"Failed to call EventBridge list_event_buses for region {region} - {e}")

    return event_buses


@timeit
def transform_event_buses(buses: List[Dict], region: str) -> List[Dict]:
    event_buses = []
    for event_bus in buses:
        event_bus["region"] = region
        event_bus["arn"] = event_bus["Arn"]
        event_bus["consolelink"] = aws_console_link.get_console_link(arn=event_bus["arn"])
        event_buses.append(event_bus)

    return event_buses


def load_event_buses(
    session: neo4j.Session,
    event_buses: List[Dict],
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    session.execute_write(_load_event_buses_tx, event_buses, current_aws_account_id, aws_update_tag)


@timeit
def _load_event_buses_tx(
    tx: neo4j.Transaction,
    event_buses: List[Dict],
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    query: str = """
    UNWIND $Records as record
    MERGE (bus:AWSEventBridgeEventBus{id: record.Arn})
    ON CREATE SET bus.firstseen = timestamp(),
        bus.arn = record.Arn
    SET bus.lastupdated = $aws_update_tag,
        bus.name = record.Name,
        bus.consolelink = record.consolelink,
        bus.region = record.region,
        bus.policy = record.Policy
    WITH bus
    MATCH (owner:AWSAccount{id: $AWS_ACCOUNT_ID})
    MERGE (owner)-[r:RESOURCE]->(bus)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $aws_update_tag
    """

    tx.run(
        query,
        Records=event_buses,
        AWS_ACCOUNT_ID=current_aws_account_id,
        aws_update_tag=aws_update_tag,
    )


@timeit
def cleanup_event_buses(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job("aws_import_cloudwatch_event_buses_cleanup.json", neo4j_session, common_job_parameters)


@timeit
@aws_handle_regions
def get_event_rules(boto3_session: boto3.session.Session, region, account_id):
    event_rules = []
    try:
        client = boto3_session.client("events", region_name=region, config=get_botocore_config())
        paginator = client.get_paginator("list_rules")

        page_iterator = paginator.paginate()
        for page in page_iterator:
            event_rules.extend(page["Rules"])

    except ClientError as e:
        logger.error(f"Failed to call CloudWatch event list_rules: {region} - {e}")
    return event_rules


@timeit
def transform_rules(rules: List[Dict], region: str, account_id) -> List[Dict]:
    event_rules = []
    for event_rule in rules:
        console_arn = f"arn:aws:cloudwatch:{region if region else ''}:{account_id if account_id else ''}:rule/{event_rule['Name']}"
        event_rule["consolelink"] = aws_console_link.get_console_link(arn=console_arn)
        event_rule["region"] = region
        event_rules.append(event_rule)

    return event_rules


def load_event_rules(
    session: neo4j.Session,
    event_buses: List[Dict],
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    session.execute_write(_load_event_rules_tx, event_buses, current_aws_account_id, aws_update_tag)


@timeit
def _load_event_rules_tx(
    tx: neo4j.Transaction,
    event_buses: List[Dict],
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    query: str = """
    UNWIND $Records as record
    MERGE (rule:AWSEventBridgeRule{id: record.Arn})
    ON CREATE SET rule.firstseen = timestamp(),
        rule.arn = record.Arn
    SET rule.lastupdated = $aws_update_tag,
        rule.name = record.Name,
        rule.region = record.region,
        rule.consolelink = record.consolelink,
        rule.event_bus_name = record.EventBusName,
        rule.event_pattern = record.EventPattern,
        rule.managed_by = record.ManagedBy,
        rule.schedule_expression = record.ScheduleExpression,
        rule.state = record.State,
        rule.role_arn = record.RoleArn
    WITH rule, record
    MATCH (bus:AWSEventBridgeEventBus{arn:record.EventBusName})
    MERGE (bus)-[rt:HAS]->(rule)
    ON CREATE SET
        rt.firstseen = timestamp()
    SET rt.lastupdated = $aws_update_tag
    WITH rule
    MATCH (owner:AWSAccount{id: $AWS_ACCOUNT_ID})
    MERGE (owner)-[r:RESOURCE]->(rule)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $aws_update_tag
    """

    tx.run(
        query,
        Records=event_buses,
        AWS_ACCOUNT_ID=current_aws_account_id,
        aws_update_tag=aws_update_tag,
    )


@timeit
def cleanup_event_rules(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job("aws_import_cloudwatch_event_rules_cleanup.json", neo4j_session, common_job_parameters)


@timeit
@aws_handle_regions
def get_log_groups(boto3_session: boto3.session.Session, region):
    log_groups = []
    try:
        client = boto3_session.client("logs", region_name=region, config=get_botocore_config())
        paginator = client.get_paginator("describe_log_groups")

        page_iterator = paginator.paginate()
        for page in page_iterator:
            log_groups.extend(page["logGroups"])

    except ClientError as e:
        if e.response["Error"]["Code"] in ["NotFoundException"]:
            logger.debug(f"Failed to call CloudWatch Logs describe_log_groups: {region} - {e}")

        else:
            logger.error(f"Failed to call CloudWatch Logs describe_log_groups: {region} - {e}")

    return log_groups


@timeit
def transform_log_groups(boto3_session: boto3.session.Session, groups: List, region: str) -> List[Dict]:
    log_groups = []
    try:
        kms_client = boto3_session.client("kms", region_name=region, config=get_botocore_config())
        for log_group in groups:
            log_group["arn"] = log_group["arn"]
            log_group["arn"].replace("/", "$252F")
            log_group["consolelink"] = aws_console_link.get_console_link(arn=log_group["arn"])
            log_group["region"] = region
            if log_group.get("kmsKeyId"):
                log_group["kms"] = kms_client.describe_key(
                    KeyId=log_group.get(
                        "kmsKeyId",
                        None,
                    ).split("/")[1],
                ).get("KeyMetadata", {})
            log_groups.append(log_group)
    except ClientError as e:
        logger.error(f"Failed to call CloudWatch Logs describe_log_groups: {region} - {e}")

    return log_groups


def load_log_groups(
    session: neo4j.Session,
    log_groups: List[Dict],
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    session.execute_write(_load_log_groups_tx, log_groups, current_aws_account_id, aws_update_tag)


@timeit
def _load_log_groups_tx(
    tx: neo4j.Transaction,
    log_groups: List[Dict],
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    query: str = """
    UNWIND $Records as record
    MERGE (gr:AWSCloudWatchLogGroup{id: record.arn})
    ON CREATE SET gr.firstseen = timestamp(),
        gr.arn = record.arn
    SET gr.lastupdated = $aws_update_tag,
        gr.name = record.logGroupName,
        gr.region = record.region,
        gr.stored_bytes = record.storedBytes,
        gr.consolelink = record.consolelink,
        gr.metric_filter_count = record.metricFilterCount,
        gr.creation_time = record.creationTime,
        gr.retention_in_days = record.retentionInDays,
        gr.aws_account_id = record.kms.AWSAccountId,
        gr.kms_key_id = record.kms.kmsKeyId,
        gr.key_enabled = record.kms.Enabled,
        gr.Key_usage = record.kms.KeyUsage,
        gr.Key_state = record.kms.KeyState,
        gr.Key_manager = record.kms.KeyManager
    WITH gr
    MATCH (owner:AWSAccount{id: $AWS_ACCOUNT_ID})
    MERGE (owner)-[r:RESOURCE]->(gr)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $aws_update_tag
    """

    tx.run(
        query,
        Records=log_groups,
        AWS_ACCOUNT_ID=current_aws_account_id,
        aws_update_tag=aws_update_tag,
    )


@timeit
def cleanup_log_groups(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job("aws_import_cloudwatch_log_groups_cleanup.json", neo4j_session, common_job_parameters)


@timeit
@aws_handle_regions
def get_metrics(boto3_session: boto3.session.Session, region):
    metrics = []
    try:
        client = boto3_session.client("cloudwatch", region_name=region, config=get_botocore_config())
        paginator = client.get_paginator("list_metrics")

        page_iterator = paginator.paginate()
        for page in page_iterator:
            metrics.extend(page["Metrics"])

    except ClientError as e:
        if e.response["Error"]["Code"] in ["AccessDenied"]:
            logger.debug(f"Failed to call CloudWatch list_metrics: {region} - {e}")

        else:
            logger.error(f"Failed to call CloudWatch list_metrics: {region} - {e}")

    return metrics


@timeit
def transform_metrics(mets: List[Dict], account_id: str, region: str) -> List[Dict]:
    metrics = []
    for metric in mets:
        console_arn = f"arn:aws:cloudwatch:{region if region else ''}:{account_id if account_id else ''}:metrics/{metric['MetricName']}"
        # metric['consolelink'] = aws_console_link.get_console_link(console_arn)
        metric["consolelink"] = aws_console_link.get_console_link(console_arn)
        metric["arn"] = f"arn:aws:cloudwatch:{region}:{account_id}:metrics/{metric['MetricName']}"
        metric["region"] = region
        metrics.append(metric)

    return metrics


def load_metrics(session: neo4j.Session, metrics: List[Dict], current_aws_account_id: str, aws_update_tag: int) -> None:
    batch_size = 500
    page_no = 0
    for paginated_metrics in batch(metrics, size=batch_size):
        logger.info(
            f"Loading metrics {page_no * batch_size} - {page_no * batch_size + batch_size} out of {len(metrics)}",
        )
        session.execute_write(_load_metrics_tx, paginated_metrics, current_aws_account_id, aws_update_tag)
        page_no += 1


@timeit
def _load_metrics_tx(
    tx: neo4j.Transaction,
    metrics: List[Dict],
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    query: str = """
    UNWIND $Records as record
    MERGE (metric:AWSCloudWatchMetric{id: record.arn})
    ON CREATE SET metric.firstseen = timestamp(),
        metric.arn = record.arn
    SET metric.lastupdated = $aws_update_tag,
        metric.name = record.MetricName,
        metric.consolelink = record.consolelink,
        metric.region = record.region,
        metric.namespace = record.Namespace
    WITH metric
    MATCH (owner:AWSAccount{id: $AWS_ACCOUNT_ID})
    MERGE (owner)-[r:RESOURCE]->(metric)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $aws_update_tag
    """

    tx.run(
        query,
        Records=metrics,
        AWS_ACCOUNT_ID=current_aws_account_id,
        aws_update_tag=aws_update_tag,
    )


@timeit
def cleanup_metrics(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job("aws_import_cloudwatch_metrics_cleanup.json", neo4j_session, common_job_parameters)


@timeit
@aws_handle_regions
def get_cloudwatch_alarm(boto3_session: boto3.session.Session, region: str) -> List[Dict]:
    alarms = []
    try:
        client = boto3_session.client("cloudwatch", region_name=region, config=get_botocore_config())
        paginator = client.get_paginator("describe_alarms")

        page_iterator = paginator.paginate()
        for page in page_iterator:
            alarms.extend(page["MetricAlarms"])

        return alarms

    except ClientError as e:
        logger.error(f"Failed to call CloudWatch describe_alarms: {region} - {e}")
        return alarms


@timeit
def transform_alarms(alms: List[Dict], region: str) -> List[Dict]:
    alarms = []
    for alarm in alms:
        alarm["arn"] = alarm["AlarmArn"]
        alarm["consolelink"] = aws_console_link.get_console_link(arn=alarm["arn"])
        alarm["region"] = region
        alarms.append(alarm)

    return alarms


def load_cloudwatch_alarm(
    session: neo4j.Session,
    alarms: List[Dict],
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    session.execute_write(_load_cloudwatch_alarm_tx, alarms, current_aws_account_id, aws_update_tag)


@timeit
def _load_cloudwatch_alarm_tx(
    tx: neo4j.Transaction,
    alarms: List[Dict],
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    query: str = """
    UNWIND $Records as record
    MERGE (alarm:AWSCloudWatchAlarm{id: record.AlarmArn})
    ON CREATE SET alarm.firstseen = timestamp(),
        alarm.arn = record.AlarmArn
    SET alarm.lastupdated = $aws_update_tag,
        alarm.name = record.AlarmName,
        alarm.region = record.region,
        alarm.alarm_actions = record.AlarmActions,
        alarm.namespace = record.Namespace,
        alarm.consolelink = record.consolelink,
        alarm.period = record.Period,
        alarm.state_value = record.StateValue,
        alarm.statistic = record.Statistic,
        alarm.actions_enabled = record.ActionsEnabled,
        alarm.metric_name = record.MetricName
    WITH alarm
    MATCH (owner:AWSAccount{id: $AWS_ACCOUNT_ID})
    MERGE (owner)-[r:RESOURCE]->(alarm)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $aws_update_tag
    """

    tx.run(
        query,
        Records=alarms,
        AWS_ACCOUNT_ID=current_aws_account_id,
        aws_update_tag=aws_update_tag,
    )


@timeit
def cleanup_cloudwatch_alarm(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job("aws_import_cloudwatch_alarm_cleanup.json", neo4j_session, common_job_parameters)


@timeit
@aws_handle_regions
def get_cloudwatch_flowlogs(boto3_session: boto3.session.Session, region: str) -> List[Dict]:
    flowlogs = []
    try:
        client = boto3_session.client("ec2", region_name=region, config=get_botocore_config())
        paginator = client.get_paginator("describe_flow_logs")

        page_iterator = paginator.paginate()
        for page in page_iterator:
            flowlogs.extend(page["FlowLogs"])

        return flowlogs

    except ClientError as e:
        logger.error(f"Failed to call EC2 describe_flow_logs: {region} - {e}")
        return flowlogs


@timeit
def transform_flow_logs(logs: List[Dict], current_aws_account_id: str, region: str) -> List[Dict]:
    flowlogs = []
    for flowlog in logs:
        flowlog["arn"] = f"arn:aws:ec2:{region}:{current_aws_account_id}:vcp-flow-log/{flowlog['FlowLogId']}"
        flowlog["region"] = region
        flowlogs.append(flowlog)

    return flowlogs


def load_cloudwatch_flowlogs(
    session: neo4j.Session,
    flowlogs: List[Dict],
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    session.execute_write(_load_cloudwatch_flowlogs_tx, flowlogs, current_aws_account_id, aws_update_tag)


@timeit
def _load_cloudwatch_flowlogs_tx(
    tx: neo4j.Transaction,
    flowlogs: List[Dict],
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    query: str = """
    UNWIND $Records as record
    MERGE (log:AWSCloudWatchFlowLog{id: record.arn})
    ON CREATE SET log.firstseen = timestamp(),
        log.arn = record.arn
    SET log.lastupdated = $aws_update_tag,
        log.name = record.FlowLogId,
        log.region = record.region,
        log.creation_time = record.CreationTime,
        log.deliver_logs_status = record.DeliverLogsStatus,
        log.flow_log_id = record.FlowLogId,
        log.flow_log_status = record.FlowLogStatus,
        log.log_group_name = record.LogGroupName,
        log.resource_id = record.ResourceId,
        log.log_destination_type = record.LogDestinationType
    WITH log
    MATCH (owner:AWSAccount{id: $AWS_ACCOUNT_ID})
    MERGE (owner)-[r:RESOURCE]->(log)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $aws_update_tag
    """

    tx.run(
        query,
        Records=flowlogs,
        AWS_ACCOUNT_ID=current_aws_account_id,
        aws_update_tag=aws_update_tag,
    )


@timeit
def cleanup_cloudwatch_flowlogs(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job("aws_import_cloudwatch_flowlog_cleanup.json", neo4j_session, common_job_parameters)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: List[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: Dict,
) -> None:
    tic = time.perf_counter()

    logger.info("Syncing Cloudwatch for account '%s', at %s.", current_aws_account_id, tic)

    alarms = []
    flowlogs = []
    event_buses = []
    log_groups = []
    # metrics = []
    rules = []
    for region in regions:
        logger.info("Syncing Cloudwatch for region '%s' in account '%s'.", region, current_aws_account_id)

        alms = get_cloudwatch_alarm(boto3_session, region)
        alarms.extend(transform_alarms(alms, region))
        flgs = get_cloudwatch_flowlogs(boto3_session, region)
        flowlogs.extend(transform_flow_logs(flgs, current_aws_account_id, region))
        ebs = get_event_buses(boto3_session, region)
        event_buses.extend(transform_event_buses(ebs, region))
        log_g = get_log_groups(boto3_session, region)
        log_groups.extend(transform_log_groups(boto3_session, log_g, region))
        # mets = get_metrics(boto3_session, region)
        # metrics.extend(transform_metrics(mets, current_aws_account_id, region))

    logger.info(f"Total Cloudwatch Alarms: {len(alarms)}")

    logger.info(f"Total Cloudwatch FlowLogs: {len(flowlogs)}")

    logger.info(f"Total Cloudwatch Event Buses: {len(event_buses)}")

    logger.info(f"Total Cloudwatch Log Groups: {len(log_groups)}")

    # logger.info(f"Total Cloudwatch Metrics: {len(metrics)}")

    logger.info(f"Total Cloudwatch Rules: {len(rules)}")

    load_cloudwatch_alarm(neo4j_session, alarms, current_aws_account_id, update_tag)

    cleanup_cloudwatch_alarm(neo4j_session, common_job_parameters)

    load_cloudwatch_flowlogs(neo4j_session, flowlogs, current_aws_account_id, update_tag)

    cleanup_cloudwatch_flowlogs(neo4j_session, common_job_parameters)

    load_event_buses(neo4j_session, event_buses, current_aws_account_id, update_tag)

    cleanup_event_buses(neo4j_session, common_job_parameters)

    load_log_groups(neo4j_session, log_groups, current_aws_account_id, update_tag)

    cleanup_log_groups(neo4j_session, common_job_parameters)

    # load_metrics(neo4j_session, metrics, current_aws_account_id, update_tag)

    # cleanup_metrics(neo4j_session, common_job_parameters)

    for region in regions:
        rls = get_event_rules(boto3_session, region, current_aws_account_id)
        rules.extend(transform_rules(rls, region, current_aws_account_id))

    load_event_rules(neo4j_session, rules, current_aws_account_id, update_tag)

    cleanup_event_rules(neo4j_session, common_job_parameters)

    toc = time.perf_counter()
    logger.info(f"Time to process Cloudwatch: {toc - tic:0.4f} seconds")
