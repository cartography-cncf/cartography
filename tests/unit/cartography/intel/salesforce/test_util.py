from unittest.mock import MagicMock
from unittest.mock import patch

from cartography.intel.salesforce.util import get_access_token_client_credentials
from cartography.intel.salesforce.util import get_access_token_jwt_bearer
from cartography.intel.salesforce.util import query_salesforce
from cartography.intel.salesforce.util import strip_attributes

INSTANCE_URL = "https://simpson.my.salesforce.com"


def test_strip_attributes_removes_salesforce_attributes_key():
    records = [
        {"attributes": {"type": "User"}, "Id": "005", "Name": "Marge"},
        {"attributes": {"type": "User"}, "Id": "006", "Name": "Homer"},
    ]
    assert strip_attributes(records) == [
        {"Id": "005", "Name": "Marge"},
        {"Id": "006", "Name": "Homer"},
    ]


def test_query_salesforce_follows_pagination():
    """query_salesforce should follow nextRecordsUrl until results are exhausted."""
    page1 = MagicMock()
    page1.json.return_value = {
        "records": [{"Id": "1"}, {"Id": "2"}],
        "nextRecordsUrl": "/services/data/v60.0/query/01gABC-2000",
    }
    page2 = MagicMock()
    page2.json.return_value = {"records": [{"Id": "3"}], "done": True}
    api_session = MagicMock()
    api_session.get.side_effect = [page1, page2]

    records = query_salesforce(api_session, INSTANCE_URL, "SELECT Id FROM User")

    assert records == [{"Id": "1"}, {"Id": "2"}, {"Id": "3"}]
    # First call hits the query endpoint with the SOQL; second follows the cursor URL.
    assert api_session.get.call_count == 2
    first_url = api_session.get.call_args_list[0].args[0]
    second_url = api_session.get.call_args_list[1].args[0]
    assert first_url == f"{INSTANCE_URL}/services/data/v60.0/query"
    assert second_url == f"{INSTANCE_URL}/services/data/v60.0/query/01gABC-2000"


@patch("cartography.intel.salesforce.util.requests.post")
def test_client_credentials_flow_posts_expected_grant(mock_post):
    resp = MagicMock()
    resp.json.return_value = {
        "access_token": "tok123",
        "instance_url": INSTANCE_URL,
    }
    mock_post.return_value = resp

    token, instance_url = get_access_token_client_credentials(
        INSTANCE_URL, "client-id", "client-secret"
    )

    assert (token, instance_url) == ("tok123", INSTANCE_URL)
    posted = mock_post.call_args
    assert posted.args[0] == f"{INSTANCE_URL}/services/oauth2/token"
    assert posted.kwargs["data"]["grant_type"] == "client_credentials"
    assert posted.kwargs["data"]["client_id"] == "client-id"
    assert posted.kwargs["data"]["client_secret"] == "client-secret"


@patch("cartography.intel.salesforce.util.jwt.encode", return_value="signed.jwt.token")
@patch("cartography.intel.salesforce.util.requests.post")
def test_jwt_bearer_flow_signs_and_posts_assertion(mock_post, mock_encode):
    resp = MagicMock()
    resp.json.return_value = {
        "access_token": "tok456",
        "instance_url": INSTANCE_URL,
    }
    mock_post.return_value = resp

    token, instance_url = get_access_token_jwt_bearer(
        INSTANCE_URL, "client-id", "user@simpson.corp", "-----BEGIN PRIVATE KEY-----"
    )

    assert (token, instance_url) == ("tok456", INSTANCE_URL)
    # The JWT claims must identify the issuer (client id), subject (user), and audience.
    claims = mock_encode.call_args.args[0]
    assert claims["iss"] == "client-id"
    assert claims["sub"] == "user@simpson.corp"
    assert claims["aud"] == INSTANCE_URL
    posted = mock_post.call_args
    assert (
        posted.kwargs["data"]["grant_type"]
        == "urn:ietf:params:oauth:grant-type:jwt-bearer"
    )
    assert posted.kwargs["data"]["assertion"] == "signed.jwt.token"
