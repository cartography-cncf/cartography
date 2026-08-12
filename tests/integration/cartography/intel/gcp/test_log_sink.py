from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.gcp.log_sink
from tests.data.gcp.log_sink import FOLDER_LOG_SINKS
from tests.data.gcp.log_sink import ORG_LOG_SINKS
from tests.data.gcp.log_sink import PROJECT_LOG_SINKS
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_ORG_ID = "organizations/123456789012"
TEST_FOLDER_ID = "folders/987654321098"
TEST_PROJECT_ID = "test-project"


def _create_prerequisite_nodes(neo4j_session):
    neo4j_session.run(
        "MERGE (o:GCPOrganization {id: $org_id}) SET o.lastupdated = $tag",
        org_id=TEST_ORG_ID,
        tag=TEST_UPDATE_TAG,
    )
    neo4j_session.run(
        "MERGE (f:GCPFolder {id: $folder_id}) SET f.lastupdated = $tag",
        folder_id=TEST_FOLDER_ID,
        tag=TEST_UPDATE_TAG,
    )
    neo4j_session.run(
        "MERGE (p:GCPProject {id: $project_id}) SET p.lastupdated = $tag",
        project_id=TEST_PROJECT_ID,
        tag=TEST_UPDATE_TAG,
    )
    neo4j_session.run(
        "MERGE (d:GCPBigQueryDataset {id: $dataset_id}) SET d.lastupdated = $tag",
        dataset_id="log-project:audit_logs",
        tag=TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.gcp.log_sink,
    "get_org_log_sinks",
    return_value=ORG_LOG_SINKS,
)
@patch.object(
    cartography.intel.gcp.log_sink,
    "get_folder_log_sinks",
    return_value=FOLDER_LOG_SINKS,
)
@patch.object(
    cartography.intel.gcp.log_sink,
    "get_project_log_sinks",
    return_value=PROJECT_LOG_SINKS,
)
def test_sync_gcp_log_sinks(
    mock_get_project_log_sinks,
    mock_get_folder_log_sinks,
    mock_get_org_log_sinks,
    neo4j_session,
):
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _create_prerequisite_nodes(neo4j_session)
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ORG_RESOURCE_NAME": TEST_ORG_ID,
        "PROJECT_ID": TEST_PROJECT_ID,
    }

    cartography.intel.gcp.log_sink.sync_gcp_log_sinks(
        neo4j_session,
        MagicMock(),
        TEST_ORG_ID,
        [{"name": TEST_FOLDER_ID}],
        [{"projectId": TEST_PROJECT_ID}],
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    assert check_nodes(
        neo4j_session,
        "GCPLogSink",
        [
            "id",
            "parent_type",
            "parent_id",
            "disabled",
            "include_children",
            "bigquery_dataset_id",
        ],
    ) == {
        (
            "organizations/123456789012/sinks/org-audit-sink",
            "organization",
            TEST_ORG_ID,
            False,
            True,
            "log-project:audit_logs",
        ),
        (
            "folders/987654321098/sinks/folder-disabled-sink",
            "folder",
            TEST_FOLDER_ID,
            True,
            False,
            None,
        ),
        (
            "projects/test-project/sinks/project-system-event-sink",
            "project",
            f"projects/{TEST_PROJECT_ID}",
            False,
            False,
            None,
        ),
    }

    assert check_rels(
        neo4j_session,
        "GCPOrganization",
        "id",
        "GCPLogSink",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_ORG_ID, "organizations/123456789012/sinks/org-audit-sink"),
    }

    assert check_rels(
        neo4j_session,
        "GCPFolder",
        "id",
        "GCPLogSink",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_FOLDER_ID, "folders/987654321098/sinks/folder-disabled-sink"),
    }

    assert check_rels(
        neo4j_session,
        "GCPProject",
        "id",
        "GCPLogSink",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_PROJECT_ID, "projects/test-project/sinks/project-system-event-sink"),
    }

    assert check_rels(
        neo4j_session,
        "GCPLogSink",
        "id",
        "GCPBigQueryDataset",
        "id",
        "DELIVERS_TO",
        rel_direction_right=True,
    ) == {
        (
            "organizations/123456789012/sinks/org-audit-sink",
            "log-project:audit_logs",
        ),
    }
