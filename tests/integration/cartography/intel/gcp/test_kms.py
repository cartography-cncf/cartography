import json
import logging
from unittest.mock import MagicMock
from unittest.mock import patch

from googleapiclient.errors import HttpError

import cartography.intel.gcp.kms as kms
from tests.data.gcp.kms import MOCK_KEY_RINGS
from tests.data.gcp.kms import MOCK_KEYS_BY_RING
from tests.data.gcp.kms import MOCK_LOCATIONS
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_PROJECT_ID = "test-project"
TEST_UPDATE_TAG = 123456789


def _make_http_error(status: int, payload: dict) -> HttpError:
    resp = MagicMock()
    resp.status = status
    return HttpError(resp=resp, content=json.dumps(payload).encode("utf-8"))


class _KeyRingListRequest:
    def __init__(self, error: HttpError):
        self.execute = MagicMock(side_effect=error)


class _KMSClientWithKeyRingListError:
    def __init__(self, request: _KeyRingListRequest):
        self._request = request

    def projects(self) -> "_KMSClientWithKeyRingListError":
        return self

    def locations(self) -> "_KMSClientWithKeyRingListError":
        return self

    def keyRings(self) -> "_KMSClientWithKeyRingListError":
        return self

    def list(self, parent: str) -> _KeyRingListRequest:
        return self._request

    def list_next(
        self,
        previous_request: _KeyRingListRequest,
        previous_response: dict,
    ) -> None:
        return None


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


def test_sync_kms_preserves_existing_data_when_billing_disabled(
    monkeypatch,
    caplog,
    neo4j_session,
):
    old_update_tag = TEST_UPDATE_TAG - 1

    neo4j_session.run(
        """
        MERGE (p:GCPProject {id: $project_id_short})
        SET p.lastupdated = $tag, p.projectid = $project_id_short
        """,
        project_id_short=TEST_PROJECT_ID,
        tag=old_update_tag,
    )

    existing_key_rings = kms.transform_key_rings(MOCK_KEY_RINGS, TEST_PROJECT_ID)
    kms.load_key_rings(
        neo4j_session,
        existing_key_rings,
        TEST_PROJECT_ID,
        old_update_tag,
    )

    for ring in MOCK_KEY_RINGS:
        keyring_id = ring["name"]
        crypto_keys = kms.transform_crypto_keys(
            MOCK_KEYS_BY_RING.get(keyring_id, []),
            keyring_id,
        )
        if crypto_keys:
            kms.load_crypto_keys(
                neo4j_session,
                crypto_keys,
                TEST_PROJECT_ID,
                old_update_tag,
            )

    billing_error = _make_http_error(
        400,
        {
            "error": {
                "message": (
                    "Billing is disabled for project 123456789. Enable it by "
                    "visiting https://console.cloud.google.com/billing/projects "
                    "and associating your project with a billing account."
                ),
                "details": [
                    {
                        "@type": "type.googleapis.com/google.rpc.PreconditionFailure",
                        "violations": [
                            {
                                "type": "BILLING_DISABLED",
                                "subject": "123456789",
                            }
                        ],
                    }
                ],
            }
        },
    )

    request = _KeyRingListRequest(billing_error)
    client = _KMSClientWithKeyRingListError(request)

    monkeypatch.setattr(
        "cartography.intel.gcp.kms.get_kms_locations",
        lambda _client, _project_id: MOCK_LOCATIONS,
    )

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "PROJECT_ID": TEST_PROJECT_ID,
    }

    with caplog.at_level(logging.WARNING):
        kms.sync(
            neo4j_session,
            client,
            TEST_PROJECT_ID,
            TEST_UPDATE_TAG,
            common_job_parameters,
        )

    expected_keyrings = {
        (MOCK_KEY_RINGS[0]["name"],),
        (MOCK_KEY_RINGS[1]["name"],),
    }
    assert check_nodes(neo4j_session, "GCPKeyRing", ["id"]) == expected_keyrings

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
    assert check_nodes(neo4j_session, "GCPCryptoKey", ["id"]) == expected_cryptokeys
    request.execute.assert_called_once_with(num_retries=5)
    assert (
        "Billing is disabled for project test-project while listing KMS key rings. "
        "Skipping KMS sync to preserve existing data."
    ) in caplog.text
