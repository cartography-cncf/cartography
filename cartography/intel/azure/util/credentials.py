import logging
from datetime import datetime
from datetime import timedelta
from typing import Any
from typing import Optional

import adal
import requests
from azure.common.credentials import get_azure_cli_credentials
from azure.common.credentials import get_cli_profile
from azure.core.exceptions import HttpResponseError
from azure.identity import ClientSecretCredential
from msrestazure.azure_active_directory import AADTokenCredentials

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
        elif "tenant_id" in self.aad_graph_credentials.token:
            return self.aad_graph_credentials.token["tenant_id"]
        else:
            # This is a last resort, e.g. for MSI authentication
            try:
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

            arm_credentials, subscription_id, tenant_id = get_azure_cli_credentials(
                with_tenant=True,
            )
            aad_graph_credentials, placeholder_1, placeholder_2 = (
                get_azure_cli_credentials(
                    with_tenant=True,
                    resource="https://graph.windows.net",
                )
            )

            profile = get_cli_profile()

            return Credentials(
                arm_credentials,
                aad_graph_credentials,
                tenant_id=tenant_id,
                current_user=profile.get_current_account_user(),
                subscription_id=subscription_id,
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

            aad_graph_credentials = ClientSecretCredential(
                client_id=client_id,
                client_secret=client_secret,
                tenant_id=tenant_id,
                resource="https://graph.windows.net",
            )

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
