from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.huntress.account
import cartography.intel.huntress.agents
import cartography.intel.huntress.incident_reports
import cartography.intel.huntress.memberships
import cartography.intel.huntress.organizations
from tests.data.huntress.account import ACCOUNT
from tests.data.huntress.agents import AGENTS
from tests.data.huntress.incident_reports import INCIDENT_REPORTS
from tests.data.huntress.memberships import MEMBERSHIPS
from tests.data.huntress.organizations import ORGANIZATIONS
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_ACCOUNT_ID = 1000
TEST_BASE_URI = "https://api.huntress.io"


def _sync_everything(neo4j_session, update_tag: int = TEST_UPDATE_TAG) -> None:
    api_session = MagicMock()
    account_id = cartography.intel.huntress.account.sync(
        neo4j_session,
        api_session,
        TEST_BASE_URI,
        update_tag,
    )
    args = (
        neo4j_session,
        api_session,
        TEST_BASE_URI,
        account_id,
        update_tag,
        {"UPDATE_TAG": update_tag, "ACCOUNT_ID": account_id},
    )
    cartography.intel.huntress.organizations.sync(*args)
    cartography.intel.huntress.agents.sync(*args)
    cartography.intel.huntress.incident_reports.sync(*args)
    cartography.intel.huntress.memberships.sync(*args)


@patch.object(cartography.intel.huntress.account, "get", return_value=ACCOUNT)
@patch.object(
    cartography.intel.huntress.organizations, "get", return_value=ORGANIZATIONS
)
@patch.object(cartography.intel.huntress.agents, "get", return_value=AGENTS)
@patch.object(
    cartography.intel.huntress.incident_reports, "get", return_value=INCIDENT_REPORTS
)
@patch.object(cartography.intel.huntress.memberships, "get", return_value=MEMBERSHIPS)
def test_sync_huntress(
    mock_memberships_get,
    mock_incident_reports_get,
    mock_agents_get,
    mock_organizations_get,
    mock_account_get,
    neo4j_session,
):
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")

    # Act
    _sync_everything(neo4j_session)

    # Assert: the account is the tenant
    assert check_nodes(
        neo4j_session, "HuntressAccount", ["id", "name", "subdomain", "status"]
    ) == {
        (
            TEST_ACCOUNT_ID,
            "Springfield Nuclear Power Plant",
            "springfield",
            "enabled",
        ),
    }

    # Assert: organizations
    assert check_nodes(
        neo4j_session, "HuntressOrganization", ["id", "name", "key"]
    ) == {
        (2001, "Springfield Elementary", "springfield"),
        (2002, "Shelbyville Elementary", "shelbyville"),
    }
    assert check_rels(
        neo4j_session,
        "HuntressAccount",
        "id",
        "HuntressOrganization",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_ACCOUNT_ID, 2001),
        (TEST_ACCOUNT_ID, 2002),
    }

    # Assert: agents, including the Linux host that reports no serial number
    assert check_nodes(
        neo4j_session,
        "HuntressAgent",
        ["id", "hostname", "serial_number", "platform", "firewall_status"],
    ) == {
        (3001, "homer-desktop", "SN-HOMER-0001", "windows", "Enabled"),
        (3002, "marge-macbook", "SN-MARGE-0002", "darwin", "Enabled"),
        (3003, "bart-server", None, "linux", "Disabled"),
    }
    assert check_rels(
        neo4j_session,
        "HuntressAccount",
        "id",
        "HuntressAgent",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_ACCOUNT_ID, 3001),
        (TEST_ACCOUNT_ID, 3002),
        (TEST_ACCOUNT_ID, 3003),
    }
    assert check_rels(
        neo4j_session,
        "HuntressAgent",
        "id",
        "HuntressOrganization",
        "id",
        "MEMBER_OF",
        rel_direction_right=True,
    ) == {
        (3001, 2001),
        (3002, 2001),
        (3003, 2002),
    }

    # Assert: incident reports, with the remediation summary derived from the inlined list
    assert check_nodes(
        neo4j_session,
        "HuntressIncidentReport",
        ["id", "severity", "status", "platform", "remediation_count"],
    ) == {
        (4001, "critical", "sent", "windows", 2),
        (4002, "low", "closed", "darwin", 0),
        (4003, "high", "dismissed", "microsoft_365", None),
    }
    assert neo4j_session.run(
        "MATCH (i:HuntressIncidentReport {id: 4001}) RETURN i.remediation_types AS types"
    ).single()["types"] == ["containment", "manual"]

    # Assert: an incident points at the agent it was raised on. 4003 is an identity
    # incident with no agent, so it has no AFFECTS edge.
    assert check_rels(
        neo4j_session,
        "HuntressIncidentReport",
        "id",
        "HuntressAgent",
        "id",
        "AFFECTS",
        rel_direction_right=True,
    ) == {
        (4001, 3001),
        (4002, 3002),
    }
    assert check_rels(
        neo4j_session,
        "HuntressIncidentReport",
        "id",
        "HuntressOrganization",
        "id",
        "MEMBER_OF",
        rel_direction_right=True,
    ) == {
        (4001, 2001),
        (4002, 2001),
        (4003, 2002),
    }

    # Assert: console users are deduped across their memberships
    assert check_nodes(neo4j_session, "HuntressUser", ["id", "email", "name"]) == {
        (6001, "homer@springfield.example.com", "Homer Simpson"),
        (6002, "marge@springfield.example.com", "Marge Simpson"),
    }

    # Assert: roles are synthesised per scope, so the same label granted on the account
    # and on an organization stays two distinct grants
    assert check_nodes(neo4j_session, "HuntressRole", ["id", "name", "scope"]) == {
        ("1000/Admin", "Admin", "account"),
        ("2001/Read-only", "Read-only", "org"),
        ("2002/Security Engineer", "Security Engineer", "org"),
    }
    assert check_rels(
        neo4j_session,
        "HuntressUser",
        "id",
        "HuntressRole",
        "id",
        "HAS_ROLE",
        rel_direction_right=True,
    ) == {
        (6001, "1000/Admin"),
        (6001, "2002/Security Engineer"),
        (6002, "2001/Read-only"),
    }
    assert check_rels(
        neo4j_session,
        "HuntressUser",
        "id",
        "HuntressOrganization",
        "id",
        "MEMBER_OF",
        rel_direction_right=True,
    ) == {
        (6001, 2002),
        (6002, 2001),
    }

    # Cleanup
    neo4j_session.run("MATCH (n) DETACH DELETE n")


