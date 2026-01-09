import logging
import requests
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# Standard Microsoft Graph / Security API endpoints
# Note: MDE data is often accessed via the Microsoft Graph API nowadays
GRAPH_URL = "https://graph.microsoft.com/v1.0"


class MDEClient:
    def __init__(self, tenant_id: str, client_id: str, client_secret: str):
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.session = requests.Session()
        self._auth_token = None

    def _get_token(self) -> str:
        """
        Authenticates with Azure AD to get a Bearer Token.
        """
        url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
        payload = {
            "scope": "https://graph.microsoft.com/.default",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials",
        }
        try:
            response = self.session.post(url, data=payload)
            response.raise_for_status()
            return response.json().get("access_token")
        except requests.exceptions.RequestException as e:
            logger.error(f"MDE Auth failed: {e}")
            raise

    def get_machines(self) -> List[Dict[str, Any]]:
        """
        Fetches MDE machines (device inventory) with automatic pagination.
        Using MS Graph 'security/runHuntingQuery' or standard device list.
        For this PR, we assume the standard 'machine' export or Graph 'deviceManagement' endpoint.
        """
        if not self._auth_token:
            self._auth_token = self._get_token()

        headers = {
            "Authorization": f"Bearer {self._auth_token}",
            "Content-Type": "application/json",
        }

        # NOTE: Adjust endpoint if using the legacy MDE API vs MS Graph
        # Using the standard machine list endpoint for demonstration
        # url = "https://api.securitycenter.microsoft.com/api/machines"
        # Or MS Graph:
        url = "https://graph.microsoft.com/v1.0/deviceManagement/managedDevices"

        all_machines = []

        while url:
            try:
                response = self.session.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()

                # Normalize MS Graph 'value' list
                machines_page = data.get("value", [])
                all_machines.extend(machines_page)

                # Handle Pagination
                url = data.get("@odata.nextLink", None)

            except requests.exceptions.RequestException as e:
                logger.error(f"Failed to fetch MDE page: {e}")
                # We stop pagination on error but return what we have so far
                break

        logger.info(f"Retrieved {len(all_machines)} machines from MDE.")
        return all_machines
