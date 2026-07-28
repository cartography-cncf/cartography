from unittest.mock import patch

import requests

import cartography.intel.supabase.apikeys
import tests.data.supabase.apikeys
from tests.integration.cartography.intel.supabase.test_organizations import (
    _ensure_local_neo4j_has_test_organizations,
)
from tests.integration.cartography.intel.supabase.test_projects import (
    _ensure_local_neo4j_has_test_projects,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_ORG_SLUG = "simpson-corp"
TEST_PROJECT_REF = "nuclearplantdbaaaaaa"
TEST_BASE_URL = "https://api.fake-supabase.com"
# A later tag, so cleanup removes the nodes loaded by earlier tests in this
# module: the integration suite shares one database per test module.
TEST_CLEANUP_UPDATE_TAG = TEST_UPDATE_TAG + 1


def _common_job_parameters():
    return {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "BASE_URL": TEST_BASE_URL,
        "ORG_SLUG": TEST_ORG_SLUG,
        "PROJECT_REF": TEST_PROJECT_REF,
    }


@patch.object(
    cartography.intel.supabase.apikeys,
    "get_signing_keys",
    return_value=tests.data.supabase.apikeys.SUPABASE_SIGNING_KEYS,
)
@patch.object(
    cartography.intel.supabase.apikeys,
    "get",
    return_value=tests.data.supabase.apikeys.SUPABASE_API_KEYS,
)
def test_load_supabase_api_keys(mock_get, mock_get_signing_keys, neo4j_session):
    """
    Ensure API keys and signing keys are loaded and attached to their project.
    """
    # Arrange
    api_session = requests.Session()
    _ensure_local_neo4j_has_test_organizations(neo4j_session)
    _ensure_local_neo4j_has_test_projects(neo4j_session)

    # Act
    cartography.intel.supabase.apikeys.sync(
        neo4j_session,
        api_session,
        _common_job_parameters(),
    )

    # Assert keys exist. The legacy key has no id in the API response, so its node
    # id is synthesised from the project ref plus type.
    expected_nodes = {
        ("key-publishable-1", "default publishable", "publishable"),
        ("key-secret-1", "server key", "secret"),
        (f"{TEST_PROJECT_REF}/legacy", "anon", "legacy"),
    }
    assert (
        check_nodes(neo4j_session, "SupabaseApiKey", ["id", "name", "type"])
        == expected_nodes
    )

    # Assert signing keys exist
    expected_signing_keys = {
        ("signing-key-current", "ES256", "in_use"),
        ("signing-key-standby", "ES256", "standby"),
    }
    assert (
        check_nodes(neo4j_session, "SupabaseSigningKey", ["id", "algorithm", "status"])
        == expected_signing_keys
    )

    # Assert both are attached to the project
    assert (
        check_rels(
            neo4j_session,
            "SupabaseApiKey",
            "id",
            "SupabaseProject",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == {
            ("key-publishable-1", TEST_PROJECT_REF),
            ("key-secret-1", TEST_PROJECT_REF),
            (f"{TEST_PROJECT_REF}/legacy", TEST_PROJECT_REF),
        }
    )
    assert (
        check_rels(
            neo4j_session,
            "SupabaseSigningKey",
            "id",
            "SupabaseProject",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == {
            ("signing-key-current", TEST_PROJECT_REF),
            ("signing-key-standby", TEST_PROJECT_REF),
        }
    )


@patch.object(
    cartography.intel.supabase.apikeys,
    "get_signing_keys",
    return_value=tests.data.supabase.apikeys.SUPABASE_SIGNING_KEYS,
)
@patch.object(
    cartography.intel.supabase.apikeys,
    "get",
    return_value=tests.data.supabase.apikeys.SUPABASE_API_KEYS,
)
def test_supabase_api_keys_never_store_key_material(
    mock_get,
    mock_get_signing_keys,
    neo4j_session,
):
    """
    Ensure no key material lands on the graph. Cartography lists keys without the
    `reveal` parameter, so `api_key` is never returned, and the node schema has no
    property for it.
    """
    # Arrange
    api_session = requests.Session()
    _ensure_local_neo4j_has_test_organizations(neo4j_session)
    _ensure_local_neo4j_has_test_projects(neo4j_session)

    # Act
    cartography.intel.supabase.apikeys.sync(
        neo4j_session,
        api_session,
        _common_job_parameters(),
    )

    # Assert
    record = neo4j_session.run(
        """
        MATCH (k:SupabaseApiKey)
        WITH collect(keys(k)) AS all_keys
        RETURN [k IN reduce(acc = [], ks IN all_keys | acc + ks) WHERE k IN
                ['api_key', 'secret_jwt_template', 'public_jwk']] AS forbidden
        """,
    ).single()
    assert record["forbidden"] == []

    # The non-secret prefix and hash are kept, so the key stays identifiable.
    prefix_record = neo4j_session.run(
        """
        MATCH (k:SupabaseApiKey {id: 'key-secret-1'})
        RETURN k.prefix AS prefix, k.hash AS hash
        """,
    ).single()
    assert prefix_record["prefix"] == "sb_secret_"
    assert prefix_record["hash"] == "hash-secret-1"


@patch.object(
    cartography.intel.supabase.apikeys,
    "get_signing_keys",
    return_value=None,
)
@patch.object(
    cartography.intel.supabase.apikeys,
    "get",
    return_value=None,
)
def test_supabase_api_keys_tolerate_unavailable(
    mock_get,
    mock_get_signing_keys,
    neo4j_session,
):
    """
    Ensure a project whose key endpoints are unavailable syncs without error.
    """
    # Arrange
    api_session = requests.Session()
    _ensure_local_neo4j_has_test_organizations(neo4j_session)
    _ensure_local_neo4j_has_test_projects(neo4j_session)

    # Act
    cartography.intel.supabase.apikeys.sync(
        neo4j_session,
        api_session,
        {**_common_job_parameters(), "UPDATE_TAG": TEST_CLEANUP_UPDATE_TAG},
    )

    # Assert
    assert check_nodes(neo4j_session, "SupabaseApiKey", ["id"]) == set()
    assert check_nodes(neo4j_session, "SupabaseSigningKey", ["id"]) == set()


@patch.object(
    cartography.intel.supabase.apikeys,
    "get_signing_keys",
    return_value=tests.data.supabase.apikeys.SUPABASE_SIGNING_KEYS,
)
@patch.object(
    cartography.intel.supabase.apikeys,
    "get",
    return_value=tests.data.supabase.apikeys.SUPABASE_API_KEYS,
)
def test_supabase_api_key_ontology_labels(
    mock_get,
    mock_get_signing_keys,
    neo4j_session,
):
    """
    Ensure the APIKey semantic label and its _ont_* properties are applied.
    """
    # Arrange
    api_session = requests.Session()
    _ensure_local_neo4j_has_test_organizations(neo4j_session)
    _ensure_local_neo4j_has_test_projects(neo4j_session)

    # Act
    cartography.intel.supabase.apikeys.sync(
        neo4j_session,
        api_session,
        _common_job_parameters(),
    )

    # Assert
    record = neo4j_session.run(
        """
        MATCH (k:SupabaseApiKey:APIKey {id: 'key-secret-1'})
        RETURN k._ont_name AS name, k._ont_source AS source
        """,
    ).single()
    assert record["name"] == "server key"
    assert record["source"] == "supabase"
