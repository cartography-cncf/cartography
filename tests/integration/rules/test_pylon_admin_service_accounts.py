from unittest.mock import patch

import cartography.intel.pylon
import cartography.intel.pylon.organization
import cartography.intel.pylon.roles
import cartography.intel.pylon.teams
import cartography.intel.pylon.users
import tests.data.pylon.organization
import tests.data.pylon.roles
import tests.data.pylon.teams
import tests.data.pylon.users
from cartography.client.core.tx import read_list_of_dicts_tx
from cartography.client.core.tx import read_single_value_tx
from cartography.config import Config
from cartography.rules.data.rules.pylon_admin_service_accounts import (
    pylon_admin_service_accounts,
)
from tests.data.pylon.organization import PYLON_ORG_ID
from tests.data.pylon.users import ZAPIER_TOKEN_ID

_FACT = pylon_admin_service_accounts.facts[0]


@patch.object(
    cartography.intel.pylon.teams,
    "get",
    return_value=tests.data.pylon.teams.PYLON_TEAMS,
)
@patch.object(
    cartography.intel.pylon.users,
    "get",
    return_value=tests.data.pylon.users.PYLON_USERS,
)
@patch.object(
    cartography.intel.pylon.roles,
    "get",
    return_value=tests.data.pylon.roles.PYLON_ROLES,
)
@patch.object(
    cartography.intel.pylon.organization,
    "get",
    return_value=tests.data.pylon.organization.PYLON_ME,
)
def test_only_active_admin_service_accounts_are_flagged(
    mock_me,
    mock_roles,
    mock_users,
    mock_teams,
    neo4j_session,
) -> None:
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    cartography.intel.pylon.start_pylon_ingestion(
        neo4j_session,
        Config(
            neo4j_uri="bolt://localhost:7687",
            update_tag=1,
            pylon_api_token="pylon_api_test",
        ),
    )

    # Act
    rows = neo4j_session.execute_read(read_list_of_dicts_tx, _FACT.cypher_query)
    evaluated = neo4j_session.execute_read(
        read_single_value_tx,
        _FACT.cypher_count_query,
    )

    # Assert: the Admin user and the deactivated Admin token aren't flagged,
    # and neither is the active Member bot.
    assert rows == [
        {
            "name": "Zapier - Write Back",
            "id": ZAPIER_TOKEN_ID,
            "organization": "Springfield Nuclear",
            "organization_id": PYLON_ORG_ID,
        },
    ]
    assert evaluated == 2
