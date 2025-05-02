import logging
from typing import Dict
from typing import List

import requests.auth

from cartography.util import timeit

logger = logging.getLogger(__name__)
# Connect and read timeouts of 60 seconds each; see https://requests.readthedocs.io/en/master/user/advanced/#timeouts
_TIMEOUT = (60, 60)


@timeit
def call_jamf_api(
    api_and_parameters: str,
    jamf_base_uri: str,
    jamf_user: str,
    jamf_password: str,
) -> List[Dict]:
    uri = jamf_base_uri + api_and_parameters
    jamf_auth = requests.auth.HTTPBasicAuth(jamf_user, jamf_password)
    try:
        response = requests.get(
            uri,
            auth=jamf_auth,
            headers={"Accept": "application/json"},
            timeout=_TIMEOUT,
        )
    except requests.exceptions.Timeout:
        # Add context and re-raise for callers to handle
        logger.warning(f"Jamf: requests.get('{uri}') timed out.")
        raise
    # if call failed, use requests library to raise an exception
    response.raise_for_status()
    return response.json()
