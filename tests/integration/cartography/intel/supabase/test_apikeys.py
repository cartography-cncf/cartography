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

    # Assert keys exist. Every node id is prefixed with the project ref, because the
    # legacy key ids the API returns are the same in every project. The "/legacy"
    # entry covers the fallback for the spec's nullable `id`.
    expected_nodes = {
        (f"{TEST_PROJECT_REF}/key-publishable-1", "default publishable", "publishable"),
        (f"{TEST_PROJECT_REF}/key-secret-1", "server key", "secret"),
        (f"{TEST_PROJECT_REF}/legacy", "anon", "legacy"),
        (f"{TEST_PROJECT_REF}/service_role", "service_role", "legacy"),
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
    assert check_rels(
        neo4j_session,
        "SupabaseApiKey",
        "id",
        "SupabaseProject",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        (f"{TEST_PROJECT_REF}/key-publishable-1", TEST_PROJECT_REF),
        (f"{TEST_PROJECT_REF}/key-secret-1", TEST_PROJECT_REF),
        (f"{TEST_PROJECT_REF}/legacy", TEST_PROJECT_REF),
        (f"{TEST_PROJECT_REF}/service_role", TEST_PROJECT_REF),
    }
    assert check_rels(
        neo4j_session,
        "SupabaseSigningKey",
        "id",
        "SupabaseProject",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        ("signing-key-current", TEST_PROJECT_REF),
        ("signing-key-standby", TEST_PROJECT_REF),
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
def test_supabase_api_keys_never_store_key_material(
    mock_get,
    mock_get_signing_keys,
    neo4j_session,
):
    """
    Ensure no key material lands on the graph.

    The live endpoint returns the full `api_key` value even without `reveal`, so
    this is the guarantee that matters: the value is dropped in transform and no
    property on any node holds it.
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

    # Belt and braces: no property value anywhere in the graph contains any of the
    # dummy key values from the fixture.
    leaked = neo4j_session.run(
        """
        MATCH (n)
        UNWIND keys(n) AS k
        WITH n[k] AS v
        WHERE valueType(v) STARTS WITH 'STRING' AND v CONTAINS 'must_be_dropped'
        RETURN count(*) AS leaked
        """,
    ).single()
    assert leaked["leaked"] == 0

    # The non-secret prefix and hash are kept, so the key stays identifiable.
    prefix_record = neo4j_session.run(
        """
        MATCH (k:SupabaseApiKey {id: $id})
        RETURN k.prefix AS prefix, k.hash AS hash
        """,
        id=f"{TEST_PROJECT_REF}/key-secret-1",
    ).single()
    assert prefix_record["prefix"] == "sb_secret_"
    assert prefix_record["hash"] == "hash-secret-1"


def test_supabase_api_keys_unavailable_keeps_existing_inventory(neo4j_session):
    """
    A tolerated status must not delete the keys already in the graph.

    "We could not read the key list" is not "this project has no keys". Running
    cleanup on the former would let a plan downgrade, a revoked token scope or a
    transient 403 silently wipe a real key inventory.
    """
    # Arrange: a successful sync first, so there is real inventory to protect.
    api_session = requests.Session()
    _ensure_local_neo4j_has_test_organizations(neo4j_session)
    _ensure_local_neo4j_has_test_projects(neo4j_session)
    with (
        patch.object(
            cartography.intel.supabase.apikeys,
            "get",
            return_value=tests.data.supabase.apikeys.SUPABASE_API_KEYS,
        ),
        patch.object(
            cartography.intel.supabase.apikeys,
            "get_signing_keys",
            return_value=tests.data.supabase.apikeys.SUPABASE_SIGNING_KEYS,
        ),
    ):
        cartography.intel.supabase.apikeys.sync(
            neo4j_session,
            api_session,
            _common_job_parameters(),
        )
    before = check_nodes(neo4j_session, "SupabaseApiKey", ["id"])
    signing_before = check_nodes(neo4j_session, "SupabaseSigningKey", ["id"])
    assert before, "arrange step should have loaded API keys"

    # Act: both endpoints go unavailable, on a later update tag so a cleanup would
    # consider every existing node stale and delete it.
    with (
        patch.object(cartography.intel.supabase.apikeys, "get", return_value=None),
        patch.object(
            cartography.intel.supabase.apikeys, "get_signing_keys", return_value=None
        ),
    ):
        cartography.intel.supabase.apikeys.sync(
            neo4j_session,
            api_session,
            {**_common_job_parameters(), "UPDATE_TAG": TEST_CLEANUP_UPDATE_TAG},
        )

    # Assert: nothing was deleted.
    assert check_nodes(neo4j_session, "SupabaseApiKey", ["id"]) == before
    assert check_nodes(neo4j_session, "SupabaseSigningKey", ["id"]) == signing_before


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
        MATCH (k:SupabaseApiKey:APIKey {id: $id})
        RETURN k._ont_name AS name, k._ont_source AS source
        """,
        id=f"{TEST_PROJECT_REF}/key-secret-1",
    ).single()
    assert record["name"] == "server key"
    assert record["source"] == "supabase"


@patch.object(
    cartography.intel.supabase.apikeys,
    "get_signing_keys",
    return_value=None,
)
@patch.object(
    cartography.intel.supabase.apikeys,
    "get",
    return_value=tests.data.supabase.apikeys.SUPABASE_API_KEYS,
)
def test_supabase_legacy_api_keys_do_not_merge_across_projects(
    mock_get,
    mock_get_signing_keys,
    neo4j_session,
):
    """
    The API returns "anon" and "service_role" as the ids of the legacy keys, which
    are identical in every project. Node ids must therefore be scoped to the
    project, or two projects would collapse onto one node whose metadata each sync
    overwrites and which both projects point at.
    """
    # Arrange: two projects in the same organization, both with legacy keys.
    api_session = requests.Session()
    _ensure_local_neo4j_has_test_organizations(neo4j_session)
    _ensure_local_neo4j_has_test_projects(neo4j_session)
    other_project_ref = "kwikemartdbbbbbbbbbb"

    # Act
    for ref in (TEST_PROJECT_REF, other_project_ref):
        cartography.intel.supabase.apikeys.sync(
            neo4j_session,
            api_session,
            {**_common_job_parameters(), "PROJECT_REF": ref},
        )

    # Assert each project has its own service_role node.
    service_role_nodes = {
        row[0]
        for row in check_nodes(neo4j_session, "SupabaseApiKey", ["id"])
        if row[0].endswith("/service_role")
    }
    assert service_role_nodes == {
        f"{TEST_PROJECT_REF}/service_role",
        f"{other_project_ref}/service_role",
    }

    # And no key node is shared between the two projects.
    shared = neo4j_session.run(
        """
        MATCH (p:SupabaseProject)-[:RESOURCE]->(k:SupabaseApiKey)
        WITH k, count(DISTINCT p) AS projects
        WHERE projects > 1
        RETURN count(k) AS shared
        """,
    ).single()
    assert shared["shared"] == 0
