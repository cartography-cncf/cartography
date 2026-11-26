from unittest.mock import Mock

import pytest

from cartography.intel.duo.api_host import sync_duo_api_host
from cartography.intel.duo.endpoints import sync_duo_endpoints
from cartography.intel.duo.users import sync_duo_users
from tests.data.duo.endpoints import GET_ENDPOINTS_RESPONSE
from tests.data.duo.users import GET_USERS_RESPONSE
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_API_HOSTNAME = "https://api-1234.duo.com"
COMMON_JOB_PARAMETERS = {
    "DUO_API_HOSTNAME": TEST_API_HOSTNAME,
    "UPDATE_TAG": TEST_UPDATE_TAG,
}


def test_sync_duo_endpoints(neo4j_session):
    # Arrange
    mock_client = Mock(
        get_users=Mock(return_value=GET_USERS_RESPONSE),
        get_endpoints=Mock(return_value=GET_ENDPOINTS_RESPONSE),
    )

    # Act
    sync_duo_api_host(neo4j_session, COMMON_JOB_PARAMETERS)
    sync_duo_users(mock_client, neo4j_session, COMMON_JOB_PARAMETERS)
    sync_duo_endpoints(mock_client, neo4j_session, COMMON_JOB_PARAMETERS)

    # Assert
    assert check_nodes(
        neo4j_session,
        "DuoEndpoint",
        ["id", "epkey", "os_family", "email", "username"],
    ) == {
        ("epkey1", "epkey1", "iOS", "mbsimpson@simpson.corp", "mbsimpson"),
        ("epkey2", "epkey2", "iOS", "hjsimpson@simpson.corp", "hjsimpson"),
        ("epkey3", "epkey3", "iOS", "lmsimpson@simpson.corp", "lmsimpson"),
        ("epkey4", "epkey4", "iOS", "bjsimpson@simpson.corp", "bjsimpson"),
        ("epkey5", "epkey5", "iOS", "email5@example.com", "username5"),
    }

    assert check_rels(
        neo4j_session,
        "DuoApiHost",
        "id",
        "DuoEndpoint",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_API_HOSTNAME, "epkey1"),
        (TEST_API_HOSTNAME, "epkey2"),
        (TEST_API_HOSTNAME, "epkey3"),
        (TEST_API_HOSTNAME, "epkey4"),
        (TEST_API_HOSTNAME, "epkey5"),
    }

    assert check_rels(
        neo4j_session,
        "DuoUser",
        "id",
        "DuoEndpoint",
        "id",
        "HAS_DUO_ENDPOINT",
        rel_direction_right=True,
    ) == {
        ("userid1", "epkey1"),
        ("userid2", "epkey2"),
        ("userid3", "epkey3"),
        ("userid4", "epkey4"),
    }


@pytest.mark.parametrize("email", ["", None, " \t "])
@pytest.mark.parametrize(
    "sync_functions",
    [
        (sync_duo_users, sync_duo_endpoints),
        (sync_duo_endpoints, sync_duo_users),
    ],
    ids=["users-first", "endpoints-first"],
)
def test_sync_duo_endpoints_with_blank_emails(neo4j_session, email, sync_functions):
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n").consume()
    users = [{**user, "email": email} for user in GET_USERS_RESPONSE[:2]]
    endpoints = [
        {**endpoint, "email": email} for endpoint in GET_ENDPOINTS_RESPONSE[:2]
    ]
    mock_client = Mock(
        get_users=Mock(return_value=users),
        get_endpoints=Mock(return_value=endpoints),
    )
    sync_duo_api_host(neo4j_session, COMMON_JOB_PARAMETERS)

    # Act
    for sync_function in sync_functions:
        sync_function(mock_client, neo4j_session, COMMON_JOB_PARAMETERS)

    # Assert
    assert check_nodes(neo4j_session, "DuoUser", ["id"]) == {
        ("userid1",),
        ("userid2",),
    }
    assert check_nodes(neo4j_session, "DuoEndpoint", ["id"]) == {
        ("epkey1",),
        ("epkey2",),
    }
    assert (
        check_rels(
            neo4j_session,
            "DuoUser",
            "id",
            "DuoEndpoint",
            "id",
            "HAS_DUO_ENDPOINT",
            rel_direction_right=True,
        )
        == set()
    )


@pytest.mark.parametrize("sync_function", [sync_duo_users, sync_duo_endpoints])
def test_sync_duo_cleans_up_blank_email_ownership(neo4j_session, sync_function):
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n").consume()
    mock_client = Mock(
        get_users=Mock(
            return_value=[{**user, "email": ""} for user in GET_USERS_RESPONSE[:2]],
        ),
        get_endpoints=Mock(
            return_value=[
                {**endpoint, "email": ""} for endpoint in GET_ENDPOINTS_RESPONSE[:2]
            ],
        ),
    )
    sync_duo_api_host(neo4j_session, COMMON_JOB_PARAMETERS)
    sync_duo_users(mock_client, neo4j_session, COMMON_JOB_PARAMETERS)
    sync_duo_endpoints(mock_client, neo4j_session, COMMON_JOB_PARAMETERS)
    # Reproduce the graph left by an older sync, including its empty emails.
    neo4j_session.run(
        """
        MATCH (u:DuoUser), (e:DuoEndpoint)
        SET u.email = '', e.email = ''
        MERGE (u)-[r:HAS_DUO_ENDPOINT]->(e)
        SET r.lastupdated = $update_tag
        """,
        update_tag=TEST_UPDATE_TAG,
    ).consume()
    next_job_parameters = {
        **COMMON_JOB_PARAMETERS,
        "UPDATE_TAG": TEST_UPDATE_TAG + 1,
    }

    # Act
    sync_function(mock_client, neo4j_session, next_job_parameters)

    # Assert
    assert check_nodes(neo4j_session, "DuoUser", ["id"]) == {
        ("userid1",),
        ("userid2",),
    }
    assert check_nodes(neo4j_session, "DuoEndpoint", ["id"]) == {
        ("epkey1",),
        ("epkey2",),
    }
    assert (
        check_rels(
            neo4j_session,
            "DuoUser",
            "id",
            "DuoEndpoint",
            "id",
            "HAS_DUO_ENDPOINT",
            rel_direction_right=True,
        )
        == set()
    )
