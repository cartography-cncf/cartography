from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.workos.application_client_secrets
import tests.data.workos.application_client_secrets
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_CLIENT_ID = "client_1234567890abcdef"
TEST_APP_IDS = [
    "conn_app_01HXYZ1111111111AAAAAAAA",
    "conn_app_02HXYZ2222222222BBBBBBBB",
]


def _ensure_local_neo4j_has_test_environment(neo4j_session):
    neo4j_session.run(
        """
        MERGE (e:WorkOSEnvironment{id: $client_id})
        ON CREATE SET e.firstseen = timestamp()
        SET e.lastupdated = $update_tag
        """,
        client_id=TEST_CLIENT_ID,
        update_tag=TEST_UPDATE_TAG,
    )


def _ensure_local_neo4j_has_test_applications(neo4j_session):
    for app_id in TEST_APP_IDS:
        neo4j_session.run(
            """
            MERGE (a:WorkOSApplication{id: $app_id})
            ON CREATE SET a.firstseen = timestamp()
            SET a.lastupdated = $update_tag
            """,
            app_id=app_id,
            update_tag=TEST_UPDATE_TAG,
        )


@patch.object(
    cartography.intel.workos.application_client_secrets,
    "get",
    return_value=tests.data.workos.application_client_secrets.WORKOS_APPLICATION_CLIENT_SECRETS_BY_APP,
)
def test_load_workos_application_client_secrets(mock_api, neo4j_session):
    # Arrange
    _ensure_local_neo4j_has_test_environment(neo4j_session)
    _ensure_local_neo4j_has_test_applications(neo4j_session)
    client = MagicMock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "WORKOS_CLIENT_ID": TEST_CLIENT_ID,
    }

    # Act
    cartography.intel.workos.application_client_secrets.sync(
        neo4j_session,
        client,
        TEST_APP_IDS,
        common_job_parameters,
    )

    # Assert secrets exist
    expected_nodes = {
        ("secret_01HXYZAAAA1111111111AAAA", "...abc1"),
        ("secret_02HXYZBBBB2222222222BBBB", "...xyz9"),
        ("secret_02HXYZCCCC3333333333CCCC", "...def2"),
    }
    assert (
        check_nodes(
            neo4j_session,
            "WorkOSApplicationClientSecret",
            ["id", "secret_hint"],
        )
        == expected_nodes
    )

    # Assert secrets are linked to the environment
    expected_env_rels = {
        ("secret_01HXYZAAAA1111111111AAAA", TEST_CLIENT_ID),
        ("secret_02HXYZBBBB2222222222BBBB", TEST_CLIENT_ID),
        ("secret_02HXYZCCCC3333333333CCCC", TEST_CLIENT_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "WorkOSApplicationClientSecret",
            "id",
            "WorkOSEnvironment",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_env_rels
    )

    # Assert secrets are linked to their parent application
    expected_app_rels = {
        (
            "secret_01HXYZAAAA1111111111AAAA",
            "conn_app_01HXYZ1111111111AAAAAAAA",
        ),
        (
            "secret_02HXYZBBBB2222222222BBBB",
            "conn_app_02HXYZ2222222222BBBBBBBB",
        ),
        (
            "secret_02HXYZCCCC3333333333CCCC",
            "conn_app_02HXYZ2222222222BBBBBBBB",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "WorkOSApplicationClientSecret",
            "id",
            "WorkOSApplication",
            "id",
            "HAS_SECRET",
            rel_direction_right=False,
        )
        == expected_app_rels
    )
