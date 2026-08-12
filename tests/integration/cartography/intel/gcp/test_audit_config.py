from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.gcp.audit_config
from tests.data.gcp.audit_config import FOLDER_AUDIT_CONFIGS
from tests.data.gcp.audit_config import ORG_AUDIT_CONFIGS
from tests.data.gcp.audit_config import PROJECT_AUDIT_CONFIGS
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_ORG_ID = "organizations/123456789012"
TEST_FOLDER_ID = "folders/987654321098"
TEST_PROJECT_ID = "test-project"
TEST_PROJECT_NUMBER = "1234567890"


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


@patch.object(
    cartography.intel.gcp.audit_config,
    "get_org_audit_config",
    return_value=ORG_AUDIT_CONFIGS,
)
@patch.object(
    cartography.intel.gcp.audit_config,
    "get_folder_audit_config",
    return_value=FOLDER_AUDIT_CONFIGS,
)
@patch.object(
    cartography.intel.gcp.audit_config,
    "get_project_audit_config",
    return_value=PROJECT_AUDIT_CONFIGS,
)
def test_sync_gcp_audit_configs(
    mock_get_project_audit_config,
    mock_get_folder_audit_config,
    mock_get_org_audit_config,
    neo4j_session,
):
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _create_prerequisite_nodes(neo4j_session)
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ORG_RESOURCE_NAME": TEST_ORG_ID,
        "PROJECT_ID": TEST_PROJECT_ID,
    }

    cartography.intel.gcp.audit_config.sync_gcp_audit_configs(
        neo4j_session,
        MagicMock(),
        TEST_ORG_ID,
        [{"name": TEST_FOLDER_ID}],
        [{"projectId": TEST_PROJECT_ID, "projectNumber": TEST_PROJECT_NUMBER}],
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    assert check_nodes(
        neo4j_session,
        "GCPAuditConfig",
        [
            "id",
            "parent_type",
            "parent_id",
            "service",
            "has_admin_read",
            "has_data_read",
            "has_data_write",
        ],
    ) == {
        (
            f"{TEST_ORG_ID}/auditConfigs/allServices",
            "organization",
            TEST_ORG_ID,
            "allServices",
            True,
            True,
            True,
        ),
        (
            f"{TEST_ORG_ID}/auditConfigs/cloudtasks.googleapis.com",
            "organization",
            TEST_ORG_ID,
            "cloudtasks.googleapis.com",
            False,
            True,
            False,
        ),
        (
            f"{TEST_ORG_ID}/auditConfigs/empty.googleapis.com",
            "organization",
            TEST_ORG_ID,
            "empty.googleapis.com",
            False,
            False,
            False,
        ),
        (
            f"{TEST_ORG_ID}/auditConfigs/exempted.googleapis.com",
            "organization",
            TEST_ORG_ID,
            "exempted.googleapis.com",
            False,
            True,
            False,
        ),
        (
            f"{TEST_FOLDER_ID}/auditConfigs/allServices",
            "folder",
            TEST_FOLDER_ID,
            "allServices",
            True,
            False,
            True,
        ),
        (
            f"projects/{TEST_PROJECT_ID}/auditConfigs/cloudtasks.googleapis.com",
            "project",
            f"projects/{TEST_PROJECT_ID}",
            "cloudtasks.googleapis.com",
            False,
            True,
            True,
        ),
    }

    assert check_rels(
        neo4j_session,
        "GCPOrganization",
        "id",
        "GCPAuditConfig",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_ORG_ID, f"{TEST_ORG_ID}/auditConfigs/allServices"),
        (TEST_ORG_ID, f"{TEST_ORG_ID}/auditConfigs/cloudtasks.googleapis.com"),
        (TEST_ORG_ID, f"{TEST_ORG_ID}/auditConfigs/empty.googleapis.com"),
        (TEST_ORG_ID, f"{TEST_ORG_ID}/auditConfigs/exempted.googleapis.com"),
    }

    assert check_rels(
        neo4j_session,
        "GCPFolder",
        "id",
        "GCPAuditConfig",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_FOLDER_ID, f"{TEST_FOLDER_ID}/auditConfigs/allServices"),
    }

    assert check_rels(
        neo4j_session,
        "GCPProject",
        "id",
        "GCPAuditConfig",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (
            TEST_PROJECT_ID,
            f"projects/{TEST_PROJECT_ID}/auditConfigs/cloudtasks.googleapis.com",
        ),
    }
