from unittest.mock import patch

import cartography.intel.snowflake.authentication_policies
import cartography.intel.snowflake.data_policies
import cartography.intel.snowflake.password_policies
import cartography.intel.snowflake.policy_references
import cartography.intel.snowflake.session_policies
from cartography.intel.snowflake.util import sf_fqn
from cartography.intel.snowflake.util import sf_id
from tests.data.snowflake.account import SNOWFLAKE_ACCOUNT_ID
from tests.data.snowflake.authentication_policies import (
    SNOWFLAKE_AUTHENTICATION_POLICIES,
)
from tests.data.snowflake.data_policies import SNOWFLAKE_DATA_POLICIES
from tests.data.snowflake.password_policies import SNOWFLAKE_PASSWORD_POLICIES
from tests.data.snowflake.policy_references import SNOWFLAKE_POLICY_REFERENCES
from tests.data.snowflake.session_policies import SNOWFLAKE_SESSION_POLICIES
from tests.integration.cartography.intel.snowflake.test_account import (
    _ensure_local_neo4j_has_test_account,
)
from tests.integration.cartography.intel.snowflake.test_account import build_test_client
from tests.integration.cartography.intel.snowflake.test_account import TEST_UPDATE_TAG
from tests.integration.cartography.intel.snowflake.test_users import (
    _ensure_local_neo4j_has_test_users,
)
from tests.integration.util import check_rels


def _ensure_local_neo4j_has_test_policies(neo4j_session) -> None:
    """Load one policy of each kind through its own loader.

    The attachment edges are keyed on the policy node ids, so they have to be built
    the same way the policy syncs build them rather than restated here.
    """
    modules_and_data = (
        (
            cartography.intel.snowflake.data_policies,
            cartography.intel.snowflake.data_policies.load_data_policies,
            SNOWFLAKE_DATA_POLICIES,
        ),
        (
            cartography.intel.snowflake.password_policies,
            cartography.intel.snowflake.password_policies.load_password_policies,
            SNOWFLAKE_PASSWORD_POLICIES,
        ),
        (
            cartography.intel.snowflake.session_policies,
            cartography.intel.snowflake.session_policies.load_session_policies,
            SNOWFLAKE_SESSION_POLICIES,
        ),
        (
            cartography.intel.snowflake.authentication_policies,
            cartography.intel.snowflake.authentication_policies.load_authentication_policies,
            SNOWFLAKE_AUTHENTICATION_POLICIES,
        ),
    )
    for module, loader, payload in modules_and_data:
        loader(
            neo4j_session,
            module.transform(payload, SNOWFLAKE_ACCOUNT_ID),
            SNOWFLAKE_ACCOUNT_ID,
            TEST_UPDATE_TAG,
        )


def _seed_protected_table(neo4j_session) -> None:
    neo4j_session.run(
        """
        MERGE (t:SnowflakeTable:SnowflakeSecurable {id: $table_id})
          SET t.name = 'REACTOR_READINGS', t.lastupdated = $update_tag
        """,
        table_id=sf_id(
            SNOWFLAKE_ACCOUNT_ID,
            "table",
            sf_fqn("SPRINGFIELD", "NUCLEAR_PLANT", "REACTOR_READINGS"),
        ),
        update_tag=TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.snowflake.policy_references,
    "get",
    return_value=SNOWFLAKE_POLICY_REFERENCES,
)
def test_sync_snowflake_policy_references(mock_get, neo4j_session):
    # Arrange
    client = build_test_client()
    _ensure_local_neo4j_has_test_account(neo4j_session)
    _ensure_local_neo4j_has_test_users(neo4j_session)
    _ensure_local_neo4j_has_test_policies(neo4j_session)
    _seed_protected_table(neo4j_session)
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID,
    }

    # Act
    complete = cartography.intel.snowflake.policy_references.sync(
        neo4j_session, client, common_job_parameters
    )

    # Assert
    assert complete is True
    # Two rows name the same policy and table for different columns, and they have
    # to collapse into one edge.
    assert check_rels(
        neo4j_session,
        "SnowflakeDataPolicy",
        "name",
        "SnowflakeTable",
        "name",
        "APPLIED_TO",
        rel_direction_right=True,
    ) == {("MASK_EMPLOYEE_ID", "REACTOR_READINGS")}

    # An account-wide authentication policy attaches to the account node, not to the
    # locator the view reports.
    assert check_rels(
        neo4j_session,
        "SnowflakeAuthenticationPolicy",
        "name",
        "SnowflakeAccount",
        "id",
        "APPLIED_TO",
        rel_direction_right=True,
    ) == {("REQUIRE_MFA", SNOWFLAKE_ACCOUNT_ID)}

    assert check_rels(
        neo4j_session,
        "SnowflakePasswordPolicy",
        "name",
        "SnowflakeUser",
        "name",
        "APPLIED_TO",
        rel_direction_right=True,
    ) == {("STRICT_PASSWORDS", "HOMER")}

    assert check_rels(
        neo4j_session,
        "SnowflakeSessionPolicy",
        "name",
        "SnowflakeUser",
        "name",
        "APPLIED_TO",
        rel_direction_right=True,
    ) == {("SHORT_SESSIONS", "HOMER")}

    # The attachment's own properties are what say whether the policy is actually in
    # force and which column it protects.
    attachment = neo4j_session.run(
        """
        MATCH (:SnowflakeDataPolicy {name: 'MASK_EMPLOYEE_ID'})
              -[r:APPLIED_TO]->(:SnowflakeTable)
        RETURN r.ref_entity_domain AS domain, r.ref_column_name AS column_name,
               r.policy_status AS status
        """,
    ).single()
    assert attachment["domain"] == "TABLE"
    assert attachment["column_name"] == "EMPLOYEE_ID"
    assert attachment["status"] == "ACTIVE"


def test_transform_skips_unmodelled_policy_kinds():
    """A tag-based masking attachment has no policy node, so it must be counted."""
    # Act
    edges, skipped = cartography.intel.snowflake.policy_references.transform(
        SNOWFLAKE_POLICY_REFERENCES, SNOWFLAKE_ACCOUNT_ID
    )

    # Assert
    assert skipped == 1
    assert sum(len(rows) for rows in edges.values()) == 4


@patch.object(cartography.intel.snowflake.policy_references, "get", return_value=None)
def test_sync_reports_incomplete_when_attachments_cannot_be_read(
    mock_get, neo4j_session
):
    """Losing ACCOUNT_USAGE must not delete the attachments of an earlier run."""
    # Arrange
    client = build_test_client()
    _ensure_local_neo4j_has_test_account(neo4j_session)
    neo4j_session.run("MATCH ()-[r:APPLIED_TO]->() DELETE r")
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID,
    }

    # Act
    complete = cartography.intel.snowflake.policy_references.sync(
        neo4j_session, client, common_job_parameters
    )

    # Assert
    assert complete is False
    assert (
        neo4j_session.run(
            "MATCH ()-[r:APPLIED_TO]->() RETURN count(r) AS total"
        ).single()["total"]
        == 0
    )
