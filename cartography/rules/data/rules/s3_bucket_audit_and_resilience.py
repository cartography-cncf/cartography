"""
AWS S3 server access logging, event notifications and account-level BPA

Server access logging is checked on every bucket. Upstream's
aws_cloudtrail_s3_bucket_access_logging only covers the bucket a trail writes
to, found by traversing LOGS_TO, so the two do not overlap.

The event-notification check is best effort: only SNS topic configurations are
modelled, so a bucket that notifies SQS or Lambda alone appears to have none.

Every property and relationship used here is already synced by the AWS
intel module; no collector change is required. All rules are
EXPERIMENTAL until validated against a live graph.
"""

from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule


class AwsS3AccountPublicAccessBlockOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    pab_id: str | None = None
    region: str | None = None
    ignore_public_acls: str | None = None
    restrict_public_buckets: str | None = None


_aws_s3_account_public_access_block_fact = Fact(
    id="aws_s3_account_public_access_block_fact",
    name="S3 account BPA gaps",
    description="Account-level BPA nodes with ignore_public_acls or restrict_public_buckets not true.",
    cypher_query="""

        MATCH (a:AWSAccount)-[:RESOURCE]->(pab:AWSS3AccountPublicAccessBlock)
        WHERE coalesce(pab.ignore_public_acls, false) = false
           OR coalesce(pab.restrict_public_buckets, false) = false
        RETURN a.id AS account_id, a.name AS account, pab.id AS pab_id,
               pab.region AS region, pab.ignore_public_acls AS ignore_public_acls,
               pab.restrict_public_buckets AS restrict_public_buckets

    """,
    cypher_visual_query="""

        MATCH (a:AWSAccount)-[:RESOURCE]->(pab:AWSS3AccountPublicAccessBlock)
        WHERE coalesce(pab.ignore_public_acls, false) = false
           OR coalesce(pab.restrict_public_buckets, false) = false
        RETURN a.id AS account_id, a.name AS account, pab.id AS pab_id,
               pab.region AS region, pab.ignore_public_acls AS ignore_public_acls,
               pab.restrict_public_buckets AS restrict_public_buckets

    """,
    cypher_count_query="""
    MATCH (pab:AWSS3AccountPublicAccessBlock)
        RETURN COUNT(pab) AS count, COUNT(pab) AS total_assets,
               COUNT(CASE WHEN coalesce(pab.ignore_public_acls, false) = false OR coalesce(pab.restrict_public_buckets, false) = false THEN 1 END) AS failing
    """,
    asset_label="AWSS3AccountPublicAccessBlock",
    asset_id_field="pab_id",
    identity_fields=("account_id", "region"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_s3_account_public_access_block = Rule(
    id="aws_s3_account_public_access_block",
    name="S3 Account-Level Block Public Access",
    description="Account-level Block Public Access does not ignore public ACLs or does not restrict public buckets (ignore_public_acls != true or restrict_public_buckets != true, null treated as not enforced). Settings are account-global in AWS but stored as one node per region with identical values, so a failing account yields one finding per region node.",
    output_model=AwsS3AccountPublicAccessBlockOutput,
    facts=(_aws_s3_account_public_access_block_fact,),
    tags=("security", "s3", "attack_surface", "cspm"),
    version="0.1.0",
)


class AwsS3BucketAccessLoggingOutput(Finding):
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


_aws_s3_bucket_access_logging_fact = Fact(
    id="aws_s3_bucket_access_logging_fact",
    name="S3 access logging disabled",
    description="Buckets with logging_enabled=null/false.",
    cypher_query="""

        MATCH (a:AWSAccount)-[:RESOURCE]->(b:AWSS3Bucket)
        WHERE b.logging_enabled IS NULL OR b.logging_enabled = false
        RETURN a.id AS account_id, a.name AS account, b.id AS bucket_id,
               b.name AS bucket_name, b.logging_enabled AS logging_enabled,
               b.logging_target_bucket AS logging_target_bucket

    """,
    cypher_visual_query="""

        MATCH (a:AWSAccount)-[:RESOURCE]->(b:AWSS3Bucket)
        WHERE b.logging_enabled IS NULL OR b.logging_enabled = false
        RETURN a.id AS account_id, a.name AS account, b.id AS bucket_id,
               b.name AS bucket_name, b.logging_enabled AS logging_enabled,
               b.logging_target_bucket AS logging_target_bucket

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


aws_s3_bucket_access_logging = Rule(
    id="aws_s3_bucket_access_logging",
    name="S3 Bucket Server Access Logging",
    description="S3 bucket has no server access logging configuration (logging_enabled null/false). Evaluates all buckets, unlike the built-in aws_cloudtrail_s3_bucket_access_logging which only covers CloudTrail trail destinations.",
    output_model=AwsS3BucketAccessLoggingOutput,
    facts=(_aws_s3_bucket_access_logging_fact,),
    tags=("security", "s3", "logging", "cspm"),
    version="0.1.0",
)


class AwsS3BucketEventNotificationsOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    bucket_id: str | None = None
    bucket_name: str | None = None
    region: str | None = None


_aws_s3_bucket_event_notifications_fact = Fact(
    id="aws_s3_bucket_event_notifications_fact",
    name="S3 bucket without SNS notifications",
    description="Buckets with no outgoing NOTIFIES edge to an SNS topic.",
    cypher_query="""

        MATCH (a:AWSAccount)-[:RESOURCE]->(b:AWSS3Bucket)
        WHERE NOT EXISTS {
            MATCH (b)-[:NOTIFIES]->(t:AWSSNSTopic)
        }
        RETURN a.id AS account_id, a.name AS account, b.id AS bucket_id,
               b.name AS bucket_name, b.region AS region

    """,
    cypher_visual_query="""

        MATCH p=(a:AWSAccount)-[:RESOURCE]->(b:AWSS3Bucket)
        WHERE NOT EXISTS {
            MATCH (b)-[:NOTIFIES]->(t:AWSSNSTopic)
        }
        RETURN *

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


aws_s3_bucket_event_notifications = Rule(
    id="aws_s3_bucket_event_notifications",
    name="S3 Bucket Event Notifications",
    description="S3 bucket with no NOTIFIES relationship to any AWSSNSTopic, i.e. no SNS event-notification destination configured. BEST-EFFORT: cartography only syncs SNS TopicConfigurations; buckets notified solely via SQS, Lambda or EventBridge are not captured and will false-positive.",
    output_model=AwsS3BucketEventNotificationsOutput,
    facts=(_aws_s3_bucket_event_notifications_fact,),
    tags=("observability", "s3", "logging", "cspm", "best-effort"),
    version="0.1.0",
)
