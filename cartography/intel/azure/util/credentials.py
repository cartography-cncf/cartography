import logging
from typing import Any
from typing import Optional

import jwt
from azure.identity import AzureCliCredential
from azure.identity import ClientSecretCredential
from azure.mgmt.resource import SubscriptionClient

logger = logging.getLogger(__name__)


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
