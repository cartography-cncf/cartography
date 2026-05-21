from cartography.rules.data.frameworks.iso27001 import iso27001_annex_a
from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule

_aws_public_s3_without_versioning = Fact(
    id="aws_public_s3_without_versioning",
    name="Public S3 buckets without versioning",
    description=(
        "S3 buckets with public access evidence and versioning not enabled. "
        "Public write, overwrite, or delete exposure is more damaging when "
        "object recovery controls are absent."
    ),
    cypher_query="""
    MATCH (bucket:S3Bucket)
    WHERE coalesce(bucket.versioning_status, '') <> 'Enabled'
      AND (
        bucket.anonymous_access = true
        OR (bucket.anonymous_actions IS NOT NULL AND size(bucket.anonymous_actions) > 0)
        OR EXISTS {
            MATCH (bucket)-[:POLICY_STATEMENT]->(stmt:S3PolicyStatement)
            WHERE stmt.effect = 'Allow'
              AND stmt.principal IN ['*', '"*"']
        }
      )
    OPTIONAL MATCH (account:AWSAccount)-[:RESOURCE]->(bucket)
    RETURN
        bucket.id AS id,
        bucket.name AS name,
        account.name AS account,
        account.id AS account_id,
        bucket.region AS region,
        'aws' AS provider,
        'versioning_disabled' AS recovery_gap,
        bucket.versioning_status AS recovery_status
    ORDER BY account, region, name
    """,
    cypher_visual_query="""
    MATCH (bucket:S3Bucket)
    WHERE coalesce(bucket.versioning_status, '') <> 'Enabled'
      AND (
        bucket.anonymous_access = true
        OR (bucket.anonymous_actions IS NOT NULL AND size(bucket.anonymous_actions) > 0)
        OR EXISTS {
            MATCH (bucket)-[:POLICY_STATEMENT]->(stmt:S3PolicyStatement)
            WHERE stmt.effect = 'Allow'
              AND stmt.principal IN ['*', '"*"']
        }
      )
    OPTIONAL MATCH p2=(account:AWSAccount)-[:RESOURCE]->(bucket)
    OPTIONAL MATCH p3=(bucket)-[:POLICY_STATEMENT]->(:S3PolicyStatement)
    RETURN *
    """,
    cypher_count_query="""
    MATCH (bucket:S3Bucket)
    RETURN COUNT(bucket) AS count
    """,
    asset_id_field="id",
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)

_gcp_public_bucket_without_versioning = Fact(
    id="gcp_public_bucket_without_versioning",
    name="Public GCS buckets without versioning",
    description=(
        "GCS buckets with unconditional public IAM bindings and object "
        "versioning disabled."
    ),
    cypher_query="""
    MATCH (bucket:GCPBucket)
    WHERE coalesce(bucket.iam_config_public_access_prevention, '') <> 'enforced'
      AND coalesce(bucket.versioning_enabled, false) = false
      AND EXISTS {
          MATCH (bucket)<-[:APPLIES_TO]-(binding:GCPPolicyBinding)
          WHERE binding.is_public = true
            AND coalesce(binding.has_condition, false) = false
      }
    OPTIONAL MATCH (project:GCPProject)-[:RESOURCE]->(bucket)
    RETURN
        bucket.id AS id,
        bucket.id AS name,
        project.id AS account,
        project.id AS account_id,
        bucket.location AS region,
        'gcp' AS provider,
        'versioning_disabled' AS recovery_gap,
        toString(bucket.versioning_enabled) AS recovery_status
    ORDER BY account, region, name
    """,
    cypher_visual_query="""
    MATCH p=(bucket:GCPBucket)<-[:APPLIES_TO]-(binding:GCPPolicyBinding)
    WHERE coalesce(bucket.iam_config_public_access_prevention, '') <> 'enforced'
      AND coalesce(bucket.versioning_enabled, false) = false
      AND binding.is_public = true
      AND coalesce(binding.has_condition, false) = false
    OPTIONAL MATCH p2=(project:GCPProject)-[:RESOURCE]->(bucket)
    RETURN *
    """,
    cypher_count_query="""
    MATCH (bucket:GCPBucket)
    RETURN COUNT(bucket) AS count
    """,
    asset_id_field="id",
    module=Module.GCP,
    maturity=Maturity.EXPERIMENTAL,
)

_azure_public_blob_without_retention = Fact(
    id="azure_public_blob_without_retention",
    name="Public Azure blob containers without retention controls",
    description=(
        "Azure blob containers with public blob/container access and no "
        "container-level retention, immutability policy, or legal hold signal."
    ),
    cypher_query="""
    MATCH (subscription:AzureSubscription)-[:RESOURCE]->(container:AzureStorageBlobContainer)
    WHERE container.public_access IN ['Container', 'Blob']
      AND coalesce(container.remaining_retention_days, 0) <= 0
      AND coalesce(container.has_immutability_policy, false) = false
      AND coalesce(container.has_legal_hold, false) = false
    OPTIONAL MATCH (account:AzureStorageAccount)-[:USES]->(:AzureStorageBlobService)-[:CONTAINS]->(container)
    RETURN
        container.id AS id,
        container.name AS name,
        subscription.id AS account,
        subscription.id AS account_id,
        account.location AS region,
        account.name AS storage_account,
        'azure' AS provider,
        'no_retention_or_immutability' AS recovery_gap,
        toString(container.remaining_retention_days) AS recovery_status
    ORDER BY account, region, name
    """,
    cypher_visual_query="""
    MATCH p=(subscription:AzureSubscription)-[:RESOURCE]->(container:AzureStorageBlobContainer)
    WHERE container.public_access IN ['Container', 'Blob']
      AND coalesce(container.remaining_retention_days, 0) <= 0
      AND coalesce(container.has_immutability_policy, false) = false
      AND coalesce(container.has_legal_hold, false) = false
    OPTIONAL MATCH p2=(account:AzureStorageAccount)-[:USES]->(:AzureStorageBlobService)-[:CONTAINS]->(container)
    RETURN *
    """,
    cypher_count_query="""
    MATCH (container:AzureStorageBlobContainer)
    RETURN COUNT(container) AS count
    """,
    asset_id_field="id",
    module=Module.AZURE,
    maturity=Maturity.EXPERIMENTAL,
)


class PublicObjectStorageWithoutRecovery(Finding):
    id: str | None = None
    name: str | None = None
    account: str | None = None
    account_id: str | None = None
    region: str | None = None
    storage_account: str | None = None
    provider: str | None = None
    recovery_gap: str | None = None
    recovery_status: str | None = None


public_object_storage_without_recovery = Rule(
    id="public_object_storage_without_recovery",
    name="Public Object Storage Without Recovery Controls",
    description=(
        "Public object storage locations that lack versioning, retention, "
        "immutability, or similar recovery controls available in the current "
        "graph. These findings combine exposure with tamper/recovery impact."
    ),
    output_model=PublicObjectStorageWithoutRecovery,
    facts=(
        _aws_public_s3_without_versioning,
        _azure_public_blob_without_retention,
        _gcp_public_bucket_without_versioning,
    ),
    tags=(
        "data",
        "storage",
        "attack_surface",
        "resilience",
        "stride:information_disclosure",
        "stride:tampering",
    ),
    version="0.1.0",
    frameworks=(
        iso27001_annex_a("8.3"),
        iso27001_annex_a("8.10"),
        iso27001_annex_a("8.13"),
    ),
)
