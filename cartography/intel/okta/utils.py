# Okta intel module - utility functions
import logging
import time

from okta.framework import PagedResults
from okta.framework.ApiClient import ApiClient
from requests import Response

logger = logging.getLogger(__name__)


def is_last_page(response: PagedResults) -> bool:
    """
    Determine if we are at the last page of a Paged result flow
    :param response: server response
    :return: boolean indicating if we are at the last page or not
    """
    # from https://github.com/okta/okta-sdk-python/blob/master/okta/framework/PagedResults.py
    return not ("next" in response.links)


def create_api_client(okta_org: str, path_name: str, api_key: str) -> ApiClient:
    """
    Create Okta ApiClient
    :param okta_org: Okta organization name
    :param path_name: API Path
    :param api_key: Okta api key
    :return: Instance of ApiClient
    """
    api_client = ApiClient(
        base_url=f"https://{okta_org}.okta.com/",
        pathname=path_name,
        api_token=api_key,
    )

    return api_client


def check_rate_limit(response: Response) -> None:
    """
    Checks if we are about to hit the rate limit and waits until reset if so
    :param response: server response
    """
    rate_limit_threshold = 0.1

    remaining = response.headers.get("x-rate-limit-remaining")
    limit = response.headers.get("x-rate-limit-limit")
    reset_time = response.headers.get("x-rate-limit-reset")

    if remaining and limit and reset_time:
        if (int(remaining) / int(limit)) < rate_limit_threshold:
            sleep_time_seconds = int(reset_time) - int(time.time())
            if sleep_time_seconds <= 0:
                # A negative sleep time does not make sense so treat it the same as a 0 sleep time
                return
            if sleep_time_seconds > 60:
                raise ValueError(
                    f"Okta API limit exceeded. Sleep time of {sleep_time_seconds} would exceed one minute. Crashing "
                    f"Okta sync to avoid blocking.",
                )
            logger.warning(
                f"Okta rate limit threshold reached. Waiting {sleep_time_seconds} seconds.",
            )
            time.sleep(sleep_time_seconds)
