DATABRICKS_SECRET_SCOPES = [
    {
        "name": "ci-cd",
        "backend_type": "DATABRICKS",
    },
    {
        "name": "azure-kv-backed",
        "backend_type": "AZURE_KEYVAULT",
        "keyvault_metadata": {
            "resource_id": "/subscriptions/aaaa/resourceGroups/rg/providers/Microsoft.KeyVault/vaults/my-kv",
            "dns_name": "https://my-kv.vault.azure.net/",
        },
    },
]
