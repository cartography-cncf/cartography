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
def get_cloudrun_authorized_domains(cloudrun: Resource, project_id: str, common_job_parameters) -> List[Dict]:
    """
        Returns a list of Cloud Run Authorized Domains for a given project.

        :type cloudrun: Resource
        :param cloudrun: The cloudrun resource created by googleapiclient.discovery.build()

        :type project_id: str
        :param project_id: Current Google Project Id

        :rtype: list
        :return: List of Cloud Run Authorized Domains
    """
    try:
        domains = []
        request = cloudrun.namespaces().authorizeddomains().list(parent=f'namespaces/{project_id}')
        while request is not None:
            response = request.execute()
            if response.get('domains', []):
                domains.extend(response.get('domains', []))
            request = cloudrun.namespaces().authorizeddomains().list_next(previous_request=request, previous_response=response)

        return domains
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err.get('status', '') == 'PERMISSION_DENIED' or err.get('message', '') == 'Forbidden':
            logger.warning(
                (
                    "Could not retrieve CloudRun authorizeddomains on project %s due to permissions issues.\
                         Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return []
        else:
            raise


def transform_authorized_domains(domains: List[Dict], project_id: str) -> List[Dict]:
    authorized_domains = []
    for domain in domains:
        domain['consolelink'] = gcp_console_link.get_console_link(project_id=project_id, resource_name='cloudrun_domain')
        domain['id'] = f"projects/{project_id}/authorizedDomains/{domain['id']}"
        authorized_domains.append(domain)

    return authorized_domains


@timeit
def get_cloudrun_configurations(cloudrun: Resource, project_id: str, common_job_parameters) -> List[Dict]:
    """
        Returns a list of Cloud Run Configurations for a given project.

        :type cloudrun: Resource
        :param cloudrun: The cloudrun resource created by googleapiclient.discovery.build()

        :type project_id: str
        :param project_id: Current Google Project Id

        :rtype: list
        :return: List of Cloud Run Configurations
    """
    try:
        configurations = []
        request = cloudrun.namespaces().configurations().list(parent=f'namespaces/{project_id}')
        response = request.execute()
        if response.get('items', []):
            configurations.extend(response.get('items', []))

        return configurations
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err.get('status', '') == 'PERMISSION_DENIED' or err.get('message', '') == 'Forbidden':
            logger.warning(
                (
                    "Could not retrieve CloudRun configurations on project %s due to permissions issues.\
                         Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return []
        else:
            raise


@timeit
def transform_configurations(configurations: List[Dict], project_id: str) -> List[Dict]:
    configurations = []
    for item in configurations:
        item['consolelink'] = gcp_console_link.get_console_link(project_id=project_id, resource_name='cloudrun_home')
        item['id'] = f"projects/{project_id}/configurations/{item.get('metadata').get('name')}"
        configurations.append(item)

    return configurations


@timeit
def get_cloudrun_domainmappings(cloudrun: Resource, project_id: str, common_job_parameters) -> List[Dict]:
    """
        Returns a list of Cloud Run Domain Mappings for a given project.

        :type cloudrun: Resource
        :param cloudrun: The cloudrun resource created by googleapiclient.discovery.build()

        :type project_id: str
        :param project_id: Current Google Project Id

        :rtype: list
        :return: List of Cloud Run Domain Mappings
    """
    try:
        mappings = []
        request = cloudrun.namespaces().domainmappings().list(parent=f'namespaces/{project_id}')
        response = request.execute()
        if response.get('items', []):
            mappings.extend(response.get('items', []))

        return mappings
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err.get('status', '') == 'PERMISSION_DENIED' or err.get('message', '') == 'Forbidden':
            logger.warning(
                (
                    "Could not retrieve CloudRun Domain Mappings on project %s due to permissions issues.\
                         Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return []
        else:
            raise


@timeit
def transform_mappings(mappings: List[Dict], project_id: str) -> List[Dict]:
    mappings = []
    for item in mappings:
        item['consolelink'] = gcp_console_link.get_console_link(project_id=project_id, resource_name='cloudrun_domain')
        item['id'] = f"projects/{project_id}/domainmappings/{item.get('metadata').get('name')}"
        mappings.append(item)

    return mappings


@timeit
def get_cloudrun_revisions(cloudrun: Resource, project_id: str, common_job_parameters) -> List[Dict]:
    """
        Returns a list of Cloud Run Revisions for a given project.

        :type cloudrun: Resource
        :param cloudrun: The cloudrun resource created by googleapiclient.discovery.build()

        :type project_id: str
        :param project_id: Current Google Project Id

        :rtype: list
        :return: List of Cloud Run Revisions
    """
    try:
        revisions = []
        request = cloudrun.namespaces().revisions().list(parent=f'namespaces/{project_id}')
        response = request.execute()
        if response.get('items', []):
            revisions.extend(response.get('items', []))

        return revisions
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err.get('status', '') == 'PERMISSION_DENIED' or err.get('message', '') == 'Forbidden':
            logger.warning(
                (
                    "Could not retrieve CloudRun Revisions on project %s due to permissions issues.\
                         Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return []
        else:
            raise


@timeit
def transform_revisions(revisions: List[Dict], project_id: str) -> List[Dict]:
    revisions = []
    for item in revisions:
        item['region'] = item.get('metadata').get('labels').get('cloud.googleapis.com/location')
        item['service_name'] = item.get('metadata').get('labels').get('serving.knative.dev/route')
        item['consolelink'] = gcp_console_link.get_console_link(
            project_id=project_id,
            cloud_run_service_name=item['service_name'], region=item['region'], resource_name='cloud_run_revision',
        )
        item['id'] = f"projects/{project_id}/revisions/{item.get('metadata').get('name')}"
        revisions.append(item)
    return revisions


@timeit
def get_cloudrun_routes(cloudrun: Resource, project_id: str, common_job_parameters) -> List[Dict]:
    """
        Returns a list of Cloud Run Routes for a given project.

        :type cloudrun: Resource
        :param cloudrun: The cloudrun resource created by googleapiclient.discovery.build()

        :type project_id: str
        :param project_id: Current Google Project Id

        :rtype: list
        :return: List of Cloud Run Routes
    """
    try:
        routes = []
        request = cloudrun.namespaces().routes().list(parent=f'namespaces/{project_id}')
        response = request.execute()
        if response.get('items', []):
            routes.extend(response.get('items', []))

        return routes
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err.get('status', '') == 'PERMISSION_DENIED' or err.get('message', '') == 'Forbidden':
            logger.warning(
                (
                    "Could not retrieve CloudRun Routes on project %s due to permissions issues. Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return []
        else:
            raise


@timeit
def transform_routes(routes: List[Dict], project_id: str) -> List[Dict]:
    items = []
    for item in routes:
        item['consolelink'] = gcp_console_link.get_console_link(project_id=project_id, resource_name='cloudrun_home')
        item['id'] = f"projects/{project_id}/routes/{item.get('metadata').get('name')}"
        items.append(item)

    return items


@timeit
def get_cloudrun_services(cloudrun: Resource, project_id: str, common_job_parameters) -> List[Dict]:
    """
        Returns a list of Cloud Run Services for a given project.

        :type cloudrun: Resource
        :param cloudrun: The cloudrun resource created by googleapiclient.discovery.build()

        :type project_id: str
        :param project_id: Current Google Project Id

        :rtype: list
        :return: List of Cloud Run Services
    """
    try:
        services = []
        request = cloudrun.namespaces().services().list(parent=f'namespaces/{project_id}')
        response = request.execute()
        if response.get('items', []):
            services.extend(response.get('items', []))

        return services
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err.get('status', '') == 'PERMISSION_DENIED' or err.get('message', '') == 'Forbidden':
            logger.warning(
                (
                    "Could not retrieve CloudRun Services on project %s due to permissions issues. \
                        Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return []

        elif err.get('status', '') == 'UNAVAILABLE' or err.get('code', '') == 503:
            logger.warning(
                (
                    "Could not retrieve CloudRun Services due to the service is currently unavailable for Project %s \
                         Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return []

        else:
            raise


@timeit
def transform_services(services: List[Dict], project_id: str) -> List[Dict]:
    services = []
    for item in services:
        item['region'] = item.get('metadata').get('labels').get('cloud.googleapis.com/location')
        item['consolelink'] = gcp_console_link.get_console_link(
            project_id=project_id,
            cloud_run_service_name=item.get('metadata').get('name'), region=item['region'], resource_name='cloud_run_service',
        )
        item['id'] = f"projects/{project_id}/services/{item.get('metadata').get('name')}"
        services.append(item)

    return services


@timeit
def load_cloudrun_authorized_domains(
    session: neo4j.Session, data_list: List[Dict],
    project_id: str, update_tag: int,
) -> None:
    session.execute_write(_load_cloudrun_authorized_domains_tx, data_list, project_id, update_tag)


@timeit
def _load_cloudrun_authorized_domains_tx(
    tx: neo4j.Transaction, authorized_domains: List[Resource],
    project_id: str, gcp_update_tag: int,
) -> None:
    """
        :type neo4j_transaction: Neo4j transaction object
        :param neo4j transaction: The Neo4j transaction object

        :type authorized_domains_resp: List
        :param authorized_domains_resp: A list GCP Cloud Run Authorized Domains

        :type project_id: str
        :param project_id: Current Google Project Id

        :type gcp_update_tag: timestamp
        :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with
    """
    ingest_cloudrun_authorized_domains = """
    UNWIND $authorized_domains as ad
    MERGE (authorized_domain:GCPCloudRunAuthorizedDomain{id:ad.id})
    ON CREATE SET
        authorized_domain.firstseen = timestamp()
    SET
        authorized_domain.id = ad.id,
        authorized_domain.name = ad.name,
        authorized_domain.region = $region,
        authorized_domain.lastupdated = $gcp_update_tag,
        authorized_domain.consolelink = ad.consolelink
    WITH authorized_domain
    MATCH (owner:GCPProject{id: $ProjectId})
    MERGE (owner)-[r:RESOURCE]->(authorized_domain)
    ON CREATE SET
        r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag
    """
    tx.run(
        ingest_cloudrun_authorized_domains,
        authorized_domains=authorized_domains,
        ProjectId=project_id,
        region="global",
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def load_cloudrun_configurations(
    session: neo4j.Session, data_list: List[Dict],
    project_id: str, update_tag: int,
) -> None:
    session.execute_write(_load_cloudrun_configurations_tx, data_list, project_id, update_tag)


@timeit
def _load_cloudrun_configurations_tx(
    tx: neo4j.Transaction, configurations: List[Resource],
    project_id: str, gcp_update_tag: int,
) -> None:
    """
        :type neo4j_transaction: Neo4j transaction object
        :param neo4j transaction: The Neo4j transaction object

        :type configurations_resp: List
        :param configurations_resp: A list GCP Cloud Run Configurations

        :type project_id: str
        :param project_id: Current Google Project Id

        :type gcp_update_tag: timestamp
        :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with
    """
    ingest_cloudrun_configurations = """
    UNWIND $configurations as config
    MERGE (configuration:GCPCloudRunConfiguration{id:config.id})
    ON CREATE SET
        configuration.firstseen = timestamp()
    SET
        configuration.name = config.metadata.name,
        configuration.namspace = config.metadata.namespace,
        configuration.selfLink = config.metadata.selfLink,
        configuration.uid = config.metadata.uid,
        configuration.region = $region,
        configuration.consolelink = config.consolelink,

        configuration.resourceVersion = config.metadata.resourceVersion,
        configuration.creationTimestamp = config.metadata.creationTimestamp,
        configuration.deletionTimestamp = config.metadata.deletionTimestamp,
        configuration.clusterName = config.metadata.clusterName,
        configuration.observedGeneration = config.spec.observedGeneration,
        configuration.latestCreatedRevisionName = config.spec.latestCreatedRevisionName,
        configuration.latestReadyRevisionName = config.spec.latestReadyRevisionName,
        configuration.lastupdated = $gcp_update_tag
    WITH configuration
    MATCH (owner:GCPProject{id: $ProjectId})
    MERGE (owner)-[r:RESOURCE]->(configuration)
    ON CREATE SET
        r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag
    """
    tx.run(
        ingest_cloudrun_configurations,
        configurations=configurations,
        ProjectId=project_id,
        region="global",
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def load_cloudrun_domainmappings(
    session: neo4j.Session, data_list: List[Dict],
    project_id: str, update_tag: int,
) -> None:
    session.execute_write(_load_cloudrun_domainmappings_tx, data_list, project_id, update_tag)


@timeit
def _load_cloudrun_domainmappings_tx(
    tx: neo4j.Transaction, domainmappings: List[Resource],
    project_id: str, gcp_update_tag: int,
) -> None:
    """
        :type neo4j_transaction: Neo4j transaction object
        :param neo4j transaction: The Neo4j transaction object

        :type domainmappings_resp: List
        :param domainmappings_resp: A list GCP Cloud Run Domain Mappings

        :type project_id: str
        :param project_id: Current Google Project Id

        :type gcp_update_tag: timestamp
        :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with
    """
    ingest_cloudrun_domainmappings = """
    UNWIND $domainmappings as domainmap
    MERGE (domainmapping:GCPCloudRunDomainMap{id:domainmap.id})
    ON CREATE SET
        domainmapping.firstseen = timestamp()
    SET
        domainmapping.name = domainmap.metadata.name,
        domainmapping.namspace = domainmap.metadata.namespace,
        domainmapping.selfLink = domainmap.metadata.selfLink,
        domainmapping.uid = domainmap.metadata.uid,
        domainmapping.region = $region,
        domainmapping.consolelink = domainmap.consolelink,
        domainmapping.resourceVersion = domainmap.metadata.resourceVersion,
        domainmapping.creationTimestamp = domainmap.metadata.creationTimestamp,
        domainmapping.deletionTimestamp = domainmap.metadata.deletionTimestamp,
        domainmapping.routeName = domainmap.spec.routeName,
        domainmapping.certificateMode = domainmap.spec.certificateMode,
        domainmapping.forceOverride = domainmap.spec.forceOveride,
        domainmapping.lastupdated = $gcp_update_tag
    WITH domainmapping
    MATCH (owner:GCPProject{id: $ProjectId})
    MERGE (owner)-[r:RESOURCE]->(domainmapping)
    ON CREATE SET
        r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag
    """
    tx.run(
        ingest_cloudrun_domainmappings,
        domainmappings=domainmappings,
        ProjectId=project_id,
        region="global",
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def load_cloudrun_revisions(session: neo4j.Session, data_list: List[Dict], project_id: str, update_tag: int) -> None:
    session.execute_write(_load_cloudrun_revisions_tx, data_list, project_id, update_tag)


@timeit
def _load_cloudrun_revisions_tx(
    tx: neo4j.Transaction, revisions: List[Resource],
    project_id: str, gcp_update_tag: int,
) -> None:
    """
        :type neo4j_transaction: Neo4j transaction object
        :param neo4j transaction: The Neo4j transaction object

        :type revisions_resp: List
        :param revisions_resp: A list GCP Cloud Run Revisions

        :type project_id: str
        :param project_id: Current Google Project Id

        :type gcp_update_tag: timestamp
        :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with
    """
    ingest_cloudrun_revisions = """
    UNWIND $revisions as rev
    MERGE (revision:GCPCloudRunRevision{id:rev.id})
    ON CREATE SET
        revision.firstseen = timestamp()
    SET
        revision.name = rev.metadata.name,
        revision.namspace = rev.metadata.namespace,
        revision.selfLink = rev.metadata.selfLink,
        revision.uid = rev.metadata.uid,
        revision.region = rev.region,
        revision.consolelink = rev.consolelink,
        revision.resourceVersion = rev.metadata.resourceVersion,
        revision.creationTimestamp = rev.metadata.creationTimestamp,
        revision.deletionTimestamp = rev.metadata.deletionTimestamp,
        revision.containerConcurrency = rev.specs.containerConcurrency,
        revision.timeoutSeconds = rev.specs.timeoutSeconds,
        revision.lastupdated = $gcp_update_tag
    WITH revision
    MATCH (owner:GCPProject{id: $ProjectId})
    MERGE (owner)-[r:RESOURCE]->(revision)
    ON CREATE SET
        r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag
    """
    tx.run(
        ingest_cloudrun_revisions,
        revisions=revisions,
        ProjectId=project_id,
        region="global",
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def load_cloudrun_routes(session: neo4j.Session, data_list: List[Dict], project_id: str, update_tag: int) -> None:
    session.execute_write(_load_cloudrun_routes_tx, data_list, project_id, update_tag)


@timeit
def _load_cloudrun_routes_tx(
    tx: neo4j.Transaction, routes: List[Resource],
    project_id: str, gcp_update_tag: int,
) -> None:
    """
        :type neo4j_transaction: Neo4j transaction object
        :param neo4j transaction: The Neo4j transaction object

        :type routes_resp: List
        :param routes_resp: A list GCP Cloud Run Routes

        :type project_id: str
        :param project_id: Current Google Project Id

        :type gcp_update_tag: timestamp
        :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with
    """
    ingest_cloudrun_routes = """
    UNWIND $routes as rt
    MERGE (route:GCPCloudRunRoute{id:rt.id})
    ON CREATE SET
        route.firstseen = timestamp()
    SET
        route.name = rt.metadata.name,
        route.namespace = rt.metadata.namespace,
        route.selfLink = rt.metadata.selfLink,
        route.uid = rt.metadata.uid,
        route.region = $region,
        route.consolelink = rt.consolelink,
        route.resourceVersion = rt.metadata.resourceVersion,
        route.creationTimestamp = rt.metadata.creationTimestamp,
        route.deletionTimestamp = rt.metadata.deletionTimestamp,
        route.observedGeneration = rt.status.observedGeneration,
        route.url = rt.status.url,
        route.lastupdated = $gcp_update_tag
    WITH route
    MATCH (owner:GCPProject{id: $ProjectId})
    MERGE (owner)-[r:RESOURCE]->(route)
    ON CREATE SET
        r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag
    """
    tx.run(
        ingest_cloudrun_routes,
        routes=routes,
        ProjectId=project_id,
        region="global",
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def load_cloudrun_services(session: neo4j.Session, data_list: List[Dict], project_id: str, update_tag: int) -> None:
    session.execute_write(_load_cloudrun_services_tx, data_list, project_id, update_tag)


@timeit
def _load_cloudrun_services_tx(
    tx: neo4j.Transaction, services: List[Resource],
    project_id: str, gcp_update_tag: int,
) -> None:
    """
        :type neo4j_transaction: Neo4j transaction object
        :param neo4j transaction: The Neo4j transaction object

        :type services_resp: List
        :param services_resp: A list GCP Cloud Run Services

        :type project_id: str
        :param project_id: Current Google Project Id

        :type gcp_update_tag: timestamp
        :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with
    """
    ingest_cloudrun_services = """
    UNWIND $services as svc
    MERGE (service:GCPCloudRunService{id:svc.id})
    ON CREATE SET
        service.firstseen = timestamp()
    SET
        service.name = svc.metadata.name,
        service.namspace = svc.metadata.namespace,
        service.selfLink = svc.metadata.selfLink,
        service.uid = svc.metadata.uid,
        service.region = svc.region,
        service.consolelink = svc.consolelink,
        service.resourceVersion = svc.metadata.resourceVersion,
        service.creationTimestamp = svc.metadata.creationTimestamp,
        service.deletionTimestamp = svc.metadata.deletionTimestamp,
        service.observedGeneration = svc.status.observedGeneration,
        service.latestReadyRevisionName = svc.status.latestReadyRevisionName,
        service.latestCreatedRevisionName = svc.status.latestCreatedRevisionName,
        service.lastupdated = $gcp_update_tag
    WITH service
    MATCH (owner:GCPProject{id: $ProjectId})
    MERGE (owner)-[r:RESOURCE]->(service)
    ON CREATE SET
        r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag
    """
    tx.run(
        ingest_cloudrun_services,
        services=services,
        ProjectId=project_id,
        region="global",
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def cleanup_gcp_cloudrun(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    """
    Delete out-of-date GCP Cloud Run and relationships

    :type neo4j_session: The Neo4j session object
    :param neo4j_session: The Neo4j session

    :type common_job_parameters: dict
    :param common_job_parameters: Dictionary of other job parameters to pass to Neo4j

    :rtype: NoneType
    :return: Nothing
    """
    run_cleanup_job('gcp_cloudrun_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync(
    neo4j_session: neo4j.Session, cloudrun: Resource, project_id: str, gcp_update_tag: int,
    common_job_parameters: Dict, regions: list,
) -> None:
    """
        Get GCP Cloud CloudRun using the Cloud CloudRun resource object, ingest to Neo4j, and clean up old data.

        :type neo4j_session: The Neo4j session object
        :param neo4j_session: The Neo4j session

        :type cloudrun: The GCP CloudRun  resource object created by googleapiclient.discovery.build()
        :param cloudrun: The GCP CloudRun resource object

        :type project_id: str
        :param project_id: The project ID of the corresponding project

        :type gcp_update_tag: timestamp
        :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with

        :type common_job_parameters: dict
        :param common_job_parameters: Dictionary of other job parameters to pass to Neo4j

        :rtype: NoneType
        :return: Nothing
    """
    tic = time.perf_counter()

    logger.info("Syncing CloudRun for project '%s', at %s.", project_id, tic)

    # CLOUDRUN AUTHORIZED DOMAINS
    domains = get_cloudrun_authorized_domains(cloudrun, project_id, common_job_parameters)
    authorized_domains = transform_authorized_domains(domains, project_id)
    load_cloudrun_authorized_domains(neo4j_session, authorized_domains, project_id, gcp_update_tag)
    label.sync_labels(
        neo4j_session, domains, gcp_update_tag, common_job_parameters,
        'cloudrun authorized domains', 'GCPCloudRunAuthorizedDomain',
    )

    # CLOUDRUN CONFIGURATIONS
    configs = get_cloudrun_configurations(cloudrun, project_id, common_job_parameters)
    configurations = transform_configurations(configs, project_id)
    load_cloudrun_configurations(neo4j_session, configurations, project_id, gcp_update_tag)
    label.sync_labels(
        neo4j_session, configurations, gcp_update_tag, common_job_parameters,
        'cloudrun configurations', 'GCPCloudRunConfiguration',
    )

    # CLOUDRUN DOMAIN MAPPINGS
    domainmappings = get_cloudrun_domainmappings(cloudrun, project_id, common_job_parameters)
    mappings = transform_mappings(domainmappings, project_id)
    load_cloudrun_domainmappings(neo4j_session, mappings, project_id, gcp_update_tag)
    label.sync_labels(
        neo4j_session, domainmappings, gcp_update_tag, common_job_parameters,
        'cloudrun domainmappings', 'GCPCloudRunDomainMap',
    )

    # CLOUDRUN REVISIONS
    revs = get_cloudrun_revisions(cloudrun, project_id, common_job_parameters)
    revisions = transform_revisions(revs, project_id)
    load_cloudrun_revisions(neo4j_session, revisions, project_id, gcp_update_tag)
    label.sync_labels(
        neo4j_session, revisions, gcp_update_tag, common_job_parameters,
        'cloudrun revisions', 'GCPCloudRunRevision',
    )

    # CLOUDRUN ROUTES
    rts = get_cloudrun_routes(cloudrun, project_id, common_job_parameters)
    routes = transform_routes(rts, project_id)
    load_cloudrun_routes(neo4j_session, routes, project_id, gcp_update_tag)
    label.sync_labels(
        neo4j_session, routes, gcp_update_tag,
        common_job_parameters, 'cloudrun routes', 'GCPCloudRunRoute',
    )

    # CLOUDRUN SERVICES
    svcs = get_cloudrun_services(cloudrun, project_id, common_job_parameters)
    services = transform_services(svcs, project_id)
    load_cloudrun_services(neo4j_session, services, project_id, gcp_update_tag)
    cleanup_gcp_cloudrun(neo4j_session, common_job_parameters)
    label.sync_labels(
        neo4j_session, services, gcp_update_tag, common_job_parameters,
        'cloudrun services', 'GCPCloudRunService',
    )

    toc = time.perf_counter()
    logger.info(f"Time to process CloudRun: {toc - tic:0.4f} seconds")
