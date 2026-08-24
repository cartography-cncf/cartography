from unittest.mock import patch

import requests

import cartography.intel.supabase.functions
import tests.data.supabase.functions
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


def _common_job_parameters():
    return {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "BASE_URL": TEST_BASE_URL,
        "ORG_SLUG": TEST_ORG_SLUG,
        "PROJECT_REF": TEST_PROJECT_REF,
    }


@patch.object(
    cartography.intel.supabase.functions,
    "get_secrets",
    return_value=tests.data.supabase.functions.SUPABASE_SECRETS,
)
@patch.object(
    cartography.intel.supabase.functions,
    "get",
    return_value=tests.data.supabase.functions.SUPABASE_EDGE_FUNCTIONS,
)
def test_load_supabase_edge_functions(mock_get, mock_get_secrets, neo4j_session):
    """
    Ensure edge functions are loaded with their JWT verification flag and attached
    to their project.
    """
    # Arrange
    api_session = requests.Session()
    _ensure_local_neo4j_has_test_organizations(neo4j_session)
    _ensure_local_neo4j_has_test_projects(neo4j_session)

    # Act
    cartography.intel.supabase.functions.sync(
        neo4j_session,
        api_session,
        _common_job_parameters(),
    )

    # Assert
    expected_nodes = {
        ("fn-meltdown-alert", "meltdown-alert", "ACTIVE", True),
        ("fn-public-webhook", "public-webhook", "ACTIVE", False),
    }
    assert (
        check_nodes(
            neo4j_session,
            "SupabaseEdgeFunction",
            ["id", "slug", "status", "verify_jwt"],
        )
        == expected_nodes
    )

    # verify_jwt False means the function is invokable without a project JWT.
    assert check_nodes(
        neo4j_session, "SupabaseEdgeFunction", ["id", "exposed_internet"]
    ) == {
        ("fn-meltdown-alert", False),
        ("fn-public-webhook", True),
    }

    assert check_rels(
        neo4j_session,
        "SupabaseEdgeFunction",
        "id",
        "SupabaseProject",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        ("fn-meltdown-alert", TEST_PROJECT_REF),
        ("fn-public-webhook", TEST_PROJECT_REF),
    }


@patch.object(
    cartography.intel.supabase.functions,
    "get_secrets",
    return_value=tests.data.supabase.functions.SUPABASE_SECRETS,
)
@patch.object(
    cartography.intel.supabase.functions,
    "get",
    return_value=tests.data.supabase.functions.SUPABASE_EDGE_FUNCTIONS,
)
def test_supabase_edge_function_epoch_ms_timestamps(
    mock_get,
    mock_get_secrets,
    neo4j_session,
):
    """
    Ensure the functions endpoints' epoch-millisecond timestamps become native
    Neo4j datetimes rather than integers.
    """
    # Arrange
    api_session = requests.Session()
    _ensure_local_neo4j_has_test_organizations(neo4j_session)
    _ensure_local_neo4j_has_test_projects(neo4j_session)

    # Act
    cartography.intel.supabase.functions.sync(
        neo4j_session,
        api_session,
        _common_job_parameters(),
    )

    # Assert
    record = neo4j_session.run(
        """
        MATCH (f:SupabaseEdgeFunction {id: 'fn-meltdown-alert'})
        RETURN f.created_at AS created_at, f.updated_at AS updated_at
        """,
    ).single()
    # 1782000000000 ms == 2026-06-21T06:40:00Z
    created_at = record["created_at"].to_native()
    assert (created_at.year, created_at.month, created_at.day) == (2026, 6, 21)
    assert record["updated_at"].to_native() > created_at


@patch.object(
    cartography.intel.supabase.functions,
    "get_secrets",
    return_value=tests.data.supabase.functions.SUPABASE_SECRETS,
)
@patch.object(
    cartography.intel.supabase.functions,
    "get",
    return_value=tests.data.supabase.functions.SUPABASE_EDGE_FUNCTIONS,
)
def test_load_supabase_secrets(mock_get, mock_get_secrets, neo4j_session):
    """
    Ensure secrets are loaded by name only, with the value dropped.
    """
    # Arrange
    api_session = requests.Session()
    _ensure_local_neo4j_has_test_organizations(neo4j_session)
    _ensure_local_neo4j_has_test_projects(neo4j_session)

    # Act
    cartography.intel.supabase.functions.sync(
        neo4j_session,
        api_session,
        _common_job_parameters(),
    )

    # Assert
    expected_nodes = {
        (f"{TEST_PROJECT_REF}/SENTRY_DSN", "SENTRY_DSN"),
        (f"{TEST_PROJECT_REF}/PLANT_CONTROL_TOKEN", "PLANT_CONTROL_TOKEN"),
    }
    assert (
        check_nodes(neo4j_session, "SupabaseSecret", ["id", "name"]) == expected_nodes
    )

    # No secret value anywhere on any secret node.
    record = neo4j_session.run(
        """
        MATCH (s:SupabaseSecret)
        WITH collect(keys(s)) AS all_keys
        RETURN [k IN reduce(acc = [], ks IN all_keys | acc + ks)
                WHERE k = 'value'] AS forbidden
        """,
    ).single()
    assert record["forbidden"] == []

    assert check_rels(
        neo4j_session,
        "SupabaseSecret",
        "id",
        "SupabaseProject",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        (f"{TEST_PROJECT_REF}/SENTRY_DSN", TEST_PROJECT_REF),
        (f"{TEST_PROJECT_REF}/PLANT_CONTROL_TOKEN", TEST_PROJECT_REF),
    }


@patch.object(
    cartography.intel.supabase.functions,
    "get_secrets",
    return_value=tests.data.supabase.functions.SUPABASE_SECRETS,
)
@patch.object(
    cartography.intel.supabase.functions,
    "get",
    return_value=tests.data.supabase.functions.SUPABASE_EDGE_FUNCTIONS,
)
def test_supabase_functions_ontology_labels(mock_get, mock_get_secrets, neo4j_session):
    """
    Ensure the Function and Secret semantic labels are applied with their _ont_*
    properties.
    """
    # Arrange
    api_session = requests.Session()
    _ensure_local_neo4j_has_test_organizations(neo4j_session)
    _ensure_local_neo4j_has_test_projects(neo4j_session)

    # Act
    cartography.intel.supabase.functions.sync(
        neo4j_session,
        api_session,
        _common_job_parameters(),
    )

    # Assert
    fn_record = neo4j_session.run(
        """
        MATCH (f:SupabaseEdgeFunction:Function {id: 'fn-meltdown-alert'})
        RETURN f._ont_name AS name,
               f._ont_deployment_type AS deployment_type,
               f._ont_source AS source
        """,
    ).single()
    assert fn_record["name"] == "meltdown-alert"
    assert fn_record["deployment_type"] == "code"
    assert fn_record["source"] == "supabase"

    secret_record = neo4j_session.run(
        """
        MATCH (s:SupabaseSecret:Secret {name: 'SENTRY_DSN'})
        RETURN s._ont_name AS name, s._ont_source AS source
        """,
    ).single()
    assert secret_record["name"] == "SENTRY_DSN"
    assert secret_record["source"] == "supabase"
