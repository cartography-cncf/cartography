import json
import logging
import time
from typing import Dict
from typing import List

import neo4j
from cloudconsolelink.clouds.gcp import GCPLinker
from googleapiclient.discovery import HttpError
from googleapiclient.discovery import Resource

from . import iam
from . import label
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)
gcp_console_link = GCPLinker()


@timeit
def get_apigateway_locations(apigateway: Resource, project_id: str, common_job_parameters) -> List[Dict]:
    """
        Returns a list of locations within the given project.

        :type apigateway: The GCP APIGateway resource object
        :param apigateway: The APIGateway resource object created by googleapiclient.discovery.build()

        :type project_id: str
        :param project_id: Current Google Project Id

        :rtype: list
        :return: List of locations
    """
    locations = []
    try:
        req = apigateway.projects().locations().list(name=f'projects/{project_id}')
        while req is not None:
            res = req.execute()
            if res.get('locations', []):
                locations.extend(res.get('locations', []))
            req = apigateway.projects().locations().list_next(previous_request=req, previous_response=res)

        return locations
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err.get('status', '') == 'PERMISSION_DENIED' or err.get('message', '') == 'Forbidden':
            logger.warning(
                (
                    "Could not retrieve api gateway locations on project %s due to permissions issues. Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return []
        else:
            raise


@timeit
def transform_locations(locations: List[Dict], project_id: str) -> List[Dict]:
    locations = []
    for location in locations:
        location['project_id'] = project_id
        location['id'] = location['locationId']
        location['consolelink'] = gcp_console_link.get_console_link(project_id=project_id, resource_name='apigateway_home')
        location['location_name'] = location.get('name').split('/')[-1]
        locations.append(location)

    return locations


@timeit
def get_apis(apigateway: Resource, project_id: str, regions: list, common_job_parameters) -> List[Dict]:
    """
        Returns a list of apis within the given project.

        :type apigateway: The GCP APIGateway resource object
        :param apigateway: The APIGateway resource object created by googleapiclient.discovery.build()

        :type project_id: str
        :param project_id: Current Google Project Id

        :type locations: List
        :param locations: Locations List

        :rtype: list
        :return: List of apis
    """
    apis = []
    try:
        if regions is None:
            regions = ['global']

        for region in regions:
            req = apigateway.projects().locations().apis().list(parent=f'projects/{project_id}/locations/{region}')
            while req is not None:
                res = req.execute()
                if res.get('apis', []):
                    for api in res['apis']:
                        api['project_id'] = project_id
                        api['id'] = api['name']
                        api['api_name'] = api.get('name').split('/')[-1]
                        x = api.get('name').split('/')
                        x = x[x.index('locations') + 1].split("-")
                        api['region'] = x[0]
                        if len(x) > 1:
                            api['region'] = f"{x[0]}-{x[1]}"

                        api_entities, public_access = get_api_policy_entities(apigateway, api, project_id)
                        api['entities'] = api_entities
                        api['public_access'] = public_access
                        api['consolelink'] = gcp_console_link.get_console_link(
                            resource_name='api', project_id=project_id, managed_service_name=api['managedService'], api_name=api['displayName'],
                        )
                        apis.append(api)
                req = apigateway.projects().locations().apis().list_next(previous_request=req, previous_response=res)

        return apis
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err.get('status', '') == 'PERMISSION_DENIED' or err.get('message', '') == 'Forbidden':
            logger.warning(
                (
                    "Could not retrieve apis on project %s due to permissions issues. Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return []
        else:
            raise


@timeit
def get_api_policy_entities(apigateway: Resource, api: Dict, project_id: str) -> List[Dict]:
    """
        Returns a list of users attached to IAM policy of an API within the given project.

        :type apigateway: The GCP APIGateway resource object
        :param apigateway: The APIGateway resource object created by googleapiclient.discovery.build()

        :type api: Dict
        :param api: The Dict of API object

        :type project_id: str
        :param project_id: Current Google Project Id

        : type locations: List
        : param Location: List of locations

        :rtype: list
        :return: List of api iam policy users
    """
    entity_list = []
    try:
        iam_policy = apigateway.projects().locations().apis().getIamPolicy(
            resource=api['id'],
        ).execute()
        bindings = iam_policy.get('bindings', [])
        entity_list, public_access = iam.transform_bindings(bindings, project_id)
        return entity_list, public_access
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err.get('status', '') == 'PERMISSION_DENIED' or err.get('message', '') == 'Forbidden':
            logger.warning(
                (
                    "Could not retrieve iam policy of apis on project %s due to permissions issues. Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return []
        else:
            raise


@timeit
def get_api_configs(apigateway: Resource, project_id: str, api: Dict, regions: list) -> List[Dict]:
    """
        Returns a list of apis configs within the given project.

        :type apigateway: The GCP APIGateway resource object
        :param apigateway: The APIGateway resource object created by googleapiclient.discovery.build()

        :type project_id: str
        :param project_id: Current Google Project Id

        :type apis: List
        :param: apis: List of apis

        :rtype: list
        :return: List of api configs.
    """
    api_configs = []
    try:
        # if regions is None:
        #     regions = ['global']

        # for region in regions:
        req = apigateway.projects().locations().apis().configs().list(
            # parent=f'projects/{project_id}/locations/{region}/apis/{api["name"].split('/')[-1]}',
            parent=api['name'],
        )
        while req is not None:
            res = req.execute()
            if res.get('apiConfigs', []):
                for apiConfig in res['apiConfigs']:
                    apiConfig['api_id'] = api['name']
                    # apiConfig['api_id'] = f"projects/{project_id}/locations/{region}/apis/\
                    # {apiConfig.get('name').split('/')[-3]}"
                    apiConfig['id'] = apiConfig['name']
                    apiConfig['apiconfig_name'] = apiConfig.get('name').split('/')[-1]
                    apiConfig['project_id'] = project_id
                    x = apiConfig.get('name').split('/')
                    x = x[x.index('locations') + 1].split("-")
                    apiConfig['region'] = x[0]
                    if len(x) > 1:
                        apiConfig['region'] = f"{x[0]}-{x[1]}"
                    apiConfig['consolelink'] = gcp_console_link.get_console_link(
                        resource_name='api_config', project_id=project_id, managed_service_name=api['managedService'],
                        api_name=api.get('name').split('/')[-1],
                        api_config_name=apiConfig.get('name').split('/')[-1], api_configuration_id=apiConfig['serviceConfigId'],
                    )
                    api_configs.append(apiConfig)
            req = apigateway.projects().locations().apis().configs().list_next(
                previous_request=req,
                previous_response=res,
            )

        return api_configs
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err.get('status', '') == 'PERMISSION_DENIED' or err.get('message', '') == 'Forbidden':
            logger.warning(
                (
                    "Could not retrieve apis configs on project %s due to permissions issues. Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return []
        else:
            # raise
            logger.warning(
                (
                    "Could not retrieve apis configs on project %s, api %s. Code: %s, Message: %s"
                ), project_id, api['name'], err['code'], err['message'],
            )
            return []


@timeit
def get_gateways(apigateway: Resource, project_id: str, regions: list, common_job_parameters) -> List[Dict]:
    """
        Returns a list of gateways within the given project.

        :type apigateway: The GCP APIGateway resource object
        :param apigateway: The APIGateway resource object created by googleapiclient.discovery.build()

        :type project_id: str
        :param project_id: Current Google Project Id

        :type locations: List
        :param locations: List of locations

        :rtype: list
        :return: List of gateways.
    """
    gateways = []
    try:
        if regions is None:
            regions = ['global']

        for region in regions:
            req = apigateway.projects().locations().gateways().list(parent=f'projects/{project_id}/locations/{region}')
            while req is not None:
                res = req.execute()
                if res.get('gateways', []):
                    for gateway in res['gateways']:
                        gateway['id'] = gateway['name']
                        gateway['geteway_name'] = gateway.get('name').split('/')[-1]
                        gateway['project_id'] = project_id
                        x = gateway.get('name').split('/')
                        x = x[x.index('locations') + 1].split("-")
                        gateway['region'] = x[0]
                        if len(x) > 1:
                            gateway['region'] = f"{x[0]}-{x[1]}"
                        gateway_entities, public_access = get_api_policy_entities(apigateway, gateway, project_id)
                        gateway['entities'] = gateway_entities
                        gateway['public_access'] = public_access
                        gateway['consolelink'] = gcp_console_link.get_console_link(
                            resource_name='api_gateway', project_id=project_id, region=gateway['region'], api_gateway_name=gateway.get('name').split('/')[-1],
                        )
                        gateways.append(gateway)
                req = apigateway.projects().locations().gateways().list_next(previous_request=req, previous_response=res)

        return gateways
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err.get('status', '') == 'PERMISSION_DENIED' or err.get('message', '') == 'Forbidden':
            logger.warning(
                (
                    "Could not retrieve gateways on project %s due to permissions issues. Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return []
        else:
            raise


@timeit
def get_api_gateway_policy_entities(apigateway: Resource, gateway: Dict, project_id: str) -> List[Dict]:
    """
        Returns a list of users attached to IAM policy of an API Gateway within the given project.

        :type apigateway: The GCP APIGateway resource object
        :param apigateway: The APIGateway resource object created by googleapiclient.discovery.build()

        :type gateway: Dict
        :param gateway: The Dict of gateway object

        :type project_id: str
        :param project_id: Current Google Project Id

        : type locations: List
        : param Location: List of locations

        :rtype: list
        :return: List of api gateway iam policy users
    """
    try:
        iam_policy = apigateway.projects().locations().gateways().getIamPolicy(
            resource=gateway.get('name'),
        ).execute()
        bindings = iam_policy.get('bindings', [])
        entity_list, public_access = iam.transform_bindings(bindings, project_id)
        return entity_list, public_access
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err.get('status', '') == 'PERMISSION_DENIED' or err.get('message', '') == 'Forbidden':
            logger.warning(
                (
                    "Could not retrieve iam policy of api gateway on project %s due to permissions issues. Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return []
        else:
            raise


@timeit
def load_apigateway_locations(session: neo4j.Session, data_list: List[Dict], project_id: str, update_tag: int) -> None:
    session.execute_write(load_apigateway_locations_tx, data_list, project_id, update_tag)


@timeit
def load_apigateway_locations_tx(
    tx: neo4j.Transaction, locations: List[Dict],
    project_id: str, gcp_update_tag: int,


) -> None:
    """
        Ingest GCP Project Locations into Neo4j

        :type neo4j_session: Neo4j session object
        :param neo4j session: The Neo4j session object

        :type locations: Dict
        :param locations: A GCP Project Locations

        :type project_id: str
        :param project_id: Current Google Project Id

        :type gcp_update_tag: timestamp
        :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with

        :rtype: NoneType
        :return: Nothing
    """
    ingest_project_locations = """
    UNWIND $locations as loc
    MERGE (location:GCPLocation{id:loc.id})
    ON CREATE SET
        location.firstseen = timestamp()
    SET
        location.name = loc.name,
        location.location_name = loc.location_name,
        location.locationId = loc.locationId,
        location.consolelink = loc.consolelink,
        location.displayName = loc.displayName,
        location.region = loc.locationId,
        location.lastupdated = $gcp_update_tag
    WITH location
    MATCH (owner:GCPProject{id: $ProjectId})
    MERGE (owner)-[r:RESOURCE]->(location)
    ON CREATE SET
        r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag
    """
    tx.run(
        ingest_project_locations,
        locations=locations,
        ProjectId=project_id,
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def cleanup_apigateway_locations(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    """
       Delete out-of-date GCP Project Locations

       :type neo4j_session: The Neo4j session object
       :param neo4j_session: The Neo4j session

       :type common_job_parameters: dict
       :param common_job_parameters: Dictionary of other job parameters to pass to Neo4j

       :rtype: NoneType
       :return: Nothing
   """
    run_cleanup_job('gcp_apigateway_locations_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def load_apis(session: neo4j.Session, data_list: List[Dict], project_id: str, update_tag: int) -> None:
    session.execute_write(load_apis_tx, data_list, project_id, update_tag)


@timeit
def load_apis_tx(tx: neo4j.Transaction, apis: List[Dict], project_id: str, gcp_update_tag: int) -> None:
    """
        Ingest GCP APIs into Neo4j

        :type neo4j_session: Neo4j session object
        :param neo4j session: The Neo4j session object

        :type apis: Dict
        :param apis: A list of GCP APIs

        :type project_id: str
        :param project_id: Current Google Project Id

        :type gcp_update_tag: timestamp
        :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with

        :rtype: NoneType
        :return: Nothing
    """
    ingest_apis = """
    UNWIND $apis as ap
    MERGE (api:GCPAPI{id:ap.id})
    ON CREATE SET
        api.firstseen = timestamp()
    SET
        api.name = ap.name,
        api.api_name = ap.api_name,
        api.createTime = ap.createTime,
        api.region = ap.region,
        api.updateTime = ap.updateTime,
        api.public_access = ap.public_access,
        api.displayName = ap.displayName,
        api.managedService = ap.managedService,
        api.consolelink = ap.consolelink,
        api.lastupdated = $gcp_update_tag
    WITH api
    MATCH (owner:GCPProject{id: $ProjectId})
    MERGE (owner)-[r:HAS_API_ENABLED]->(api)
    ON CREATE SET
        r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag
    """
    tx.run(
        ingest_apis,
        apis=apis,
        ProjectId=project_id,
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def cleanup_apis(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    """
       Delete out-of-date GCP APIs

       :type neo4j_session: The Neo4j session object
       :param neo4j_session: The Neo4j session

       :type common_job_parameters: dict
       :param common_job_parameters: Dictionary of other job parameters to pass to Neo4j

       :rtype: NoneType
       :return: Nothing
   """
    run_cleanup_job('gcp_apigateway_apis_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def load_apis_entity_relation(session: neo4j.Session, api: Dict, update_tag: int) -> None:
    session.execute_write(load_apis_entity_relation_tx, api, update_tag)


@timeit
def load_apis_entity_relation_tx(tx: neo4j.Transaction, api: Dict, gcp_update_tag: int) -> None:
    """
        :type neo4j_session: Neo4j session object
        :param neo4j session: The Neo4j session object

        :type apis: Dict
        :param apis: A list of GCP APIs

        :type project_id: str
        :param project_id: Current Google Project Id

        :type gcp_update_tag: timestamp
        :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with

        :rtype: NoneType
        :return: Nothing
    """
    ingest_entities = """
    UNWIND $entities AS entity
    MATCH (principal:GCPPrincipal{email:entity.email})
    WITH principal
    MATCH (api:GCPAPI{id: $api_id})
    MERGE (principal)-[r:USES]->(api)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag    """
    tx.run(
        ingest_entities,
        api_id=api.get('id', None),
        entities=api.get('entities', []),
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def load_gateway_entity_relation(session: neo4j.Session, gateway: Dict, update_tag: int) -> None:
    session.execute_write(load_gateway_entity_relation_tx, gateway, update_tag)


@timeit
def load_gateway_entity_relation_tx(tx: neo4j.Transaction, gateway: Dict, gcp_update_tag: int) -> None:
    """
        :type neo4j_session: Neo4j session object
        :param neo4j session: The Neo4j session object

        :type gateway: Dict
        :param gateway: Gateway Dict object

        :type project_id: str
        :param project_id: Current Google Project Id

        :type gcp_update_tag: timestamp
        :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with

        :rtype: NoneType
        :return: Nothing
    """
    ingest_entities = """
    UNWIND $entities AS entity
    MATCH (principal:GCPPrincipal{email:entity.email})
    WITH principal
    MATCH (gateway:GCPAPIGateway{id: $gateway_id})
    MERGE (principal)-[r:USES]->(gateway)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag    """
    tx.run(
        ingest_entities,
        gateway_id=gateway.get('id', None),
        entities=gateway.get('entities', []),
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def load_api_configs(session: neo4j.Session, data_list: List[Dict], project_id: str, update_tag: int) -> None:
    session.execute_write(load_api_configs_tx, data_list, project_id, update_tag)


@timeit
def load_api_configs_tx(tx: neo4j.Transaction, configs: List[Dict], project_id: str, gcp_update_tag: int) -> None:
    """
        Ingest GCP API Configs into Neo4j

        :type neo4j_session: Neo4j session object
        :param neo4j session: The Neo4j session object

        :type configs: Dict
        :param configs: A list of GCP API Configs

        :type project_id: str
        :param project_id: Current Google Project Id

        :type gcp_update_tag: timestamp
        :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with

        :rtype: NoneType
        :return: Nothing
    """
    ingest_api_configs = """
    UNWIND $configs as conf
    MERGE (config:GCPAPIConfig{id:conf.id})
    ON CREATE SET
        config.firstseen = timestamp()
    SET
        config.name = conf.name,
        config.apiconfig_name = conf.apiconfig_name,
        config.createTime = conf.createTime,
        config.region = conf.region,
        config.updateTime = conf.updateTime,
        config.displayName = conf.displayName,
        config.gatewayServiceAccount = conf.gatewayServiceAccount,
        config.serviceConfigId = conf.serviceConfigId,
        config.state = conf.state,
        config.consolelink = conf.consolelink,
        config.lastupdated = $gcp_update_tag
    WITH config,conf
    MATCH (api:GCPAPI{id:conf.api_id})
    MERGE (api)-[r:HAS_CONFIG]->(config)
    ON CREATE SET
        r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag
    """
    tx.run(
        ingest_api_configs,
        configs=configs,
        ProjectId=project_id,
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def cleanup_api_configs(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    """
       Delete out-of-date GCP API Configs

       :type neo4j_session: The Neo4j session object
       :param neo4j_session: The Neo4j session

       :type common_job_parameters: dict
       :param common_job_parameters: Dictionary of other job parameters to pass to Neo4j

       :rtype: NoneType
       :return: Nothing
   """
    run_cleanup_job('gcp_apigateway_configs_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def load_gateways(session: neo4j.Session, data_list: List[Dict], project_id: str, update_tag: int) -> None:
    session.execute_write(load_gateways_tx, data_list, project_id, update_tag)


@timeit
def load_gateways_tx(tx: neo4j.Transaction, gateways: List[Dict], project_id: str, gcp_update_tag: int) -> None:
    """
        Ingest GCP API Gateways into Neo4j

        :type neo4j_session: Neo4j session object
        :param neo4j session: The Neo4j session object

        :type gateways: Dict
        :param gateways: A list of GCP API Gateways

        :type project_id: str
        :param project_id: Current Google Project Id

        :type gcp_update_tag: timestamp
        :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with

        :rtype: NoneType
        :return: Nothing
    """
    ingest_gateways = """
    UNWIND $gateways as g
    MERGE (gateway:GCPAPIGateway{id:g.id})
    ON CREATE SET
        gateway.firstseen = timestamp()
    SET
        gateway.name = g.name,
        gateway.gateway_name = g.gateway_name,
        gateway.createTime = g.createTime,
        gateway.updateTime = g.updateTime,
        gateway.displayName = g.displayName,
        gateway.region = g.region,
        gateway.public_access = g.public_access,
        gateway.apiConfig = g.apiConfig,
        gateway.state = g.state,
        gateway.defaultHostname = g.defaultHostname,
        gateway.consolelink = g.consolelink,
        gateway.lastupdated = $gcp_update_tag
    WITH gateway,g
    MATCH (apiconfig:GCPAPIConfig{id:g.apiConfig})
    MERGE (apiconfig)-[r:HAS_GATEWAY]->(gateway)
    ON CREATE SET
        r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag
    """
    tx.run(
        ingest_gateways,
        gateways=gateways,
        ProjectId=project_id,
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def cleanup_api_gateways(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    """
       Delete out-of-date GCP API Gateways

       :type neo4j_session: The Neo4j session object
       :param neo4j_session: The Neo4j session

       :type common_job_parameters: dict
       :param common_job_parameters: Dictionary of other job parameters to pass to Neo4j

       :rtype: NoneType
       :return: Nothing
   """
    run_cleanup_job('gcp_apigateway_gateways_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync(
    neo4j_session: neo4j.Session, apigateway: Resource, project_id: str, gcp_update_tag: int,
    common_job_parameters: Dict, regions: list,
) -> None:
    """
        Get GCP API Gateway Resources using the API Gateway resource object, ingest to Neo4j, and clean up old data.

        :type neo4j_session: The Neo4j session object
        :param neo4j_session: The Neo4j session

        :type apigateway: The apigateway resource object created by googleapiclient.discovery.build()
        :param dns: The GCP apigateway resource object

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

    logger.info("Syncing Apigateway for project '%s', at %s.", project_id, tic)

    # API Gateway Locations
    locs = get_apigateway_locations(apigateway, project_id, common_job_parameters)
    locations = transform_locations(locs, project_id)
    load_apigateway_locations(neo4j_session, locations, project_id, gcp_update_tag)

    # Cleanup Locations
    cleanup_apigateway_locations(neo4j_session, common_job_parameters)
    label.sync_labels(
        neo4j_session, locations, gcp_update_tag,
        common_job_parameters, 'apigateway_locations', 'GCPLocation',
    )

    # API Gateway APIs
    apis = get_apis(apigateway, project_id, regions, common_job_parameters)
    load_apis(neo4j_session, apis, project_id, gcp_update_tag)
    for api in apis:
        load_apis_entity_relation(neo4j_session, api, gcp_update_tag)

    # Cleanup APIs
    cleanup_apis(neo4j_session, common_job_parameters)

    # API Gateway API Configs
    for api in apis:
        configs = get_api_configs(apigateway, project_id, api, regions)
        load_api_configs(neo4j_session, configs, project_id, gcp_update_tag)

    # Cleanup API Gateway Configs
    cleanup_api_configs(neo4j_session, common_job_parameters)

    # API Gateway Gateways
    gateways = get_gateways(apigateway, project_id, regions, common_job_parameters)
    load_gateways(neo4j_session, gateways, project_id, gcp_update_tag)
    for gateway in gateways:
        load_gateway_entity_relation(neo4j_session, gateway, gcp_update_tag)

    # Cleanup API Gateway Gateways
    cleanup_api_gateways(neo4j_session, common_job_parameters)

    toc = time.perf_counter()
    logger.info(f"Time to process ApiGateway: {toc - tic:0.4f} seconds")
