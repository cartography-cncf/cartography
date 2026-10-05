from types import SimpleNamespace
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.okta.log_streams
from cartography.intel.okta.common import OktaApiError
from tests.data.okta.log_streams import LOG_STREAMS
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ORG_ID = "test-okta-org-id"
TEST_UPDATE_TAG = 123456789


def _common_job_parameters() -> dict[str, int | str]:
    return {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "OKTA_ORG_ID": TEST_ORG_ID,
    }


def _seed_graph(neo4j_session) -> None:
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    neo4j_session.run(
        """
        MERGE (org:OktaOrganization {id: $org_id})
        SET org.lastupdated = $update_tag
        MERGE (org)-[:RESOURCE]->(stale:OktaLogStream {id: 'stale-stream'})
        SET stale.lastupdated = 1
        """,
        org_id=TEST_ORG_ID,
        update_tag=TEST_UPDATE_TAG,
    )


def _log_stream_sync_metadata(neo4j_session) -> list[int]:
    return [
        record["lastupdated"]
        for record in neo4j_session.run(
            """
            MATCH (m:ModuleSyncMetadata {
                grouptype: 'OktaOrganization', syncedtype: 'OktaLogStream'
            })
            WHERE m.groupid = $org_id
            RETURN m.lastupdated AS lastupdated
            """,
            org_id=TEST_ORG_ID,
        )
    ]


@patch.object(
    cartography.intel.okta.log_streams,
    "_get_okta_log_streams",
    new_callable=AsyncMock,
)
def test_sync_okta_log_streams(mock_get_log_streams, neo4j_session) -> None:
    # Arrange
    _seed_graph(neo4j_session)
    mock_get_log_streams.return_value = LOG_STREAMS

    # Act
    cartography.intel.okta.log_streams.sync_okta_log_streams(
        MagicMock(),
        neo4j_session,
        _common_job_parameters(),
    )

    # Assert
    assert check_nodes(
        neo4j_session,
        "OktaLogStream",
        ["id", "type", "status", "aws_account_id", "splunk_host"],
    ) == {
        ("0oa-eventbridge", "aws_eventbridge", "ACTIVE", "123456789012", None),
        (
            "0oa-splunk",
            "splunk_cloud_logstreaming",
            "INACTIVE",
            None,
            "example.splunkcloud.com",
        ),
    }
    assert check_rels(
        neo4j_session,
        "OktaOrganization",
        "id",
        "OktaLogStream",
        "id",
        "RESOURCE",
    ) == {(TEST_ORG_ID, "0oa-eventbridge"), (TEST_ORG_ID, "0oa-splunk")}
    assert _log_stream_sync_metadata(neo4j_session) == [TEST_UPDATE_TAG]


@patch.object(
    cartography.intel.okta.log_streams,
    "_get_okta_log_streams",
    new_callable=AsyncMock,
)
def test_sync_okta_log_streams_skips_when_scope_missing(
    mock_get_log_streams,
    neo4j_session,
) -> None:
    # Arrange
    _seed_graph(neo4j_session)
    mock_get_log_streams.side_effect = OktaApiError(
        "/api/v1/logStreams",
        SimpleNamespace(error_code="E0000006"),
    )

    # Act
    cartography.intel.okta.log_streams.sync_okta_log_streams(
        MagicMock(),
        neo4j_session,
        _common_job_parameters(),
    )

    # Assert
    assert check_nodes(neo4j_session, "OktaLogStream", ["id"]) == {("stale-stream",)}
    assert _log_stream_sync_metadata(neo4j_session) == []
