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
def get_gcp_functions(function: Resource, project_id: str, regions: list, common_job_parameters) -> List[Dict]:
    """
        Returns a list of functions for a given project.

        :type functions: Resource
        :param function: The function resource created by googleapiclient.discovery.build()

        :type project_id: str
        :param project_id: Current Google Project Id

        :type region: string
        :param region: The region in which the function is defined

        :rtype: list
        :return: List of Functions
    """
    try:
        locations = []
        request = function.projects().locations().list(name=f"projects/{project_id}")
        while request is not None:
            response = request.execute()
            for location in response['locations']:
                location["id"] = location.get("name", None)
                location['location_name'] = location['name'].split('/')[-1]
                if regions is None or len(regions) == 0:
                    locations.append(location)
                else:
                    if location['locationId'] in regions or location['locationId'] == 'global':
                        locations.append(location)

            request = function.projects().locations().list_next(previous_request=request, previous_response=response)
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err.get('status', '') == 'PERMISSION_DENIED' or err.get('message', '') == 'Forbidden':
            logger.warning(
                (
                    "Could not retrieve Functions locations on project %s due to permissions issues.\
                        Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return []
        else:
            raise

    try:
        functions = []
        for region in locations:
            request = function.projects().locations().functions().list(
                parent=region.get('name', None),
            )
            while request is not None:
                response = request.execute()
                for func in response.get('functions', []):
                    func['id'] = func['name']
                    func['function_name'] = func['name'].split('/')[-1]
                    func['region'] = region.get('locationId', 'global')
                    func['consolelink'] = gcp_console_link.get_console_link(
                        resource_name='cloud_function', project_id=project_id, cloud_function_name=func['name'].split('/')[-1], region=func['region'],
                    )
                    functions.append(func)
                request = function.projects().locations().functions().list_next(
                    previous_request=request,
                    previous_response=response,
                )

        return functions
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err.get('status', '') == 'PERMISSION_DENIED' or err.get('message', '') == 'Forbidden':
            logger.warning(
                (
                    "Could not retrieve Functions on project %s due to permissions issues. Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return []
        else:
            raise


def get_function_policy_bindings(function: Resource, fns: Dict, project_id: str) -> List[Dict]:
    """
        Returns a list of bindings attached to IAM policy of a Function within the given project.

        :type function: The GCP function resource object
        :param function: The functions resource object created by googleapiclient.discovery.build()

        :type Func: Dict
        :param fns: The Dict object of function

        :type project_id: str
        :param project_id: Current Google Project Id

        :rtype: list
        :return: List of gcp function iam policy bindings
    """
    try:
        iam_policy = function.projects().locations().functions().getIamPolicy(resource=fns['name']).execute()
        bindings = iam_policy.get('bindings', [])
        return bindings
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err.get('status', '') == 'PERMISSION_DENIED' or err.get('message', '') == 'Forbidden':
            logger.warning(
                (
                    "Could not retrieve iam policy of function on project %s due to permissions issues. Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return []
        else:
            raise


@timeit
def transform_function_policy_bindings(response_objects: List[Dict], function_id: str, project_id: str) -> List[Dict]:
    """
    Process the GCP function_policy_binding objects and return a flattened list of GCP bindings with all the necessary fields
    we need to load it into Neo4j
    :param response_objects: The return data from get_gcp_function_policy_bindings()
    :return: A list of GCP GCP bindings
    """
    binding_list = []
    for res in response_objects:
        res['id'] = f"projects/{project_id}/function/{function_id}/role/{res['role']}"
        binding_list.append(res)
    return binding_list


@timeit
def load_functions(session: neo4j.Session, data_list: List[Dict], project_id: str, update_tag: int) -> None:
    session.execute_write(_load_functions_tx, data_list, project_id, update_tag)


@timeit
def _load_functions_tx(tx: neo4j.Transaction, functions: List[Resource], project_id: str, gcp_update_tag: int) -> None:
    """
        :type neo4j_transaction: Neo4j transaction object
        :param neo4j transaction: The Neo4j transaction object

        :type function_resp: List
        :param function_resp: A list GCP Functions

        :type project_id: str
        :param project_id: Current Google Project Id

        :type gcp_update_tag: timestamp
        :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with
    """
    ingest_functions = """
    UNWIND $functions as func
    MERGE (function:GCPFunction{id:func.id})
    ON CREATE SET
        function.firstseen = timestamp()
    SET
        function.name = func.name,
        function.function_name = func.function_name,
        function.description = func.description,
        function.status = func.status,
        function.region = func.region,
        function.entryPoint = func.entryPoint,
        function.runtime = func.runtime,
        function.timeout = func.timeout,
        function.availableMemoryMb = func.availableMemoryMb,
        function.serviceAccountEmail = func.serviceAccountEmail,
        function.updateTime = func.updateTime,
        function.versionId = func.versionId,
        function.ingressSettings = func.ingressSettings,
        function.network = func.network,
        function.maxInstances = func.maxInstances,
        function.vpcConnector = func.vpcConnector,
        function.vpcConnectorEgressSettings = func.vpcConnectorEgressSettings,
        function.ingressSettings = func.ingressSettings,
        function.buildWorkerPool = func.buildWorkerPool,
        function.buildId = func.buildId,
        function.sourceToken = func.sourceToken,
        function.sourceArchiveUrl = func.sourceArchiveUrl,
        function.consolelink = func.consolelink,
        function.lastupdated = $gcp_update_tag
    WITH function
    MATCH (owner:GCPProject{id: $ProjectId})
    MERGE (owner)-[r:RESOURCE]->(function)
    ON CREATE SET
        r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag
    """
    tx.run(
        ingest_functions,
        functions=functions,
        ProjectId=project_id,
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def load_function_entity_relation(session: neo4j.Session, function: Dict, update_tag: int) -> None:
    session.execute_write(load_function_entity_relation_tx, function, update_tag)


@timeit
def load_function_entity_relation_tx(tx: neo4j.Transaction, function: Dict, gcp_update_tag: int) -> None:
    """
        :type neo4j_session: Neo4j session object
        :param neo4j session: The Neo4j session object

        :type function: Dict
        :param fucntion: Function Dict object

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
    MATCH (function:GCPFunction{id: $function_id})
    MERGE (principal)-[r:USES]->(function)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag    """
    tx.run(
        ingest_entities,
        function_id=function.get('id', None),
        entities=function.get('entities', []),
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def attach_function_to_binding(session: neo4j.Session, function_id: str, bindings: List[Dict], gcp_update_tag: int) -> None:
    session.execute_write(attach_function_to_bindings_tx, bindings, function_id, gcp_update_tag)


@timeit
def attach_function_to_bindings_tx(
    tx: neo4j.Transaction, bindings: List[Dict],
    function_id: str, gcp_update_tag: int,
) -> None:

    query = """
    UNWIND $Records as record
    MERGE (binding:GCPBinding{id: record.id})
    ON CREATE SET
        binding.firstseen = timestamp()
    SET
        binding.lastupdated = $gcp_update_tag,
        binding.members = record.members,
        binding.role = record.role
    WITH binding
    MATCH (function:GCPFunction{id: $FunctionId})
    MERGE (function)-[a:ATTACHED_BINDING]->(binding)
    ON CREATE SET
        a.firstseen = timestamp()
    SET a.lastupdated = $gcp_update_tag
    """
    tx.run(
        query,
        Records=bindings,
        FunctionId=function_id,
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def cleanup_gcp_functions(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    """
    Delete out-of-date GCP Functions and relationships

    :type neo4j_session: The Neo4j session object
    :param neo4j_session: The Neo4j session

    :type common_job_parameters: dict
    :param common_job_parameters: Dictionary of other job parameters to pass to Neo4j

    :rtype: NoneType
    :return: Nothing
    """
    run_cleanup_job('gcp_function_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def cleanup_function_policy_bindings(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    """
    Delete out-of-date GCP Bindings and relationships

    :type neo4j_session: The Neo4j session object
    :param neo4j_session: The Neo4j session

    :type common_job_parameters: dict
    :param common_job_parameters: Dictionary of other job parameters to pass to Neo4j

    :rtype: NoneType
    :return: Nothing
    """
    run_cleanup_job('gcp_function_policy_bindings_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync(
    neo4j_session: neo4j.Session, function: Resource, project_id: str, gcp_update_tag: int,
    common_job_parameters: Dict, regions: list,
) -> None:
    """
    Get GCP Cloud Functions using the Cloud Function resource object, ingest to Neo4j, and clean up old data.

    :type neo4j_session: The Neo4j session object
    :param neo4j_session: The Neo4j session

    :type function: The GCP Cloud Function resource object created by googleapiclient.discovery.build()
    :param function: The GCP Cloud Function resource object

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

    logger.info("Syncing Cloud Functions for project '%s', at %s.", project_id, tic)

    # FUNCTIONS
    functions = get_gcp_functions(function, project_id, regions, common_job_parameters)

    load_functions(neo4j_session, functions, project_id, gcp_update_tag)
    for func in functions:
        load_function_entity_relation(neo4j_session, func, gcp_update_tag)
        bindings = get_function_policy_bindings(function, func, project_id)
        bindings_list = transform_function_policy_bindings(bindings, func['id'], project_id)
        attach_function_to_binding(neo4j_session, func['id'], bindings_list, gcp_update_tag)

    cleanup_function_policy_bindings(neo4j_session, common_job_parameters)
    cleanup_gcp_functions(neo4j_session, common_job_parameters)
    label.sync_labels(neo4j_session, functions, gcp_update_tag, common_job_parameters, 'functions', 'GCPFunction')

    toc = time.perf_counter()
    logger.info(f"Time to process Cloud Functions: {toc - tic:0.4f} seconds")
