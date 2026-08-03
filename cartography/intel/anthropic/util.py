from typing import Any

import requests


def resolve_org_id(
    common_job_parameters: dict[str, Any],
    header_org_id: str,
) -> str:
    """Prefer the organization id resolved by the organization sync.

    That id comes from GET /organizations/me and is authoritative. The
    `anthropic-organization-id` response header is only a fallback, for syncs run in
    isolation (tests, seeds) where the organization sync has not populated ORG_ID.
    """
    return common_job_parameters.get("ORG_ID") or header_org_id


def paginated_get_by_page(
    api_session: requests.Session,
    url: str,
    timeout: tuple[int, int],
    headers: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    """Helper function to get data from the Anthropic API's page-cursor endpoints.

    The Anthropic API has two pagination families. The older organization endpoints
    use the `after_id` cursor handled by `paginated_get`; service accounts,
    federation resources and the workspace-scoped endpoints use an opaque `page`
    cursor instead, returning the next one in `next_page`.

    Args:
        api_session (requests.Session): The requests session to use for making API calls.
        url (str): The URL to make the API call to.
        timeout (tuple[int, int]): The timeout for the API call.
        headers (dict[str, str] | None): Extra headers for this call, e.g. a beta
            opt-in. Beta headers are per-call because some are mutually exclusive.
    Returns:
        list[dict[str, Any]]: The results across every page.
    """
    results: list[dict[str, Any]] = []
    page: str | None = None
    while True:
        params = {"page": page} if page else {}
        req = api_session.get(url, params=params, timeout=timeout, headers=headers)
        req.raise_for_status()
        result = req.json()
        results.extend(result.get("data", []))
        page = result.get("next_page")
        if not page:
            return results


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
