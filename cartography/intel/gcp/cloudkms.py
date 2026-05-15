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
def get_kms_locations(kms: Resource, project_id: str, regions: list, common_job_parameters) -> List[Dict]:
    """
        Returns a list of kms locations for a given project.

        :type kms: Resource
        :param kms: The kms resource created by googleapiclient.discovery.build()

        :type project_id: str
        :param project_id: Current Google Project Id

        :rtype: list
        :return: List of KMS Locations
    """
    try:
        locations = []
        request = kms.projects().locations().list(name=f"projects/{project_id}")
        while request is not None:
            response = request.execute()
            if response.get('locations', []):
                for location in response['locations']:
                    location['id'] = location['name']
                    location['location_name'] = location['name'].split('/')[-1]
                    if regions is None or len(regions) == 0:
                        locations.append(location)
                    else:
                        if location['locationId'] in regions or location['locationId'] == 'global':
                            locations.append(location)
            request = kms.projects().locations().list_next(previous_request=request, previous_response=response)

        return locations
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err.get('status', '') == 'PERMISSION_DENIED' or err.get('message', '') == 'Forbidden':
            logger.warning(
                (
                    "Could not retrieve KMS locations on project %s due to permissions issues. Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return []
        else:
            raise


@timeit
def get_kms_keyrings(kms: Resource, kms_locations: List[Dict], project_id: str) -> List[Dict]:
    """
        Returns a list of kms keyrings for a given project and locations.

        :type kms: Resource
        :param kms: The kms resource created by googleapiclient.discovery.build()

        :type kms_locations: List
        :param kms_locations: List of kms locations

        :type project_id: str
        :param project_id: Current Google Project Id

        :rtype: list
        :return: List of KMS Keyrings in Locations
    """
    try:
        key_rings = []
        for loc in kms_locations:
            request = kms.projects().locations().keyRings().list(parent=loc['name'])
            while request is not None:
                response = request.execute()
                if response.get('keyRings', []):
                    for key_ring in response['keyRings']:
                        key_ring['loc_id'] = loc['id']
                        key_ring['id'] = key_ring['name']
                        key_ring['key_ring_name'] = key_ring['name'].split('/')[-1]
                        key_ring['region'] = loc.get("locationId", "global")
                        key_ring['consolelink'] = gcp_console_link.get_console_link(
                            resource_name='kms_key_ring', project_id=project_id, kms_key_ring_name=key_ring['name'].split('/')[-1], region=key_ring['region'],
                        )
                        key_rings.append(key_ring)
                request = kms.projects().locations().keyRings().list_next(
                    previous_request=request,
                    previous_response=response,
                )
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err.get('status', '') == 'PERMISSION_DENIED' or err.get('message', '') == 'Forbidden':
            logger.warning(
                (
                    "Could not retrieve KMS keyrings in locations on project %s due to permissions issues.\
                         Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return []
        else:
            raise
    return key_rings


@timeit
def get_keyring_policy_bindings(kms: Resource, keyring: Dict, project_id: str) -> List[Dict]:
    """
        Returns a list of users attached to IAM policy of a keyring within the given project.

        :type kms: The GCP KMS resource object
        :param kms: The KMS resource object created by googleapiclient.discovery.build()

        :type keyrings: Dict
        :param keyrings: The Dict of Keyring object

        :type project_id: str
        :param project_id: Current Google Project Id

        :rtype: list
        :return: List of keyring iam policy users
    """
    try:
        iam_policy = kms.projects().locations().keyRings().getIamPolicy(resource=keyring['id']).execute()
        bindings = iam_policy.get('bindings', [])
        return bindings
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err.get('status', '') == 'PERMISSION_DENIED' or err.get('message', '') == 'Forbidden':
            logger.warning(
                (
                    "Could not retrieve iam policy of keyring on project %s due to permissions issues. Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return []
        else:
            raise


@timeit
def transform_keryring_policy_bindings(response_objects: List[Dict], keyring_id: str, project_id: str) -> List[Dict]:
    """
    Process the GCP kms_policy_binding objects and return a flattened list of GCP bindings with all the necessary fields
    we need to load it into Neo4j
    :param response_objects: The return data from get_gcp_function_policy_bindings()
    :return: A list of GCP GCP bindings
    """
    binding_list = []
    for res in response_objects:
        res['id'] = f"projects/{project_id}/keyring/{keyring_id}/role/{res['role']}"
        binding_list.append(res)
    return binding_list


@timeit
def attach_keyring_to_binding(session: neo4j.Session, keyring_id: str, bindings: List[Dict], gcp_update_tag: int) -> None:
    session.execute_write(attach_keyring_to_bindings_tx, bindings, keyring_id, gcp_update_tag)


@timeit
def attach_keyring_to_bindings_tx(
    tx: neo4j.Transaction, bindings: List[Dict],
    keyring_id: str, gcp_update_tag: int,
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
    MATCH (keyring:GCPKMSKeyRing{id: $KeyringId})
    MERGE (keyring)-[a:ATTACHED_BINDING]->(binding)
    ON CREATE SET
        a.firstseen = timestamp()
    SET a.lastupdated = $gcp_update_tag
    """
    tx.run(
        query,
        Records=bindings,
        KeyringId=keyring_id,
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def get_kms_crypto_keys(kms: Resource, key_rings: List[Dict], project_id: str) -> List[Dict]:
    """
        Returns a list of kms cryptokeys for a given keyrings and locations.

        :type kms: Resource
        :param kms: The kms resource created by googleapiclient.discovery.build()

        :type key_rings: List
        :param key_rings: List of kms key rings

        :type project_id: str
        :param project_id: Current Google Project Id

        :rtype: list
        :return: List of KMS Cryptokeys for Keyrings and Locations
    """
    try:
        crypto_keys = []
        for key_ring in key_rings:
            request = kms.projects().locations().keyRings().cryptoKeys().list(parent=key_ring['name'])
            while request is not None:
                response = request.execute()
                if response.get('cryptoKeys', []):
                    for crypto_key in response['cryptoKeys']:
                        crypto_key['keyring_id'] = key_ring['id']
                        crypto_key['id'] = crypto_key['name']
                        crypto_key['crypto_key_name'] = crypto_key['name'].split('/')[-1]
                        crypto_key['region'] = key_ring.get("region", "global")
                        crypto_key['consolelink'] = gcp_console_link.get_console_link(
                            resource_name='kms_key', project_id=project_id, kms_key_ring_name=key_ring['name'].split('/')[-1], region=crypto_key['region'], kms_key_name=crypto_key['name'].split('/')[-1],
                        )
                        crypto_keys.append(crypto_key)
                request = kms.projects().locations().keyRings().cryptoKeys().list_next(
                    previous_request=request,
                    previous_response=response,
                )
        return crypto_keys
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err.get('status', '') == 'PERMISSION_DENIED' or err.get('message', '') == 'Forbidden':
            logger.warning(
                (
                    "Could not retrieve KMS cryptokeys for keyrings in locations on project %s \
                        due to permissions issues. Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return []
        else:
            raise


def load_kms_locations(session: neo4j.Session, data_list: List[Dict], project_id: str, update_tag: int) -> None:
    session.execute_write(_load_kms_locations_tx, data_list, project_id, update_tag)


def _load_kms_locations_tx(
    tx: neo4j.Transaction, locations: List[Resource],
    project_id: str, gcp_update_tag: int,
) -> None:
    """
        :type neo4j_transaction: Neo4j transaction object
        :param neo4j transaction: The Neo4j transaction object

        :type locations_resp: List
        :param locations_resp: A list GCP KMS Locations

        :type project_id: str
        :param project_id: Current Google Project Id

        :type gcp_update_tag: timestamp
        :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with
    """
    ingest_kms_locations = """
    UNWIND $locations as loc
    MERGE (location:GCPLocation{id:loc.id})
    ON CREATE SET
        location.firstseen = timestamp()
    SET
        location.name = loc.name,
        location.location_name = loc.location_name,
        location.locationId = loc.locationId,
        location.displayName = loc.displayName,
        location.region = loc.locationId,
        location.lastupdated = $gcp_update_tag
    WITH location, loc
    MATCH (owner:GCPProject{id: $ProjectId})
    MERGE (owner)-[r:RESOURCE]->(location)
    ON CREATE SET
        r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag
    """
    tx.run(
        ingest_kms_locations,
        locations=locations,
        ProjectId=project_id,
        gcp_update_tag=gcp_update_tag,
    )


def load_kms_key_rings(session: neo4j.Session, data_list: List[Dict], project_id: str, update_tag: int) -> None:
    session.execute_write(_load_kms_key_rings_tx, data_list, project_id, update_tag)


def _load_kms_key_rings_tx(
    tx: neo4j.Transaction, key_rings: List[Resource],
    project_id: str, gcp_update_tag: int,
) -> None:
    """
        :type neo4j_transaction: Neo4j transaction object
        :param neo4j transaction: The Neo4j transaction object

        :type key_rings_resp: List
        :param key_rings_resp: A list GCP KMS Keyrings for locations

        :type project_id: str
        :param project_id: Current Google Project Id

        :type gcp_update_tag: timestamp
        :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with
    """
    ingest_kms_key_rings = """
    UNWIND $key_rings as keyr
    MERGE (keyring:GCPKMSKeyRing{id:keyr.id})
    ON CREATE SET
        keyring.firstseen = timestamp()
    SET
        keyring.name = keyr.name,
        keyring.key_ring_name = keyr.key_ring_name,
        keyring.region = keyr.region,
        keyring.public_access = keyr.public_access,
        keyring.createTime = keyr.createTime,
        keyring.consolelink = keyr.consolelink,
        keyring.lastupdated = $gcp_update_tag
    WITH keyring, keyr
    MATCH (location:GCPLocation{id:keyr.loc_id})
    MERGE (location)-[r:RESOURCE]->(keyring)
    ON CREATE SET
        r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag
    """
    tx.run(
        ingest_kms_key_rings,
        key_rings=key_rings,
        ProjectId=project_id,
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def load_keyring_entity_relation(session: neo4j.Session, keyring: Dict, update_tag: int) -> None:
    session.execute_write(load_keyring_entity_relation_tx, keyring, update_tag)


@timeit
def load_keyring_entity_relation_tx(tx: neo4j.Transaction, keyring: Dict, gcp_update_tag: int) -> None:
    """
        :type neo4j_session: Neo4j session object
        :param neo4j session: The Neo4j session object

        :type keyring: Dict
        :param keyring: Keyring Dict object

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
    MATCH (keyring:GCPKMSKeyRing{id: $keyring_id})
    MERGE (principal)-[r:USES]->(keyring)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag    """
    tx.run(
        ingest_entities,
        keyring_id=keyring.get('id', None),
        entities=keyring.get('entities', []),
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def load_kms_crypto_keys(session: neo4j.Session, data_list: List[Dict], project_id: str, update_tag: int) -> None:
    session.execute_write(_load_kms_crypto_keys_tx, data_list, project_id, update_tag)


@timeit
def _load_kms_crypto_keys_tx(
    tx: neo4j.Transaction, crypto_keys: List[Resource],
    project_id: str, gcp_update_tag: int,
) -> None:
    """
        :type neo4j_transaction: Neo4j transaction object
        :param neo4j transaction: The Neo4j transaction object

        :type crypto_keys_resp: List
        :param crypt_keys_resp: A list GCP KMS CryptoKeys for keyrings in locations

        :type project_id: str
        :param project_id: Current Google Project Id

        :type gcp_update_tag: timestamp
        :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with
    """
    ingest_crypto_keys = """
    UNWIND $crypto_keys as ck
    MERGE (crypto_key:GCPKMSCryptoKey{id:ck.id})
    ON CREATE SET
        crypto_key.firstseen = timestamp()
    SET
        crypto_key.name = ck.name,
        crypto_key.crypto_key_name = ck.crypto_key_name,
        crypto_key.purpose = ck.purpose,
        crypto_key.region = ck.region,
        crypto_key.createTime = ck.createTime,
        crypto_key.nextRotationTime = ck.nextRotationTime,
        crypto_key.rotationPeriod = ck.rotationPeriod,
        crypto_key.consolelink = ck.consolelink,
        crypto_key.lastupdated = $gcp_update_tag
    WITH crypto_key, ck
    MATCH (key_ring:GCPKMSKeyRing{id:ck.keyring_id})
    MERGE (key_ring)-[r:RESOURCE]->(crypto_key)
    ON CREATE SET
        r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag
    """
    tx.run(
        ingest_crypto_keys,
        crypto_keys=crypto_keys,
        ProjectId=project_id,
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def cleanup_gcp_kms(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    """
    Delete out-of-date GCP KMS and relationships

    :type neo4j_session: The Neo4j session object
    :param neo4j_session: The Neo4j session

    :type common_job_parameters: dict
    :param common_job_parameters: Dictionary of other job parameters to pass to Neo4j

    :rtype: NoneType
    :return: Nothing
    """
    run_cleanup_job('gcp_kms_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync(
    neo4j_session: neo4j.Session, kms: Resource, project_id: str, gcp_update_tag: int,
    common_job_parameters: Dict, regions: list,
) -> None:
    """
    Get GCP Cloud KMS using the Cloud KMS resource object, ingest to Neo4j, and clean up old data.

    :type neo4j_session: The Neo4j session object
    :param neo4j_session: The Neo4j session

    :type kms: The GCP Cloud KMS resource object created by googleapiclient.discovery.build()
    :param kms: The GCP Cloud KMS resource object

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

    logger.info("Syncing Cloud KMS for project '%s', at %s.", project_id, tic)

    # KMS LOCATIONS
    locations = get_kms_locations(kms, project_id, regions, common_job_parameters)
    load_kms_locations(neo4j_session, locations, project_id, gcp_update_tag)
    label.sync_labels(neo4j_session, locations, gcp_update_tag, common_job_parameters, 'kms_locations', 'GCPLocation')
    # KMS KEYRINGS
    key_rings = get_kms_keyrings(kms, locations, project_id)
    load_kms_key_rings(neo4j_session, key_rings, project_id, gcp_update_tag)
    for key_ring in key_rings:
        load_keyring_entity_relation(neo4j_session, key_ring, gcp_update_tag)
        bindings = get_keyring_policy_bindings(kms, key_ring, project_id)
        bindings_list = transform_keryring_policy_bindings(bindings, key_ring['id'], project_id)
        attach_keyring_to_binding(neo4j_session, key_ring['id'], bindings_list, gcp_update_tag)
    label.sync_labels(neo4j_session, key_rings, gcp_update_tag, common_job_parameters, 'keyrings', 'GCPKMSKeyRing')
    crypto_keys = get_kms_crypto_keys(kms, key_rings, project_id)
    load_kms_crypto_keys(neo4j_session, crypto_keys, project_id, gcp_update_tag)
    cleanup_gcp_kms(neo4j_session, common_job_parameters)

    toc = time.perf_counter()
    logger.info(f"Time to process Cloud KMS: {toc - tic:0.4f} seconds")
