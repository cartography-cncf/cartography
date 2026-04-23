import logging
from typing import Any

import requests
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import HTTPError
from requests.exceptions import ReadTimeout

logger = logging.getLogger(__name__)
_TIMEOUT = (60, 60)
_PAGE_SIZE = 100
_MAX_RETRIES = 3
_BASE_URL = "https://api.endorlabs.com"


def paginated_get(
    bearer_token: str,
    namespace: str,
    resource_path: str,
) -> list[dict[str, Any]]:
    all_objects: list[dict[str, Any]] = []
    page_token: str | None = None
    retries = 0
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/jsoncompact",
    }
    url = f"{_BASE_URL}/v1/namespaces/{namespace}/{resource_path}"

    while True:
        params: dict[str, Any] = {
            "list_parameters.page_size": _PAGE_SIZE,
        }
        if page_token:
            params["list_parameters.page_token"] = page_token

        try:
            response = requests.get(
                url,
                headers=headers,
                params=params,
                timeout=_TIMEOUT,
            )
            response.raise_for_status()
            data = response.json()
        except (ReadTimeout, HTTPError, RequestsConnectionError):
            retries += 1
            logger.warning(
                "Failed to fetch %s (attempt %d/%d). Retrying...",
                resource_path,
                retries,
                _MAX_RETRIES,
            )
            if retries >= _MAX_RETRIES:
                raise
            continue

        retries = 0
        objects = data.get("list", {}).get("objects", [])
        all_objects.extend(objects)

        next_token = data.get("list", {}).get("response", {}).get("next_page_token")
        if not next_token or not objects:
            break
        page_token = next_token

    logger.debug("Fetched %d Endor Labs %s", len(all_objects), resource_path)
    return all_objects
