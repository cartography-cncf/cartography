import time
from unittest.mock import MagicMock
from unittest.mock import patch

import jwt
import pytest
from azure.core.exceptions import ClientAuthenticationError

from cartography.config import Config
from cartography.intel.azure import start_azure_ingestion
from cartography.intel.azure.util.credentials import Authenticator
from cartography.intel.azure.util.credentials import StaticAccessTokenCredential
from cartography.intel.azure.util.credentials import UnsupportedTokenScopeError

TEST_TENANT_ID = "00000000-0000-0000-0000-000000000001"
TEST_SUBSCRIPTION_ID = "00000000-0000-0000-0000-000000000002"
ARM_SCOPE = "https://management.azure.com/.default"


def _token(**overrides) -> str:
    claims = {
        "aud": "https://management.azure.com",
        "tid": TEST_TENANT_ID,
        "exp": int(time.time()) + 3600,
    }
    claims.update(overrides)
    return jwt.encode(
        {k: v for k, v in claims.items() if v is not None},
        "test-signing-key-not-verified-by-cartography",
        "HS256",
    )


def _mock_subscriptions(mock_subscription_client, *subscription_ids):
    subscriptions = [MagicMock(subscription_id=sid) for sid in subscription_ids]
    mock_subscription_client.return_value.subscriptions.list.return_value = iter(
        subscriptions,
    )


@pytest.mark.parametrize(
    "audience",
    [
        "https://management.azure.com",
        "https://management.azure.com/",
        "https://management.core.windows.net/",
        "797f4846-ba00-4fd7-ba43-dac1f8f63013",
        ["https://management.azure.com"],
    ],
)
@patch("cartography.intel.azure.util.credentials.SubscriptionClient")
def test_authenticate_access_token_accepts_arm_audiences(
    mock_subscription_client,
    audience,
):
    _mock_subscriptions(mock_subscription_client, TEST_SUBSCRIPTION_ID)
    token = _token(aud=audience)

    credentials = Authenticator().authenticate_access_token(token)

    assert credentials.tenant_id == TEST_TENANT_ID
    assert credentials.subscription_id == TEST_SUBSCRIPTION_ID
    assert credentials.credential.get_token(ARM_SCOPE).token == token


def test_authenticate_access_token_rejects_graph_token():
    with pytest.raises(ValueError, match="not issued for Azure Resource Manager"):
        Authenticator().authenticate_access_token(
            _token(aud="https://graph.microsoft.com"),
        )


def test_authenticate_access_token_rejects_expired_token():
    with pytest.raises(ValueError, match="expired"):
        Authenticator().authenticate_access_token(
            _token(exp=int(time.time()) - 60),
        )


def test_authenticate_access_token_rejects_token_without_tenant():
    with pytest.raises(ValueError, match="tenant ID"):
        Authenticator().authenticate_access_token(_token(tid=None))


def test_authenticate_access_token_rejects_non_jwt():
    with pytest.raises(ValueError, match="not a valid JWT"):
        Authenticator().authenticate_access_token("not-a-jwt")


@patch("cartography.intel.azure.util.credentials.SubscriptionClient")
def test_authenticate_access_token_requires_a_visible_subscription(
    mock_subscription_client,
):
    _mock_subscriptions(mock_subscription_client)

    with pytest.raises(RuntimeError, match="No Azure subscriptions found"):
        Authenticator().authenticate_access_token(_token())


def test_static_credential_serves_both_arm_scope_forms():
    credential = StaticAccessTokenCredential("token", int(time.time()) + 3600)

    assert credential.get_token(ARM_SCOPE).token == "token"
    assert (
        credential.get_token("https://management.core.windows.net//.default").token
        == "token"
    )


def test_static_credential_refuses_other_audiences():
    credential = StaticAccessTokenCredential("token", int(time.time()) + 3600)

    with pytest.raises(UnsupportedTokenScopeError, match="vault.azure.net"):
        credential.get_token("https://vault.azure.net/.default")


def test_static_credential_fails_once_expired():
    credential = StaticAccessTokenCredential("token", int(time.time()) - 1)

    with pytest.raises(ClientAuthenticationError, match="expired") as excinfo:
        credential.get_token(ARM_SCOPE)
    assert not isinstance(excinfo.value, UnsupportedTokenScopeError)


@patch.object(Authenticator, "authenticate_sp")
@patch.object(Authenticator, "authenticate_access_token")
def test_start_azure_ingestion_rejects_token_with_sp_auth(
    mock_authenticate_access_token,
    mock_authenticate_sp,
):
    config = Config(
        neo4j_uri="bolt://localhost:7687",
        update_tag=1,
        azure_sp_auth=True,
        azure_tenant_id=TEST_TENANT_ID,
        azure_client_id="client-id",
        azure_client_secret="client-secret",
        azure_access_token=_token(),
    )

    with pytest.raises(ValueError, match="cannot be combined"):
        start_azure_ingestion(MagicMock(), config)
    mock_authenticate_access_token.assert_not_called()
    mock_authenticate_sp.assert_not_called()
