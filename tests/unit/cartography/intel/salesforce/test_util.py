from datetime import datetime
from datetime import timezone
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from cartography.intel.salesforce.util import get_salesforce_client
from cartography.intel.salesforce.util import parse_sf_datetime
from cartography.intel.salesforce.util import SalesforceClient


def test_parse_sf_datetime():
    assert parse_sf_datetime(None) is None
    assert parse_sf_datetime("2023-01-02T03:04:05.000+0000") == datetime(
        2023, 1, 2, 3, 4, 5, tzinfo=timezone.utc
    )


def _token_response():
    resp = MagicMock()
    resp.json.return_value = {
        "access_token": "tok",
        "instance_url": "https://my.instance.salesforce.com/",
    }
    return resp


@patch("cartography.intel.salesforce.util.requests.post")
def test_client_credentials_flow(mock_post):
    mock_post.return_value = _token_response()

    client = get_salesforce_client(
        login_url="https://login.salesforce.com/",
        client_id="cid",
        client_secret="secret",
    )

    # Client credentials grant was used, and the instance url is normalized
    sent = mock_post.call_args.kwargs["data"]
    assert sent["grant_type"] == "client_credentials"
    assert client.instance_url == "https://my.instance.salesforce.com"
    assert client.session.headers["Authorization"] == "Bearer tok"


@patch("cartography.intel.salesforce.util.jwt.encode", return_value="signed-jwt")
@patch("cartography.intel.salesforce.util.requests.post")
def test_jwt_bearer_flow(mock_post, mock_encode):
    mock_post.return_value = _token_response()

    get_salesforce_client(
        login_url="https://login.salesforce.com",
        client_id="cid",
        username="user@example.com",
        private_key="-----BEGIN PRIVATE KEY-----",
    )

    sent = mock_post.call_args.kwargs["data"]
    assert sent["grant_type"] == "urn:ietf:params:oauth:grant-type:jwt-bearer"
    assert sent["assertion"] == "signed-jwt"


def test_missing_credentials_raises():
    with pytest.raises(ValueError):
        get_salesforce_client(login_url="https://login.salesforce.com", client_id="cid")


def _page(records, done, next_url=None):
    resp = MagicMock()
    body = {"records": records, "done": done}
    if next_url is not None:
        body["nextRecordsUrl"] = next_url
    resp.json.return_value = body
    return resp


def test_query_all_follows_pagination_and_strips_attributes():
    session = MagicMock()
    session.get.side_effect = [
        _page(
            [{"Id": "a", "attributes": {"type": "User"}}],
            done=False,
            next_url="/services/data/v60.0/query/01g-200",
        ),
        _page([{"Id": "b", "attributes": {"type": "User"}}], done=True),
    ]
    client = SalesforceClient(session, "https://my.instance.salesforce.com")

    assert client.query_all("SELECT Id FROM User") == [{"Id": "a"}, {"Id": "b"}]


def test_query_all_fails_fast_on_truncated_response():
    session = MagicMock()
    # done=False with no nextRecordsUrl would silently truncate
    session.get.return_value = _page([{"Id": "a"}], done=False)
    client = SalesforceClient(session, "https://my.instance.salesforce.com")

    with pytest.raises(ValueError):
        client.query_all("SELECT Id FROM User")
