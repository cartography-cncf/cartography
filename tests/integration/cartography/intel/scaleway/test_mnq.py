from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.scaleway.mnq.sqs
from tests.data.scaleway.mnq import SCALEWAY_MNQ_SQS_CREDENTIALS
from tests.data.scaleway.mnq import SCALEWAY_MNQ_SQS_INFO
from tests.data.scaleway.mnq import TEST_CREDENTIAL_ID
from tests.data.scaleway.mnq import TEST_PROJECT_ID
from tests.integration.cartography.intel.scaleway.test_projects import (
    _ensure_local_neo4j_has_test_projects_and_orgs,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_ORG_ID = "0681c477-fbb9-4820-b8d6-0eef10cfcd6d"


@patch.object(
    cartography.intel.scaleway.mnq.sqs,
    "get",
    return_value=(
        SCALEWAY_MNQ_SQS_INFO,
        SCALEWAY_MNQ_SQS_CREDENTIALS,
        [TEST_PROJECT_ID],
    ),
)
def test_load_scaleway_mnq_sqs(_mock_get, neo4j_session):
    # Arrange
    client = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ORG_ID": TEST_ORG_ID,
    }
    _ensure_local_neo4j_has_test_projects_and_orgs(neo4j_session)
    namespace_id = f"{TEST_PROJECT_ID}/fr-par"

    # Act
    cartography.intel.scaleway.mnq.sqs.sync(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=TEST_ORG_ID,
        projects_id=[TEST_PROJECT_ID],
        update_tag=TEST_UPDATE_TAG,
    )

    # Assert nodes
    assert check_nodes(neo4j_session, "ScalewayMnqSqsNamespace", ["id", "status"]) == {
        (namespace_id, "enabled"),
    }
    assert check_nodes(
        neo4j_session,
        "ScalewayMnqSqsCredential",
        ["id", "name", "can_publish", "can_receive", "can_manage"],
    ) == {
        (TEST_CREDENTIAL_ID, "demo-sqs-credentials", True, True, False),
    }

    # The credential's plaintext secret_key must never reach the graph.
    cred_props = neo4j_session.run(
        "MATCH (n:ScalewayMnqSqsCredential {id: $id}) RETURN properties(n) AS props",
        id=TEST_CREDENTIAL_ID,
    ).single()["props"]
    assert "secret_key" not in cred_props
    assert "secret_checksum" not in cred_props

    # Cross-cloud ontology label
    assert check_nodes(neo4j_session, "Secret", ["id"]) == {(TEST_CREDENTIAL_ID,)}

    # Project ownership
    assert check_rels(
        neo4j_session,
        "ScalewayMnqSqsNamespace",
        "id",
        "ScalewayProject",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {(namespace_id, TEST_PROJECT_ID)}
    assert check_rels(
        neo4j_session,
        "ScalewayMnqSqsCredential",
        "id",
        "ScalewayProject",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {(TEST_CREDENTIAL_ID, TEST_PROJECT_ID)}

    # Namespace -> Credential
    assert check_rels(
        neo4j_session,
        "ScalewayMnqSqsNamespace",
        "id",
        "ScalewayMnqSqsCredential",
        "id",
        "HAS",
        rel_direction_right=True,
    ) == {(namespace_id, TEST_CREDENTIAL_ID)}


@patch.object(
    cartography.intel.scaleway.mnq.sqs,
    "get",
    return_value=(
        SCALEWAY_MNQ_SQS_INFO,
        SCALEWAY_MNQ_SQS_CREDENTIALS,
        [TEST_PROJECT_ID],
    ),
)
def test_scaleway_mnq_sqs_cleanup_removes_stale_resources(mock_get, neo4j_session):
    # Arrange: one full sync, then everything upstream is gone.
    client = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ORG_ID": TEST_ORG_ID,
    }
    _ensure_local_neo4j_has_test_projects_and_orgs(neo4j_session)
    cartography.intel.scaleway.mnq.sqs.sync(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=TEST_ORG_ID,
        projects_id=[TEST_PROJECT_ID],
        update_tag=TEST_UPDATE_TAG,
    )

    # Act
    mock_get.return_value = (SCALEWAY_MNQ_SQS_INFO, [], [TEST_PROJECT_ID])
    common_job_parameters["UPDATE_TAG"] = TEST_UPDATE_TAG + 1
    cartography.intel.scaleway.mnq.sqs.sync(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=TEST_ORG_ID,
        projects_id=[TEST_PROJECT_ID],
        update_tag=TEST_UPDATE_TAG + 1,
    )

    # Assert: stale credentials are gone, but the namespace itself survives.
    assert check_nodes(neo4j_session, "ScalewayMnqSqsNamespace", ["id"]) == {
        (f"{TEST_PROJECT_ID}/fr-par",),
    }
    assert check_nodes(neo4j_session, "ScalewayMnqSqsCredential", ["id"]) == set()
