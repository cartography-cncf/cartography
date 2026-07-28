from unittest.mock import patch

import requests

import cartography.intel.supabase.network
import tests.data.supabase.network
from tests.integration.cartography.intel.supabase.test_organizations import (
    _ensure_local_neo4j_has_test_organizations,
)
from tests.integration.cartography.intel.supabase.test_projects import (
    _ensure_local_neo4j_has_test_databases,
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


def _arrange(neo4j_session):
    _ensure_local_neo4j_has_test_organizations(neo4j_session)
    _ensure_local_neo4j_has_test_projects(neo4j_session)
    _ensure_local_neo4j_has_test_databases(neo4j_session)


@patch.object(
    cartography.intel.supabase.network,
    "get_custom_hostname",
    return_value=tests.data.supabase.network.SUPABASE_CUSTOM_HOSTNAME,
)
@patch.object(
    cartography.intel.supabase.network,
    "get",
    return_value=tests.data.supabase.network.SUPABASE_POOLERS,
)
def test_load_supabase_poolers(mock_get, mock_get_hostname, neo4j_session):
    """
    Ensure the connection pooler is loaded and linked both to its project and to
    the database it fronts.
    """
    # Arrange
    api_session = requests.Session()
    _arrange(neo4j_session)

    # Act
    cartography.intel.supabase.network.sync(
        neo4j_session,
        api_session,
        _common_job_parameters(),
    )

    # Assert
    assert check_nodes(
        neo4j_session,
        "SupabasePooler",
        ["id", "db_host", "db_port", "pool_mode", "is_using_scram_auth"],
    ) == {
        (
            f"{TEST_PROJECT_REF}/{TEST_PROJECT_REF}",
            "aws-0-us-east-2.pooler.supabase.com",
            6543,
            "transaction",
            True,
        ),
    }

    assert check_rels(
        neo4j_session,
        "SupabasePooler",
        "id",
        "SupabaseProject",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {(f"{TEST_PROJECT_REF}/{TEST_PROJECT_REF}", TEST_PROJECT_REF)}

    assert check_rels(
        neo4j_session,
        "SupabasePooler",
        "id",
        "SupabaseDatabase",
        "id",
        "CONNECTS_TO",
        rel_direction_right=True,
    ) == {
        (
            f"{TEST_PROJECT_REF}/{TEST_PROJECT_REF}",
            f"{TEST_PROJECT_REF}/postgres",
        ),
    }


@patch.object(
    cartography.intel.supabase.network,
    "get_custom_hostname",
    return_value=tests.data.supabase.network.SUPABASE_CUSTOM_HOSTNAME,
)
@patch.object(
    cartography.intel.supabase.network,
    "get",
    return_value=tests.data.supabase.network.SUPABASE_POOLERS,
)
def test_supabase_pooler_drops_connection_string(
    mock_get,
    mock_get_hostname,
    neo4j_session,
):
    """
    Ensure the credential-bearing pooler connection strings are not ingested.
    """
    # Arrange
    api_session = requests.Session()
    _arrange(neo4j_session)

    # Act
    cartography.intel.supabase.network.sync(
        neo4j_session,
        api_session,
        _common_job_parameters(),
    )

    # Assert
    record = neo4j_session.run(
        """
        MATCH (p:SupabasePooler)
        WITH collect(keys(p)) AS all_keys
        RETURN [k IN reduce(acc = [], ks IN all_keys | acc + ks)
                WHERE k IN ['connection_string', 'connectionString']] AS forbidden
        """,
    ).single()
    assert record["forbidden"] == []


@patch.object(
    cartography.intel.supabase.network,
    "get_custom_hostname",
    return_value=tests.data.supabase.network.SUPABASE_CUSTOM_HOSTNAME,
)
@patch.object(
    cartography.intel.supabase.network,
    "get",
    return_value=tests.data.supabase.network.SUPABASE_POOLERS,
)
def test_load_supabase_custom_hostname(mock_get, mock_get_hostname, neo4j_session):
    """
    Ensure the custom hostname is loaded with its TLS status and points at the
    project it fronts.
    """
    # Arrange
    api_session = requests.Session()
    _arrange(neo4j_session)

    # Act
    cartography.intel.supabase.network.sync(
        neo4j_session,
        api_session,
        _common_job_parameters(),
    )

    # Assert
    assert check_nodes(
        neo4j_session,
        "SupabaseCustomHostname",
        ["id", "hostname", "type", "ssl_status"],
    ) == {
        (
            f"{TEST_PROJECT_REF}/api.simpson.corp",
            "api.simpson.corp",
            "CNAME",
            "active",
        ),
    }

    assert check_rels(
        neo4j_session,
        "SupabaseCustomHostname",
        "id",
        "SupabaseProject",
        "id",
        "POINTS_TO",
        rel_direction_right=True,
    ) == {(f"{TEST_PROJECT_REF}/api.simpson.corp", TEST_PROJECT_REF)}


@patch.object(
    cartography.intel.supabase.network,
    "get_custom_hostname",
    return_value=tests.data.supabase.network.SUPABASE_CUSTOM_HOSTNAME_UNSET,
)
@patch.object(
    cartography.intel.supabase.network,
    "get",
    return_value=tests.data.supabase.network.SUPABASE_POOLERS,
)
def test_supabase_custom_hostname_not_configured(
    mock_get,
    mock_get_hostname,
    neo4j_session,
):
    """
    Ensure a 200 response with an empty custom hostname config produces no node.
    """
    # Arrange
    api_session = requests.Session()
    _arrange(neo4j_session)

    # Act
    cartography.intel.supabase.network.sync(
        neo4j_session,
        api_session,
        {**_common_job_parameters(), "UPDATE_TAG": TEST_CLEANUP_UPDATE_TAG},
    )

    # Assert
    assert check_nodes(neo4j_session, "SupabaseCustomHostname", ["id"]) == set()
    # The pooler still loaded.
    assert check_nodes(neo4j_session, "SupabasePooler", ["id"]) != set()


def test_supabase_network_unavailable_keeps_existing_inventory(neo4j_session):
    """
    A tolerated status must not delete the poolers and hostnames already in the
    graph.

    Both endpoints are plan-gated, so an expiring add-on must not erase the record
    of a reachable database endpoint or a live custom domain.
    """
    # Arrange: a successful sync first, so there is real inventory to protect.
    api_session = requests.Session()
    _arrange(neo4j_session)
    with (
        patch.object(
            cartography.intel.supabase.network,
            "get",
            return_value=tests.data.supabase.network.SUPABASE_POOLERS,
        ),
        patch.object(
            cartography.intel.supabase.network,
            "get_custom_hostname",
            return_value=tests.data.supabase.network.SUPABASE_CUSTOM_HOSTNAME,
        ),
    ):
        cartography.intel.supabase.network.sync(
            neo4j_session,
            api_session,
            _common_job_parameters(),
        )
    poolers_before = check_nodes(neo4j_session, "SupabasePooler", ["id"])
    hostnames_before = check_nodes(neo4j_session, "SupabaseCustomHostname", ["id"])
    assert poolers_before and hostnames_before, "arrange step should have loaded both"

    # Act: both endpoints go unavailable, on a later update tag so a cleanup would
    # consider every existing node stale and delete it.
    with (
        patch.object(cartography.intel.supabase.network, "get", return_value=None),
        patch.object(
            cartography.intel.supabase.network, "get_custom_hostname", return_value=None
        ),
    ):
        cartography.intel.supabase.network.sync(
            neo4j_session,
            api_session,
            {**_common_job_parameters(), "UPDATE_TAG": TEST_CLEANUP_UPDATE_TAG + 1},
        )

    # Assert: nothing was deleted.
    assert check_nodes(neo4j_session, "SupabasePooler", ["id"]) == poolers_before
    assert (
        check_nodes(neo4j_session, "SupabaseCustomHostname", ["id"]) == hostnames_before
    )


@patch.object(
    cartography.intel.supabase.network,
    "get_custom_hostname",
    return_value=tests.data.supabase.network.SUPABASE_CUSTOM_HOSTNAME,
)
@patch.object(
    cartography.intel.supabase.network,
    "get",
    return_value=tests.data.supabase.network.SUPABASE_POOLERS,
)
def test_supabase_custom_hostname_ontology_labels(
    mock_get,
    mock_get_hostname,
    neo4j_session,
):
    """
    Ensure the DNSRecord semantic label and its _ont_* properties are applied.
    """
    # Arrange
    api_session = requests.Session()
    _arrange(neo4j_session)

    # Act
    cartography.intel.supabase.network.sync(
        neo4j_session,
        api_session,
        _common_job_parameters(),
    )

    # Assert
    record = neo4j_session.run(
        """
        MATCH (h:SupabaseCustomHostname:DNSRecord {hostname: 'api.simpson.corp'})
        RETURN h._ont_name AS name, h._ont_type AS type, h._ont_source AS source
        """,
    ).single()
    assert record["name"] == "api.simpson.corp"
    assert record["type"] == "CNAME"
    assert record["source"] == "supabase"
