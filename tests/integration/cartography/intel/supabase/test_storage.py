from unittest.mock import patch

import requests

import cartography.intel.supabase.storage
import tests.data.supabase.storage
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
    cartography.intel.supabase.storage,
    "get",
    return_value=tests.data.supabase.storage.SUPABASE_STORAGE_BUCKETS,
)
def test_load_supabase_storage_buckets(mock_get, neo4j_session):
    """
    Ensure buckets are loaded with their public flag and attached to their project.
    """
    # Arrange
    api_session = requests.Session()
    _ensure_local_neo4j_has_test_organizations(neo4j_session)
    _ensure_local_neo4j_has_test_projects(neo4j_session)

    # Act
    cartography.intel.supabase.storage.sync(
        neo4j_session,
        api_session,
        _common_job_parameters(),
    )

    # Assert. Bucket ids are only unique within a project, so the node id is
    # prefixed with the project ref.
    expected_nodes = {
        (f"{TEST_PROJECT_REF}/avatars", "avatars", True),
        (f"{TEST_PROJECT_REF}/reactor-logs", "reactor-logs", False),
    }
    assert (
        check_nodes(
            neo4j_session,
            "SupabaseStorageBucket",
            ["id", "name", "public"],
        )
        == expected_nodes
    )

    # A public bucket serves every object without authentication.
    assert check_nodes(
        neo4j_session, "SupabaseStorageBucket", ["id", "exposed_internet"]
    ) == {
        (f"{TEST_PROJECT_REF}/avatars", True),
        (f"{TEST_PROJECT_REF}/reactor-logs", False),
    }

    assert check_rels(
        neo4j_session,
        "SupabaseStorageBucket",
        "id",
        "SupabaseProject",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        (f"{TEST_PROJECT_REF}/avatars", TEST_PROJECT_REF),
        (f"{TEST_PROJECT_REF}/reactor-logs", TEST_PROJECT_REF),
    }


@patch.object(
    cartography.intel.supabase.storage,
    "get",
    return_value=tests.data.supabase.storage.SUPABASE_STORAGE_BUCKETS,
)
def test_supabase_storage_bucket_ontology_labels(mock_get, neo4j_session):
    """
    Ensure the ObjectStorage semantic label and its _ont_* properties are applied,
    so the bucket is reachable from cross-provider public-storage queries.
    """
    # Arrange
    api_session = requests.Session()
    _ensure_local_neo4j_has_test_organizations(neo4j_session)
    _ensure_local_neo4j_has_test_projects(neo4j_session)

    # Act
    cartography.intel.supabase.storage.sync(
        neo4j_session,
        api_session,
        _common_job_parameters(),
    )

    # Assert
    record = neo4j_session.run(
        """
        MATCH (b:SupabaseStorageBucket:ObjectStorage {name: 'avatars'})
        RETURN b._ont_name AS name, b._ont_public AS public, b._ont_source AS source
        """,
    ).single()
    assert record["name"] == "avatars"
    assert record["public"] is True
    assert record["source"] == "supabase"


def test_supabase_storage_unavailable_keeps_existing_buckets(neo4j_session):
    """
    A tolerated status must not delete the buckets already in the graph.

    "We could not list the buckets" is not "this project has no buckets". Cleaning
    up on the former would let a revoked scope or a transient 403 erase a real
    bucket inventory, including the public ones that matter most.
    """
    # Arrange: a successful sync first, so there is real inventory to protect.
    api_session = requests.Session()
    _ensure_local_neo4j_has_test_organizations(neo4j_session)
    _ensure_local_neo4j_has_test_projects(neo4j_session)
    with patch.object(
        cartography.intel.supabase.storage,
        "get",
        return_value=tests.data.supabase.storage.SUPABASE_STORAGE_BUCKETS,
    ):
        cartography.intel.supabase.storage.sync(
            neo4j_session,
            api_session,
            _common_job_parameters(),
        )
    before = check_nodes(neo4j_session, "SupabaseStorageBucket", ["id"])
    assert before, "arrange step should have loaded buckets"

    # Act: the endpoint goes unavailable, on a later update tag so a cleanup would
    # consider every existing bucket stale and delete it.
    with patch.object(cartography.intel.supabase.storage, "get", return_value=None):
        cartography.intel.supabase.storage.sync(
            neo4j_session,
            api_session,
            {**_common_job_parameters(), "UPDATE_TAG": TEST_CLEANUP_UPDATE_TAG},
        )

    # Assert: nothing was deleted.
    assert check_nodes(neo4j_session, "SupabaseStorageBucket", ["id"]) == before
