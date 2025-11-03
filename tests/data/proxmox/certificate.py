"""
Mock data for Proxmox certificate tests.
"""

MOCK_CERTIFICATE_DATA = {
    "node1": [
        {
            "filename": "pveproxy-ssl.pem",
            "fingerprint": "AA:BB:CC:DD:EE:FF:00:11:22:33:44:55:66:77:88:99:AA:BB:CC:DD",
            "issuer": "CN=Proxmox Virtual Environment,OU=PVE Cluster Node,O=PVE",
            "subject": "CN=node1",
            "san": ["DNS:node1", "DNS:node1.example.com", "IP:10.0.0.1"],
            "notbefore": 1672531200,  # Jan 1, 2023
            "notafter": 1735689600,   # Jan 1, 2025
            "public-key-type": "RSA",
            "public-key-bits": 2048,
            "pem": "-----BEGIN CERTIFICATE-----\nMIIDXTCC...sample...==\n-----END CERTIFICATE-----",
        },
    ],
    "node2": [
        {
            "filename": "pveproxy-ssl.pem",
            "fingerprint": "11:22:33:44:55:66:77:88:99:AA:BB:CC:DD:EE:FF:00:11:22:33:44",
            "issuer": "CN=Proxmox Virtual Environment,OU=PVE Cluster Node,O=PVE",
            "subject": "CN=node2",
            "san": ["DNS:node2", "DNS:node2.example.com", "IP:10.0.0.2"],
            "notbefore": 1672531200,  # Jan 1, 2023
            "notafter": 1704067200,   # Jan 1, 2024 (expired)
            "public-key-type": "RSA",
            "public-key-bits": 2048,
            "pem": "-----BEGIN CERTIFICATE-----\nMIIDXTCC...sample...==\n-----END CERTIFICATE-----",
        },
    ],
}
