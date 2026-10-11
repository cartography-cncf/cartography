import logging
import time
from typing import Any
from typing import Optional
from urllib.parse import urlparse

import jwt
from azure.core.credentials import AccessToken
from azure.core.exceptions import ClientAuthenticationError
from azure.identity import AzureCliCredential
from azure.identity import ClientSecretCredential
from azure.mgmt.resource.subscriptions import SubscriptionClient

logger = logging.getLogger(__name__)

# Azure Resource Manager accepts tokens issued for either of its two resource
# URIs, and some management SDKs still request the legacy one.
ARM_RESOURCES = frozenset(
    {
        "https://management.azure.com",
        "https://management.core.windows.net",
    },
)
ARM_APP_ID = "797f4846-ba00-4fd7-ba43-dac1f8f63013"


class UnsupportedTokenScopeError(ClientAuthenticationError):
    """
    Raised when a static access token is asked for an audience it was not issued
    for, such as the Key Vault data plane. Callers can catch it to skip a
    data-plane sync without masking genuine authentication failures.
    """


def _resource_of(value: str) -> str:
    parsed = urlparse(value)
    if not parsed.scheme or not parsed.netloc:
        return value
    return f"{parsed.scheme}://{parsed.netloc}".lower()


def _is_arm_audience(audience: str) -> bool:
    return audience == ARM_APP_ID or _resource_of(audience) in ARM_RESOURCES


class StaticAccessTokenCredential:
    """
    A ``TokenCredential`` that serves one pre-issued Azure Resource Manager access
    token. It cannot refresh the token, so a sync must finish before the token
    expires, and it refuses every non-ARM scope because one bearer token is only
    valid for the audience it was issued for.
    """

    def __init__(self, token: str, expires_on: int) -> None:
        self._token = AccessToken(token, expires_on)

    def get_token(self, *scopes: str, **kwargs: Any) -> AccessToken:
        unsupported = [scope for scope in scopes if not _is_arm_audience(scope)]
        if unsupported:
            raise UnsupportedTokenScopeError(
                "The Azure access token was issued for Azure Resource Manager and "
                f"cannot be used for {', '.join(unsupported)}.",
            )
        if self._token.expires_on <= time.time():
            raise ClientAuthenticationError(
                "The Azure access token expired during the sync. Issue a new token "
                "and run the sync again.",
            )
        return self._token


def _first_subscription_id(credential: Any) -> Optional[str]:
    subscription_client = SubscriptionClient(credential)
    subscription = next(subscription_client.subscriptions.list(), None)
    return subscription.subscription_id if subscription else None


def _get_tenant_id_from_token(credential: Any) -> str:
    """
    A helper function to get the tenant ID from the claims in an access token.
    """
    token = credential.get_token("https://management.azure.com/.default")
    decoded_token = jwt.decode(token.token, options={"verify_signature": False})
    return decoded_token.get("tid", "")


class Credentials:
    """
    A simple data container for the credential object and its associated IDs.
    """

    def __init__(
        self,
        credential: Any,
        tenant_id: Optional[str] = None,
        subscription_id: Optional[str] = None,
    ) -> None:
        self.credential = credential
        self.tenant_id = tenant_id
        self.subscription_id = subscription_id


class Authenticator:

    def authenticate_cli(self) -> Optional[Credentials]:
        """
        Implements authentication using the Azure CLI with the modern library.
        """
        logging.getLogger("urllib3").setLevel(logging.ERROR)
        logging.getLogger(
            "azure.core.pipeline.policies.http_logging_policy",
        ).setLevel(logging.ERROR)
        try:
            credential = AzureCliCredential()

            subscription_client = SubscriptionClient(credential)
            subscription = next(subscription_client.subscriptions.list())
            subscription_id = subscription.subscription_id

            tenant_id = _get_tenant_id_from_token(credential)

            return Credentials(
                credential=credential,
                tenant_id=tenant_id,
                subscription_id=subscription_id,
            )
        except Exception as e:
            logger.error(
                f"Failed to authenticate with Azure CLI. Have you run 'az login'? Details: {e}"
            )
            return None

    def authenticate_sp(
        self,
        tenant_id: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        subscription_id: Optional[str] = None,
    ) -> Optional[Credentials]:
        """
        Implements authentication using a Service Principal with the modern library.
        """
        try:
            credential = ClientSecretCredential(
                client_id=client_id,
                client_secret=client_secret,
                tenant_id=tenant_id,
            )
            return Credentials(
                credential=credential,
                tenant_id=tenant_id,
                subscription_id=subscription_id,
            )
        except Exception as e:
            logger.error(
                (
                    "Failed to authenticate with Service Principal. "
                    "Please ensure the tenant ID, client ID, and client secret are correct. Details: %s"
                ),
                e,
            )
            return None

    def authenticate_access_token(self, access_token: str) -> Credentials:
        """
        Authenticate with a pre-issued Azure Resource Manager access token, such as
        a signed-in user's delegated ``user_impersonation`` token. The token is
        validated up front so a Microsoft Graph token or an expired token fails
        with a clear message instead of a generic 401 from the first ARM call.
        """
        try:
            claims = jwt.decode(access_token, options={"verify_signature": False})
        except jwt.PyJWTError as e:
            raise ValueError(
                "The Azure access token is not a valid JWT.",
            ) from e

        audience = claims.get("aud")
        audiences = audience if isinstance(audience, list) else [audience]
        if not any(isinstance(a, str) and _is_arm_audience(a) for a in audiences):
            raise ValueError(
                "The Azure access token was not issued for Azure Resource Manager "
                f"(audience: {audience!r}). Request a token for "
                "https://management.azure.com, not Microsoft Graph.",
            )

        tenant_id = claims.get("tid")
        if not tenant_id:
            raise ValueError("The Azure access token has no tenant ID (tid) claim.")

        expires_on = claims.get("exp")
        if not isinstance(expires_on, int) or expires_on <= time.time():
            raise ValueError(
                "The Azure access token is expired or has no expiry (exp) claim.",
            )
        logger.info(
            "Using a static Azure access token; it expires in %d minutes and "
            "cannot be refreshed.",
            (expires_on - int(time.time())) // 60,
        )

        credential = StaticAccessTokenCredential(access_token, expires_on)
        subscription_id = _first_subscription_id(credential)
        if not subscription_id:
            raise RuntimeError(
                "No Azure subscriptions found. Ensure the identity behind the "
                "access token has a role such as Reader on at least one subscription.",
            )
        return Credentials(
            credential=credential,
            tenant_id=tenant_id,
            subscription_id=subscription_id,
        )
