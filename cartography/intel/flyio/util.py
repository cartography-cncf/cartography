from typing import Any

import requests


def get_json(
    api_session: requests.Session,
    url: str,
    **params: Any,
) -> Any:
    response = api_session.get(url, params=params, timeout=(60, 60))
    response.raise_for_status()
    return response.json()
