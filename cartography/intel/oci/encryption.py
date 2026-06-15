# Copyright (c) 2020, Oracle and/or its affiliates.
# OCI Key Management Service (KMS) API-centric functions
# https://docs.oracle.com/en-us/iaas/Content/KeyManagement/Concepts/keyoverview.htm
import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j
import oci
import oci.key_management

from . import utils
from cartography.util import run_cleanup_job

logger = logging.getLogger(__name__)


# ============================================================
# KMS Vaults
# ============================================================

def get_vault_list_data(
    kms_vault: oci.key_management.KmsVaultClient,
    compartment_id: str,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Get all KMS vaults in a compartment.
    """
    try:
        response = oci.pagination.list_call_get_all_results(
            kms_vault.list_vaults, compartment_id=compartment_id,
        )
        return {'Vaults': utils.oci_object_to_json(response.data)}
    except oci.exceptions.ServiceError as e:
        logger.warning(
            "Could not retrieve KMS vaults for compartment '%s': %s",
            compartment_id, e.message,
        )
        return {'Vaults': []}


def load_vaults(
    neo4j_session: neo4j.Session,
    vaults: List[Dict[str, Any]],
    tenancy_id: str,
    compartment_id: str,
    region: str,
    oci_update_tag: int,
) -> None:
    """
    Ingest OCI KMS Vault data into Neo4j.
    """
    ingest_vault = """
    MERGE (v:OCIKmsVault{ocid: $OCID})
    ON CREATE SET v.firstseen = timestamp(),
    v.createdate = $TIME_CREATED
    SET v.display_name = $DISPLAY_NAME,
    v.compartment_id = $COMPARTMENT_ID,
    v.resource_type = 'oci-kms-vault',
    v.vault_type = $VAULT_TYPE,
    v.lifecycle_state = $LIFECYCLE_STATE,
    v.crypto_endpoint = $CRYPTO_ENDPOINT,
    v.management_endpoint = $MANAGEMENT_ENDPOINT,
    v.region = $REGION,
    v.lastupdated = $oci_update_tag
    WITH v
    MATCH (cc:OCICompartment{ocid: $COMPARTMENT_ID})
    MERGE (cc)-[r:RESOURCE]->(v)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $oci_update_tag
    """

    for vault in vaults:
        neo4j_session.run(
            ingest_vault,
            OCID=vault.get("id"),
            DISPLAY_NAME=vault.get("display-name"),
            COMPARTMENT_ID=vault.get("compartment-id", compartment_id),
            VAULT_TYPE=vault.get("vault-type", ""),
            LIFECYCLE_STATE=vault.get("lifecycle-state"),
            CRYPTO_ENDPOINT=vault.get("crypto-endpoint", ""),
            MANAGEMENT_ENDPOINT=vault.get("management-endpoint", ""),
            REGION=region,
            TIME_CREATED=str(vault.get("time-created", "")),
            oci_update_tag=oci_update_tag,
        )


def sync_vaults(
    neo4j_session: neo4j.Session,
    kms_vault: oci.key_management.KmsVaultClient,
    compartments: List[Dict[str, Any]],
    tenancy_id: str,
    region: str,
    oci_update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    """
    Sync all KMS vaults across compartments.
    """
    logger.debug("Syncing OCI KMS vaults for tenancy '%s', region '%s'.", tenancy_id, region)
    for compartment in compartments:
        data = get_vault_list_data(kms_vault, compartment["ocid"])
        if data["Vaults"]:
            load_vaults(
                neo4j_session, data["Vaults"], tenancy_id,
                compartment["ocid"], region, oci_update_tag,
            )


# ============================================================
# KMS Keys
# ============================================================

def get_key_list_data(
    management_endpoint: str,
    credentials: Dict[str, Any],
    compartment_id: str,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Get all keys managed by a vault (via its management endpoint).
    Each vault exposes its own management endpoint for key operations.
    """
    try:
        kms_management = oci.key_management.KmsManagementClient(
            credentials, service_endpoint=management_endpoint,
        )
        response = oci.pagination.list_call_get_all_results(
            kms_management.list_keys, compartment_id=compartment_id,
        )
        return {'Keys': utils.oci_object_to_json(response.data)}
    except oci.exceptions.ServiceError as e:
        logger.warning(
            "Could not retrieve KMS keys from endpoint '%s': %s",
            management_endpoint, e.message,
        )
        return {'Keys': []}


def get_key_details(
    management_endpoint: str,
    credentials: Dict[str, Any],
    key_id: str,
) -> Dict[str, Any]:
    """
    Get full details of a single key (includes key versions, rotation info).
    """
    try:
        kms_management = oci.key_management.KmsManagementClient(
            credentials, service_endpoint=management_endpoint,
        )
        response = kms_management.get_key(key_id=key_id)
        return utils.oci_single_object_to_json(response.data)
    except oci.exceptions.ServiceError as e:
        logger.warning(
            "Could not retrieve KMS key '%s': %s", key_id, e.message,
        )
        return {}


def load_keys(
    neo4j_session: neo4j.Session,
    keys: List[Dict[str, Any]],
    vault_id: str,
    tenancy_id: str,
    compartment_id: str,
    region: str,
    oci_update_tag: int,
) -> None:
    """
    Ingest OCI KMS Key data into Neo4j and link to vault.
    """
    ingest_key = """
    MERGE (k:OCIKmsKey{ocid: $OCID})
    ON CREATE SET k.firstseen = timestamp(),
    k.createdate = $TIME_CREATED
    SET k.display_name = $DISPLAY_NAME,
    k.compartment_id = $COMPARTMENT_ID,
    k.resource_type = 'oci-kms-key',
    k.vault_id = $VAULT_ID,
    k.algorithm = $ALGORITHM,
    k.protection_mode = $PROTECTION_MODE,
    k.lifecycle_state = $LIFECYCLE_STATE,
    k.current_key_version = $CURRENT_KEY_VERSION,
    k.region = $REGION,
    k.lastupdated = $oci_update_tag
    WITH k
    MATCH (v:OCIKmsVault{ocid: $VAULT_ID})
    MERGE (v)-[r:OCI_KMS_KEY]->(k)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $oci_update_tag
    """

    for key in keys:
        neo4j_session.run(
            ingest_key,
            OCID=key.get("id"),
            DISPLAY_NAME=key.get("display-name"),
            COMPARTMENT_ID=key.get("compartment-id", compartment_id),
            VAULT_ID=vault_id,
            ALGORITHM=key.get("algorithm", ""),
            PROTECTION_MODE=key.get("protection-mode", ""),
            LIFECYCLE_STATE=key.get("lifecycle-state"),
            CURRENT_KEY_VERSION=key.get("current-key-version", ""),
            REGION=region,
            TIME_CREATED=str(key.get("time-created", "")),
            oci_update_tag=oci_update_tag,
        )


def sync_keys(
    neo4j_session: neo4j.Session,
    kms_vault: oci.key_management.KmsVaultClient,
    compartments: List[Dict[str, Any]],
    tenancy_id: str,
    region: str,
    oci_update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    """
    Sync all KMS keys by iterating vaults already in Neo4j and fetching keys
    from each vault's management endpoint.
    """
    logger.debug("Syncing OCI KMS keys for tenancy '%s', region '%s'.", tenancy_id, region)
    credentials = kms_vault.base_client.config

    for compartment in compartments:
        query = (
            "MATCH (:OCICompartment{ocid: $COMPARTMENT_ID})"
            "-[:RESOURCE]->(v:OCIKmsVault) "
            "WHERE v.region = $REGION AND v.lifecycle_state = 'ACTIVE' "
            "RETURN v.ocid as ocid, v.management_endpoint as endpoint"
        )
        vaults = neo4j_session.run(
            query, COMPARTMENT_ID=compartment["ocid"], REGION=region,
        )
        for vault in vaults:
            endpoint = vault["endpoint"]
            if not endpoint:
                continue
            data = get_key_list_data(endpoint, credentials, compartment["ocid"])
            if data["Keys"]:
                load_keys(
                    neo4j_session, data["Keys"], vault["ocid"],
                    tenancy_id, compartment["ocid"], region, oci_update_tag,
                )


# ============================================================
# Top-level sync function
# ============================================================

def sync(
    neo4j_session: neo4j.Session,
    encryption: oci.key_management.KmsVaultClient,
    tenancy_id: str,
    oci_update_tag: int,
    common_job_parameters: Dict[str, Any],
    regions: List[str] = None,
) -> None:
    """
    Sync OCI Encryption (KMS) resources: Vaults and Keys.
    """
    compartment_ocid = common_job_parameters.get("OCI_COMPARTMENT_ID", tenancy_id)
    logger.info("Syncing OCI Encryption for compartment '%s'.", compartment_ocid)

    compartments = [
        {"ocid": compartment_ocid, "name": "target", "compartmentid": tenancy_id},
    ]

    if not regions:
        regions = [encryption.base_client.region or ""]

    for region in regions:
        logger.info(
            "Syncing OCI Encryption in region '%s' for compartment '%s'.",
            region, compartment_ocid,
        )
        encryption.base_client.set_region(region)

        # Sync vaults first
        sync_vaults(
            neo4j_session, encryption, compartments, tenancy_id,
            region, oci_update_tag, common_job_parameters,
        )

        # Sync keys (depends on vaults being in Neo4j)
        sync_keys(
            neo4j_session, encryption, compartments, tenancy_id,
            region, oci_update_tag, common_job_parameters,
        )

    # Cleanup stale encryption nodes
    run_cleanup_job(
        'oci_import_encryption_cleanup.json', neo4j_session, common_job_parameters,
    )
