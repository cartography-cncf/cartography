from unittest.mock import MagicMock

import cartography.intel.snowflake.account_parameters
from tests.data.snowflake.account import SNOWFLAKE_ACCOUNT_ID
from tests.data.snowflake.account_parameters import SNOWFLAKE_NETWORK_POLICY_PARAMETERS


def test_get_account_network_policy_reads_the_filtered_listing(mocker):
    """The account-level policy is only stated by the NETWORK_POLICY parameter."""
    # Arrange
    client = MagicMock(account_id=SNOWFLAKE_ACCOUNT_ID)
    client.run_sql = mocker.Mock(return_value=SNOWFLAKE_NETWORK_POLICY_PARAMETERS)

    # Act
    network_policy = (
        cartography.intel.snowflake.account_parameters.get_account_network_policy(
            client
        )
    )

    # Assert
    assert network_policy == "PLANT_PERIMETER"
