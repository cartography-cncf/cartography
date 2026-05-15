import json
import logging
import time
from typing import Dict
from typing import List

import neo4j
from cloudconsolelink.clouds.gcp import GCPLinker
from googleapiclient.discovery import HttpError
from googleapiclient.discovery import Resource

from . import label
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)
gcp_console_link = GCPLinker()


@timeit
def get_compute_zones(compute: Resource, project_id: str) -> List[Dict]:
    compute_zones = []
    try:
        req = compute.zones().list(project=project_id)
        while req is not None:
            res = req.execute()
            if res.get('items'):
                for zone in res['items']:
                    compute_zones.append(zone)
            req = compute.zones().list_next(previous_request=req, previous_response=res)

        return compute_zones
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err.get('status', '') == 'PERMISSION_DENIED' or err.get('message', '') == 'Forbidden':
            logger.warning(
                (
                    "Could not retrieve zones on project %s due to permissions issues. Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return []
        else:
            raise


@timeit
def get_global_health_checks(compute: Resource, project_id: str, common_job_parameters) -> List[Dict]:
    global_health_checks = []
    try:
        req = compute.healthChecks().list(project=project_id)
        while req is not None:
            res = req.execute()
            if 'items' in res:
                global_health_checks.extend(res['items'])
            req = compute.healthChecks().list_next(previous_request=req, previous_response=res)

        return global_health_checks
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err.get('status', '') == 'PERMISSION_DENIED' or err.get('message', '') == 'Forbidden':
            logger.warning(
                (
                    "Could not retrieve global health checks on project %s due to permissions issues. Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return []
        else:
            raise


@timeit
def transform_global_health_checks(health_checks: List, project_id: str):
    list_health_checks = []

    for health_check in health_checks:
        health_check['id'] = f"projects/{project_id}/global/healthChecks/{health_check['name']}"
        health_check['region'] = 'global'
        health_check['type'] = 'global'
        health_check['consolelink'] = gcp_console_link.get_console_link(
            project_id=project_id,
            health_check_name=health_check['name'], resource_name='global_health_check',
        )
        list_health_checks.append(health_check)

    return list_health_checks


@timeit
def get_regional_health_checks(compute: Resource, project_id: str, region: str, common_job_parameters) -> List[Dict]:
    regional_health_checks = []
    try:
        req = compute.regionHealthChecks().list(project=project_id, region=region)
        while req is not None:
            res = req.execute()
            if 'items' in res:
                regional_health_checks.extend(res['items'])
            req = compute.regionHealthChecks().list_next(previous_request=req, previous_response=res)

        return regional_health_checks
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err.get('status', '') == 'PERMISSION_DENIED' or err.get('message', '') == 'Forbidden' or err.get('code') == 400:
            logger.warning(
                (
                    "Could not retrieve regional health checks on project %s due to permissions issues. Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return []
        else:
            raise


@timeit
def transform_regional_health_checks(health_checks: List, project_id: str, region: str):
    list_health_checks = []

    for health_check in health_checks:
        health_check['id'] = f"projects/{project_id}/regions/{region}/healthChecks/{health_check['name']}"
        health_check['region'] = region
        health_check['type'] = 'regional'
        health_check['consolelink'] = gcp_console_link.get_console_link(
            project_id=project_id, health_check_name=health_check['name'],
            region=health_check['region'], resource_name='regional_health_check',
        )
        list_health_checks.append(health_check)

    return list_health_checks


@timeit
def load_health_checks(session: neo4j.Session, health_checks: List[Dict], project_id: str, update_tag: int) -> None:
    session.execute_write(load_health_checks_tx, health_checks, project_id, update_tag)


@timeit
def load_health_checks_tx(
    tx: neo4j.Transaction, health_checks: List[Dict],
    project_id: str, gcp_update_tag: int,
) -> None:

    query = """
    UNWIND $HealthChecks as hc
    MERGE (healthcheck:GCPHealthCheck{id:hc.id})
    ON CREATE SET
        healthcheck.firstseen = timestamp()
    SET
        healthcheck.uniqueId = hc.id,
        healthcheck.region = hc.region,
        healthcheck.type = hc.type,
        healthcheck.consolelink = hc.consolelink,
        healthcheck.checkIntervalSec = hc.checkIntervalSec,
        healthcheck.timeoutSec = hc.timeoutSec,
        healthcheck.lastupdated = $gcp_update_tag
    WITH healthcheck
    MATCH (owner:GCPProject{id: $ProjectId})
    MERGE (owner)-[r:RESOURCE]->(healthcheck)
    ON CREATE SET
        r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag
    """

    tx.run(
        query,
        HealthChecks=health_checks,
        ProjectId=project_id,
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def cleanup_health_checks(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('gcp_health_checks_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync_global_health_checks(
    neo4j_session: neo4j.Session, compute: Resource, project_id: str,
    gcp_update_tag: int, common_job_parameters: Dict,
) -> None:

    health_checks = get_global_health_checks(compute, project_id, common_job_parameters)
    global_health_checks = transform_global_health_checks(health_checks, project_id)

    load_health_checks(neo4j_session, global_health_checks, project_id, gcp_update_tag)
    cleanup_health_checks(neo4j_session, common_job_parameters)
    label.sync_labels(neo4j_session, global_health_checks, gcp_update_tag, common_job_parameters, 'health_check', 'GCPHealthCheck')


@timeit
def sync_regional_health_checks(
    neo4j_session: neo4j.Session, compute: Resource, project_id: str, regions: List,
    gcp_update_tag: int, common_job_parameters: Dict,
) -> None:

    if regions:
        for region in regions:
            health_checks = get_regional_health_checks(compute, project_id, region, common_job_parameters)
            regional_health_checks = transform_regional_health_checks(health_checks, project_id, region)

            load_health_checks(neo4j_session, regional_health_checks, project_id, gcp_update_tag)
            cleanup_health_checks(neo4j_session, common_job_parameters)
            label.sync_labels(neo4j_session, regional_health_checks, gcp_update_tag, common_job_parameters, 'health_check', 'GCPHealthCheck')


@timeit
def get_global_instance_groups(compute: Resource, project_id: str, zone: Dict, common_job_parameters) -> List[Dict]:
    global_instance_groups = []
    try:
        req = compute.instanceGroups().list(project=project_id, zone=zone['name'])
        while req is not None:
            res = req.execute()
            if 'items' in res:
                global_instance_groups.extend(res['items'])
            req = compute.instanceGroups().list_next(previous_request=req, previous_response=res)

        return global_instance_groups
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err.get('status', '') == 'PERMISSION_DENIED' or err.get('message', '') == 'Forbidden':
            logger.warning(
                (
                    "Could not retrieve global instance groups on project %s due to permissions issues. Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return []
        else:
            raise


@timeit
def transform_global_instance_groups(instance_groups: List, project_id: str, zone: dict):
    list_instance_groups = []

    for instancegroup in instance_groups:
        instancegroup['id'] = f"projects/{project_id}/zones/{zone['name']}/instanceGroups/{instancegroup['name']}"
        instancegroup['type'] = 'global'
        instancegroup['region'] = 'global'
        instancegroup['consolelink'] = gcp_console_link.get_console_link(
            project_id=project_id, instance_group_name=instancegroup['name'],
            zone=zone['name'], resource_name='global_instance_group',
        )
        list_instance_groups.append(instancegroup)

    return list_instance_groups


@timeit
def get_regional_instance_groups(compute: Resource, project_id: str, region: str, common_job_parameters) -> List[Resource]:
    regional_instance_groups = []
    try:
        req = compute.regionInstanceGroups().list(project=project_id, region=region)
        while req is not None:
            res = req.execute()
            if 'items' in res:
                regional_instance_groups.extend(res['items'])
            req = compute.regionInstanceGroups().list_next(previous_request=req, previous_response=res)

        return regional_instance_groups
    except HttpError as e:
        if e.status_code == 404:
            logger.warning(
                (
                    "Could not retrieve regional instance groups on project %s due to 404. Code: %s, Message: %s"
                ), project_id, e.status_code, e.reason,
            )
            return []

        err = json.loads(e.content.decode('utf-8'))['error']
        if err.get('status', '') == 'PERMISSION_DENIED' or err.get('message', '') == 'Forbidden':
            logger.warning(
                (
                    "Could not retrieve regional instance groups on project %s due to permissions issues. Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return []
        else:
            raise


@timeit
def transform_regional_instance_groups(instance_groups: List, project_id: str, region: str):
    list_instance_groups = []

    for instancegroup in instance_groups:
        instancegroup['id'] = f"projects/{project_id}/regions/{region}/instanceGroups/{instancegroup['name']}"
        instancegroup['type'] = 'regional'
        instancegroup['region'] = region
        instancegroup['consolelink'] = gcp_console_link.get_console_link(
            project_id=project_id, instance_group_name=instancegroup['name'],
            region=instancegroup['name'], resource_name='regional_instance_group',
        )
        list_instance_groups.append(instancegroup)

    return list_instance_groups


@timeit
def load_instance_groups(session: neo4j.Session, instance_groups: List[Dict], project_id: str, update_tag: int) -> None:
    session.execute_write(load_instance_groups_tx, instance_groups, project_id, update_tag)


@timeit
def load_instance_groups_tx(
    tx: neo4j.Transaction, instance_groups: List[Dict],
    project_id: str, gcp_update_tag: int,
) -> None:

    query = """
    UNWIND $InstanceGroups as ig
    MERGE (instancegroup:GCPInstanceGroup{id:ig.id})
    ON CREATE SET
        instancegroup.firstseen = timestamp()
    SET
        instancegroup.uniqueId = ig.id,
        instancegroup.type = ig.type,
        instancegroup.region = ig.region,
        instancegroup.size = ig.size,
        instancegroup.consolelink = ig.consolelink,
        instancegroup.network = ig.network,
        instancegroup.subnetwork = ig.subnetwork,
        instancegroup.lastupdated = $gcp_update_tag
    WITH instancegroup
    MATCH (owner:GCPProject{id: $ProjectId})
    MERGE (owner)-[r:RESOURCE]->(instancegroup)
    ON CREATE SET
        r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag
    """

    tx.run(
        query,
        InstanceGroups=instance_groups,
        ProjectId=project_id,
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def cleanup_instance_groups(neo4j_session: neo4j.Session, common_job_parameters) -> None:
    run_cleanup_job('gcp_instance_groups_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync_global_instance_groups(
    neo4j_session: neo4j.Session, compute: Resource, project_id: str,
    gcp_update_tag: int, common_job_parameters: Dict,
) -> None:

    zones = get_compute_zones(compute, project_id)
    for zone in zones:
        instance_groups = get_global_instance_groups(compute, project_id, zone, common_job_parameters)
        global_instance_groups = transform_global_instance_groups(instance_groups, project_id, zone)
        load_instance_groups(neo4j_session, global_instance_groups, project_id, gcp_update_tag)
        label.sync_labels(neo4j_session, global_instance_groups, gcp_update_tag, common_job_parameters, 'instance_group', 'GCPInstanceGroup')
    cleanup_instance_groups(neo4j_session, common_job_parameters)


@timeit
def sync_regional_instance_groups(
    neo4j_session: neo4j.Session, compute: Resource, project_id: str, regions: List,
    gcp_update_tag: int, common_job_parameters: Dict,
) -> None:

    if regions:
        for region in regions:
            instance_groups = get_regional_instance_groups(compute, project_id, region, common_job_parameters)
            regional_instance_groups = transform_regional_instance_groups(instance_groups, project_id, region)
            load_instance_groups(neo4j_session, regional_instance_groups, project_id, gcp_update_tag)
            cleanup_instance_groups(neo4j_session, common_job_parameters)
            label.sync_labels(neo4j_session, regional_instance_groups, gcp_update_tag, common_job_parameters, 'instance_group', 'GCPInstanceGroup')


@timeit
def get_global_url_maps(compute: Resource, project_id: str, common_job_parameters) -> List[Dict]:
    global_url_maps = []
    try:
        req = compute.urlMaps().list(project=project_id)
        while req is not None:
            res = req.execute()
            if 'items' in res:
                global_url_maps.extend(res['items'])
            req = compute.urlMaps().list_next(previous_request=req, previous_response=res)

        return global_url_maps
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err.get('status', '') == 'PERMISSION_DENIED' or err.get('message', '') == 'Forbidden':
            logger.warning(
                (
                    "Could not retrieve global url maps on project %s due to permissions issues. Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return []
        else:
            raise


@timeit
def transform_global_url_maps(url_maps: List, project_id: str):
    list_url_maps = []

    for url_map in url_maps:
        url_map['region'] = 'global'
        url_map['type'] = 'global'
        url_map['consolelink'] = gcp_console_link.get_console_link(project_id=project_id, resource_name='load_balancer_home')
        url_map['id'] = f"projects/{project_id}/global/urlmaps/{url_map['name']}"
        list_url_maps.append(url_map)

    return list_url_maps


@timeit
def get_regional_url_maps(compute: Resource, project_id: str, region: str, common_job_parameters) -> List[Dict]:
    regional_url_maps = []
    try:
        req = compute.regionUrlMaps().list(project=project_id, region=region)
        while req is not None:
            res = req.execute()
            if 'items' in res:
                regional_url_maps.extend(res['items'])
            req = compute.regionUrlMaps().list_next(previous_request=req, previous_response=res)

        return regional_url_maps
    except HttpError as e:
        if e.status_code == 404:
            logger.warning(
                (
                    "Could not retrieve regional url maps on project %s due to 404. Code: %s, Message: %s"
                ), project_id, e.status_code, e.reason,
            )
            return []

        err = json.loads(e.content.decode('utf-8'))['error']
        if err.get('status', '') == 'PERMISSION_DENIED' or err.get('message', '') == 'Forbidden':
            logger.warning(
                (
                    "Could not retrieve regional url maps on project %s due to permissions issues. Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return []
        else:
            raise


@timeit
def transform_regional_url_maps(maps: List, region: str, project_id: str):
    list_url_maps = []

    for url_map in maps:
        url_map['region'] = region
        url_map['type'] = 'regional'
        url_map['consolelink'] = gcp_console_link.get_console_link(project_id=project_id, resource_name='load_balancer_home')
        url_map['id'] = f"projects/{project_id}/regions/{region}/urlmaps/{url_map['name']}"
        list_url_maps.append(url_map)

    return list_url_maps


@timeit
def load_url_maps(session: neo4j.Session, url_maps: List[Dict], project_id: str, update_tag: int) -> None:
    session.execute_write(load_url_maps_tx, url_maps, project_id, update_tag)


@timeit
def load_url_maps_tx(
    tx: neo4j.Transaction, url_maps: List[Dict],
    project_id: str, gcp_update_tag: int,
) -> None:

    query = """
    UNWIND $Maps as mp
    MERGE (map:GCPUrlMap{id:mp.id})
    ON CREATE SET
        map.firstseen = timestamp()
    SET
        map.lastupdated = $gcp_update_tag,
        map.region = mp.region,
        map.type = mp.type,
        map.consolelink = mp.consolelink,
        map.uniqueId = mp.id,
        map.name = mp.name,
        map.defaultService = mp.defaultService
    WITH map
    MATCH (owner:GCPProject{id: $ProjectId})
    MERGE (owner)-[r:RESOURCE]->(map)
    ON CREATE SET
        r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag
    """

    tx.run(
        query,
        Maps=url_maps,
        ProjectId=project_id,
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def cleanup_url_maps(neo4j_session: neo4j.Session, common_job_parameters) -> None:
    run_cleanup_job('gcp_url_maps_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync_global_url_maps(
    neo4j_session: neo4j.Session, compute: Resource, project_id: str,
    gcp_update_tag: int, common_job_parameters: Dict,
) -> None:

    maps = get_global_url_maps(compute, project_id, common_job_parameters)
    global_maps = transform_global_url_maps(maps, project_id)
    load_url_maps(neo4j_session, global_maps, project_id, gcp_update_tag)
    cleanup_url_maps(neo4j_session, common_job_parameters)
    label.sync_labels(neo4j_session, global_maps, gcp_update_tag, common_job_parameters, 'url_map', 'GCPUrlMap')


@timeit
def sync_regional_url_maps(
    neo4j_session: neo4j.Session, compute: Resource, project_id: str, regions: List,
    gcp_update_tag: int, common_job_parameters: Dict,
) -> None:

    if regions:
        for region in regions:
            maps = get_regional_url_maps(compute, project_id, region, common_job_parameters)
            regional_maps = transform_regional_url_maps(maps, region, project_id)
            load_url_maps(neo4j_session, regional_maps, project_id, gcp_update_tag)
            cleanup_url_maps(neo4j_session, common_job_parameters)
            label.sync_labels(neo4j_session, regional_maps, gcp_update_tag, common_job_parameters, 'url_map', 'GCPUrlMap')


@timeit
def get_ssl_policies(compute: Resource, project_id: str, common_job_parameters) -> List[Dict]:
    ssl_policies = []
    try:
        req = compute.sslPolicies().list(project=project_id)
        while req is not None:
            res = req.execute()
            if 'items' in res:
                ssl_policies.extend(res['items'])
            req = compute.sslPolicies().list_next(previous_request=req, previous_response=res)

        return ssl_policies
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err.get('status', '') == 'PERMISSION_DENIED' or err.get('message', '') == 'Forbidden':
            logger.warning(
                (
                    "Could not retrieve ssl policies on project %s due to permissions issues. Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return []
        else:
            raise


@timeit
def transform_ssl_policies(ssl_policies: List, project_id: str):
    list_ssl_policies = []

    for policy in ssl_policies:
        policy['id'] = f"projects/{project_id}/global/sslPolicies/{policy['name']}"
        policy['region'] = 'global'
        policy['consolelink'] = gcp_console_link.get_console_link(
            project_id=project_id,
            ssl_policy_name=policy['name'], resource_name='ssl_policy',
        )
        list_ssl_policies.append(policy)

    return list_ssl_policies


@timeit
def load_ssl_policies(session: neo4j.Session, ssl_policies: List[Dict], project_id: str, update_tag: int) -> None:
    session.execute_write(load_ssl_policies_tx, ssl_policies, project_id, update_tag)


@timeit
def load_ssl_policies_tx(
    tx: neo4j.Transaction, ssl_policies: List[Dict],
    project_id: str, gcp_update_tag: int,
) -> None:

    query = """
    UNWIND $SSLPolicies as pol
    MERGE (policy:GCPSSLPolicy{id:pol.id})
    ON CREATE SET
        policy.firstseen = timestamp()
    SET
        policy.uniqueId = pol.id,
        policy.region = pol.region,
        policy.name = pol.name,
        policy.consolelink = pol.consolelink,
        policy.minTlsVersion = pol.minTlsVersion,
        policy.lastupdated = $gcp_update_tag
    WITH policy
    MATCH (owner:GCPProject{id: $ProjectId})
    MERGE (owner)-[r:RESOURCE]->(policy)
    ON CREATE SET
        r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag
    """

    tx.run(
        query,
        SSLPolicies=ssl_policies,
        ProjectId=project_id,
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def cleanup_ssl_policies(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('gcp_ssl_policies_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync_ssl_policies(
    neo4j_session: neo4j.Session, compute: Resource, project_id: str,
    gcp_update_tag: int, common_job_parameters: Dict,
) -> None:

    policies = get_ssl_policies(compute, project_id, common_job_parameters)
    ssl_policies = transform_ssl_policies(policies, project_id)
    load_ssl_policies(neo4j_session, ssl_policies, project_id, gcp_update_tag)
    cleanup_ssl_policies(neo4j_session, common_job_parameters)
    label.sync_labels(neo4j_session, ssl_policies, gcp_update_tag, common_job_parameters, 'ssl_policy', 'GCPSSLPolicy')


def sync(
    neo4j_session: neo4j.Session, compute: Resource, project_id: str, gcp_update_tag: int,
    common_job_parameters: Dict, regions: List,
) -> None:
    tic = time.perf_counter()

    logger.info(f"Syncing load balancer for project {project_id}, at {tic}")

    sync_global_health_checks(neo4j_session, compute, project_id, gcp_update_tag, common_job_parameters)
    sync_regional_health_checks(neo4j_session, compute, project_id, regions, gcp_update_tag, common_job_parameters)
    sync_global_instance_groups(neo4j_session, compute, project_id, gcp_update_tag, common_job_parameters)
    sync_regional_instance_groups(neo4j_session, compute, project_id, regions, gcp_update_tag, common_job_parameters)
    sync_global_url_maps(neo4j_session, compute, project_id, gcp_update_tag, common_job_parameters)
    sync_regional_url_maps(neo4j_session, compute, project_id, regions, gcp_update_tag, common_job_parameters)
    sync_ssl_policies(neo4j_session, compute, project_id, gcp_update_tag, common_job_parameters)

    toc = time.perf_counter()
    logger.info(f"Time to process load balancer: {toc - tic:0.4f} seconds")
