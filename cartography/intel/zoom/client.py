import time
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

TOKEN_URL = "https://zoom.us/oauth/token"
USERS_URL = "https://api.zoom.us/v2/users"


class ZoomClient:
    """Account-scoped server-to-server OAuth with a limited HTTP retry count."""

    def __init__(self, account_id: str, client_id: str, client_secret: str) -> None:
        self.account_id = account_id
        self.auth = (client_id, client_secret)
        self.session = requests.Session()
        self.session.mount(
            "https://",
            HTTPAdapter(
                max_retries=Retry(
                    total=3,
                    backoff_factor=1,
                    status_forcelist={429, 500, 502, 503, 504},
                    # Token issuance can be retried; it does not invalidate existing tokens.
                    allowed_methods={"GET", "POST"},
                    raise_on_status=False,
                )
            ),
        )
        self._access_token = ""
        self._expires_at = 0.0

    def _refresh_token(self) -> None:
        response = self.session.post(
            TOKEN_URL,
            data={"grant_type": "account_credentials", "account_id": self.account_id},
            auth=self.auth,
            timeout=(10, 60),
            allow_redirects=False,
        )
        response.raise_for_status()
        if response.status_code != 200:
            raise requests.HTTPError(
                "Unexpected Zoom token response status", response=response
            )
        token = response.json()
        self._access_token = token["access_token"]
        self._expires_at = time.monotonic() + int(token["expires_in"]) - 60

    def get_users_page(self, params: dict[str, Any]) -> dict[str, Any]:
        if time.monotonic() >= self._expires_at:
            self._refresh_token()
        # Refresh once on early revocation/expiry; a second 401 is fatal.
        for attempt in range(2):
            response = self.session.get(
                USERS_URL,
                params=params,
                headers={"Authorization": f"Bearer {self._access_token}"},
                timeout=(10, 60),
                allow_redirects=False,
            )
            if response.status_code != 401 or attempt:
                response.raise_for_status()
                if response.status_code != 200:
                    raise requests.HTTPError(
                        "Unexpected Zoom users response status", response=response
                    )
                return response.json()
            self._refresh_token()
        raise AssertionError("Unreachable")
