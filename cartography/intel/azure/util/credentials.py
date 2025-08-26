import logging
from datetime import datetime
from datetime import timedelta
from typing import Any
from typing import Optional

import adal
import requests
from azure.core.exceptions import HttpResponseError
from azure.identity import AzureCliCredential
from azure.identity import ClientSecretCredential
from msrestazure.azure_active_directory import AADTokenCredentials
from azure.mgmt.resource import SubscriptionClient

logger = logging.getLogger(__name__)
AUTHORITY_HOST_URI = "https://login.microsoftonline.com"


class Credentials:

    def __init__(
        self,
        arm_credentials: Any,
        aad_graph_credentials: Any,
        tenant_id: Optional[str] = None,
        subscription_id: Optional[str] = None,
        context: Optional[adal.AuthenticationContext] = None,
        current_user: Optional[str] = None,
    ) -> None:
        self.arm_credentials = arm_credentials  # Azure Resource Manager API credentials
        self.aad_graph_credentials = (
            aad_graph_credentials  # Azure AD Graph API credentials
        )
        self.tenant_id = tenant_id
        self.subscription_id = subscription_id
        self.context = context
        self.current_user = current_user

    def get_current_user(self) -> Optional[str]:
        return self.current_user

    def get_tenant_id(self) -> Any:
        if self.tenant_id:
            return self.tenant_id
        elif (
            hasattr(self.aad_graph_credentials, "token")
            and "tenant_id" in self.aad_graph_credentials.token
        ):
            return self.aad_graph_credentials.token["tenant_id"]
        else:
            # This is a last resort, e.g. for MSI authentication
            try:
                if (
                    hasattr(self.arm_credentials, "token")
                    and "access_token" in self.arm_credentials.token
                ):
                    h = {
                        "Authorization": "Bearer {}".format(
                            self.arm_credentials.token["access_token"],
                        ),
                    }
                    r = requests.get(
                        "https://management.azure.com/tenants?api-version=2020-01-01",
                        headers=h,
                    )
                    r2 = r.json()
                    return r2.get("value")[0].get("tenantId")
            except requests.ConnectionError as e:
                logger.error(f"Unable to infer tenant ID: {e}")
            return None

    def get_credentials(self, resource: str) -> Any:
        if resource == "arm":
            self.arm_credentials = self.get_fresh_credentials(self.arm_credentials)
            return self.arm_credentials
        elif resource == "aad_graph":
            self.aad_graph_credentials = self.get_fresh_credentials(
                self.aad_graph_credentials,
            )
            return self.aad_graph_credentials
        else:
            raise Exception("Invalid credentials resource type")

    def get_fresh_credentials(self, credentials: Any) -> Any:
        """
        Check if credentials are outdated and if so refresh them.
        """
        if self.context and hasattr(credentials, "token"):
            expiration_datetime = datetime.fromtimestamp(
                credentials.token["expires_on"],
            )
            current_datetime = datetime.now()
            expiration_delta = expiration_datetime - current_datetime
            if expiration_delta < timedelta(minutes=5):
                return self.refresh_credential(credentials)
        return credentials

    def refresh_credential(self, credentials: Any) -> Any:
        """
        Refresh credentials
        """
        logger.debug("Refreshing credentials")
        authority_uri = AUTHORITY_HOST_URI + "/" + self.get_tenant_id()
        if self.context:
            existing_cache = self.context.cache
            context = adal.AuthenticationContext(authority_uri, cache=existing_cache)

        else:
            context = adal.AuthenticationContext(authority_uri)

        new_token = context.acquire_token(
            credentials.token["resource"],
            credentials.token["user_id"],
            credentials.token["_client_id"],
        )

        new_credentials = AADTokenCredentials(
            new_token,
            credentials.token.get("_client_id"),
        )
        return new_credentials


class Authenticator:

    def authenticate_cli(self) -> Credentials:
        """
        Implements authentication for the Azure provider
        """
        try:

            # Set logging level to error for libraries as otherwise generates a lot of warnings
            logging.getLogger("adal-python").setLevel(logging.ERROR)
            logging.getLogger("msrest").setLevel(logging.ERROR)
            logging.getLogger("msrestazure.azure_active_directory").setLevel(
                logging.ERROR,
            )
            logging.getLogger("urllib3").setLevel(logging.ERROR)
            logging.getLogger(
                "azure.core.pipeline.policies.http_logging_policy",
            ).setLevel(logging.ERROR)

            # Use Azure CLI credential without relying on azure-cli-core Python APIs
            credential = AzureCliCredential()

            # Discover tenant and subscription via ARM SDK (no subprocess)
            sub_client = SubscriptionClient(credential)

            # Tenant ID: pick the first tenant returned by the API
            tenant_id: Optional[str] = None
            try:
                tenants = list(sub_client.tenants.list())
                if tenants:
                    # type: ignore[attr-defined] — azure SDK models expose tenant_id
                    tenant_id = getattr(tenants[0], "tenant_id", None)
            except Exception:
                # Fall through; tenant_id remains None
                pass

            # Subscription ID: pick the first accessible subscription for non-all-subscriptions flows
            subscription_id: Optional[str] = None
            try:
                subs = list(sub_client.subscriptions.list())
                if subs:
                    subscription_id = getattr(subs[0], "subscription_id", None)
            except Exception:
                # Fall through; subscription_id remains None
                pass

            # We don't have a reliable user principal name without Graph; use a generic identifier
            current_user = "azure-cli"

            return Credentials(
                credential,
                credential,
                tenant_id=tenant_id,
                subscription_id=subscription_id,
                current_user=current_user,
            )

        except Exception as e:
            raise e

    def authenticate_sp(
        self,
        tenant_id: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
    ) -> Credentials:
        """
        Implements authentication for the Azure provider
        """
        try:

            # Set logging level to error for libraries as otherwise generates a lot of warnings
            logging.getLogger("adal-python").setLevel(logging.ERROR)
            logging.getLogger("msrest").setLevel(logging.ERROR)
            logging.getLogger("msrestazure.azure_active_directory").setLevel(
                logging.ERROR,
            )
            logging.getLogger("urllib3").setLevel(logging.ERROR)
            logging.getLogger(
                "azure.core.pipeline.policies.http_logging_policy",
            ).setLevel(logging.ERROR)

            arm_credentials = ClientSecretCredential(
                client_id=client_id,
                client_secret=client_secret,
                tenant_id=tenant_id,
            )

            # Reuse the same credential for any legacy Graph calls; AAD Graph is deprecated
            aad_graph_credentials = arm_credentials

            return Credentials(
                arm_credentials,
                aad_graph_credentials,
                tenant_id=tenant_id,
                current_user=client_id,
            )

        except HttpResponseError as e:
            if (
                ", AdalError: Unsupported wstrust endpoint version. "
                "Current supported version is wstrust2005 or wstrust13." in e.args
            ):
                logger.error(
                    f"You are likely authenticating with a Microsoft Account. \
                    This authentication mode only supports Azure Active Directory principal authentication.\
                    {e}",
                )

            raise e
