from unittest.mock import MagicMock

import requests

import cartography.intel.netlify.certificates

TEST_SITE_ID = "11111111-2222-3333-4444-555555555555"
TEST_BASE_URL = "https://api.netlify.com/api/v1"


def test_certificate_endpoint_returning_null_yields_no_node() -> None:
    """
    A site with no custom domain answers the TLS endpoint with a JSON `null` body rather than a
    404. Treating that as a certificate would create a node with a null domain.
    """
    # Arrange
    api_session = MagicMock(spec=requests.Session)
    response = MagicMock()
    response.status_code = 200
    response.headers = {}
    response.json.return_value = None
    api_session.get.return_value = response

    # Act / Assert
    assert (
        cartography.intel.netlify.certificates.get_netlify_certificate(
            api_session,
            TEST_BASE_URL,
            TEST_SITE_ID,
        )
        is None
    )
