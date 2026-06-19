# Copyright (c) 2020, Oracle and/or its affiliates.
# OCI Monitoring, Events, Notifications, and Cloud Guard API-centric functions
import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j
import oci
import oci.cloud_guard
import oci.events
import oci.monitoring
import oci.ons

from . import utils
from cartography.util import run_cleanup_job

logger = logging.getLogger(__name__)


# ============================================================
# Monitoring Alarms
# ============================================================

def get_alarm_list_data(
    monitoring: oci.monitoring.MonitoringClient,
    compartment_id: str,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Get all monitoring alarms in a compartment.
    """
    try:
        response = oci.pagination.list_call_get_all_results(
            monitoring.list_alarms, compartment_id=compartment_id,
        )
        return {'Alarms': utils.oci_object_to_json(response.data)}
    except oci.exceptions.ServiceError as e:
        logger.warning(
            "Could not retrieve alarms for compartment '%s': %s",
            compartment_id, e.message,
        )
        return {'Alarms': []}


def load_alarms(
    neo4j_session: neo4j.Session,
    alarms: List[Dict[str, Any]],
    tenancy_id: str,
    compartment_id: str,
    region: str,
    oci_update_tag: int,
) -> None:
    """
    Ingest OCI Monitoring Alarm data into Neo4j.
    """
    ingest_alarm = """
    MERGE (a:OCIMonitoringAlarm{id: $OCID})
    ON CREATE SET a.firstseen = timestamp()
    SET a.ocid = $OCID,
    a.display_name = $DISPLAY_NAME,
    a.compartment_id = $COMPARTMENT_ID,
    a.resource_type = 'oci-monitoring-alarm',
    a.namespace = $NAMESPACE,
    a.query = $QUERY,
    a.severity = $SEVERITY,
    a.is_enabled = $IS_ENABLED,
    a.lifecycle_state = $LIFECYCLE_STATE,
    a.metric_compartment_id = $METRIC_COMPARTMENT_ID,
    a.destinations = $DESTINATIONS,
    a.region = $REGION,
    a.lastupdated = $oci_update_tag
    WITH a
    MATCH (cc:OCICompartment{id: $COMPARTMENT_ID})
    MERGE (cc)-[r:RESOURCE]->(a)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $oci_update_tag
    """

    for alarm in alarms:
        neo4j_session.run(
            ingest_alarm,
            OCID=alarm.get("id"),
            DISPLAY_NAME=alarm.get("display-name"),
            COMPARTMENT_ID=alarm.get("compartment-id", compartment_id),
            NAMESPACE=alarm.get("namespace", ""),
            QUERY=alarm.get("query", ""),
            SEVERITY=alarm.get("severity", ""),
            IS_ENABLED=alarm.get("is-enabled", False),
            LIFECYCLE_STATE=alarm.get("lifecycle-state"),
            METRIC_COMPARTMENT_ID=alarm.get("metric-compartment-id", ""),
            DESTINATIONS=alarm.get("destinations", []),
            REGION=region,
            oci_update_tag=oci_update_tag,
        )


def sync_alarms(
    neo4j_session: neo4j.Session,
    monitoring: oci.monitoring.MonitoringClient,
    compartments: List[Dict[str, Any]],
    tenancy_id: str,
    region: str,
    oci_update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    logger.debug("Syncing OCI monitoring alarms for tenancy '%s', region '%s'.", tenancy_id, region)
    for compartment in compartments:
        data = get_alarm_list_data(monitoring, compartment["ocid"])
        if data["Alarms"]:
            load_alarms(
                neo4j_session, data["Alarms"], tenancy_id,
                compartment["ocid"], region, oci_update_tag,
            )


# ============================================================
# Cloud Guard
# ============================================================

def get_cloud_guard_configuration(
    cloud_guard: oci.cloud_guard.CloudGuardClient,
    compartment_id: str,
) -> Dict[str, Any]:
    """
    Get Cloud Guard configuration for a compartment (tenancy root).
    """
    try:
        response = cloud_guard.get_configuration(compartment_id=compartment_id)
        return utils.oci_single_object_to_json(response.data)
    except oci.exceptions.ServiceError as e:
        logger.warning(
            "Could not retrieve Cloud Guard config for compartment '%s': %s",
            compartment_id, e.message,
        )
        return {}


def load_cloud_guard(
    neo4j_session: neo4j.Session,
    config_data: Dict[str, Any],
    tenancy_id: str,
    compartment_id: str,
    region: str,
    oci_update_tag: int,
) -> None:
    """
    Ingest OCI Cloud Guard configuration into Neo4j.
    """
    ingest_cg = """
    MERGE (cg:OCICloudGuard{id: $CONFIG_ID})
    ON CREATE SET cg.firstseen = timestamp()
    SET cg.ocid = $CONFIG_ID,
    cg.resource_type = 'oci-monitoring-cloud-guard',
    cg.compartment_id = $COMPARTMENT_ID,
    cg.status = $STATUS,
    cg.reporting_region = $REPORTING_REGION,
    cg.region = $REGION,
    cg.lastupdated = $oci_update_tag
    WITH cg
    MATCH (cc:OCICompartment{id: $COMPARTMENT_ID})
    MERGE (cc)-[r:RESOURCE]->(cg)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $oci_update_tag
    """

    neo4j_session.run(
        ingest_cg,
        CONFIG_ID=f"oci.cloudguard.{compartment_id}.{region}",
        COMPARTMENT_ID=compartment_id,
        STATUS=config_data.get("status", "DISABLED"),
        REPORTING_REGION=config_data.get("reporting-region", ""),
        REGION=region,
        oci_update_tag=oci_update_tag,
    )


def sync_cloud_guard(
    neo4j_session: neo4j.Session,
    cloud_guard: oci.cloud_guard.CloudGuardClient,
    compartments: List[Dict[str, Any]],
    tenancy_id: str,
    region: str,
    oci_update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    logger.debug("Syncing OCI Cloud Guard for tenancy '%s', region '%s'.", tenancy_id, region)
    for compartment in compartments:
        data = get_cloud_guard_configuration(cloud_guard, compartment["ocid"])
        if data:
            load_cloud_guard(
                neo4j_session, data, tenancy_id,
                compartment["ocid"], region, oci_update_tag,
            )


# ============================================================
# Events Rules
# ============================================================

def get_event_rule_list_data(
    events: oci.events.EventsClient,
    compartment_id: str,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Get all event rules in a compartment.
    """
    try:
        response = oci.pagination.list_call_get_all_results(
            events.list_rules, compartment_id=compartment_id,
        )
        return {'Rules': utils.oci_object_to_json(response.data)}
    except oci.exceptions.ServiceError as e:
        logger.warning(
            "Could not retrieve event rules for compartment '%s': %s",
            compartment_id, e.message,
        )
        return {'Rules': []}


def load_event_rules(
    neo4j_session: neo4j.Session,
    rules: List[Dict[str, Any]],
    tenancy_id: str,
    compartment_id: str,
    region: str,
    oci_update_tag: int,
) -> None:
    """
    Ingest OCI Events Rule data into Neo4j.
    """
    ingest_rule = """
    MERGE (er:OCIEventRule{id: $OCID})
    ON CREATE SET er.firstseen = timestamp(),
    er.createdate = $TIME_CREATED
    SET er.ocid = $OCID,
    er.display_name = $DISPLAY_NAME,
    er.compartment_id = $COMPARTMENT_ID,
    er.resource_type = 'oci-monitoring-event-rule',
    er.condition = $CONDITION,
    er.is_enabled = $IS_ENABLED,
    er.lifecycle_state = $LIFECYCLE_STATE,
    er.description = $DESCRIPTION,
    er.region = $REGION,
    er.lastupdated = $oci_update_tag
    WITH er
    MATCH (cc:OCICompartment{id: $COMPARTMENT_ID})
    MERGE (cc)-[r:RESOURCE]->(er)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $oci_update_tag
    """

    for rule in rules:
        neo4j_session.run(
            ingest_rule,
            OCID=rule.get("id"),
            DISPLAY_NAME=rule.get("display-name"),
            COMPARTMENT_ID=rule.get("compartment-id", compartment_id),
            CONDITION=rule.get("condition", ""),
            IS_ENABLED=rule.get("is-enabled", False),
            LIFECYCLE_STATE=rule.get("lifecycle-state"),
            DESCRIPTION=rule.get("description", ""),
            REGION=region,
            TIME_CREATED=str(rule.get("time-created", "")),
            oci_update_tag=oci_update_tag,
        )


def sync_event_rules(
    neo4j_session: neo4j.Session,
    events: oci.events.EventsClient,
    compartments: List[Dict[str, Any]],
    tenancy_id: str,
    region: str,
    oci_update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    logger.debug("Syncing OCI event rules for tenancy '%s', region '%s'.", tenancy_id, region)
    for compartment in compartments:
        data = get_event_rule_list_data(events, compartment["ocid"])
        if data["Rules"]:
            load_event_rules(
                neo4j_session, data["Rules"], tenancy_id,
                compartment["ocid"], region, oci_update_tag,
            )


# ============================================================
# Notification Topics (ONS)
# ============================================================

def get_notification_topic_list_data(
    ons: oci.ons.NotificationControlPlaneClient,
    compartment_id: str,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Get all notification topics in a compartment.
    """
    try:
        response = oci.pagination.list_call_get_all_results(
            ons.list_topics, compartment_id=compartment_id,
        )
        return {'Topics': utils.oci_object_to_json(response.data)}
    except oci.exceptions.ServiceError as e:
        logger.warning(
            "Could not retrieve notification topics for compartment '%s': %s",
            compartment_id, e.message,
        )
        return {'Topics': []}


def load_notification_topics(
    neo4j_session: neo4j.Session,
    topics: List[Dict[str, Any]],
    tenancy_id: str,
    compartment_id: str,
    region: str,
    oci_update_tag: int,
) -> None:
    """
    Ingest OCI Notification Topic data into Neo4j.
    """
    ingest_topic = """
    MERGE (t:OCINotificationTopic{id: $OCID})
    ON CREATE SET t.firstseen = timestamp(),
    t.createdate = $TIME_CREATED
    SET t.ocid = $OCID,
    t.display_name = $NAME,
    t.compartment_id = $COMPARTMENT_ID,
    t.resource_type = 'oci-monitoring-notification-topic',
    t.topic_id = $TOPIC_ID,
    t.lifecycle_state = $LIFECYCLE_STATE,
    t.description = $DESCRIPTION,
    t.api_endpoint = $API_ENDPOINT,
    t.region = $REGION,
    t.lastupdated = $oci_update_tag
    WITH t
    MATCH (cc:OCICompartment{id: $COMPARTMENT_ID})
    MERGE (cc)-[r:RESOURCE]->(t)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $oci_update_tag
    """

    for topic in topics:
        neo4j_session.run(
            ingest_topic,
            OCID=topic.get("topic-id", topic.get("id", "")),
            NAME=topic.get("name", ""),
            COMPARTMENT_ID=topic.get("compartment-id", compartment_id),
            TOPIC_ID=topic.get("topic-id", ""),
            LIFECYCLE_STATE=topic.get("lifecycle-state"),
            DESCRIPTION=topic.get("description", ""),
            API_ENDPOINT=topic.get("api-endpoint", ""),
            REGION=region,
            TIME_CREATED=str(topic.get("time-created", "")),
            oci_update_tag=oci_update_tag,
        )


def sync_notification_topics(
    neo4j_session: neo4j.Session,
    ons: oci.ons.NotificationControlPlaneClient,
    compartments: List[Dict[str, Any]],
    tenancy_id: str,
    region: str,
    oci_update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    logger.debug(
        "Syncing OCI notification topics for tenancy '%s', region '%s'.",
        tenancy_id, region,
    )
    for compartment in compartments:
        data = get_notification_topic_list_data(ons, compartment["ocid"])
        if data["Topics"]:
            load_notification_topics(
                neo4j_session, data["Topics"], tenancy_id,
                compartment["ocid"], region, oci_update_tag,
            )


# ============================================================
# Top-level sync function
# ============================================================

def sync(
    neo4j_session: neo4j.Session,
    monitoring: oci.monitoring.MonitoringClient,
    tenancy_id: str,
    oci_update_tag: int,
    common_job_parameters: Dict[str, Any],
    regions: List[str] = None,
) -> None:
    """
    Sync OCI Monitoring resources: Alarms, Cloud Guard, Event Rules,
    and Notification Topics.
    """
    compartment_ocid = common_job_parameters.get("OCI_COMPARTMENT_ID", tenancy_id)
    logger.info("Syncing OCI Monitoring for compartment '%s'.", compartment_ocid)

    compartments = [
        {"ocid": compartment_ocid, "name": "target", "compartmentid": tenancy_id},
    ]

    if not regions:
        regions = [monitoring.base_client.region or ""]

    # Create additional clients from the monitoring client's config/signer.
    cloud_guard = oci.cloud_guard.CloudGuardClient(
        config=monitoring.base_client.config,
        signer=getattr(monitoring.base_client, "signer", None),
    )
    events = oci.events.EventsClient(
        config=monitoring.base_client.config,
        signer=getattr(monitoring.base_client, "signer", None),
    )
    ons = oci.ons.NotificationControlPlaneClient(
        config=monitoring.base_client.config,
        signer=getattr(monitoring.base_client, "signer", None),
    )

    for region in regions:
        logger.info(
            "Syncing OCI Monitoring in region '%s' for compartment '%s'.",
            region, compartment_ocid,
        )
        monitoring.base_client.set_region(region)
        cloud_guard.base_client.set_region(region)
        events.base_client.set_region(region)
        ons.base_client.set_region(region)

        # Sync monitoring alarms
        sync_alarms(
            neo4j_session, monitoring, compartments, tenancy_id,
            region, oci_update_tag, common_job_parameters,
        )

        # Sync Cloud Guard configuration
        sync_cloud_guard(
            neo4j_session, cloud_guard, compartments, tenancy_id,
            region, oci_update_tag, common_job_parameters,
        )

        # Sync event rules
        sync_event_rules(
            neo4j_session, events, compartments, tenancy_id,
            region, oci_update_tag, common_job_parameters,
        )

        # Sync notification topics
        sync_notification_topics(
            neo4j_session, ons, compartments, tenancy_id,
            region, oci_update_tag, common_job_parameters,
        )

    # Cleanup stale monitoring nodes
    run_cleanup_job(
        'oci_import_monitoring_cleanup.json', neo4j_session, common_job_parameters,
    )
