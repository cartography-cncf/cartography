from typing import Any

import requests


def paginated_get(
    api_session: requests.Session,
    url: str,
    timeout: tuple[int, int],
    after: str | None = None,
) -> tuple[str, list[dict[str, Any]]]:
    """Helper function to get paginated data from the Anthropic API.

    This function handles the pagination of the API requests and returns
    the results in a list. It also retrieves the organization ID from the
    response headers. The function will continue to make requests until
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
        tuple[str, list[dict[str, Any]]]: A tuple containing the organization ID and a list of
            dictionaries representing the results.
    """
    results: list[dict[str, Any]] = []
    params = {"after_id": after} if after else {}
    req = api_session.get(
        url,
        params=params,
        timeout=timeout,
    )
    req.raise_for_status()
    # Get organization_id from the headers
    organization_id = req.headers.get("anthropic-organization-id", "")
    result = req.json()
    results.extend(result.get("data", []))
    if result.get("has_more"):
        _, next_results = paginated_get(
            api_session,
            url,
            timeout=timeout,
            after=result.get("last_id"),
        )
        results.extend(next_results)
    return organization_id, results
