from unittest.mock import patch

import cartography.intel.snowflake.account
import cartography.intel.snowflake.databases
import cartography.intel.snowflake.shares
from cartography.intel.snowflake.util import sf_fqn
from cartography.intel.snowflake.util import sf_id
from tests.data.snowflake.account import SNOWFLAKE_ACCOUNT_ID
from tests.data.snowflake.account import SNOWFLAKE_MANAGED_ACCOUNTS
from tests.data.snowflake.databases import SNOWFLAKE_DATABASES
from tests.data.snowflake.shares import SNOWFLAKE_SHARE_CONSUMERS
from tests.data.snowflake.shares import SNOWFLAKE_SHARE_GRANTS
from tests.data.snowflake.shares import SNOWFLAKE_SHARES
from tests.integration.cartography.intel.snowflake.test_account import (
    _ensure_local_neo4j_has_test_account,
)
from tests.integration.cartography.intel.snowflake.test_account import build_test_client
from tests.integration.cartography.intel.snowflake.test_account import TEST_UPDATE_TAG
from tests.integration.util import check_nodes
from tests.integration.util import check_rels


def _ensure_local_neo4j_has_test_managed_accounts(neo4j_session) -> None:
    managed_accounts = cartography.intel.snowflake.account.transform_managed_accounts(
        SNOWFLAKE_MANAGED_ACCOUNTS, SNOWFLAKE_ACCOUNT_ID
    )
    cartography.intel.snowflake.account.load_managed_accounts(
        neo4j_session, managed_accounts, SNOWFLAKE_ACCOUNT_ID, TEST_UPDATE_TAG
    )


def _seed_shared_objects(neo4j_session) -> None:
    """Seed the database and table the outbound share exposes.

    They carry the shared securable label because that is what the share's exposure
    edge matches on, exactly as the grant edges do.
    """
    neo4j_session.run(
        """
        MERGE (d:SnowflakeDatabase:SnowflakeSecurable {id: $database_id})
          SET d.name = 'SPRINGFIELD', d.lastupdated = $update_tag
        MERGE (t:SnowflakeTable:SnowflakeSecurable {id: $table_id})
          SET t.name = 'REACTOR_READINGS', t.lastupdated = $update_tag
        """,
        database_id=sf_id(SNOWFLAKE_ACCOUNT_ID, "database", sf_fqn("SPRINGFIELD")),
        table_id=sf_id(
            SNOWFLAKE_ACCOUNT_ID,
            "table",
            sf_fqn("SPRINGFIELD", "NUCLEAR_PLANT", "REACTOR_READINGS"),
        ),
        update_tag=TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.snowflake.shares,
    "get_share_consumers",
    side_effect=lambda client, name: SNOWFLAKE_SHARE_CONSUMERS.get(name, []),
)
@patch.object(
    cartography.intel.snowflake.shares,
    "get_share_grants",
    side_effect=lambda client, name: SNOWFLAKE_SHARE_GRANTS.get(name, []),
)
@patch.object(
    cartography.intel.snowflake.shares, "get_shares", return_value=SNOWFLAKE_SHARES
)
def test_sync_snowflake_shares(mock_shares, mock_grants, mock_consumers, neo4j_session):
    # Arrange
    client = build_test_client()
    _ensure_local_neo4j_has_test_account(neo4j_session)
    _ensure_local_neo4j_has_test_managed_accounts(neo4j_session)
    _seed_shared_objects(neo4j_session)
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID,
    }

    # Act
    complete = cartography.intel.snowflake.shares.sync(
        neo4j_session, client, common_job_parameters
    )

    # Assert
    assert complete is True
    # The two inbound shares are both called SAMPLE_DATA and come from different
    # providers. They must stay two nodes, distinguished by owner_account: keying a
    # share on its name alone would merge one provider's data into the other's.
    assert check_nodes(
        neo4j_session,
        "SnowflakeShare",
        ["name", "owner_account", "share_kind", "shared_with_account_count"],
    ) == {
        ("REACTOR_FEED", "SPRINGFIELD.NUCLEAR", "OUTBOUND", 2),
        ("SAMPLE_DATA", "SNOW.SFC_SAMPLES", "INBOUND", 0),
        ("SAMPLE_DATA", "SHELBYVILLE.CITYHALL", "INBOUND", 0),
    }
    assert check_nodes(neo4j_session, "SnowflakeShare", ["id"]) == {
        (f"{SNOWFLAKE_ACCOUNT_ID}/share/NUCLEAR.REACTOR_FEED",),
        (f"{SNOWFLAKE_ACCOUNT_ID}/share/SFC_SAMPLES.SAMPLE_DATA",),
        (f"{SNOWFLAKE_ACCOUNT_ID}/share/CITYHALL.SAMPLE_DATA",),
    }

    # A consumer outside the organization has no node, so the raw list is the only
    # record that the share reaches it at all.
    shared_with = neo4j_session.run(
        """
        MATCH (share:SnowflakeShare {name: 'REACTOR_FEED'})
        RETURN share.shared_with_accounts AS accounts
        """,
    ).single()["accounts"]
    assert shared_with == ["SHELBYVILLE.CITYHALL", "SPRINGFIELD.SHELBYVILLE_READER"]

    assert check_rels(
        neo4j_session,
        "SnowflakeShare",
        "name",
        "SnowflakeAccount",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        ("REACTOR_FEED", SNOWFLAKE_ACCOUNT_ID),
        ("SAMPLE_DATA", SNOWFLAKE_ACCOUNT_ID),
    }

    # The exposure edge is what turns a share into a traversable egress path.
    assert check_rels(
        neo4j_session,
        "SnowflakeShare",
        "name",
        "SnowflakeDatabase",
        "name",
        "SHARES",
        rel_direction_right=True,
    ) == {("REACTOR_FEED", "SPRINGFIELD")}
    assert check_rels(
        neo4j_session,
        "SnowflakeShare",
        "name",
        "SnowflakeTable",
        "name",
        "SHARES",
        rel_direction_right=True,
    ) == {("REACTOR_FEED", "REACTOR_READINGS")}

    assert check_rels(
        neo4j_session,
        "SnowflakeShare",
        "name",
        "SnowflakeManagedAccount",
        "name",
        "SHARED_WITH",
        rel_direction_right=True,
    ) == {("REACTOR_FEED", "SHELBYVILLE_READER")}


