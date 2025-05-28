import logging
import time

import requests

logger = logging.getLogger(__name__)
# Connect and read timeouts of 60 seconds each; see https://requests.readthedocs.io/en/master/user/advanced/#timeouts
_TIMEOUT = (60, 60)


class AirbyteClient:
    # DOC
    def __init__(self, base_url: str, client_id: str, client_secret: str):
        self._client_id = client_id
        self._client_secret = client_secret
        self.base_url = base_url
        self._access_token_expiry: int | None = None
        self._session = requests.Session()

    def get(self, uri: str, params: dict = None):
        # DOC
        self.authenticate()
        response = self._session.get(
            f"{self.base_url}{uri}", params=params, timeout=_TIMEOUT
        )
        response.raise_for_status()
        data = response.json().get("data")
        # WIP: Uggly debugging
        if data is None:
            print(response.json())
        return data

    def authenticate(self) -> None:
        # DOC
        if self._access_token_expiry and self._access_token_expiry >= time.time():
            return
        self._session.headers.pop("Authorization", None)
        payload = {
            "grant-type": "client_credentials",
            "client_id": self._client_id,
            "client_secret": self._client_secret,
        }
        response = self._session.post(
            f"{self.base_url}/applications/token", json=payload, timeout=_TIMEOUT
        )
        response.raise_for_status()
        data = response.json()
        self._session.headers["Authorization"] = (
            f"Bearer {data.get('access_token', '')}"
        )
        token_expiry = data.get("expires_in", 0)
        self._access_token_expiry = time.time() + token_expiry
        # WIP: Change for logger
        print(f"Access token renewed, expires in {token_expiry} seconds.")
