"""
Integration tests for Proxmox certificate sync.
"""

from typing import Any
from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.proxmox.certificate
from tests.data.proxmox.certificate import MOCK_CERTIFICATE_DATA
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_CLUSTER_ID = "test-cluster"


@patch.object(cartography.intel.proxmox.certificate, "get_node_certificates")
def test_sync_certificates(mock_get_node_certs, neo4j_session):
    """
    Test that SSL/TLS certificates sync correctly.
    """

    # Arrange
    def get_certs_side_effect(proxmox_client, node_name):
        return MOCK_CERTIFICATE_DATA.get(node_name, [])

    mock_get_node_certs.side_effect = get_certs_side_effect

    common_job_parameters: dict[str, Any] = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "CLUSTER_ID": TEST_CLUSTER_ID,
    }

    # Create cluster first
    neo4j_session.run(
        """
        MERGE (c:ProxmoxCluster {id: $cluster_id})
        SET c.name = $cluster_id,
            c.lastupdated = $update_tag
        """,
        cluster_id=TEST_CLUSTER_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    # Create nodes for relationship tests
    neo4j_session.run(
        """
        MERGE (n1:ProxmoxNode {id: 'node1'})
        SET n1.name = 'node1', n1.lastupdated = $update_tag
        MERGE (n2:ProxmoxNode {id: 'node2'})
        SET n2.name = 'node2', n2.lastupdated = $update_tag
        """,
        update_tag=TEST_UPDATE_TAG,
    )

    # Mock proxmox_client.nodes.get()
    mock_proxmox_client = Mock()
    mock_proxmox_client.nodes.get.return_value = [
        {"node": "node1"},
        {"node": "node2"},
    ]

    # Act
    cartography.intel.proxmox.certificate.sync(
        neo4j_session,
        mock_proxmox_client,
        TEST_CLUSTER_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert - Certificates exist
    expected_certs = {
        ("node1:pveproxy-ssl.pem", "node1"),
        ("node2:pveproxy-ssl.pem", "node2"),
    }
    assert (
        check_nodes(neo4j_session, "ProxmoxCertificate", ["id", "node_name"])
        == expected_certs
    )

    # Assert - Certificate to cluster relationships
    expected_cert_cluster_rels = {
        ("node1:pveproxy-ssl.pem", TEST_CLUSTER_ID),
        ("node2:pveproxy-ssl.pem", TEST_CLUSTER_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "ProxmoxCertificate",
            "id",
            "ProxmoxCluster",
            "id",
            "RESOURCE",
            rel_direction_right=True,
        )
        == expected_cert_cluster_rels
    )

    # Assert - Node to certificate relationships
    expected_node_cert_rels = {
        ("node1", "node1:pveproxy-ssl.pem"),
        ("node2", "node2:pveproxy-ssl.pem"),
    }
    assert (
        check_rels(
            neo4j_session,
            "ProxmoxNode",
            "id",
            "ProxmoxCertificate",
            "id",
            "HAS_CERTIFICATE",
            rel_direction_right=True,
        )
        == expected_node_cert_rels
    )

    # Assert - Certificate properties for node1
    result = neo4j_session.run(
        """
        MATCH (cert:ProxmoxCertificate {node_name: 'node1'})
        RETURN cert.fingerprint as fingerprint,
               cert.subject as subject,
               cert.issuer as issuer,
               cert.notbefore as notbefore,
               cert.notafter as notafter,
               cert.public_key_type as key_type,
               cert.public_key_bits as key_bits,
               cert.san as san
        """
    )
    cert_props = result.single()
    assert (
        cert_props["fingerprint"]
        == "AA:BB:CC:DD:EE:FF:00:11:22:33:44:55:66:77:88:99:AA:BB:CC:DD"
    )
    assert cert_props["subject"] == "CN=node1"
    assert (
        cert_props["issuer"]
        == "CN=Proxmox Virtual Environment,OU=PVE Cluster Node,O=PVE"
    )
    assert cert_props["notbefore"] == 1672531200
    assert cert_props["notafter"] == 1735689600
    assert cert_props["key_type"] == "RSA"
    assert cert_props["key_bits"] == 2048
    assert set(cert_props["san"]) == {
        "DNS:node1",
        "DNS:node1.example.com",
        "IP:10.0.0.1",
    }

    # Assert - Certificate expiration (node2 is expired)
    result = neo4j_session.run(
        """
        MATCH (cert:ProxmoxCertificate {node_name: 'node2'})
        RETURN cert.notafter as notafter
        """
    )
    node2_cert = result.single()
    assert node2_cert["notafter"] == 1704067200  # Jan 1, 2024
