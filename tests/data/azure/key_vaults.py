MOCK_VAULTS = [
    {
        "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.KeyVault/vaults/my-test-key-vault",
        "name": "my-test-key-vault",
        "location": "eastus",
        "properties": {
            "tenant_id": "00-00-00-00",
            "sku": {
                "name": "standard",
            },
            "vault_uri": "https://my-test-key-vault.vault.azure.net/",
        },
    },
]

MOCK_SECRETS = [
    {
        "id": "https://my-test-key-vault.vault.azure.net/secrets/my-secret",
        "name": "my-secret",
        "enabled": True,
        "created_on": "2025-01-01T12:00:00.000Z",
        "updated_on": "2025-01-01T12:05:00.000Z",
    },
]

MOCK_KEYS = [
    {
        "id": "https://my-test-key-vault.vault.azure.net/keys/my-key",
        "name": "my-key",
        "key_type": "RSA",
        "enabled": True,
        "created_on": "2025-01-02T12:00:00.000Z",
        "updated_on": "2025-01-02T12:05:00.000Z",
    },
]

MOCK_CERTIFICATES = [
    {
        "id": "https://my-test-key-vault.vault.azure.net/certificates/my-cert",
        "name": "my-cert",
        "enabled": True,
        "created_on": "2025-01-03T12:00:00.000Z",
        "updated_on": "2025-01-03T12:05:00.000Z",
        "x5t": "THUMBPRINT_STRING",
    },
]
