import time

import jwt
import pytest
from azure.core.exceptions import ClientAuthenticationError

from cartography.intel.common.access_token import AZURE_RESOURCE_MANAGER
from cartography.intel.common.access_token import MICROSOFT_GRAPH
from cartography.intel.common.access_token import parse_access_token
from cartography.intel.common.access_token import StaticAccessTokenCredential
from cartography.intel.common.access_token import UnsupportedTokenScopeError

TEST_TENANT_ID = "00000000-0000-0000-0000-000000000001"


def _token(**claims) -> str:
    return jwt.encode(
        {
            "tid": TEST_TENANT_ID,
            "exp": int(time.time()) + 3600,
            **claims,
        },
        "test-signing-key-not-verified-by-cartography",
        "HS256",
    )


@pytest.mark.parametrize(
    "audience, token_audience",
    [
        (MICROSOFT_GRAPH, "https://graph.microsoft.com"),
        (MICROSOFT_GRAPH, "00000003-0000-0000-c000-000000000000"),
        (AZURE_RESOURCE_MANAGER, "https://management.azure.com/"),
    ],
)
def test_parse_access_token_accepts_matching_audience(audience, token_audience):
    # Act
    claims = parse_access_token(_token(aud=token_audience), audience)

    # Assert
    assert claims.tenant_id == TEST_TENANT_ID


@pytest.mark.parametrize(
    "audience, token_audience",
    [
        (MICROSOFT_GRAPH, "https://management.azure.com"),
        (AZURE_RESOURCE_MANAGER, "https://graph.microsoft.com"),
    ],
)
def test_parse_access_token_rejects_other_audience(audience, token_audience):
    # Act and assert
    with pytest.raises(ValueError, match=f"not issued for {audience.name}"):
        parse_access_token(_token(aud=token_audience), audience)


def test_static_credential_serves_both_arm_scope_forms():
    # Arrange
    credential = StaticAccessTokenCredential(
        "token", int(time.time()) + 3600, AZURE_RESOURCE_MANAGER
    )

    # Act
    tokens = {
        credential.get_token("https://management.azure.com/.default").token,
        credential.get_token("https://management.core.windows.net//.default").token,
    }

    # Assert
    assert tokens == {"token"}


@pytest.mark.parametrize(
    "audience, scope",
    [
        (AZURE_RESOURCE_MANAGER, "https://vault.azure.net/.default"),
        (AZURE_RESOURCE_MANAGER, "https://management.azure.com.example/.default"),
        (MICROSOFT_GRAPH, "https://management.azure.com/.default"),
    ],
)
def test_static_credential_refuses_other_audiences(audience, scope):
    # Arrange
    credential = StaticAccessTokenCredential("token", int(time.time()) + 3600, audience)

    # Act and assert
    with pytest.raises(UnsupportedTokenScopeError):
        credential.get_token(scope)


def test_static_credential_fails_once_expired():
    # Arrange
    credential = StaticAccessTokenCredential(
        "token", int(time.time()) - 1, MICROSOFT_GRAPH
    )

    # Act
    with pytest.raises(ClientAuthenticationError, match="expired") as excinfo:
        credential.get_token("https://graph.microsoft.com/.default")

    # Assert
    assert not isinstance(excinfo.value, UnsupportedTokenScopeError)
