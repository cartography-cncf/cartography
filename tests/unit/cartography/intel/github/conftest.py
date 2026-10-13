from unittest.mock import patch

import pytest

import cartography.intel.github.repos


@pytest.fixture(autouse=True)
def no_repo_security_settings():
    """
    Keep repos.sync() tests offline: no repository security settings are visible,
    so the REST repository list is never fetched. Tests that need them patch
    `get_repo_security_and_analysis_by_url` themselves.
    """
    with patch.object(
        cartography.intel.github.repos,
        "get_repo_security_and_analysis_by_url",
        return_value={},
    ):
        yield
