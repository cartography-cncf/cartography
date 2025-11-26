from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule

# AWS Facts
_aws_s3_public = Fact(
    id="aws_s3_public",
    name="Internet-Accessible S3 Storage Attack Surface",
    description=("AWS S3 buckets accessible from the internet"),
    cypher_query="""
    MATCH (b:S3Bucket)
    WHERE b.anonymous_access = true
    OR (b.anonymous_actions IS NOT NULL AND size(b.anonymous_actions) > 0)
    OR EXISTS {
        MATCH (b)-[:POLICY_STATEMENT]->(stmt:S3PolicyStatement)
        WHERE stmt.effect = 'Allow'
        AND (stmt.principal = '*' OR stmt.principal CONTAINS 'AllUsers')
    }
    RETURN
        b.id as id,
        b.name AS name,
        b.region AS region,
        b.anonymous_access AS public_access,
        b.anonymous_actions AS public_actions
    """,
    cypher_visual_query="""
    MATCH (b:S3Bucket)
    WHERE b.anonymous_access = true
    OR (b.anonymous_actions IS NOT NULL AND size(b.anonymous_actions) > 0)
    OR EXISTS {
        MATCH (b)-[:POLICY_STATEMENT]->(stmt:S3PolicyStatement)
        WHERE stmt.effect = 'Allow'
        AND (stmt.principal = '*' OR stmt.principal CONTAINS 'AllUsers')
    }
    WITH b
    OPTIONAL MATCH p=(b)-[:POLICY_STATEMENT]->(:S3PolicyStatement)
    RETURN *
    """,
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)

# Azure Facts
_azure_storage_public_blob_access = Fact(
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
    RETURN
        sa.id AS account_id,
        sa.name AS account,
        sa.resourcegroup AS resource_group,
        sa.location AS region,
        bc.id as id,
        bc.name AS name,
        bc.publicaccess AS public_access_element,
        bc.publicaccess IN ['Container', 'Blob'] AS public_access
    """,
    cypher_visual_query="""
    MATCH p=(sa:AzureStorageAccount)-[:USES]->(bs:AzureStorageBlobService)-[:CONTAINS]->(bc:AzureStorageBlobContainer)
    WHERE bc.publicaccess IN ['Container', 'Blob']
    RETURN *
    """,
    module=Module.AZURE,
    maturity=Maturity.EXPERIMENTAL,
)


# Rule
class ObjectStoragePublic(Finding):
    name: str | None = None
    id: str | None = None
    account: str | None = None
    account_id: str | None = None
    region: str | None = None
    public_access: bool | None = None


object_storage_public = Rule(
    id="object_storage_public",
    name="Public Object Storage Attack Surface",
    description=(
        "Publicly accessible object storage services such as AWS S3 buckets and Azure Storage Blob Containers"
    ),
    output_model=ObjectStoragePublic,
    facts=(
        _aws_s3_public,
        _azure_storage_public_blob_access,
    ),
    tags=("infrastructure", "attack_surface"),
    version="0.1.0",
)
