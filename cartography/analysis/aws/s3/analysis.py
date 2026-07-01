from cartography.graph.analysis import AnalysisJob
from cartography.graph.analysis import AnalysisStatement
from cartography.graph.analysis import Expr
from cartography.graph.analysis import ScopedTo
from cartography.graph.analysis import SetProperties

AWS_S3ACL_ANALYSIS = AnalysisJob(
    name="AWS S3 Acl exposure analysis",
    short_name="aws_s3acl_analysis",
    scope=ScopedTo("AWSAccount", "AWS_ID"),
    statements=(
        AnalysisStatement(
            match="""
            MATCH (acl:S3Acl)-[:APPLIES_TO]->(bucket:S3Bucket)<-[:RESOURCE]-(aws:AWSAccount{id: $AWS_ID})
            WHERE acl.uri IN ['http://acs.amazonaws.com/groups/global/AllUsers', 'http://acs.amazonaws.com/groups/global/AuthenticatedUsers']
            AND acl.permission = 'READ'
            """,
            effects=(
                SetProperties(
                    "bucket",
                    {
                        "anonymous_access": True,
                        "anonymous_actions": Expr(
                            "coalesce(bucket.anonymous_actions, []) + ['s3:ListBucket', 's3:ListBucketVersions', 's3:ListBucketMultipartUploads']"
                        ),
                    },
                    label="S3Bucket",
                ),
            ),
        ),
        AnalysisStatement(
            match="""
            MATCH (acl:S3Acl)-[:APPLIES_TO]->(bucket:S3Bucket)<-[:RESOURCE]-(aws:AWSAccount{id: $AWS_ID})
            WHERE acl.uri IN ['http://acs.amazonaws.com/groups/global/AllUsers', 'http://acs.amazonaws.com/groups/global/AuthenticatedUsers']
            AND acl.permission = 'WRITE'
            """,
            effects=(
                SetProperties(
                    "bucket",
                    {
                        "anonymous_access": True,
                        "anonymous_actions": Expr(
                            "coalesce(bucket.anonymous_actions, []) + ['s3:PutObject']"
                        ),
                    },
                    label="S3Bucket",
                ),
            ),
        ),
        AnalysisStatement(
            match="""
            MATCH (acl:S3Acl)-[:APPLIES_TO]->(bucket:S3Bucket)<-[:RESOURCE]-(aws:AWSAccount{id: $AWS_ID})
            WHERE acl.uri IN ['http://acs.amazonaws.com/groups/global/AllUsers', 'http://acs.amazonaws.com/groups/global/AuthenticatedUsers']
            AND acl.permission = 'READ_ACP'
            """,
            effects=(
                SetProperties(
                    "bucket",
                    {
                        "anonymous_access": True,
                        "anonymous_actions": Expr(
                            "coalesce(bucket.anonymous_actions, []) + ['s3:GetBucketAcl']"
                        ),
                    },
                    label="S3Bucket",
                ),
            ),
        ),
        AnalysisStatement(
            match="""
            MATCH (acl:S3Acl)-[:APPLIES_TO]->(bucket:S3Bucket)<-[:RESOURCE]-(aws:AWSAccount{id: $AWS_ID})
            WHERE acl.uri IN ['http://acs.amazonaws.com/groups/global/AllUsers', 'http://acs.amazonaws.com/groups/global/AuthenticatedUsers']
            AND acl.permission = 'WRITE_ACP'
            """,
            effects=(
                SetProperties(
                    "bucket",
                    {
                        "anonymous_access": True,
                        "anonymous_actions": Expr(
                            "coalesce(bucket.anonymous_actions, []) + ['s3:PutBucketAcl']"
                        ),
                    },
                    label="S3Bucket",
                ),
            ),
        ),
        AnalysisStatement(
            match="""
            MATCH (acl:S3Acl)-[:APPLIES_TO]->(bucket:S3Bucket)<-[:RESOURCE]-(aws:AWSAccount{id: $AWS_ID})
            WHERE acl.uri IN ['http://acs.amazonaws.com/groups/global/AllUsers', 'http://acs.amazonaws.com/groups/global/AuthenticatedUsers']
            AND acl.permission = 'FULL_CONTROL'
            """,
            effects=(
                SetProperties(
                    "bucket",
                    {
                        "anonymous_access": True,
                        "anonymous_actions": Expr(
                            "coalesce(bucket.anonymous_actions, []) + ['s3:ListBucket', 's3:ListBucketVersions', 's3:ListBucketMultipartUploads', 's3:PutObject', 's3:DeleteObject', 's3:DeleteObjectVersion', 's3:GetBucketAcl', 's3:PutBucketAcl']"
                        ),
                    },
                    label="S3Bucket",
                ),
            ),
        ),
    ),
)
