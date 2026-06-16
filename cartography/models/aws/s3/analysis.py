from cartography.graph.analysis import AnalysisJob
from cartography.graph.analysis import AnalysisScope
from cartography.graph.analysis import AnalysisStatement
from cartography.graph.analysis import PropertyEffect

AWS_SCOPE = AnalysisScope("AWSAccount", "AWS_ID")

AWS_S3ACL_ANALYSIS = AnalysisJob(
    name="AWS S3 Acl exposure analysis",
    short_name="aws_s3acl_analysis",
    scope=AWS_SCOPE,
    effect=PropertyEffect("S3Bucket", ("anonymous_access", "anonymous_actions")),
    statements=(
        AnalysisStatement(
            "MATCH (acl:S3Acl)-[:APPLIES_TO]->(bucket:S3Bucket)<-[:RESOURCE]-(aws:AWSAccount{id: $AWS_ID})\n"
            "WHERE acl.uri IN ['http://acs.amazonaws.com/groups/global/AllUsers', 'http://acs.amazonaws.com/groups/global/AuthenticatedUsers'] AND acl.permission = 'READ'\n"
            "SET bucket.anonymous_access = true, bucket.anonymous_actions = coalesce(bucket.anonymous_actions, []) + ['s3:ListBucket', 's3:ListBucketVersions', 's3:ListBucketMultipartUploads']",
        ),
        AnalysisStatement(
            "MATCH (acl:S3Acl)-[:APPLIES_TO]->(bucket:S3Bucket)<-[:RESOURCE]-(aws:AWSAccount{id: $AWS_ID})\n"
            "WHERE acl.uri IN ['http://acs.amazonaws.com/groups/global/AllUsers', 'http://acs.amazonaws.com/groups/global/AuthenticatedUsers'] AND acl.permission = 'WRITE'\n"
            "SET bucket.anonymous_access = true, bucket.anonymous_actions = coalesce(bucket.anonymous_actions, []) + ['s3:PutObject']",
        ),
        AnalysisStatement(
            "MATCH (acl:S3Acl)-[:APPLIES_TO]->(bucket:S3Bucket)<-[:RESOURCE]-(aws:AWSAccount{id: $AWS_ID})\n"
            "WHERE acl.uri IN ['http://acs.amazonaws.com/groups/global/AllUsers', 'http://acs.amazonaws.com/groups/global/AuthenticatedUsers'] AND acl.permission = 'READ_ACP'\n"
            "SET bucket.anonymous_access = true, bucket.anonymous_actions = coalesce(bucket.anonymous_actions, []) + ['s3:GetBucketAcl']",
        ),
        AnalysisStatement(
            "MATCH (acl:S3Acl)-[:APPLIES_TO]->(bucket:S3Bucket)<-[:RESOURCE]-(aws:AWSAccount{id: $AWS_ID})\n"
            "WHERE acl.uri IN ['http://acs.amazonaws.com/groups/global/AllUsers', 'http://acs.amazonaws.com/groups/global/AuthenticatedUsers'] AND acl.permission = 'WRITE_ACP'\n"
            "SET bucket.anonymous_access = true, bucket.anonymous_actions = coalesce(bucket.anonymous_actions, []) + ['s3:PutBucketAcl']",
        ),
        AnalysisStatement(
            "MATCH (acl:S3Acl)-[:APPLIES_TO]->(bucket:S3Bucket)<-[:RESOURCE]-(aws:AWSAccount{id: $AWS_ID})\n"
            "WHERE acl.uri IN ['http://acs.amazonaws.com/groups/global/AllUsers', 'http://acs.amazonaws.com/groups/global/AuthenticatedUsers'] AND acl.permission = 'FULL_CONTROL'\n"
            "SET bucket.anonymous_access = true, bucket.anonymous_actions = coalesce(bucket.anonymous_actions, []) + ['s3:ListBucket', 's3:ListBucketVersions', 's3:ListBucketMultipartUploads', 's3:PutObject', 's3:DeleteObject', 's3:DeleteObjectVersion', 's3:PutBucketAcl']",
        ),
    ),
)
