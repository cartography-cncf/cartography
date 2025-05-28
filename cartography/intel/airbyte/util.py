import logging
import time
from typing import Any

import requests

logger = logging.getLogger(__name__)
# Connect and read timeouts of 60 seconds each; see https://requests.readthedocs.io/en/master/user/advanced/#timeouts
_TIMEOUT = (60, 60)


class AirbyteClient:
    """A client for interacting with the Airbyte API.
    This client handles authentication and provides methods to make GET requests to the Airbyte API.
    It automatically handles pagination for GET requests that return multiple pages of data.
    """

    def __init__(self, base_url: str, client_id: str, client_secret: str) -> None:
        self._client_id = client_id
        self._client_secret = client_secret
        self.base_url = base_url
        self._access_token_expiry: int | None = None
        self._session = requests.Session()

    def get(self, uri: str, params: dict | None = None, offset: int = 0) -> list[dict]:
        """Make a GET request to the Airbyte API.
        This method handles authentication and pagination.
        Args:
            uri (str): The URI to make the GET request to.
            params (dict | None): Optional parameters to include in the request.
            offset (int): The offset for pagination, defaults to 0.
        Returns:
            list[dict]: A list of dictionaries containing the data from the response.
        """
        self.authenticate()
        if params is None:
            params_with_pagination = {}
        else:
            params_with_pagination = params.copy()
        params_with_pagination["offset"] = offset
        response = self._session.get(
            f"{self.base_url}{uri}", params=params_with_pagination, timeout=_TIMEOUT
        )
        response.raise_for_status()
        data = response.json().get("data")
        if response.json().get("next", "") != "":
            data.extend(
                self.get(
                    uri,
                    params=params,
                    offset=offset + len(data),
                )
            )
        return data

    def authenticate(self) -> None:
        """Authenticate with the Airbyte API using client credentials.
        This method checks if the access token is still valid and renews it if necessary.
        If the access token is expired or not set, it will make a request to obtain a new access token.
        """
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
        logger.debug("Access token renewed, expires in %s seconds.", token_expiry)


def normalize_airbyte_config(config: dict[str, Any]) -> dict[str, Any]:
    """Normalize the Airbyte configuration dictionary.
    This function takes a configuration dictionary and normalizes it by mapping keys to a standard set of keys.
    This is useful for ensuring consistency across different configurations, and will allow to connect to existing nodes.
    Args:
        config (dict[str, Any]): The configuration dictionary to normalize.
    Returns:
        dict[str, Any]: A normalized configuration dictionary with standardized keys.
    """
    normalized_config = {}
    for key in config:
        if key in ("host", "port", "name", "region", "endpoint", "account", ""):
            normalized_config[key] = config[key]
        elif key in ("aws_region_name", "region_name", "s3_bucket_region"):
            normalized_config["region"] = config[key]
        elif key in ("queue_url", "url", "s3_endpoint"):
            normalized_config["endpoint"] = config[key]
        elif key in ("azure_blob_storage_account_name", "storage_account_name"):
            normalized_config["account"] = config[key]
        elif key in (
            "azure_blob_storage_container_name",
            "bucket",
            "database",
            "s3_bucket_name",
        ):
            normalized_config["name"] = config[key]
    return normalized_config


def list_to_string(lst: list[str]) -> str | None:
    """Convert a list of strings to a comma-separated string."""
    if len(lst) == 0:
        return None
    # Sublist
    formated_list: list[str] = []
    for item in lst:
        if isinstance(item, list):
            formated_list.append("|".join(item))
        else:
            formated_list.append(str(item))
    return ",".join(formated_list)
