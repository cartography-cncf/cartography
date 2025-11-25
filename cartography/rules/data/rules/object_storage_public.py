from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule
from cartography.rules.spec.model import RuleReference

# AWS Facts
_aws_s3_public = Fact(
    id="aws_s3_public",
    name="AWS S3 Buckets with Public or Anonymous Access",
    description=(
        "Finds AWS S3 buckets that allow anonymous access through: the anonymous_access flag, anonymous_actions "
        "defined, or bucket policy statements with Allow effect where the principal is '*' or contains 'AllUsers'."
    ),
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
    name="Azure Storage Blob Containers with Public Access Enabled",
    description=(
        "Finds Azure Storage blob containers where the 'publicaccess' property is set to 'Container' (anonymous "
        "read access for containers and blobs) or 'Blob' (anonymous read access for blobs only), indicating the "
        "container allows public internet access without authentication."
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
    name="Publicly Accessible Object Storage Buckets and Containers",
    description=(
        "Detects object storage resources (buckets, containers) configured to allow anonymous public access from "
        "the internet. Public object storage exposure is one of the most common cloud misconfigurations and has been "
        "responsible for numerous high-profile data breaches involving exposed records, PII, credentials, intellectual "
        "property, and sensitive business data. Publicly accessible storage can result from misconfigured policies that "
        "grant access to wildcard principals, overly permissive ACLs, or container-level public access settings. Even "
        "when accidental, public storage exposure creates immediate data breach risk, compliance violations (GDPR, HIPAA, "
        "PCI-DSS), and potential for data tampering or ransomware injection. Attackers actively scan for exposed storage "
        "using automated tools, and exposed buckets are often indexed by search engines. Organizations should disable "
        "public access at the account level, implement policies that explicitly deny public access, use pre-signed URLs "
        "or CDN distributions for controlled content delivery, enable versioning and deletion protection for critical data, "
        "monitor for policy changes, and regularly audit storage permissions."
    ),
    output_model=ObjectStoragePublic,
    facts=(
        _aws_s3_public,
        _azure_storage_public_blob_access,
    ),
    tags=("infrastructure", "attack_surface", "data_exposure"),
    version="0.2.0",
    references=[
        RuleReference(
            text="AWS - S3 Security Best Practices",
            url="https://docs.aws.amazon.com/AmazonS3/latest/userguide/security-best-practices.html",
        ),
        RuleReference(
            text="Azure - Storage Blob Prevent Anonymous Read Access",
            url="https://learn.microsoft.com/en-us/azure/storage/blobs/anonymous-read-access-prevent?tabs=portal",
        ),
        RuleReference(
            text="Google Cloud - Preventing Public Access to Storage",
            url="https://docs.cloud.google.com/storage/docs/using-public-access-prevention",
        ),
    ],
)
