from cartography.intel.aws.s3 import _load_s3_acls
from cartography.intel.aws.s3 import load_s3_buckets
from cartography.intel.aws.s3 import parse_acl
from tests.data.aws.s3 import LIST_BUCKETS
from tests.data.aws.s3 import OPEN_BUCKET_ACLS
from tests.integration.cartography.intel.aws.iam.test_iam import _create_base_account
from tests.integration.util import check_nodes

TEST_ACCOUNT_ID = '000000000000'
TEST_REGION = 'us-east-1'
TEST_UPDATE_TAG = 123456789


def test_load_s3_acls(neo4j_session):
    """
    Ensure that the S3 ACL that sets anonymous_access and anonymous_actions works.
    """
    # Arrange: hackily add s3 data to the test graph
    _create_base_account(neo4j_session)
    load_s3_buckets(neo4j_session, LIST_BUCKETS, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
    parsed_acls = []
    for bucket_name, acl in OPEN_BUCKET_ACLS.items():
        acl = parse_acl(acl, bucket_name, TEST_ACCOUNT_ID)
        if acl:
            parsed_acls.extend(acl)

    # Act: run the analysis job
    _load_s3_acls(neo4j_session, parsed_acls, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    # Assert that the anonymous_access field is set as expected
    assert check_nodes(neo4j_session, 'S3Bucket', ['name', 'anonymous_access']) == {
        ('bucket-1', None),
        ('bucket-3', True),
        ('bucket-2', True),
    }

    # Assert that we properly set anonymous_actions on the S3Bucket based on the attached S3Acls
    # (Can't use check_nodes() here because anonymous_actions is a list and is non-hashable.)
    actual = neo4j_session.run(
        """
        MATCH (r:S3Bucket) RETURN r.name, r.anonymous_actions;
        """,
    )
    actual_nodes = [
        (n['r.name'], sorted(n['r.anonymous_actions']) if n['r.anonymous_actions'] else []) for n in actual
    ]
    assert sorted(actual_nodes) == [
        ('bucket-1', []),
        ('bucket-2', ['s3:GetBucketAcl', 's3:ListBucket', 's3:ListBucketMultipartUploads', 's3:ListBucketVersions']),
        ('bucket-3', ['s3:PutBucketAcl', 's3:PutObject']),
    ]
