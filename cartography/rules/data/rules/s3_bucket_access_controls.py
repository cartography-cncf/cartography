"""
AWS S3 bucket access controls: ACLs, policy principals and transport

Read and write ACL grants to AllUsers/AuthenticatedUsers, bucket ACLs left
enabled through Object Ownership, cross-account principals in bucket policy
Allow statements, wildcard-principal write permissions, and the absence of a
Deny statement on aws:SecureTransport.

Cartography stores ACL grants as their own nodes and policy principals and
conditions as serialized JSON, so the policy checks are keyword approximations
rather than policy evaluation. They over- and under-match; each rule says so.
Block Public Access neutralization is not applied here.

Every property and relationship used here is already synced by the AWS
intel module; no collector change is required. All rules are
EXPERIMENTAL until validated against a live graph.
"""

from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule


class AwsS3BucketAclDisabledOutput(Finding):
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


_aws_s3_bucket_acl_disabled_fact = Fact(
    id="aws_s3_bucket_acl_disabled_fact",
    name="S3 ACLs enabled",
    description="Buckets whose object_ownership is not BucketOwnerEnforced.",
    cypher_query="""

        MATCH (a:AWSAccount)-[:RESOURCE]->(b:AWSS3Bucket)
        WHERE b.object_ownership IS NULL OR b.object_ownership <> 'BucketOwnerEnforced'
        RETURN a.id AS account_id, a.name AS account, b.id AS bucket_id,
               b.name AS bucket_name, b.object_ownership AS object_ownership

    """,
    cypher_visual_query="""

        MATCH (a:AWSAccount)-[:RESOURCE]->(b:AWSS3Bucket)
        WHERE b.object_ownership IS NULL OR b.object_ownership <> 'BucketOwnerEnforced'
        RETURN a.id AS account_id, a.name AS account, b.id AS bucket_id,
               b.name AS bucket_name, b.object_ownership AS object_ownership

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


aws_s3_bucket_acl_disabled = Rule(
    id="aws_s3_bucket_acl_disabled",
    name="S3 Bucket ACLs Not Disabled",
    description="S3 bucket Object Ownership is not BucketOwnerEnforced, so bucket/object ACLs remain enabled (null treated as ACLs enabled).",
    output_model=AwsS3BucketAclDisabledOutput,
    facts=(_aws_s3_bucket_acl_disabled_fact,),
    tags=("security", "s3", "cspm"),
    version="0.1.0",
)


class AwsS3BucketCrossAccountAccessOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    bucket_name: str | None = None
    statement_id: str | None = None
    sid: str | None = None
    principal: str | None = None


_aws_s3_bucket_cross_account_access_fact = Fact(
    id="aws_s3_bucket_cross_account_access_fact",
    name="S3 cross-account policy statement",
    description="Allow statements whose serialized principal names a wildcard or a foreign account (approximate).",
    cypher_query="""

        MATCH (a:AWSAccount)-[:RESOURCE]->(b:AWSS3Bucket)-[:POLICY_STATEMENT]-(stmt:AWSS3PolicyStatement)
        WHERE stmt.effect = 'Allow'
          AND (toString(stmt.principal) CONTAINS '*'
               OR ANY(tok IN split(toString(stmt.principal), '"')
                      WHERE ANY(part IN split(tok, ':')
                                WHERE part =~ '[0-9]{12}' AND part <> a.id)))
        RETURN DISTINCT a.id AS account_id, a.name AS account, b.name AS bucket_name,
               stmt.id AS statement_id, stmt.sid AS sid,
               toString(stmt.principal) AS principal

    """,
    cypher_visual_query="""

        MATCH (a:AWSAccount)-[:RESOURCE]->(b:AWSS3Bucket)-[:POLICY_STATEMENT]-(stmt:AWSS3PolicyStatement)
        WHERE stmt.effect = 'Allow'
          AND (toString(stmt.principal) CONTAINS '*'
               OR ANY(tok IN split(toString(stmt.principal), '"')
                      WHERE ANY(part IN split(tok, ':')
                                WHERE part =~ '[0-9]{12}' AND part <> a.id)))
        RETURN DISTINCT a.id AS account_id, a.name AS account, b.name AS bucket_name,
               stmt.id AS statement_id, stmt.sid AS sid,
               toString(stmt.principal) AS principal

    """,
    cypher_count_query="""

        MATCH (stmt:AWSS3PolicyStatement)
        OPTIONAL MATCH (a:AWSAccount)-[:RESOURCE]->(b:AWSS3Bucket)-[:POLICY_STATEMENT]-(stmt)
        RETURN COUNT(DISTINCT stmt) AS count, COUNT(DISTINCT stmt) AS total_assets,
               COUNT(DISTINCT CASE WHEN stmt.effect = 'Allow'
          AND (toString(stmt.principal) CONTAINS '*'
               OR ANY(tok IN split(toString(stmt.principal), '"')
                      WHERE ANY(part IN split(tok, ':')
                                WHERE part =~ '[0-9]{12}' AND part <> a.id))) THEN stmt END) AS failing

    """,
    asset_label="AWSS3PolicyStatement",
    asset_id_field="statement_id",
    identity_fields=("account_id", "bucket_name", "statement_id"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_s3_bucket_cross_account_access = Rule(
    id="aws_s3_bucket_cross_account_access",
    name="S3 Bucket Policy Cross-Account Access",
    description="BEST-EFFORT (EXPERIMENTAL): S3 bucket policy Allow statement names a principal outside the owning account (wildcard '*' or another AWS account ID). principal is stored as a serialized expression, so detection is string parsing: wildcard, or a 12-digit account token different from the owning account (resolved via (AWSAccount)-[:RESOURCE]->(AWSS3Bucket)). Service/federated principals are excluded by construction; statement conditions and NotPrincipal are not evaluated, so statements restricted by e.g. aws:PrincipalOrgID may be over-flagged. Buckets without a policy pass. Needs live-graph validation and likely Python JSON refinement.",
    output_model=AwsS3BucketCrossAccountAccessOutput,
    facts=(_aws_s3_bucket_cross_account_access_fact,),
    tags=("security", "s3", "attack_surface", "cspm", "best-effort"),
    version="0.1.0",
)


class AwsS3BucketPublicListAclOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    bucket_name: str | None = None
    bucket_id: str | None = None
    anonymous_access: str | None = None
    anonymous_actions: str | None = None
    permission: str | None = None
    grantee_uri: str | None = None


_aws_s3_bucket_public_list_acl_fact = Fact(
    id="aws_s3_bucket_public_list_acl_fact",
    name="S3 public list ACL",
    description="Public group ACL grants allowing list/read.",
    cypher_query="""

        MATCH (a:AWSAccount)-[:RESOURCE]->(b:AWSS3Bucket)<-[:APPLIES_TO]-(acl:AWSS3Acl)
        WHERE (acl.uri ENDS WITH 'AllUsers' OR acl.uri ENDS WITH 'AuthenticatedUsers')
          AND acl.permission IN ['READ', 'READ_ACP', 'FULL_CONTROL']
        RETURN DISTINCT a.id AS account_id, a.name AS account, b.name AS bucket_name,
               b.id AS bucket_id, acl.permission AS permission, acl.uri AS grantee_uri

    """,
    cypher_visual_query="""

        MATCH (a:AWSAccount)-[:RESOURCE]->(b:AWSS3Bucket)<-[:APPLIES_TO]-(acl:AWSS3Acl)
        WHERE (acl.uri ENDS WITH 'AllUsers' OR acl.uri ENDS WITH 'AuthenticatedUsers')
          AND acl.permission IN ['READ', 'READ_ACP', 'FULL_CONTROL']
        RETURN DISTINCT a.id AS account_id, a.name AS account, b.name AS bucket_name,
               b.id AS bucket_id, acl.permission AS permission, acl.uri AS grantee_uri

    """,
    cypher_count_query="""
    MATCH (b:AWSS3Bucket) RETURN COUNT(b) AS count
    """,
    asset_label="AWSS3Bucket",
    asset_id_field="bucket_id",
    identity_fields=("bucket_id", "permission"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_s3_bucket_public_list_acl = Rule(
    id="aws_s3_bucket_public_list_acl",
    name="S3 Bucket Public List ACL",
    description="S3 bucket ACL grants READ/READ_ACP/FULL_CONTROL to AllUsers or AuthenticatedUsers.",
    output_model=AwsS3BucketPublicListAclOutput,
    facts=(_aws_s3_bucket_public_list_acl_fact,),
    tags=("security", "s3", "attack_surface", "cspm"),
    version="0.1.0",
)


class AwsS3BucketPublicWriteAclOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    bucket_name: str | None = None
    bucket_id: str | None = None
    anonymous_access: str | None = None
    anonymous_actions: str | None = None
    permission: str | None = None
    grantee_uri: str | None = None


_aws_s3_bucket_public_write_acl_fact = Fact(
    id="aws_s3_bucket_public_write_acl_fact",
    name="S3 public write ACL",
    description="Public group ACL grants allowing write.",
    cypher_query="""

        MATCH (a:AWSAccount)-[:RESOURCE]->(b:AWSS3Bucket)<-[:APPLIES_TO]-(acl:AWSS3Acl)
        WHERE (acl.uri ENDS WITH 'AllUsers' OR acl.uri ENDS WITH 'AuthenticatedUsers')
          AND acl.permission IN ['WRITE', 'WRITE_ACP', 'FULL_CONTROL']
        RETURN DISTINCT a.id AS account_id, a.name AS account, b.name AS bucket_name,
               b.id AS bucket_id, acl.permission AS permission, acl.uri AS grantee_uri

    """,
    cypher_visual_query="""

        MATCH (a:AWSAccount)-[:RESOURCE]->(b:AWSS3Bucket)<-[:APPLIES_TO]-(acl:AWSS3Acl)
        WHERE (acl.uri ENDS WITH 'AllUsers' OR acl.uri ENDS WITH 'AuthenticatedUsers')
          AND acl.permission IN ['WRITE', 'WRITE_ACP', 'FULL_CONTROL']
        RETURN DISTINCT a.id AS account_id, a.name AS account, b.name AS bucket_name,
               b.id AS bucket_id, acl.permission AS permission, acl.uri AS grantee_uri

    """,
    cypher_count_query="""
    MATCH (b:AWSS3Bucket) RETURN COUNT(b) AS count
    """,
    asset_label="AWSS3Bucket",
    asset_id_field="bucket_id",
    identity_fields=("bucket_id", "permission"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_s3_bucket_public_write_acl = Rule(
    id="aws_s3_bucket_public_write_acl",
    name="S3 Bucket Public Write ACL",
    description="S3 bucket ACL grants WRITE/WRITE_ACP/FULL_CONTROL to AllUsers or AuthenticatedUsers.",
    output_model=AwsS3BucketPublicWriteAclOutput,
    facts=(_aws_s3_bucket_public_write_acl_fact,),
    tags=("security", "s3", "attack_surface", "cspm"),
    version="0.1.0",
)


class AwsS3BucketPublicWritePolicyOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    bucket_name: str | None = None
    bucket_id: str | None = None
    anonymous_access: str | None = None
    anonymous_actions: str | None = None
    permission: str | None = None
    grantee_uri: str | None = None


_aws_s3_bucket_public_write_policy_fact = Fact(
    id="aws_s3_bucket_public_write_policy_fact",
    name="S3 public write policy",
    description="Allow statements with wildcard principal and write actions (approximate).",
    cypher_query="""

        MATCH (a:AWSAccount)-[:RESOURCE]->(b:AWSS3Bucket)-[:POLICY_STATEMENT]-(stmt:AWSS3PolicyStatement)
        WHERE stmt.effect = 'Allow'
          AND toString(stmt.principal) CONTAINS '*'
          AND any(x IN CASE
                  WHEN stmt.action IS :: LIST<ANY> THEN stmt.action
                  WHEN stmt.action IS NULL THEN []
                  ELSE [stmt.action]
                END WHERE
                toString(x) CONTAINS 's3:PutObject'
             OR toString(x) CONTAINS 's3:Delete'
             OR toString(x) CONTAINS 's3:*')
        RETURN DISTINCT a.id AS account_id, a.name AS account, b.name AS bucket_name,
               b.id AS bucket_id

    """,
    cypher_visual_query="""

        MATCH (a:AWSAccount)-[:RESOURCE]->(b:AWSS3Bucket)-[:POLICY_STATEMENT]-(stmt:AWSS3PolicyStatement)
        WHERE stmt.effect = 'Allow'
          AND toString(stmt.principal) CONTAINS '*'
          AND any(x IN CASE
                  WHEN stmt.action IS :: LIST<ANY> THEN stmt.action
                  WHEN stmt.action IS NULL THEN []
                  ELSE [stmt.action]
                END WHERE
                toString(x) CONTAINS 's3:PutObject'
             OR toString(x) CONTAINS 's3:Delete'
             OR toString(x) CONTAINS 's3:*')
        RETURN DISTINCT a.id AS account_id, a.name AS account, b.name AS bucket_name,
               b.id AS bucket_id

    """,
    cypher_count_query="""
    MATCH (b:AWSS3Bucket) RETURN COUNT(b) AS count
    """,
    asset_label="AWSS3Bucket",
    asset_id_field="bucket_id",
    identity_fields=("bucket_id",),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_s3_bucket_public_write_policy = Rule(
    id="aws_s3_bucket_public_write_policy",
    name="S3 Bucket Public Write Policy",
    description="BEST-EFFORT (EXPERIMENTAL): S3 bucket policy Allow statement with a wildcard principal granting write actions. Principal/action are stored as structured JSON; this toString/CONTAINS approximation needs live-graph validation and likely Python refinement.",
    output_model=AwsS3BucketPublicWritePolicyOutput,
    facts=(_aws_s3_bucket_public_write_policy_fact,),
    tags=("security", "s3", "attack_surface", "cspm", "best-effort"),
    version="0.1.0",
)


class AwsS3BucketSecureTransportPolicyOutput(Finding):
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


_aws_s3_bucket_secure_transport_policy_fact = Fact(
    id="aws_s3_bucket_secure_transport_policy_fact",
    name="S3 insecure transport not denied",
    description="Buckets lacking a Deny statement whose condition string references aws:SecureTransport=false (approximate).",
    cypher_query="""

        MATCH (a:AWSAccount)-[:RESOURCE]->(b:AWSS3Bucket)
        WHERE NOT EXISTS {
            MATCH (b)-[:POLICY_STATEMENT]-(stmt:AWSS3PolicyStatement)
            WHERE stmt.effect = 'Deny'
              AND toString(stmt.condition) CONTAINS 'aws:SecureTransport'
              AND toString(stmt.condition) CONTAINS 'false'
        }
        RETURN a.id AS account_id, a.name AS account, b.id AS bucket_id,
               b.name AS bucket_name

    """,
    cypher_visual_query="""

        MATCH (a:AWSAccount)-[:RESOURCE]->(b:AWSS3Bucket)
        WHERE NOT EXISTS {
            MATCH (b)-[:POLICY_STATEMENT]-(stmt:AWSS3PolicyStatement)
            WHERE stmt.effect = 'Deny'
              AND toString(stmt.condition) CONTAINS 'aws:SecureTransport'
              AND toString(stmt.condition) CONTAINS 'false'
        }
        RETURN a.id AS account_id, a.name AS account, b.id AS bucket_id,
               b.name AS bucket_name

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


aws_s3_bucket_secure_transport_policy = Rule(
    id="aws_s3_bucket_secure_transport_policy",
    name="S3 Bucket Secure Transport Policy",
    description="BEST-EFFORT (EXPERIMENTAL): S3 bucket has no policy, or no Deny statement whose serialized condition references aws:SecureTransport and false (i.e. requests over insecure transport are not explicitly denied). AWSS3PolicyStatement.condition is stored as a serialized expression, so this CONTAINS approximation cannot evaluate policy semantics (Bool operator, key/value pairing, statement scope) and may over- or under-flag; needs live-graph validation and Python JSON parsing for full coverage.",
    output_model=AwsS3BucketSecureTransportPolicyOutput,
    facts=(_aws_s3_bucket_secure_transport_policy_fact,),
    tags=("security", "s3", "encryption", "cspm", "best-effort"),
    version="0.1.0",
)
