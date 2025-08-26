import logging
from typing import Any
from typing import Optional

from azure.identity import AzureCliCredential
from azure.identity import ClientSecretCredential
from azure.mgmt.resource import SubscriptionClient

logger = logging.getLogger(__name__)


class Credentials:
    """
    A simple data container for the credential object and its associated IDs.
    All complex token refreshing logic is now handled automatically by the
    new azure-identity objects.
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

            # Use the modern SubscriptionClient to get the subscription and tenant ID.
            subscription_client = SubscriptionClient(credential)
            subscription = next(subscription_client.subscriptions.list())
            subscription_id = subscription.subscription_id
            tenant_id = subscription.tenant_id

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
            # The `resource=` parameter is part of the old library and is removed.
            # The new objects handle scoping automatically.
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
            logger.error(f"Failed to authenticate with Service Principal: {e}")
            return None
