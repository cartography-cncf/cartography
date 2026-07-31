from unittest.mock import patch

import requests

import cartography.intel.supabase.advisors
import tests.data.supabase.advisors
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

_RLS_FINDING_ID = f"{TEST_PROJECT_REF}/rls_disabled_in_public_public_reactor_readings"
_VIEW_FINDING_ID = f"{TEST_PROJECT_REF}/security_definer_view_public_employee_summary"


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
    cartography.intel.supabase.advisors,
    "get",
    return_value=tests.data.supabase.advisors.SUPABASE_SECURITY_ADVISORS,
)
def test_load_supabase_security_advisor_findings(mock_get, neo4j_session):
    """
    Ensure advisor lints are loaded with their affected database entity and attached
    to the project.
    """
    # Arrange
    api_session = requests.Session()
    _arrange(neo4j_session)

    # Act
    cartography.intel.supabase.advisors.sync(
        neo4j_session,
        api_session,
        _common_job_parameters(),
    )

    # Assert
    expected_nodes = {
        (
            _RLS_FINDING_ID,
            "rls_disabled_in_public",
            "ERROR",
            "EXTERNAL",
            "public.reactor_readings",
        ),
        (
            _VIEW_FINDING_ID,
            "security_definer_view",
            "WARN",
            "EXTERNAL",
            "public.employee_summary",
        ),
    }
    assert (
        check_nodes(
            neo4j_session,
            "SupabaseSecurityAdvisorFinding",
            ["id", "name", "level", "facing", "entity"],
        )
        == expected_nodes
    )

    assert check_rels(
        neo4j_session,
        "SupabaseSecurityAdvisorFinding",
        "id",
        "SupabaseProject",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        (_RLS_FINDING_ID, TEST_PROJECT_REF),
        (_VIEW_FINDING_ID, TEST_PROJECT_REF),
    }


@patch.object(
    cartography.intel.supabase.advisors,
    "get",
    return_value=tests.data.supabase.advisors.SUPABASE_SECURITY_ADVISORS,
)
def test_supabase_advisor_findings_affect_database(mock_get, neo4j_session):
    """
    Ensure findings are linked to the database they were raised against.
    """
    # Arrange
    api_session = requests.Session()
    _arrange(neo4j_session)

    # Act
    cartography.intel.supabase.advisors.sync(
        neo4j_session,
        api_session,
        _common_job_parameters(),
    )

    # Assert
    assert check_rels(
        neo4j_session,
        "SupabaseSecurityAdvisorFinding",
        "id",
        "SupabaseDatabase",
        "id",
        "AFFECTS",
        rel_direction_right=True,
    ) == {
        (_RLS_FINDING_ID, f"{TEST_PROJECT_REF}/postgres"),
        (_VIEW_FINDING_ID, f"{TEST_PROJECT_REF}/postgres"),
    }


@patch.object(
    cartography.intel.supabase.advisors,
    "get",
    return_value=tests.data.supabase.advisors.SUPABASE_SECURITY_ADVISORS,
)
def test_supabase_advisor_finding_ontology_labels(mock_get, neo4j_session):
    """
    Ensure the SecurityIssue semantic label is applied and the advisor level is
    normalised onto the shared severity scale.
    """
    # Arrange
    api_session = requests.Session()
    _arrange(neo4j_session)

    # Act
    cartography.intel.supabase.advisors.sync(
        neo4j_session,
        api_session,
        _common_job_parameters(),
    )

    # Assert ERROR normalises to high
    error_record = neo4j_session.run(
        """
        MATCH (f:SupabaseSecurityAdvisorFinding:SecurityIssue {id: $id})
        RETURN f._ont_title AS title,
               f._ont_type AS type,
               f._ont_severity AS severity,
               f._ont_source AS source
        """,
        id=_RLS_FINDING_ID,
    ).single()
    assert error_record["title"] == "RLS Disabled in Public"
    assert error_record["type"] == "rls_disabled_in_public"
    assert error_record["severity"] == "high"
    assert error_record["source"] == "supabase"

    # Assert WARN normalises to medium
    warn_record = neo4j_session.run(
        """
        MATCH (f:SupabaseSecurityAdvisorFinding:SecurityIssue {id: $id})
        RETURN f._ont_severity AS severity
        """,
        id=_VIEW_FINDING_ID,
    ).single()
    assert warn_record["severity"] == "medium"


def test_supabase_advisors_unavailable_keeps_existing_findings(neo4j_session):
    """
    A tolerated status must not delete the findings already in the graph.

    Silently dropping open security findings because the advisor endpoint was
    briefly unreadable would turn a read failure into a clean bill of health.
    """
    # Arrange: a successful sync first, so there is real inventory to protect.
    api_session = requests.Session()
    _arrange(neo4j_session)
    with patch.object(
        cartography.intel.supabase.advisors,
        "get",
        return_value=tests.data.supabase.advisors.SUPABASE_SECURITY_ADVISORS,
    ):
        cartography.intel.supabase.advisors.sync(
            neo4j_session,
            api_session,
            _common_job_parameters(),
        )
    before = check_nodes(neo4j_session, "SupabaseSecurityAdvisorFinding", ["id"])
    assert before, "arrange step should have loaded findings"

    # Act: the endpoint goes unavailable, on a later update tag so a cleanup would
    # consider every existing finding stale and delete it.
    with patch.object(cartography.intel.supabase.advisors, "get", return_value=None):
        cartography.intel.supabase.advisors.sync(
            neo4j_session,
            api_session,
            {**_common_job_parameters(), "UPDATE_TAG": TEST_CLEANUP_UPDATE_TAG},
        )

    # Assert: nothing was deleted.
    assert (
        check_nodes(neo4j_session, "SupabaseSecurityAdvisorFinding", ["id"]) == before
    )
