"""
Sync Proxmox SSL/TLS certificates.

Follows Cartography's Get → Transform → Load pattern.
"""

import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.models.proxmox.certificate import ProxmoxCertificateSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


# ============================================================================
# GET functions - retrieve data from Proxmox API
# ============================================================================


@timeit
def get_node_certificates(proxmox_client: Any, node_name: str) -> list[dict[str, Any]]:
    """
    Get SSL certificates for a specific node.

    :param proxmox_client: Proxmox API client
    :param node_name: Node name
    :return: List of certificate dicts
    :raises: Exception if API call fails
    """
    return proxmox_client.nodes(node_name).certificates.info.get()


# ============================================================================
# TRANSFORM functions - manipulate data for graph ingestion
# ============================================================================


def transform_certificate_data(
    certificates: list[dict[str, Any]],
    node_name: str,
    cluster_id: str,
) -> list[dict[str, Any]]:
    """
    Transform certificate data into standard format.

    Per Cartography guidelines:
    - Use data['field'] for required fields (will raise KeyError if missing)
    - Use data.get('field') for optional fields

    :param certificates: Raw certificate data from API
    :param node_name: Node name
    :param cluster_id: Parent cluster ID
    :return: List of transformed certificate dicts
    """
    transformed_certs = []

    for cert in certificates:
        # Create unique ID from node and filename
        filename = cert.get("filename", "unknown")
        cert_id = f"{node_name}:{filename}"

        # Parse SAN (Subject Alternative Names)
        san = []
        if cert.get("san"):
            # SAN is typically a list or comma-separated string
            if isinstance(cert["san"], list):
                san = cert["san"]
            elif isinstance(cert["san"], str):
                san = [s.strip() for s in cert["san"].split(",") if s.strip()]

        transformed_certs.append(
            {
                "id": cert_id,
                "cluster_id": cluster_id,
                "node_name": node_name,
                "filename": filename,
                "fingerprint": cert.get("fingerprint"),
                "issuer": cert.get("issuer"),
                "subject": cert.get("subject"),
                "san": san,
                "notbefore": cert.get("notbefore"),
                "notafter": cert.get("notafter"),
                "public_key_type": cert.get("public-key-type"),
                "public_key_bits": cert.get("public-key-bits"),
                "pem": cert.get("pem"),
            }
        )

    return transformed_certs


# ============================================================================
# LOAD functions - ingest data to Neo4j using modern data model
# ============================================================================


def load_certificates(
    neo4j_session: neo4j.Session,
    certificates: list[dict[str, Any]],
    cluster_id: str,
    update_tag: int,
) -> None:
    """
    Load certificate data into Neo4j using modern data model.

    :param neo4j_session: Neo4j session
    :param certificates: List of transformed certificate dicts
    :param cluster_id: Parent cluster ID
    :param update_tag: Sync timestamp
    """
    if not certificates:
        return

    load(
        neo4j_session,
        ProxmoxCertificateSchema(),
        certificates,
        lastupdated=update_tag,
        CLUSTER_ID=cluster_id,
    )


# ============================================================================
# SYNC function - orchestrates Get → Transform → Load
# ============================================================================


@timeit
def sync(
    neo4j_session: neo4j.Session,
    proxmox_client: Any,
    cluster_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync SSL/TLS certificates.

    Follows Cartography's Get → Transform → Load pattern.

    :param neo4j_session: Neo4j session
    :param proxmox_client: Proxmox API client
    :param cluster_id: Parent cluster ID
    :param update_tag: Sync timestamp
    :param common_job_parameters: Common parameters
    """
    logger.info("Syncing Proxmox SSL/TLS certificates")

    all_certificates = []

    # GET - certificates from each node
    nodes = proxmox_client.nodes.get()
    for node in nodes:
        node_name = node["node"]
        certs = get_node_certificates(proxmox_client, node_name)

        # TRANSFORM
        transformed_certs = transform_certificate_data(certs, node_name, cluster_id)
        all_certificates.extend(transformed_certs)

    # LOAD - ingest to Neo4j
    load_certificates(neo4j_session, all_certificates, cluster_id, update_tag)

    logger.info(f"Synced {len(all_certificates)} SSL/TLS certificates")
