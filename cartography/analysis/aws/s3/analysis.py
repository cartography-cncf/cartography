from cartography.graph.analysis import AddValuesToSet
from cartography.graph.analysis import AnalysisJob
from cartography.graph.analysis import AnalysisStatement
from cartography.graph.analysis import ScopeById
from cartography.graph.analysis import SetProperty

AWS_S3ACL_ANALYSIS = AnalysisJob(
    name="AWS S3 Acl exposure analysis",
    short_name="aws_s3acl_analysis",
    scope=ScopeById("AWSAccount", "AWS_ID", scope_on="bucket"),
    statements=(
        AnalysisStatement(
            match="""
            MATCH (acl:S3Acl)-[:APPLIES_TO]->(bucket:S3Bucket)
            WHERE acl.uri IN ['http://acs.amazonaws.com/groups/global/AllUsers', 'http://acs.amazonaws.com/groups/global/AuthenticatedUsers']
            AND acl.permission = 'READ'
            """,
            effects=(
                SetProperty("bucket", "anonymous_access", True, label="S3Bucket"),
                AddValuesToSet(
                    "bucket",
                    "anonymous_actions",
                    (
                        "s3:ListBucket",
                        "s3:ListBucketVersions",
                        "s3:ListBucketMultipartUploads",
                    ),
                    label="S3Bucket",
                ),
            ),
        ),
        AnalysisStatement(
            match="""
            MATCH (acl:S3Acl)-[:APPLIES_TO]->(bucket:S3Bucket)
            WHERE acl.uri IN ['http://acs.amazonaws.com/groups/global/AllUsers', 'http://acs.amazonaws.com/groups/global/AuthenticatedUsers']
            AND acl.permission = 'WRITE'
            """,
            effects=(
                SetProperty("bucket", "anonymous_access", True, label="S3Bucket"),
                AddValuesToSet(
                    "bucket",
                    "anonymous_actions",
                    ("s3:PutObject",),
                    label="S3Bucket",
                ),
            ),
        ),
        AnalysisStatement(
            match="""
            MATCH (acl:S3Acl)-[:APPLIES_TO]->(bucket:S3Bucket)
            WHERE acl.uri IN ['http://acs.amazonaws.com/groups/global/AllUsers', 'http://acs.amazonaws.com/groups/global/AuthenticatedUsers']
            AND acl.permission = 'READ_ACP'
            """,
            effects=(
                SetProperty("bucket", "anonymous_access", True, label="S3Bucket"),
                AddValuesToSet(
                    "bucket",
                    "anonymous_actions",
                    ("s3:GetBucketAcl",),
                    label="S3Bucket",
                ),
            ),
        ),
        AnalysisStatement(
            match="""
            MATCH (acl:S3Acl)-[:APPLIES_TO]->(bucket:S3Bucket)
            WHERE acl.uri IN ['http://acs.amazonaws.com/groups/global/AllUsers', 'http://acs.amazonaws.com/groups/global/AuthenticatedUsers']
            AND acl.permission = 'WRITE_ACP'
            """,
            effects=(
                SetProperty("bucket", "anonymous_access", True, label="S3Bucket"),
                AddValuesToSet(
                    "bucket",
                    "anonymous_actions",
                    ("s3:PutBucketAcl",),
                    label="S3Bucket",
                ),
            ),
        ),
        AnalysisStatement(
            match="""
            MATCH (acl:S3Acl)-[:APPLIES_TO]->(bucket:S3Bucket)
            WHERE acl.uri IN ['http://acs.amazonaws.com/groups/global/AllUsers', 'http://acs.amazonaws.com/groups/global/AuthenticatedUsers']
            AND acl.permission = 'FULL_CONTROL'
            """,
            effects=(
                SetProperty("bucket", "anonymous_access", True, label="S3Bucket"),
                AddValuesToSet(
                    "bucket",
                    "anonymous_actions",
                    (
                        "s3:ListBucket",
                        "s3:ListBucketVersions",
                        "s3:ListBucketMultipartUploads",
                        "s3:PutObject",
                        "s3:DeleteObject",
                        "s3:DeleteObjectVersion",
                        "s3:PutBucketAcl",
                    ),
                    label="S3Bucket",
                ),
            ),
        ),
    ),
)
