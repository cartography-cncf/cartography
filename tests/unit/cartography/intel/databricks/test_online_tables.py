from unittest.mock import Mock

import pytest
import requests

from cartography.intel.databricks.online_tables import get


def _http_error(status_code: int) -> requests.HTTPError:
    response = requests.Response()
    response.status_code = status_code
    return requests.HTTPError(response=response)


@pytest.mark.parametrize("status_code", [400, 404])
def test_get_skips_tables_without_online_table_twin(status_code):
    # Arrange
    api_session = Mock()
    api_session.get.side_effect = _http_error(status_code)
    candidates = [
        {
            "full_name": "catalog.schema.regular_table",
            "metastore_id": "metastore-id",
        },
    ]

    # Act
    result = get(api_session, candidates)

    # Assert
    assert result == []


@pytest.mark.parametrize("status_code", [401, 403, 429, 500])
def test_get_raises_unexpected_http_errors(status_code):
    # Arrange
    api_session = Mock()
    error = _http_error(status_code)
    api_session.get.side_effect = error
    candidates = [
        {
            "full_name": "catalog.schema.regular_table",
            "metastore_id": "metastore-id",
        },
    ]

    # Act and assert
    with pytest.raises(requests.HTTPError) as exc_info:
        get(api_session, candidates)
    assert exc_info.value is error
