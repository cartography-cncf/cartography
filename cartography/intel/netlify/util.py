import logging
from typing import Any

import requests

from cartography.util import timeit

logger = logging.getLogger(__name__)

# (connect, read) timeouts, matching the convention used by the other intel modules.
_TIMEOUT = (60, 60)
# Netlify caps `per_page` at 100.
# https://docs.netlify.com/api-and-cli-guides/api-guides/get-started-with-api/
_PER_PAGE = 100
# Backstop against a server that keeps advertising a next page. At 100 items per page this
# still allows 100k objects of a single kind, far beyond any real Netlify team.
_MAX_PAGES = 1000
# Netlify allows 500 requests per minute and reports the remaining budget on every response.
_RATE_LIMIT_WARN_THRESHOLD = 25


class NetlifyPaginationError(Exception):
    """
    Netlify advertised another page but did not give a usable URL to reach it.

    Never downgrade this to a warning-and-stop: the cleanup jobs treat whatever list they are
    handed as the exhaustive set of live resources, so a silently truncated list deletes every
    resource past the last page we managed to read.
    """


def _warn_if_rate_limit_low(response: requests.Response) -> None:
    remaining = response.headers.get("X-RateLimit-Remaining")
    if remaining is None:
        return
    try:
        remaining_int = int(remaining)
    except ValueError:
        return
    if remaining_int <= _RATE_LIMIT_WARN_THRESHOLD:
        # We do not pre-emptively sleep: the window is only a minute wide and the session's
        # Retry adapter already honours Retry-After on the 429 itself.
        logger.warning(
            "Netlify API rate limit is nearly exhausted: %d requests remaining in the "
            "current one-minute window.",
            remaining_int,
        )


@timeit
def paginated_get(
    api_session: requests.Session,
    url: str,
    params: dict[str, Any] | None = None,
    per_page: int = _PER_PAGE,
    allow_plan_gated: bool = False,
    allow_missing: bool = False,
) -> list[dict[str, Any]]:
    """
    Fetch every page of a Netlify list endpoint.

    Netlify paginates with `?page=N&per_page=M` and advertises the next page in an RFC-5988
    `Link` header, which requests already parses into `response.links`.

    :param api_session: Authenticated requests session.
    :param url: Full URL of the API endpoint.
    :param params: Query parameters for the first request only. The `Link` URL already carries
        `page` and `per_page`, so re-sending them on later requests would fight the cursor.
    :param per_page: Page size, capped at 100 by the API.
    :param allow_plan_gated: When True a 403 is treated as "feature not available on this
        plan" and the results gathered so far are returned. Only pass True for genuinely
        plan-gated endpoints, and never when a truncated result would reach a cleanup job.
    :param allow_missing: When True a 404 returns an empty list. Netlify 404s per-site
        sub-resources that were never enabled for that site.
    :return: Every object across every page.
    :raises NetlifyPaginationError: if a page advertises a successor it cannot reach, or if
        the endpoint returns something other than a JSON array.
    """
    all_results: list[dict[str, Any]] = []
    request_params: dict[str, Any] = {"per_page": per_page}
    if params:
        request_params.update(params)

    next_url: str | None = url
    pages_read = 0
    while next_url:
        # Only the first request carries our params; later ones use the Link URL verbatim.
        response = api_session.get(
            next_url,
            params=request_params if pages_read == 0 else None,
            timeout=_TIMEOUT,
        )
        if allow_missing and response.status_code == 404:
            logger.debug("Netlify returned 404 for %s, treating as empty.", next_url)
            return []
        if allow_plan_gated and response.status_code == 403:
            logger.warning(
                "Netlify returned 403 Forbidden for %s, skipping (likely plan-gated).",
                next_url,
            )
            return all_results
        _warn_if_rate_limit_low(response)
        response.raise_for_status()

        data = response.json()
        # A few endpoints answer `null` rather than `[]` when the resource does not exist.
        if data is None:
            return all_results
        if not isinstance(data, list):
            raise NetlifyPaginationError(
                f"Expected a JSON array from {next_url} but got {type(data).__name__}; "
                f"refusing to hand a misread response to a cleanup job.",
            )
        all_results.extend(data)
        pages_read += 1

        link = response.links.get("next")
        if not link:
            break
        candidate = link.get("url")
        # A page that claims more results but cannot say where they are cannot be completed.
        # Returning what we have would let cleanup delete everything past this page.
        if not candidate or candidate == next_url:
            raise NetlifyPaginationError(
                f"Netlify advertised another page for {url} but returned an unusable next "
                f"link ({candidate!r}); refusing to continue with an incomplete result set.",
            )
        if pages_read >= _MAX_PAGES:
            raise NetlifyPaginationError(
                f"Netlify still advertised more pages for {url} after {_MAX_PAGES} pages; "
                f"refusing to continue with an incomplete result set.",
            )
        next_url = candidate

    return all_results


@timeit
def get_list(
    api_session: requests.Session,
    url: str,
    params: dict[str, Any] | None = None,
    result_key: str | None = None,
    allow_missing: bool = True,
) -> list[dict[str, Any]]:
    """
    Fetch a Netlify collection that is not paginated.

    Normalises the three shapes Netlify uses for such endpoints: a bare array, an envelope
    object holding the array under a key (`{"branches": [...]}`), and a bare object where the
    array would have had a single element (the site functions endpoint does this).

    :param api_session: Authenticated requests session.
    :param url: Full URL of the API endpoint.
    :param params: Query parameters.
    :param result_key: Envelope key holding the array, when the endpoint uses one.
    :param allow_missing: When True, a 404 or a JSON `null` body returns an empty list.
    :return: The collection.
    """
    response = api_session.get(url, params=params, timeout=_TIMEOUT)
    if allow_missing and response.status_code == 404:
        logger.debug("Netlify returned 404 for %s, treating as empty.", url)
        return []
    _warn_if_rate_limit_low(response)
    response.raise_for_status()

    data = response.json()
    if data is None:
        return []
    if result_key is not None:
        # Strict access: surface an endpoint/key mismatch instead of silently handing an empty
        # list to a cleanup job that would then delete everything.
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a JSON object with key '{result_key}' from {url} but got "
                f"{type(data).__name__}",
            )
        return data[result_key]
    if isinstance(data, dict):
        return [data]
    return data


@timeit
def get_one(
    api_session: requests.Session,
    url: str,
    params: dict[str, Any] | None = None,
    allow_missing: bool = True,
) -> dict[str, Any] | None:
    """
    Fetch a single Netlify object.

    :param api_session: Authenticated requests session.
    :param url: Full URL of the API endpoint.
    :param params: Query parameters.
    :param allow_missing: When True, a 404 or a JSON `null` body returns None. Netlify uses
        both to mean "this site does not have one of these" (for example a site with no
        custom domain answers `null` on the TLS certificate endpoint).
    :return: The object, or None when it does not exist.
    """
    response = api_session.get(url, params=params, timeout=_TIMEOUT)
    if allow_missing and response.status_code == 404:
        logger.debug("Netlify returned 404 for %s, treating as absent.", url)
        return None
    _warn_if_rate_limit_low(response)
    response.raise_for_status()
    data = response.json()
    if data is None:
        return None
    if not isinstance(data, dict):
        raise ValueError(
            f"Expected a JSON object from {url} but got {type(data).__name__}"
        )
    return data
