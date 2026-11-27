"""
AWS S3 bucket default encryption

Two checks: whether default encryption is configured at all, and whether it
uses a KMS key rather than SSE-S3. A bucket with no default encryption fails
both, since ``encryption_algorithm`` is only populated when encryption is on.

Every property and relationship used here is already synced by the AWS
intel module; no collector change is required. All rules are
EXPERIMENTAL until validated against a live graph.
"""

from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule


class AwsS3BucketDefaultEncryptionOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    bucket_id: str | None = None
    bucket_name: str | None = None
    object_ownership: str | None = None
    default_encryption: str | None = None
    encryption_algorithm: str | None = None
    encryption_key_id: str | None = None
    versioning_status: str | None = None
    logging_enabled: str | None = None
    logging_target_bucket: str | None = None


_aws_s3_bucket_default_encryption_fact = Fact(
    id="aws_s3_bucket_default_encryption_fact",
    name="S3 default encryption missing",
    description="Buckets with default_encryption=null/false.",
    cypher_query="""

        MATCH (a:AWSAccount)-[:RESOURCE]->(b:AWSS3Bucket)
        WHERE b.default_encryption IS NULL OR b.default_encryption = false
        RETURN a.id AS account_id, a.name AS account, b.id AS bucket_id,
               b.name AS bucket_name, b.default_encryption AS default_encryption

    """,
    cypher_visual_query="""

        MATCH (a:AWSAccount)-[:RESOURCE]->(b:AWSS3Bucket)
        WHERE b.default_encryption IS NULL OR b.default_encryption = false
        RETURN a.id AS account_id, a.name AS account, b.id AS bucket_id,
               b.name AS bucket_name, b.default_encryption AS default_encryption

    """,
    cypher_count_query="""
    MATCH (b:AWSS3Bucket) RETURN COUNT(b) AS count
    """,
    asset_label="AWSS3Bucket",
    asset_id_field="bucket_id",
    identity_fields=("account_id", "account", "bucket_id"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_s3_bucket_default_encryption = Rule(
    id="aws_s3_bucket_default_encryption",
    name="S3 Bucket Default Encryption",
    description="S3 bucket has no default server-side encryption configuration (default_encryption null/false). Superseded in practice by KMS / encryption-at-rest checks; kept for coverage continuity.",
    output_model=AwsS3BucketDefaultEncryptionOutput,
    facts=(_aws_s3_bucket_default_encryption_fact,),
    tags=("security", "s3", "encryption", "cspm"),
    version="0.1.0",
)


class AwsS3BucketKmsEncryptionOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    bucket_id: str | None = None
    bucket_name: str | None = None
    object_ownership: str | None = None
    default_encryption: str | None = None
    encryption_algorithm: str | None = None
    encryption_key_id: str | None = None
    versioning_status: str | None = None
    logging_enabled: str | None = None
    logging_target_bucket: str | None = None


_aws_s3_bucket_kms_encryption_fact = Fact(
    id="aws_s3_bucket_kms_encryption_fact",
    name="S3 without KMS encryption",
    description="Buckets whose encryption_algorithm is not aws:kms/aws:kms:dsse.",
    cypher_query="""

        MATCH (a:AWSAccount)-[:RESOURCE]->(b:AWSS3Bucket)
        WHERE b.encryption_algorithm IS NULL
           OR NOT b.encryption_algorithm IN ['aws:kms', 'aws:kms:dsse']
        RETURN a.id AS account_id, a.name AS account, b.id AS bucket_id,
               b.name AS bucket_name, b.encryption_algorithm AS encryption_algorithm,
               b.encryption_key_id AS encryption_key_id

    """,
    cypher_visual_query="""

        MATCH (a:AWSAccount)-[:RESOURCE]->(b:AWSS3Bucket)
        WHERE b.encryption_algorithm IS NULL
           OR NOT b.encryption_algorithm IN ['aws:kms', 'aws:kms:dsse']
        RETURN a.id AS account_id, a.name AS account, b.id AS bucket_id,
               b.name AS bucket_name, b.encryption_algorithm AS encryption_algorithm,
               b.encryption_key_id AS encryption_key_id

    """,
    cypher_count_query="""
    MATCH (b:AWSS3Bucket) RETURN COUNT(b) AS count
    """,
    asset_label="AWSS3Bucket",
    asset_id_field="bucket_id",
    identity_fields=("account_id", "account", "bucket_id"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_s3_bucket_kms_encryption = Rule(
    id="aws_s3_bucket_kms_encryption",
    name="S3 Bucket KMS Encryption",
    description="S3 bucket default encryption does not use AWS KMS (encryption_algorithm is not aws:kms or aws:kms:dsse, e.g. AES256/SSE-S3 or unset).",
    output_model=AwsS3BucketKmsEncryptionOutput,
    facts=(_aws_s3_bucket_kms_encryption_fact,),
    tags=("security", "s3", "encryption", "cspm"),
    version="0.1.0",
)
