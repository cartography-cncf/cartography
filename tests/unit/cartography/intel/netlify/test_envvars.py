import cartography.intel.netlify.envvars

TEST_ACCOUNT_ID = "5f5a5d7053c60b4be4c8784d"
TEST_SITE_ID = "11111111-2222-3333-4444-555555555555"


def test_env_var_transform_separates_the_two_scopes() -> None:
    """
    A team-wide FOO and a site-scoped FOO are different variables with different values, so they
    must not collapse onto one node.
    """
    # Act
    transformed = cartography.intel.netlify.envvars.transform_netlify_env_vars(
        [
            (None, {"key": "FOO", "is_secret": False, "values": []}),
            (TEST_SITE_ID, {"key": "FOO", "is_secret": False, "values": []}),
        ],
        TEST_ACCOUNT_ID,
    )

    # Assert
    assert [v["id"] for v in transformed] == [
        f"{TEST_ACCOUNT_ID}|_account|FOO",
        f"{TEST_ACCOUNT_ID}|{TEST_SITE_ID}|FOO",
    ]
    assert [v["scope"] for v in transformed] == ["account", "site"]
