import cartography.intel.aws.organizations
from tests.data.aws.organizations import TEST_ACCOUNTS
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


def test_sync_aws_accounts(neo4j_session):
    """
    Ensure that sync() creates AWSAccount and AWSRootPrincipal nodes.
    """
    cartography.intel.aws.organizations.sync(
        neo4j_session,
        TEST_ACCOUNTS,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    # Verify AWSAccount nodes
    assert check_nodes(neo4j_session, "AWSAccount", ["id", "name"]) == {
        ("111111111111", "test-account-1"),
        ("222222222222", "test-account-2"),
    }

    # Verify AWSRootPrincipal nodes
    assert check_nodes(neo4j_session, "AWSRootPrincipal", ["arn"]) == {
        ("arn:aws:iam::111111111111:root",),
        ("arn:aws:iam::222222222222:root",),
    }

    # Verify AWSAccount -[:RESOURCE]-> AWSRootPrincipal
    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "AWSRootPrincipal",
        "arn",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        ("111111111111", "arn:aws:iam::111111111111:root"),
        ("222222222222", "arn:aws:iam::222222222222:root"),
    }
