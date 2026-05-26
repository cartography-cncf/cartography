import logging
import time
from typing import Any
from typing import Dict
from typing import List

import neo4j
import oci

from . import utils
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


def get_all_oci_compartments(
    identity_client: oci.identity.identity_client.IdentityClient,
    tenancy_id: str,
) -> List[Dict[str, Any]]:
    """
    Get all compartments in the tenancy (recursively).
    """
    try:
        response = oci.pagination.list_call_get_all_results(
            identity_client.list_compartments,
            tenancy_id,
            compartment_id_in_subtree=True,
            access_level="ACCESSIBLE",
        )
        compartments = []
        for comp in response.data:
            compartments.append({
                'id': comp.id,
                'compartmentId': comp.id,
                'name': comp.name,
                'description': comp.description,
                'lifecycleState': comp.lifecycle_state,
                'timeCreated': str(comp.time_created),
                'parentCompartmentId': comp.compartment_id,
            })
        return compartments
    except oci.exceptions.ServiceError as e:
        logger.error(
            "Failed to fetch compartments for tenancy '%s': %s", tenancy_id, e.message,
        )
        return []


def get_current_oci_compartment(
    identity_client: oci.identity.identity_client.IdentityClient,
    compartment_id: str,
) -> List[Dict[str, Any]]:
    """
    Get a single compartment by its OCID.
    """
    try:
        response = identity_client.get_compartment(compartment_id)
        comp = response.data
        return [{
            'id': comp.id,
            'compartmentId': comp.id,
            'name': comp.name,
            'description': comp.description,
            'lifecycleState': comp.lifecycle_state,
            'timeCreated': str(comp.time_created),
            'parentCompartmentId': comp.compartment_id,
        }]
    except oci.exceptions.ServiceError as e:
        logger.error(
            "Failed to fetch compartment '%s': %s", compartment_id, e.message,
        )
        return []


def load_oci_compartments(
    neo4j_session: neo4j.Session,
    tenancy_id: str,
    compartments: List[Dict[str, Any]],
    update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    """
    Ingest OCI compartments into Neo4j and link to tenancy via OWNER relationship.
    """
    query = """
    MERGE (t:OCITenancy{ocid: $TENANCY_ID})
    ON CREATE SET t.firstseen = timestamp()
    SET t.lastupdated = $update_tag
    WITH t
    MERGE (c:OCICompartment{ocid: $COMPARTMENT_ID})
    ON CREATE SET c.firstseen = timestamp(),
    c.createdate = $TIME_CREATED
    SET c.lastupdated = $update_tag,
    c.name = $COMPARTMENT_NAME,
    c.description = $DESCRIPTION,
    c.lifecycle_state = $LIFECYCLE_STATE,
    c.compartmentid = $PARENT_COMPARTMENT_ID
    WITH t, c
    MERGE (t)-[r:OWNER]->(c)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """
    for comp in compartments:
        neo4j_session.run(
            query,
            TENANCY_ID=tenancy_id,
            COMPARTMENT_ID=comp['compartmentId'],
            COMPARTMENT_NAME=comp['name'],
            DESCRIPTION=comp.get('description', ''),
            LIFECYCLE_STATE=comp.get('lifecycleState', ''),
            TIME_CREATED=comp.get('timeCreated', ''),
            PARENT_COMPARTMENT_ID=comp.get('parentCompartmentId', tenancy_id),
            update_tag=update_tag,
        )


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]) -> None:
    run_cleanup_job('oci_import_compartments_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    tenancy_id: str,
    compartments: List[Dict[str, Any]],
    update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    """
    Sync OCI compartments into Neo4j.
    Similar to Azure's subscription.sync.
    """
    tic = time.perf_counter()
    logger.info(f"Syncing OCI compartments for tenancy '{tenancy_id}'")
    load_oci_compartments(neo4j_session, tenancy_id, compartments, update_tag, common_job_parameters)

    for comp in compartments:
        common_job_parameters['OCI_COMPARTMENT_ID'] = comp['compartmentId']
        common_job_parameters['OCI_TENANCY_ID'] = tenancy_id

        cleanup(neo4j_session, common_job_parameters)

    del common_job_parameters['OCI_COMPARTMENT_ID']
    del common_job_parameters['OCI_TENANCY_ID']
    toc = time.perf_counter()
    logger.info(f"Time to process OCI compartments for tenancy '{tenancy_id}' ({len(compartments)} compartments): {toc - tic:0.4f} seconds")
