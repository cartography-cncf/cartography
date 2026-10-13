import cartography.intel.snowflake.policy_references
from tests.data.snowflake.account import SNOWFLAKE_ACCOUNT_ID
from tests.data.snowflake.policy_references import SNOWFLAKE_POLICY_REFERENCES


def test_transform_skips_unmodelled_policy_kinds():
    """A tag-based masking attachment has no policy node, so it must be counted."""
    # Act
    edges, skipped = cartography.intel.snowflake.policy_references.transform(
        SNOWFLAKE_POLICY_REFERENCES, SNOWFLAKE_ACCOUNT_ID
    )

    # Assert
    assert skipped == 1
    assert sum(len(rows) for rows in edges.values()) == 4
