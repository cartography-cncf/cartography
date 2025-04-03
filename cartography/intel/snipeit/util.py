import logging
from typing import Any
from typing import Dict

import requests

from cartography.settings import settings
from cartography.util import timeit

logger = logging.getLogger(__name__)
# Connect and read timeouts as defined in settings; see https://requests.readthedocs.io/en/master/user/advanced/#timeouts
_TIMEOUT = (settings.common.http_timeout, settings.common.http_timeout)


@timeit
def call_snipeit_api(api_and_parameters: str, base_uri: str, token: str) -> Dict[str, Any]:
    uri = base_uri + api_and_parameters
    try:
        logger.debug(
            "SnipeIT: Get %s", uri,
        )
        response = requests.get(
            uri,
            headers={
                'Accept': 'application/json',
                'Authorization': f'Bearer {token}',
            },
            timeout=_TIMEOUT,
        )
    except requests.exceptions.Timeout:
        # Add context and re-raise for callers to handle
        logger.warning(f"SnipeIT: requests.get('{uri}') timed out.")
        raise
    # if call failed, use requests library to raise an exception
    response.raise_for_status()
    return response.json()
