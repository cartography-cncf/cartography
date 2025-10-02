from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Module

azure_storage_public_blob_access = Fact(
    id="azure_storage_public_blob_access",
    name="Azure Storage Accounts with Public Blob Containers",
    description=(
        "Azure Storage Accounts that have blob containers with public access. "
        "If a storage blob container has public_access set to 'Container' or 'Blob', "
        "it means that the container is publicly accessible."
    ),
    cypher_query="""
    MATCH (sa:AzureStorageAccount)-[:USES]->(bs:AzureStorageBlobService)-[:CONTAINS]->(bc:AzureStorageBlobContainer)
    WHERE bc.publicaccess IN ['Container', 'Blob']
    RETURN sa.name AS storage_account,
           sa.resourcegroup AS resource_group,
           sa.location AS location,
           bc.name AS container_name,
           bc.publicaccess AS public_access
    """,
    cypher_visual_query="""
    MATCH p=(sa:AzureStorageAccount)-[:USES]->(bs:AzureStorageBlobService)-[:CONTAINS]->(bc:AzureStorageBlobContainer)
    WHERE bc.publicaccess IN ['Container', 'Blob']
    RETURN *
    """,
    module=Module.AZURE,
)
