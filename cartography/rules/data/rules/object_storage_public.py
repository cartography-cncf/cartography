from cartography.rules.data.frameworks.iso27001 import iso27001_annex_a
from cartography.rules.data.frameworks.soc2 import soc2_tsc
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
    MATCH (b:AWSS3Bucket)
    WHERE b.anonymous_access = true
    OR (b.anonymous_actions IS NOT NULL AND size(b.anonymous_actions) > 0)
    OR EXISTS {
        MATCH (b)-[:POLICY_STATEMENT]->(stmt:AWSS3PolicyStatement)
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
    MATCH (b:AWSS3Bucket)
    WHERE b.anonymous_access = true
    OR (b.anonymous_actions IS NOT NULL AND size(b.anonymous_actions) > 0)
    OR EXISTS {
        MATCH (b)-[:POLICY_STATEMENT]->(stmt:AWSS3PolicyStatement)
        WHERE stmt.effect = 'Allow'
        AND (stmt.principal = '*' OR stmt.principal CONTAINS 'AllUsers')
    }
    WITH b
    OPTIONAL MATCH p=(b)-[:POLICY_STATEMENT]->(:AWSS3PolicyStatement)
    RETURN *
    """,
    cypher_count_query="""
    MATCH (b:AWSS3Bucket)
    RETURN COUNT(b) AS count
    """,
    asset_id_field="id",
    asset_label="AWSS3Bucket",
    identity_fields=("id",),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)

# GCP Facts
_gcp_bucket_public = Fact(
    id="gcp_bucket_public",
    name="Internet-Accessible GCS Bucket Attack Surface",
    description=(
        "GCS buckets that grant unconditional access to allUsers or "
        "allAuthenticatedUsers via an IAM binding without enforced "
        "publicAccessPrevention. Bindings with an IAM Condition (time-bound, "
        "request-attribute-bound, etc.) are excluded; the binding's "
        "is_public / has_condition properties remain available for finer-"
        "grained queries."
    ),
    cypher_query="""
    MATCH (b:GCPBucket)
    WHERE coalesce(b.iam_config_public_access_prevention, '') <> 'enforced'
      AND EXISTS {
          MATCH (b)<-[:APPLIES_TO]-(binding:GCPPolicyBinding)
          WHERE binding.is_public = true
            AND coalesce(binding.has_condition, false) = false
      }
    RETURN
        b.id AS id,
        b.id AS name,
        b.location AS region,
        true AS public_access
    """,
    cypher_visual_query="""
    MATCH p=(b:GCPBucket)<-[:APPLIES_TO]-(binding:GCPPolicyBinding)
    WHERE coalesce(b.iam_config_public_access_prevention, '') <> 'enforced'
      AND binding.is_public = true
      AND coalesce(binding.has_condition, false) = false
    RETURN *
    """,
    cypher_count_query="""
    MATCH (b:GCPBucket)
    RETURN COUNT(b) AS count
    """,
    asset_id_field="id",
    asset_label="GCPBucket",
    identity_fields=("id",),
    module=Module.GCP,
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
    cypher_count_query="""
    MATCH (bc:AzureStorageBlobContainer)
    RETURN COUNT(bc) AS count
    """,
    asset_id_field="id",
    asset_label="AzureStorageBlobContainer",
    identity_fields=("id",),
    module=Module.AZURE,
    maturity=Maturity.EXPERIMENTAL,
)


# Scaleway Facts
_scaleway_bucket_public = Fact(
    id="scaleway_bucket_public",
    name="Internet-Accessible Scaleway Object Storage Attack Surface",
    description=(
        "Scaleway Object Storage buckets accessible from the internet, either "
        "through a bucket policy granting anonymous access or an ACL granting "
        "AllUsers / AuthenticatedUsers."
    ),
    cypher_query="""
    MATCH (b:ScalewayObjectStorageBucket)
    WHERE b.public = true
    RETURN
        b.id AS id,
        b.name AS name,
        b.region AS region,
        b.public AS public_access,
        b.anonymous_actions AS public_actions
    """,
    cypher_visual_query="""
    MATCH p=(b:ScalewayObjectStorageBucket)<-[:RESOURCE]-(prj:ScalewayProject)
    WHERE b.public = true
    RETURN *
    """,
    cypher_count_query="""
    MATCH (b:ScalewayObjectStorageBucket)
    RETURN COUNT(b) AS count
    """,
    asset_id_field="id",
    asset_label="ScalewayObjectStorageBucket",
    identity_fields=("id",),
    module=Module.SCALEWAY,
    maturity=Maturity.EXPERIMENTAL,
)


# Cloudflare Facts
_cloudflare_r2_bucket_public = Fact(
    id="cloudflare_r2_bucket_public",
    name="Internet-Accessible Cloudflare R2 Attack Surface",
    description=(
        "Cloudflare R2 buckets readable by anonymous callers, either through a "
        "custom public domain or through the r2.dev development URL. r2.dev is "
        "meant for testing and serves the bucket with no access control at all."
    ),
    cypher_query="""
    MATCH (b:CloudflareR2Bucket)
    WHERE b.public = true OR b.r2_dev_enabled = true
    RETURN
        b.id AS id,
        b.name AS name,
        b.location AS region,
        coalesce(b.public, false) OR coalesce(b.r2_dev_enabled, false) AS public_access
    """,
    cypher_visual_query="""
    MATCH p=(b:CloudflareR2Bucket)<-[:RESOURCE]-(acc:CloudflareAccount)
    WHERE b.public = true OR b.r2_dev_enabled = true
    RETURN *
    """,
    cypher_count_query="""
    MATCH (b:CloudflareR2Bucket)
    RETURN COUNT(b) AS count
    """,
    asset_id_field="id",
    asset_label="CloudflareR2Bucket",
    identity_fields=("id",),
    module=Module.CLOUDFLARE,
    maturity=Maturity.EXPERIMENTAL,
)


# Supabase Facts
_supabase_storage_bucket_public = Fact(
    id="supabase_storage_bucket_public",
    name="Internet-Accessible Supabase Storage Attack Surface",
    description=(
        "Supabase Storage buckets marked public. A public bucket serves its "
        "objects over the project's storage URL without any Authorization "
        "header, so row level security no longer gates reads."
    ),
    cypher_query="""
    MATCH (b:SupabaseStorageBucket)
    WHERE b.public = true
    RETURN
        b.id AS id,
        b.name AS name,
        b.public AS public_access
    """,
    cypher_visual_query="""
    MATCH p=(b:SupabaseStorageBucket)<-[:RESOURCE]-(prj:SupabaseProject)
    WHERE b.public = true
    RETURN *
    """,
    cypher_count_query="""
    MATCH (b:SupabaseStorageBucket)
    RETURN COUNT(b) AS count
    """,
    asset_id_field="id",
    asset_label="SupabaseStorageBucket",
    identity_fields=("id",),
    module=Module.SUPABASE,
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
        "Publicly accessible object storage services such as AWS S3 buckets, "
        "Azure Storage Blob Containers, GCS buckets, Scaleway Object Storage "
        "buckets, Cloudflare R2 buckets, and Supabase Storage buckets"
    ),
    output_model=ObjectStoragePublic,
    facts=(
        _aws_s3_public,
        _azure_storage_public_blob_access,
        _gcp_bucket_public,
        _scaleway_bucket_public,
        _cloudflare_r2_bucket_public,
        _supabase_storage_bucket_public,
    ),
    tags=(
        "infrastructure",
        "attack_surface",
        "stride:information_disclosure",
    ),
    version="0.1.0",
    frameworks=(
        iso27001_annex_a("8.3"),
        soc2_tsc("CC6.1"),
        soc2_tsc("CC6.6"),
    ),
)


# =============================================================================
# TODO: SOC 2 CC6.7: Partial information-movement coverage
# Covered today: transport encryption gaps and unauthorized external sharing, via
# aws_expired_ssl_tls_certificates, gcp_cloudsql_ssl_not_enforced,
# databricks_public_delta_sharing_recipient and public_snapshots.
# Missing datamodel: DLP policy state, approved transfer channels,
# removable-media controls, and the authorization context that would say whether
# a given transfer is sanctioned.
# Out of reach: data export and egress events. Cartography ingests configuration,
# not event streams.
# =============================================================================

# =============================================================================
# TODO: SOC 2 C1.1: Confidential information identification and protection
# Missing datamodel or evidence: provider-neutral data classification and
# sensitivity labels linked to databases, datasets, object storage, file
# storage, and the access or encryption controls protecting those assets.
# =============================================================================

# =============================================================================
# TODO: SOC 2 C1.2: Confidential information disposal
# Missing datamodel or evidence: retention and deletion policies, lifecycle-rule
# execution status, deletion or cryptographic-erasure evidence, and linkage to
# assets classified as confidential.
# =============================================================================
