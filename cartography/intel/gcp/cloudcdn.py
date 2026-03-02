import json
import logging
import re
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
def get_backend_buckets(compute: Resource, project_id: str) -> List[Dict]:
    backend_buckets = []
    try:
        req = compute.backendBuckets().list(project=project_id)
        while req is not None:
            res = req.execute()
            if res.get('items'):
                for bucket in res['items']:
                    bucket['region'] = 'global'
                    bucket['id'] = f"projects/{project_id}/global/backendBuckets/{bucket['bucketName']}"
                    bucket['consolelink'] = gcp_console_link.get_console_link(
                        project_id=project_id,
                        backend_bucket_name=bucket['name'], resource_name='backend_bucket',
                    )
                    backend_buckets.append(bucket)
            req = compute.backendBuckets().list_next(previous_request=req, previous_response=res)

        return backend_buckets
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err.get('status', '') == 'PERMISSION_DENIED' or err.get('message', '') == 'Forbidden':
            logger.warning(
                (
                    "Could not retrieve backend buckets on project %s due to permissions issues. Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return []
        else:
            raise


@timeit
def load_backend_buckets(session: neo4j.Session, buckets: List[Dict], project_id: str, update_tag: int) -> None:
    session.write_transaction(load_backend_buckets_tx, buckets, project_id, update_tag)


@timeit
def load_backend_buckets_tx(
    tx: neo4j.Transaction, buckets: List[Dict],
    project_id: str, gcp_update_tag: int,
) -> None:
    query = """
    UNWIND $Buckets as b
    MERGE (bucket:GCPBackendBucket{id:b.id})
    ON CREATE SET
        bucket.firstseen = timestamp()
    SET
        bucket.lastupdated = $gcp_update_tag,
        bucket.region = b.region,
        bucket.uniqueId = b.id,
        bucket.name = b.bucketName,
        bucket.consolelink = b.consolelink,
        bucket.enableCdn = b.enableCdn,
        bucket.defaultTtl = b.cdnPolicy.defaultTtl,
        bucket.maxTtl = b.cdnPolicy.maxTtl
    WITH bucket
    MATCH (owner:GCPProject{id:$ProjectId})
    MERGE (owner)-[r:RESOURCE]->(bucket)
    ON CREATE SET
        r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag
    """
    tx.run(
        query,
        Buckets=buckets,
        ProjectId=project_id,
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def cleanup_backend_buckets(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('gcp_backend_buckets_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync_backend_buckets(
    neo4j_session: neo4j.Session, compute: Resource, project_id: str,
    gcp_update_tag: int, common_job_parameters: Dict,
) -> None:

    backend_buckets = get_backend_buckets(compute, project_id)

    load_backend_buckets(neo4j_session, backend_buckets, project_id, gcp_update_tag)
    cleanup_backend_buckets(neo4j_session, common_job_parameters)
    label.sync_labels(neo4j_session, backend_buckets, gcp_update_tag, common_job_parameters, 'backend_bucket', 'GCPBackendBucket')


@timeit
def get_global_backend_services(compute: Resource, project_id: str) -> List[Dict]:
    global_backend_services = []
    try:
        req = compute.backendServices().list(project=project_id)
        while req is not None:
            res = req.execute()
            if res.get('items'):
                for backend_service in res.get('items'):
                    backend_service['region'] = 'global'
                    backend_service['type'] = 'global'
                    backend_service['id'] = f"projects/{project_id}/global/backendServices/{backend_service['name']}"
                    backend_service['consolelink'] = gcp_console_link.get_console_link(
                        project_id=project_id,
                        backend_service_name=backend_service['name'], resource_name='global_backend_service',
                    )
                    backend_service['isUserCreated'] = is_user_created_backend_service(backend_service)
                    global_backend_services.append(backend_service)
            req = compute.backendServices().list_next(previous_request=req, previous_response=res)

        return global_backend_services
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err.get('status', '') == 'PERMISSION_DENIED' or err.get('message', '') == 'Forbidden':
            logger.warning(
                (
                    "Could not retrieve global backend buckets on project %s due to permissions issues. Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return []
        else:
            raise


@timeit
def is_user_created_backend_service(service):
    name: str = service.get("name", "").lower()
    description: str = service.get("description", "").lower()
    scheme: str = service.get("loadBalancingScheme", "")
    backends: list = service.get("backends", [])
    usedBy: list = service.get("usedBy", [])
    tags: dict = service.get("params", {}).get("resourceManagerTags", {}) or service.get("labels", {})

    # List to keep all the failed checks
    gcp_managed_signals: list = []

    # A. Check for GCP managed tags or labels
    gcp_tag_prefixes = [k for k in tags.keys() if str(k).startswith(("goog-", "gcp-"))]
    if gcp_tag_prefixes:
        gcp_managed_signals.append(f"GCP-managed tag/label: {gcp_tag_prefixes[0]}")

    # B. Check for known GCP naming patterns
    gcp_managed_patterns = [
        (r'^k8s\d*-[a-f0-9]+-', "GKE Ingress/NEG pattern"),
        (r'^agg-', "Aggregated backend service"),
        (r'^goog-', "Google-managed prefix"),
        (r'^gcp-', "GCP prefix"),
        (r'^gcf-', "Cloud Functions"),
        (r'^espv2-', "ESPv2 API Gateway"),
        (r'^gae-', "App Engine"),
        (r'^cloud[-_]?run', "Cloud Run"),
        (r'^internal-backend', "Auto internal naming"),
    ]

    for pattern, reason in gcp_managed_patterns:
        if re.match(pattern, name):
            gcp_managed_signals.append(f"Name pattern match: {reason}")

    # C. Description hints
    managed_desc_hints = [
        ("managed by gke", "GKE-managed description"),
        ("managed by google", "Google-managed description"),
        ("automatically created", "Auto-created indicator"),
        ("system-generated", "System-generated indicator"),
        ("do not delete", "Protected resource warning"),
        ("auto-created", "Auto-created indicator"),
        ("gke cluster", "GKE cluster reference"),
        ("kubernetes ingress", "Kubernetes ingress reference"),
        ("google cloud", "Google Cloud service reference"),
    ]

    for keyword, reason in managed_desc_hints:
        if keyword in description:
            gcp_managed_signals.append(f"Description: {reason}")

    # D. Load Balancing Check
    if scheme == "INTERNAL_SELF_MANAGED":
        gcp_managed_signals.append("Load balancing scheme: INTERNAL_SELF_MANAGED")

    # Check for serverless NEGs
    serverless_indicators = [
        ("serverless-neg", "Serverless NEG"),
        ("cloudrun", "Cloud Run NEG"),
        ("cloud-run", "Cloud Run NEG"),
        ("gae-", "App Engine NEG"),
        ("gcf-", "Cloud Functions NEG"),
    ]

    # E. Check backend groups for GCP managed NEGs
    for idx, backend in enumerate(backends):
        group = backend.get("group", "").lower()

        if "/networkendpointgroups/" in group:
            for indicator, reason in serverless_indicators:
                if indicator in group:
                    gcp_managed_signals.append(f"Backend[{idx}]: {reason}")

            # Check for GKE NEG pattern
            if re.search(r'k8s\d*-[a-f0-9]+-', group):
                gcp_managed_signals.append(f"Backend[{idx}]: GKE NEG pattern in group")

    # F. Check Used By references
    gcp_ref_patterns = [
        (r'k8s\d*-[a-f0-9]+-', "GKE resource"),
        (r'espv2-', "ESPv2 API Gateway"),
        (r'goog-', "Google-managed resource"),
        (r'gcp-', "GCP-managed resource"),
    ]

    for ref in usedBy:
        reference = ref.get("reference", "").lower()
        for pattern, reason in gcp_ref_patterns:
            if re.search(pattern, reference):
                gcp_managed_signals.append(f"UsedBy: Referenced by {reason}")

    is_user_created = len(gcp_managed_signals) == 0
    return is_user_created


@timeit
def load_backend_services(session: neo4j.Session, backend_services: List[Dict], project_id: str, update_tag: int) -> None:
    session.write_transaction(load_backend_services_tx, backend_services, project_id, update_tag)


@timeit
def load_backend_services_tx(
    tx: neo4j.Transaction, backend_services: List[Dict],
    project_id: str, gcp_update_tag: int,
) -> None:

    query = """
    UNWIND $Services as s
    MERGE (service:GCPBackendService{id:s.id})
    ON CREATE SET
        service.firstseen = timestamp()
    SET
        service.lastupdated = $gcp_update_tag,
        service.region = s.region,
        service.type = s.type,
        service.uniqueId = s.id,
        service.name = s.name,
        service.consolelink = s.consolelink,
        service.isUserCreated = s.isUserCreated,
        service.enableCDN = s.enableCDN,
        service.sessionAffinity = s.sessionAffinity,
        service.loadBalancingScheme = s.loadBalancingScheme,
        service.defaultTtl = s.defaultTtl,
        service.negativeCaching = s.cdnPolicy.negativeCaching
    WITH service
    MATCH (owner:GCPProject{id:$ProjectId})
    MERGE (owner)-[r:RESOURCE]->(service)
    ON CREATE SET
        r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag
    """

    tx.run(
        query,
        Services=backend_services,
        ProjectId=project_id,
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def cleanup_backend_services(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('gcp_backend_services_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync_global_backend_services(
    neo4j_session: neo4j.Session, compute: Resource, project_id: str,
    gcp_update_tag: int, common_job_parameters: Dict,
) -> None:

    global_services = get_global_backend_services(compute, project_id)

    load_backend_services(neo4j_session, global_services, project_id, gcp_update_tag)
    cleanup_backend_services(neo4j_session, common_job_parameters)
    label.sync_labels(neo4j_session, global_services, gcp_update_tag, common_job_parameters, 'backend_service', 'GCPBackendService')


@timeit
def get_regional_backend_services(compute: Resource, project_id: str, regions: list) -> List[Dict]:
    regional_backend_services = []
    try:
        if regions:
            for region in regions:
                req = compute.regionBackendServices().list(project=project_id, region=region)
                while req is not None:
                    res = req.execute()
                    if res.get('items'):
                        for region_service in res.get('items'):
                            region_service['region'] = region
                            region_service['type'] = 'regional'
                            region_service['id'] = f"projects/{project_id}/regions/{region}/backendServices/{region_service['name']}"
                            region_service['consolelink'] = gcp_console_link.get_console_link(
                                project_id=project_id,
                                backend_service_name=region_service['name'], region=region_service['region'], resource_name='regional_backend_service',
                            )
                            regional_backend_services.append(region_service)
                    req = compute.regionBackendServices().list_next(previous_request=req, previous_response=res)

        return regional_backend_services
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err.get('status', '') == 'PERMISSION_DENIED' or err.get('message', '') == 'Forbidden' or err.get('code') == 400:
            logger.warning(
                (
                    "Could not retrieve regional backend services on project %s due to permissions issues. Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return []
        else:
            raise


@timeit
def sync_regional_backend_services(
    neo4j_session: neo4j.Session, compute: Resource, project_id: str, regions: list,
    gcp_update_tag: int, common_job_parameters: Dict,
) -> None:

    regional_services = get_regional_backend_services(compute, project_id, regions)

    load_backend_services(neo4j_session, regional_services, project_id, gcp_update_tag)
    cleanup_backend_services(neo4j_session, common_job_parameters)
    label.sync_labels(neo4j_session, regional_services, gcp_update_tag, common_job_parameters, 'backend_service', 'GCPBackendService')


@timeit
def get_global_url_maps(compute: Resource, project_id: str) -> List[Dict]:
    global_url_maps = []
    try:
        req = compute.urlMaps().list(project=project_id)
        while req is not None:
            res = req.execute()
            if res.get('items'):
                global_url_maps.extend(res.get('items', []))
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
def transform_global_url_maps(url_maps: List[Dict], project_id: str) -> List[Dict]:
    global_url_maps = []
    for url_map in url_maps:
        url_map['region'] = 'global'
        url_map['type'] = 'global'
        url_map['consolelink'] = gcp_console_link.get_console_link(project_id=project_id, resource_name='cdn_home')
        url_map['id'] = f"projects/{project_id}/global/urlmaps/{url_map['name']}"
        global_url_maps.append(url_map)

    return global_url_maps


@timeit
def load_url_maps(session: neo4j.Session, url_maps: List[Dict], project_id: str, update_tag: int) -> None:
    session.write_transaction(load_url_maps_tx, url_maps, project_id, update_tag)


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
def cleanup_url_maps(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('gcp_url_maps_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync_global_url_maps(
    neo4j_session: neo4j.Session, compute: Resource, project_id: str,
    gcp_update_tag: int, common_job_parameters: Dict,
) -> None:

    maps = get_global_url_maps(compute, project_id)
    global_maps = transform_global_url_maps(maps, project_id)

    load_url_maps(neo4j_session, global_maps, project_id, gcp_update_tag)
    cleanup_url_maps(neo4j_session, common_job_parameters)
    label.sync_labels(neo4j_session, global_maps, gcp_update_tag, common_job_parameters, 'url_map', 'GCPUrlMap')


@timeit
def get_regional_url_maps(compute: Resource, project_id: str, region: Dict) -> List[Dict]:
    regional_url_maps = []
    try:
        req = compute.regionUrlMaps().list(project=project_id, region=region)
        while req is not None:
            res = req.execute()
            if res.get('items'):
                regional_url_maps.extend(res.get('items', []))
            req = compute.regionUrlMaps().list_next(previous_request=req, previous_response=res)

        return regional_url_maps
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err.get('status', '') == 'PERMISSION_DENIED' or err.get('message', '') == 'Forbidden' or err.get('code') == 400:
            logger.warning(
                (
                    "Could not retrieve regional url maps on project %s due to permissions issues. Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return []
        else:
            raise


@timeit
def transform_regional_url_maps(url_maps: List[Dict], region: str, project_id: str) -> List[Dict]:
    regional_url_maps = []
    for url_map in url_maps:
        url_map['region'] = region
        url_map['type'] = 'regional'
        url_map['consolelink'] = gcp_console_link.get_console_link(project_id=project_id, resource_name='cdn_home')
        url_map['id'] = f"projects/{project_id}/regions/{region}/urlmaps/{url_map['name']}"
        regional_url_maps.append(url_map)

    return regional_url_maps


@timeit
def sync_regional_url_maps(
    neo4j_session: neo4j.Session, compute: Resource, project_id: str, regions: list,
    gcp_update_tag: int, common_job_parameters: Dict,
) -> None:

    regional_maps = []
    for region in regions:
        maps = get_regional_url_maps(compute, project_id, region)
        regional_maps_list = transform_regional_url_maps(maps, region, project_id)
        regional_maps.extend(regional_maps_list)

    load_url_maps(neo4j_session, regional_maps, project_id, gcp_update_tag)
    cleanup_url_maps(neo4j_session, common_job_parameters)
    label.sync_labels(neo4j_session, regional_maps, gcp_update_tag, common_job_parameters, 'url_map', 'GCPUrlMap')


def sync(
    neo4j_session: neo4j.Session, compute: Resource, project_id: str, gcp_update_tag: int,
    common_job_parameters: dict, regions: list,
) -> None:

    tic = time.perf_counter()

    logger.info(f"Syncing cloudcdn for project {project_id}, at {tic}")

    sync_backend_buckets(neo4j_session, compute, project_id, gcp_update_tag, common_job_parameters)
    sync_global_backend_services(neo4j_session, compute, project_id, gcp_update_tag, common_job_parameters)
    sync_regional_backend_services(neo4j_session, compute, project_id, regions, gcp_update_tag, common_job_parameters)
    sync_global_url_maps(neo4j_session, compute, project_id, gcp_update_tag, common_job_parameters)
    sync_regional_url_maps(neo4j_session, compute, project_id, regions, gcp_update_tag, common_job_parameters)

    toc = time.perf_counter()
    logger.info(f"Time to process cloudcdn: {toc - tic:0.4f} seconds")
