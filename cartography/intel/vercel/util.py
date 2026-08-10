import logging
from typing import Any

import requests

from cartography.util import timeit

logger = logging.getLogger(__name__)

_TIMEOUT = (60, 60)


@timeit
def paginated_get(
    api_session: requests.Session,
    url: str,
    result_key: str,
    team_id: str,
    params: dict[str, Any] | None = None,
    limit: int = 100,
    pagination_param: str = "until",
) -> list[dict[str, Any]]:
    """
    Fetch all pages from a paginated Vercel API endpoint.

    :param api_session: Authenticated requests session
    :param url: Full URL of the API endpoint
    :param result_key: JSON key containing the result list (e.g., "projects", "deployments").
        Pass empty string for endpoints that return a bare array.
    :param team_id: Vercel team ID for teamId query param
    :param params: Additional query parameters
    :param limit: Page size
    :param pagination_param: Query parameter used to request the next page, set to the
        value of ``pagination.next``. Vercel is inconsistent here: timestamp-cursor
        endpoints (e.g. deployments) use ``until``, while continuation-cursor endpoints
        (e.g. access-groups and their members/projects) use ``next``. Sending the wrong
        parameter name leaves the cursor unapplied, so the API keeps returning the first
        page and this loop never terminates. See https://vercel.com/docs/rest-api/reference.
    :return: Combined list of all results across all pages
    """
    all_results: list[dict[str, Any]] = []
    request_params: dict[str, Any] = {"teamId": team_id, "limit": limit}
    if params:
        request_params.update(params)

    while True:
        resp = api_session.get(url, params=request_params, timeout=_TIMEOUT)
        # Some endpoints are plan-gated (e.g. access-groups is Enterprise-only);
        # treat 403 as "feature unavailable" and return what we have so far.
        if resp.status_code == 403:
            logger.warning(
                "Vercel returned 403 Forbidden for %s — skipping (likely plan-gated).",
                url,
            )
            return all_results
        resp.raise_for_status()
        data = resp.json()

        # Some endpoints return a direct array (e.g., edge configs, log drains)
        if isinstance(data, list):
            all_results.extend(data)
            break

        # Strict access: surface endpoint/key mismatches instead of silently
        # dropping data (see firewall bypass `rules` vs `result` bug).
        results = data[result_key]
        all_results.extend(results)

        # Check for next page
        pagination = data.get("pagination", {})
        next_cursor = pagination.get("next")
        if not next_cursor or len(results) == 0:
            break

        request_params[pagination_param] = next_cursor

    return all_results
