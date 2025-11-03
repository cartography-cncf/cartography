"""
Tests for Proxmox certificate module.
"""
import pytest

from cartography.intel.proxmox.certificate import transform_certificate_data


def test_transform_certificate_data():
    """Test certificate data transformation."""
    raw_certs = [
        {
            'filename': 'pveproxy-ssl.pem',
            'fingerprint': 'AA:BB:CC:DD:EE:FF',
            'issuer': 'CN=Proxmox Virtual Environment',
            'subject': 'CN=node1',
            'san': ['DNS:node1', 'DNS:node1.example.com', 'IP:10.0.0.1'],
            'notbefore': 1672531200,
            'notafter': 1735689600,
            'public-key-type': 'RSA',
            'public-key-bits': 2048,
            'pem': '-----BEGIN CERTIFICATE-----\nMIID...\n-----END CERTIFICATE-----',
        },
        {
            'filename': 'custom-cert.pem',
            'fingerprint': '11:22:33:44:55:66',
            'issuer': 'CN=Example CA',
            'subject': 'CN=node1',
            'san': 'DNS:node1.example.com,IP:10.0.0.1',  # Test string format
            'notbefore': 1672531200,
            'notafter': 1735689600,
        },
    ]

    node_name = 'node1'
    cluster_id = 'test-cluster'
    
    result = transform_certificate_data(raw_certs, node_name, cluster_id)
    
    assert len(result) == 2
    
    # Test first certificate
    cert1 = result[0]
    assert cert1['id'] == 'node1:pveproxy-ssl.pem'
    assert cert1['node_name'] == 'node1'
    assert cert1['cluster_id'] == cluster_id
    assert cert1['filename'] == 'pveproxy-ssl.pem'
    assert cert1['fingerprint'] == 'AA:BB:CC:DD:EE:FF'
    assert cert1['issuer'] == 'CN=Proxmox Virtual Environment'
    assert cert1['subject'] == 'CN=node1'
    assert cert1['san'] == ['DNS:node1', 'DNS:node1.example.com', 'IP:10.0.0.1']
    assert cert1['notbefore'] == 1672531200
    assert cert1['notafter'] == 1735689600
    assert cert1['public_key_type'] == 'RSA'
    assert cert1['public_key_bits'] == 2048
    assert '-----BEGIN CERTIFICATE-----' in cert1['pem']
    
    # Test second certificate with string SAN
    cert2 = result[1]
    assert cert2['id'] == 'node1:custom-cert.pem'
    assert cert2['san'] == ['DNS:node1.example.com', 'IP:10.0.0.1']
    assert cert2['public_key_type'] is None
    assert cert2['public_key_bits'] is None


def test_transform_certificate_data_missing_fields():
    """Test certificate data transformation with missing optional fields."""
    raw_certs = [
        {
            # Only required fields
        },
    ]

    node_name = 'node1'
    cluster_id = 'test-cluster'
    
    result = transform_certificate_data(raw_certs, node_name, cluster_id)
    
    assert len(result) == 1
    
    cert = result[0]
    assert cert['id'] == 'node1:unknown'
    assert cert['filename'] == 'unknown'
    assert cert['fingerprint'] is None
    assert cert['issuer'] is None
    assert cert['subject'] is None
    assert cert['san'] == []
    assert cert['notbefore'] is None
    assert cert['notafter'] is None
