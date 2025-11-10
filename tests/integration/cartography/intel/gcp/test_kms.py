from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.gcp.kms as kms
from tests.data.gcp.kms import MOCK_KEY_RINGS
from tests.data.gcp.kms import MOCK_KEYS_BY_RING
from tests.data.gcp.kms import MOCK_LOCATIONS
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_PROJECT_ID = "test-project"
TEST_UPDATE_TAG = 123456789


@patch("cartography.intel.gcp.kms.get_crypto_keys")
@patch("cartography.intel.gcp.kms.get_key_rings")
@patch("cartography.intel.gcp.kms.get_kms_locations")
def test_sync_kms(mock_get_locs, mock_get_rings, mock_get_keys, neo4j_session):
    """
    Test that we can correctly sync KMS KeyRings and CryptoKeys.
    """
    # Arrange: Setup mock return values
    mock_get_locs.return_value = MOCK_LOCATIONS
    mock_get_rings.return_value = MOCK_KEY_RINGS

    # Use a side effect for get_crypto_keys to return different keys based on the keyring name
    def get_keys_side_effect(client, keyring_name):
        return MOCK_KEYS_BY_RING.get(keyring_name, [])

    mock_get_keys.side_effect = get_keys_side_effect

    # Create the prerequisite GCPProject node
    neo4j_session.run(
        """
        MERGE (p:GCPProject {id: $project_id_short})
        SET p.lastupdated = $tag, p.projectid = $project_id_short
        """,
        project_id_short=TEST_PROJECT_ID,
        tag=TEST_UPDATE_TAG,
    )

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "PROJECT_ID": f"projects/{TEST_PROJECT_ID}",
    }

    # Act: Run the sync function
    kms.sync(
        neo4j_session,
        MagicMock(),
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert Nodes: Check KeyRings
    expected_keyrings = {
        (MOCK_KEY_RINGS[0]["name"],),
        (MOCK_KEY_RINGS[1]["name"],),
    }
    actual_keyrings = check_nodes(neo4j_session, "GCPKeyRing", ["id"])
    assert actual_keyrings == expected_keyrings

    # Assert Nodes: Check CryptoKeys
    expected_cryptokeys = {
        (
            "projects/test-project/locations/global/keyRings/my-global-keyring/cryptoKeys/key-one",
        ),
        (
            "projects/test-project/locations/us-central1/keyRings/my-regional-keyring/cryptoKeys/key-two",
        ),
        (
            "projects/test-project/locations/us-central1/keyRings/my-regional-keyring/cryptoKeys/key-three",
        ),
    }
    actual_cryptokeys = check_nodes(neo4j_session, "GCPCryptoKey", ["id"])
    assert actual_cryptokeys == expected_cryptokeys

    # Assert Relationships: Project -> KeyRing (:RESOURCE)
    expected_proj_keyring_rels = {
        (TEST_PROJECT_ID, MOCK_KEY_RINGS[0]["name"]),
        (TEST_PROJECT_ID, MOCK_KEY_RINGS[1]["name"]),
    }
    actual_proj_keyring_rels = check_rels(
        neo4j_session, "GCPProject", "id", "GCPKeyRing", "id", "RESOURCE"
    )
    assert actual_proj_keyring_rels == expected_proj_keyring_rels

    # Assert Relationships: KeyRing -> CryptoKey (:CONTAINS)
    expected_keyring_key_rels = {
        (
            MOCK_KEY_RINGS[0]["name"],
            "projects/test-project/locations/global/keyRings/my-global-keyring/cryptoKeys/key-one",
        ),
        (
            MOCK_KEY_RINGS[1]["name"],
            "projects/test-project/locations/us-central1/keyRings/my-regional-keyring/cryptoKeys/key-two",
        ),
        (
            MOCK_KEY_RINGS[1]["name"],
            "projects/test-project/locations/us-central1/keyRings/my-regional-keyring/cryptoKeys/key-three",
        ),
    }
    actual_keyring_key_rels = check_rels(
        neo4j_session, "GCPKeyRing", "id", "GCPCryptoKey", "id", "CONTAINS"
    )
    assert actual_keyring_key_rels == expected_keyring_key_rels

    # Assert Relationships: Project -> CryptoKey (:RESOURCE)
    expected_proj_key_rels = {
        (
            TEST_PROJECT_ID,
            "projects/test-project/locations/global/keyRings/my-global-keyring/cryptoKeys/key-one",
        ),
        (
            TEST_PROJECT_ID,
            "projects/test-project/locations/us-central1/keyRings/my-regional-keyring/cryptoKeys/key-two",
        ),
        (
            TEST_PROJECT_ID,
            "projects/test-project/locations/us-central1/keyRings/my-regional-keyring/cryptoKeys/key-three",
        ),
    }
    actual_proj_key_rels = check_rels(
        neo4j_session, "GCPProject", "id", "GCPCryptoKey", "id", "RESOURCE"
    )
    assert actual_proj_key_rels == expected_proj_key_rels
