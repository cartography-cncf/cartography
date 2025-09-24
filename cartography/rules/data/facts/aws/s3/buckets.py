from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Provider

aws_s3_public = Fact(
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
    RETURN b.name AS bucket,
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
    OPTIONAL MATCH p=(b)--(:S3PolicyStatement)
    RETURN *
    """,
    provider=Provider.AWS,
)
