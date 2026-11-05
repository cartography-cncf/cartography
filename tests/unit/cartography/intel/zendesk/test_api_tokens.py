from unittest.mock import MagicMock

import pytest
import requests

from cartography.intel.zendesk.api_tokens import get


@pytest.mark.parametrize("status_code", [401, 429, 500])
def test_get_propagates_other_http_errors(status_code):
    # Arrange
    session = MagicMock(spec=requests.Session)
    response = requests.Response()
    response.status_code = status_code
    session.get.return_value = response

    # Act and assert
    with pytest.raises(requests.exceptions.HTTPError) as exc:
        get(session, "acme")
    assert exc.value.response is response
