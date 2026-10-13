import cartography.intel.netlify.agentrunners
import tests.data.netlify.agentrunners

TEST_USER_ID = "5f5a5d7053c60b4be4c8784b"


def test_agent_runner_transform_drops_the_contributor_list() -> None:
    """
    `contributors` repeats the creator plus everyone who has looked at the runner, which is
    session activity rather than inventory, and Neo4j cannot store the list of objects anyway.
    """
    # Act
    runners = cartography.intel.netlify.agentrunners.transform_netlify_agent_runners(
        tests.data.netlify.agentrunners.NETLIFY_AGENT_RUNNERS,
    )

    # Assert
    assert "contributors" not in runners[0]
    assert "user" not in runners[0]
    assert runners[0]["user_id"] == TEST_USER_ID
