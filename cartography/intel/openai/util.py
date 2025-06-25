from typing import Any
from typing import Generator

import requests


def paginated_get(
    api_session: requests.Session,
    url: str,
    timeout: tuple[int, int],
    after: str | None = None,
) -> Generator[dict[str, Any], None, None]:
    """Helper function to get paginated data from the OpenAI API.

    This function handles the pagination of the API requests and returns
    the results as a generator. It will continue to make requests until
    all pages of data have been retrieved. The results are returned as a
    list of dictionaries, where each dictionary represents a single
    entity.

    Args:
        api_session (requests.Session): The requests session to use for making API calls.
        url (str): The URL to make the API call to.
        timeout (tuple[int, int]): The timeout for the API call.
        after (str | None): The ID of the last item retrieved in the previous request.
            If None, the first page of results will be retrieved.
    Returns:
        Generator[dict[str, Any], None, None]: A generator yielding dictionaries representing the results.
    """
    params = {"after": after} if after else {}
    req = api_session.get(
        url,
        params=params,
        timeout=timeout,
    )
    req.raise_for_status()
    result = req.json()
    yield from result.get("data", [])
    if result.get("has_more"):
        yield from paginated_get(
            api_session,
            url,
            timeout=timeout,
            after=result.get("last_id"),
        )