@patch.object(cartography.intel.huntress.account, "get", return_value=ACCOUNT)
@patch.object(
    cartography.intel.huntress.organizations, "get", return_value=ORGANIZATIONS
)
@patch.object(cartography.intel.huntress.agents, "get", return_value=AGENTS)
@patch.object(
    cartography.intel.huntress.incident_reports, "get", return_value=INCIDENT_REPORTS
)
@patch.object(cartography.intel.huntress.memberships, "get", return_value=MEMBERSHIPS)
def test_cleanup_drops_stale_agents_and_spares_other_accounts(
    mock_memberships_get,
    mock_incident_reports_get,
    mock_agents_get,
    mock_organizations_get,
    mock_account_get,
    neo4j_session,
):
    # Arrange: an unrelated Huntress account, synced by another run at another tag
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    neo4j_session.run(
        """
        MERGE (a:HuntressAccount {id: 9999})
        SET a.lastupdated = $other_tag
        MERGE (g:HuntressAgent {id: 9001})
        SET g.lastupdated = $other_tag, g.hostname = 'stan-laptop'
        MERGE (a)-[r:RESOURCE]->(g)
        SET r.lastupdated = $other_tag
        """,
        other_tag=TEST_UPDATE_TAG + 1,
    )
    _sync_everything(neo4j_session)

    # Act: the Linux host was uninstalled, so the next sync no longer returns it
    with patch.object(
        cartography.intel.huntress.agents, "get", return_value=AGENTS[:2]
    ):
        _sync_everything(neo4j_session, TEST_UPDATE_TAG + 2)

    # Assert: the stale agent node itself is deleted, not merely detached from its
    # account, and the other account's agent is untouched.
    assert check_nodes(neo4j_session, "HuntressAgent", ["id"]) == {
        (3001,),
        (3002,),
        (9001,),
    }
    assert check_rels(
        neo4j_session,
        "HuntressAccount",
        "id",
        "HuntressAgent",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_ACCOUNT_ID, 3001),
        (TEST_ACCOUNT_ID, 3002),
        (9999, 9001),
    }

    # Cleanup
    neo4j_session.run("MATCH (n) DETACH DELETE n")


@patch.object(cartography.intel.huntress.account, "get", return_value=ACCOUNT)
@patch.object(
    cartography.intel.huntress.organizations, "get", return_value=ORGANIZATIONS
)
@patch.object(cartography.intel.huntress.agents, "get", return_value=AGENTS)
@patch.object(
    cartography.intel.huntress.incident_reports, "get", return_value=INCIDENT_REPORTS
)
def test_memberships_permission_denied_keeps_previously_ingested_users(
    mock_incident_reports_get,
    mock_agents_get,
    mock_organizations_get,
    mock_account_get,
    neo4j_session,
):
    """A credential that loses the memberships permission must not wipe users and roles.

    `get` returns None rather than an empty list precisely so the sync skips its cleanup.
    """
    # Arrange: a first run that could read memberships
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    with patch.object(
        cartography.intel.huntress.memberships, "get", return_value=MEMBERSHIPS
    ):
        _sync_everything(neo4j_session)

    # Act: a later run whose credential is no longer authorized
    with patch.object(cartography.intel.huntress.memberships, "get", return_value=None):
        _sync_everything(neo4j_session, TEST_UPDATE_TAG + 1)

    # Assert: the users and roles from the first run survived
    assert check_nodes(neo4j_session, "HuntressUser", ["id"]) == {(6001,), (6002,)}
    assert check_nodes(neo4j_session, "HuntressRole", ["id"]) == {
        ("1000/Admin",),
        ("2001/Read-only",),
        ("2002/Security Engineer",),
    }

    # Cleanup
    neo4j_session.run("MATCH (n) DETACH DELETE n")
