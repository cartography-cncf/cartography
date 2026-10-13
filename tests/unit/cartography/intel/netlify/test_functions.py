from unittest.mock import MagicMock

import requests

import cartography.intel.netlify.functions
import tests.data.netlify.functions

TEST_SITE_ID = "11111111-2222-3333-4444-555555555555"
TEST_BASE_URL = "https://api.netlify.com/api/v1"


def test_get_netlify_functions_accepts_a_bare_object() -> None:
    """
    The endpoint answers with a bare object rather than a one-element array when the site has a
    single function bundle, even though the published spec declares an array.
    """
    # Arrange
    api_session = MagicMock(spec=requests.Session)
    response = MagicMock()
    response.status_code = 200
    response.headers = {}
    response.json.return_value = tests.data.netlify.functions.NETLIFY_SITE_FUNCTIONS[0]
    api_session.get.return_value = response

    # Act
    bundles = cartography.intel.netlify.functions.get_netlify_functions(
        api_session,
        TEST_BASE_URL,
        TEST_SITE_ID,
    )

    # Assert
    assert len(bundles) == 1
    assert len(bundles[0]["functions"]) == 2
