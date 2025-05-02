import cartography.intel.aws.securityhub
import tests.data.aws.securityhub

TEST_ACCOUNT_ID = "000000000000"
TEST_UPDATE_TAG = 123456789


def test_transform_and_load_hub(neo4j_session, *args):
    """
    Ensure that expected hub gets loaded with its key fields.
    """
    data = tests.data.aws.securityhub.GET_HUB
    cartography.intel.aws.securityhub.transform_hub(data)
    cartography.intel.aws.securityhub.load_hub(
        neo4j_session,
        data,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        (
            "arn:aws:securityhub:us-east-1:000000000000:hub/default",
            1606993517,
            True,
        ),
    }

    nodes = neo4j_session.run(
        """
        MATCH (n:SecurityHub)
        RETURN n.id, n.subscribed_at, n.auto_enable_controls
        """,
    )
    actual_nodes = {
        (
            n["n.id"],
            n["n.subscribed_at"],
            n["n.auto_enable_controls"],
        )
        for n in nodes
    }
    assert actual_nodes == expected_nodes