@patch.object(
    cartography.intel.snowflake.databases,
    "get",
    return_value=SNOWFLAKE_DATABASES,
)
@patch.object(
    cartography.intel.snowflake.shares,
    "get_share_consumers",
    side_effect=lambda client, name: SNOWFLAKE_SHARE_CONSUMERS.get(name, []),
)
@patch.object(
    cartography.intel.snowflake.shares,
    "get_share_grants",
    side_effect=lambda client, name: SNOWFLAKE_SHARE_GRANTS.get(name, []),
)
@patch.object(
    cartography.intel.snowflake.shares, "get_shares", return_value=SNOWFLAKE_SHARES
)
def test_inbound_share_database_links_to_the_share_the_shares_sync_built(
    mock_shares, mock_grants, mock_consumers, mock_databases, neo4j_session
):
    """Run both real syncs so the two sides of CREATED_FROM_SHARE must agree.

    The share id is computed from ``SHOW SHARES``' ``owner_account`` plus name, and
    the database id from that database's ``origin``. Nothing here seeds a share node
    by hand, so if the two derivations disagree the edge simply does not appear.
    """
    # Arrange
    client = build_test_client()
    _ensure_local_neo4j_has_test_account(neo4j_session)
    _ensure_local_neo4j_has_test_managed_accounts(neo4j_session)
    _seed_shared_objects(neo4j_session)
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID,
    }

    # Act
    cartography.intel.snowflake.shares.sync(
        neo4j_session, client, common_job_parameters
    )
    cartography.intel.snowflake.databases.sync(
        neo4j_session, client, None, common_job_parameters
    )

    # Assert: SNOWFLAKE_SAMPLE_DATA has origin SFC_SAMPLES.SAMPLE_DATA, and the share
    # it names was reported by SHOW SHARES as name=SAMPLE_DATA with
    # owner_account=SNOW.SFC_SAMPLES. The edge resolving proves both sides reduce the
    # provider account the same way.
    assert check_rels(
        neo4j_session,
        "SnowflakeDatabase",
        "name",
        "SnowflakeShare",
        "id",
        "CREATED_FROM_SHARE",
    ) == {
        (
            "SNOWFLAKE_SAMPLE_DATA",
            f"{SNOWFLAKE_ACCOUNT_ID}/share/SFC_SAMPLES.SAMPLE_DATA",
        )
    }


@patch.object(cartography.intel.snowflake.shares, "get_shares", return_value=None)
def test_sync_reports_incomplete_when_shares_cannot_be_read(mock_shares, neo4j_session):
    """Losing the listing must not delete the shares collected on an earlier run."""
    # Arrange
    client = build_test_client()
    _ensure_local_neo4j_has_test_account(neo4j_session)
    neo4j_session.run("MATCH (share:SnowflakeShare) DETACH DELETE share")
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID,
    }

    # Act
    complete = cartography.intel.snowflake.shares.sync(
        neo4j_session, client, common_job_parameters
    )

    # Assert
    assert complete is False
    assert check_nodes(neo4j_session, "SnowflakeShare", ["id"]) == set()
