from msrest.authentication import BasicAuthentication, OAuthTokenAuthentication
from msal import PublicClientApplication, ConfidentialClientApplication
from typing import Optional
import json
import webbrowser

# Authentication Module
class AzureDevOpsAuth:
    """Authentication handler for Azure DevOps API"""

    @staticmethod
    def get_pat_credentials(token: str) -> BasicAuthentication:
        """
        Get credentials using Personal Access Token

        Args:
            token (str): Azure DevOps Personal Access Token

        Returns:
            BasicAuthentication: PAT credentials
        """
        if not token:
            raise ValueError("Personal Access Token is required for PAT authentication")
        return BasicAuthentication('', token)

    @staticmethod
    def get_oauth_device_code_credentials(client_id: str, tenant_id: Optional[str] = None) -> OAuthTokenAuthentication:
        """
        Get OAuth credentials using device code flow

        Args:
            client_id (str): OAuth client ID
            tenant_id (str, optional): Azure AD tenant ID. Defaults to 'common'.

        Returns:
            OAuthTokenAuthentication: OAuth credentials
        """
        if not client_id:
            raise ValueError("Client ID is required for OAuth device code flow")

        # Azure DevOps resource scope
        scopes = ["499b84ac-1321-427f-aa17-267ca6975798/.default"]

        # Create MSAL app
        app = PublicClientApplication(
            client_id=client_id,
            authority=f"https://login.microsoftonline.com/{tenant_id or 'common'}"
        )

        # Initiate device code flow
        flow = app.initiate_device_flow(scopes)

        # Display the message to the user
        print(flow["message"])
        webbrowser.open(flow["verification_uri"])

        # Poll for token
        result = app.acquire_token_by_device_flow(flow)

        if "access_token" not in result:
            raise Exception(f"Failed to acquire token: {result.get('error_description', 'Unknown error')}")

        # Return OAuth token authentication
        return OAuthTokenAuthentication(result["access_token"])

    @staticmethod
    def get_oauth_client_credentials(client_id: str, client_secret: str, tenant_id: str) -> OAuthTokenAuthentication:
        """
        Get OAuth credentials using client credentials flow

        Args:
            client_id (str): OAuth client ID
            client_secret (str): OAuth client secret
            tenant_id (str): Azure AD tenant ID

        Returns:
            OAuthTokenAuthentication: OAuth credentials
        """
        if not client_id or not client_secret or not tenant_id:
            raise ValueError("Client ID, Client Secret, and Tenant ID are required for OAuth client credentials flow")

        # Azure DevOps resource scope
        scopes = ["499b84ac-1321-427f-aa17-267ca6975798/.default"]

        # Create MSAL app
        app = ConfidentialClientApplication(
            client_id=client_id,
            client_credential=client_secret,
            authority=f"https://login.microsoftonline.com/{tenant_id}"
        )

        # Acquire token
        result = app.acquire_token_for_client(scopes=scopes)

        if "access_token" not in result:
            raise Exception(f"Failed to acquire token: {result.get('error_description', 'Unknown error')}")

        # Return OAuth token authentication
        return OAuthTokenAuthentication(result["access_token"])
