import logging
from typing import Any

import neo4j
from google.api_core.exceptions import PermissionDenied
from google.auth.exceptions import DefaultCredentialsError
from google.auth.exceptions import RefreshError
from googleapiclient.discovery import HttpError
from googleapiclient.discovery import Resource

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.gcp.kms_cryptokey import GCPCryptoKeySchema
from cartography.models.gcp.kms_keyring import GCPKeyRingSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_kms_locations(client: Resource, project_id: str) -> list[dict] | None:
    try:
        parent = f"projects/{project_id}"
        request = client.projects().locations().list(name=parent)

        locations = []
        while request is not None:
            response = request.execute()
            locations.extend(response.get("locations", []))
            request = (
                client.projects()
                .locations()
                .list_next(
                    previous_request=request,
                    previous_response=response,
                )
            )
        return locations
    except (PermissionDenied, DefaultCredentialsError, RefreshError):
        logger.warning(
            "Failed to get KMS locations for project due to permissions or auth error.",
            exc_info=True,
        )
        raise
    except HttpError:
        logger.warning(
            "Failed to get KMS locations for project due to a transient HTTP error.",
            exc_info=True,
        )
        return []


@timeit
def get_key_rings(
    client: Resource, project_id: str, locations: list[dict]
) -> list[dict]:
    rings = []
    for loc in locations:
        location_id = loc.get("locationId")
        if not location_id:
            continue

        try:
            parent = f"projects/{project_id}/locations/{location_id}"
            request = client.projects().locations().keyRings().list(parent=parent)

            while request is not None:
                response = request.execute()
                rings.extend(response.get("keyRings", []))
                request = (
                    client.projects()
                    .locations()
                    .keyRings()
                    .list_next(
                        previous_request=request,
                        previous_response=response,
                    )
                )
        except (PermissionDenied, DefaultCredentialsError, RefreshError):
            logger.warning(
                f"Failed to get Key Rings in location {location_id} due to permissions or auth error.",
                exc_info=True,
            )
            raise
        except HttpError:
            logger.warning(
                f"Failed to get Key Rings in location {location_id} due to a transient HTTP error.",
                exc_info=True,
            )
            continue
    return rings


@timeit
def get_crypto_keys(client: Resource, keyring_name: str) -> list[dict]:
    try:
        request = (
            client.projects()
            .locations()
            .keyRings()
            .cryptoKeys()
            .list(parent=keyring_name)
        )

        keys = []
        while request is not None:
            response = request.execute()
            keys.extend(response.get("cryptoKeys", []))
            request = (
                client.projects()
                .locations()
                .keyRings()
                .cryptoKeys()
                .list_next(
                    previous_request=request,
                    previous_response=response,
                )
            )
        return keys
    except (PermissionDenied, DefaultCredentialsError, RefreshError):
        logger.warning(
            "Failed to get Crypto Keys for keyring due to permissions or auth error.",
            exc_info=True,
        )
        raise
    except HttpError:
        logger.warning(
            "Failed to get Crypto Keys for keyring due to a transient HTTP error.",
            exc_info=True,
        )
        return []


def transform_key_rings(key_rings: list[dict], project_id: str) -> list[dict]:
    transformed = []
    for ring in key_rings:
        ring_id = ring.get("name")
        if not ring_id:
            logger.warning("Skipping key ring with missing 'name' field.")
            continue

        location = ring_id.split("/")[3]
        transformed.append(
            {
                "id": ring_id,
                "name": ring_id.split("/")[-1],
                "location": location,
                "project_id": project_id,
            }
        )
    return transformed


def transform_crypto_keys(crypto_keys: list[dict], keyring_id: str) -> list[dict]:
    transformed = []
    for key in crypto_keys:
        key_id = key.get("name")
        if not key_id:
            logger.warning("Skipping crypto key with missing 'name' field.")
            continue

        transformed.append(
            {
                "id": key_id,
                "name": key_id.split("/")[-1],
                "rotation_period": key.get("rotationPeriod"),
                "purpose": key.get("purpose"),
                "state": key.get("primary", {}).get("state"),
                "key_ring_id": keyring_id,
                "project_id": keyring_id.split("/")[1],
            }
        )
    return transformed


@timeit
def load_key_rings(
    neo4j_session: neo4j.Session,
    data: list[dict],
    project_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        GCPKeyRingSchema(),
        data,
        lastupdated=update_tag,
        PROJECT_ID=project_id,
    )


@timeit
def load_crypto_keys(
    neo4j_session: neo4j.Session,
    data: list[dict],
    project_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        GCPCryptoKeySchema(),
        data,
        lastupdated=update_tag,
        PROJECT_ID=project_id,
    )


@timeit
def cleanup_kms(neo4j_session: neo4j.Session, common_job_parameters: dict) -> None:
    GraphJob.from_node_schema(GCPCryptoKeySchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(GCPKeyRingSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    kms_client: Resource,
    project_id: str,
    gcp_update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    logger.info(f"Syncing GCP KMS for project {project_id}.")

    locations = get_kms_locations(kms_client, project_id)
    if locations is None:
        logger.warning(
            f"KMS sync for project {project_id} failed to get locations. Skipping cleanup."
        )
        return
    if not locations:
        logger.info(f"No KMS locations found for project {project_id}.")

    key_rings_raw = get_key_rings(kms_client, project_id, locations)
    if not key_rings_raw:
        logger.info(f"No KMS KeyRings found for project {project_id}.")
    else:
        key_rings = transform_key_rings(key_rings_raw, project_id)
        load_key_rings(neo4j_session, key_rings, project_id, gcp_update_tag)

        for ring in key_rings_raw:
            keyring_id = ring["name"]
            crypto_keys_raw = get_crypto_keys(kms_client, keyring_id)
            if crypto_keys_raw:
                crypto_keys = transform_crypto_keys(crypto_keys_raw, keyring_id)
                load_crypto_keys(neo4j_session, crypto_keys, project_id, gcp_update_tag)

    if locations is not None:
        cleanup_job_params = common_job_parameters.copy()
        cleanup_job_params["PROJECT_ID"] = project_id
        cleanup_kms(neo4j_session, cleanup_job_params)
