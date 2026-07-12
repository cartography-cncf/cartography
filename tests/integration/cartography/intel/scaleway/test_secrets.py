from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.scaleway.kms.keys
import cartography.intel.scaleway.secrets.secrets
from tests.data.scaleway.kms import SCALEWAY_KEYS
from tests.data.scaleway.secrets import SCALEWAY_SECRET_VERSIONS_BY_SECRET
from tests.data.scaleway.secrets import SCALEWAY_SECRETS
from tests.data.scaleway.secrets import TEST_KEY_ID
from tests.data.scaleway.secrets import TEST_SECRET_ID
from tests.integration.cartography.intel.scaleway.test_projects import (
    _ensure_local_neo4j_has_test_projects_and_orgs,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_ORG_ID = "0681c477-fbb9-4820-b8d6-0eef10cfcd6d"
TEST_PROJECT_ID = "0681c477-fbb9-4820-b8d6-0eef10cfcd6d"


@patch.object(
    cartography.intel.scaleway.kms.keys,
    "get",
    return_value=SCALEWAY_KEYS,
)
@patch.object(
    cartography.intel.scaleway.secrets.secrets,
    "get",
    return_value=(SCALEWAY_SECRETS, SCALEWAY_SECRET_VERSIONS_BY_SECRET),
)
def test_load_scaleway_secrets(_mock_secrets_get, _mock_keys_get, neo4j_session):
    # Arrange
    client = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ORG_ID": TEST_ORG_ID,
    }
    _ensure_local_neo4j_has_test_projects_and_orgs(neo4j_session)

    # Act: load keys first so the Secret -> Key ENCRYPTED_BY edge resolves.
    cartography.intel.scaleway.kms.keys.sync(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=TEST_ORG_ID,
        projects_id=[TEST_PROJECT_ID],
        update_tag=TEST_UPDATE_TAG,
    )
    cartography.intel.scaleway.secrets.secrets.sync(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=TEST_ORG_ID,
        projects_id=[TEST_PROJECT_ID],
        update_tag=TEST_UPDATE_TAG,
    )

    # Assert nodes
    assert check_nodes(neo4j_session, "ScalewaySecret", ["id", "name"]) == {
        (TEST_SECRET_ID, "demo-secret"),
    }
    assert check_nodes(neo4j_session, "ScalewaySecretVersion", ["id", "revision"]) == {
        (f"{TEST_SECRET_ID}/1", 1),
    }
    assert check_nodes(neo4j_session, "ScalewayKey", ["id", "name"]) == {
        (TEST_KEY_ID, "demo-key"),
    }

    # Cross-cloud ontology labels
    assert check_nodes(neo4j_session, "Secret", ["id"]) == {(TEST_SECRET_ID,)}
    assert check_nodes(neo4j_session, "EncryptionKey", ["id"]) == {(TEST_KEY_ID,)}

    # Project ownership
    for label in ("ScalewaySecret", "ScalewaySecretVersion", "ScalewayKey"):
        assert check_rels(
            neo4j_session,
            label,
            "id",
            "ScalewayProject",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        ), f"{label} not linked to project"

    # Secret -> Version
    assert check_rels(
        neo4j_session,
        "ScalewaySecret",
        "id",
        "ScalewaySecretVersion",
        "id",
        "HAS",
        rel_direction_right=True,
    ) == {(TEST_SECRET_ID, f"{TEST_SECRET_ID}/1")}

    # Secret -> Key (ENCRYPTED_BY)
    assert check_rels(
        neo4j_session,
        "ScalewaySecret",
        "id",
        "ScalewayKey",
        "id",
        "ENCRYPTED_BY",
        rel_direction_right=True,
    ) == {(TEST_SECRET_ID, TEST_KEY_ID)}
