import json
import logging
import time
from datetime import datetime
from datetime import timedelta
from datetime import timezone as tz
from typing import Any
from typing import Dict
from typing import List
from typing import NamedTuple
from typing import Optional
from typing import Tuple

import requests

logger = logging.getLogger(__name__)
# Connect and read timeouts of 60 seconds each; see https://requests.readthedocs.io/en/master/user/advanced/#timeouts
_TIMEOUT = (60, 60)
_GRAPHQL_RATE_LIMIT_REMAINING_THRESHOLD = 500
_REST_RATE_LIMIT_REMAINING_THRESHOLD = 100


class PaginatedGraphqlData(NamedTuple):
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]


def handle_rate_limit_sleep(token: str) -> None:
    """
    Check the remaining rate limit and sleep if remaining is below threshold
    :param token: The Github API token as string.
    """
    response = requests.get(
        "https://api.github.com/rate_limit",
        headers={"Authorization": f"token {token}"},
    )
    response.raise_for_status()
    response_json = response.json()
    rate_limit_obj = response_json["resources"]["graphql"]
    remaining = rate_limit_obj["remaining"]
    threshold = _GRAPHQL_RATE_LIMIT_REMAINING_THRESHOLD
    if remaining > threshold:
        return
    reset_at = datetime.fromtimestamp(rate_limit_obj["reset"], tz=tz.utc)
    now = datetime.now(tz.utc)
    # add an extra minute for safety
    sleep_duration = reset_at - now + timedelta(minutes=1)
    logger.warning(
        f"Github graphql ratelimit has {remaining} remaining and is under threshold {threshold},"
        f" sleeping until reset at {reset_at} for {sleep_duration}",
    )
    time.sleep(sleep_duration.total_seconds())


def call_github_api(query: str, variables: str, token: str, api_url: str) -> Dict:
    """
    Calls the GitHub v4 API and executes a query
    :param query: the GraphQL query to run
    :param variables: parameters for the query
    :param token: the Oauth token for the API
    :param api_url: the URL to call for the API
    :return: query results json
    """
    headers = {"Authorization": f"token {token}"}
    try:
        response = requests.post(
            api_url,
            json={"query": query, "variables": variables},
            headers=headers,
            timeout=_TIMEOUT,
        )
    except requests.exceptions.Timeout:
        # Add context and re-raise for callers to handle
        logger.warning("GitHub: requests.get('%s') timed out.", api_url)
        raise
    response.raise_for_status()
    response_json = response.json()
    if "errors" in response_json:
        logger.warning(
            f'call_github_api() response has errors, please investigate. Raw response: {response_json["errors"]}; '
            f"continuing sync.",
        )
    return response_json  # type: ignore


def fetch_page(
    token: str,
    api_url: str,
    organization: str,
    query: str,
    cursor: Optional[str] = None,
    **kwargs: Any,
) -> Dict[str, Any]:
    """
    Return a single page of max size 100 elements from the Github api_url using the given `query` and `cursor` params.
    :param token: The API token as string. Must have permission for the object being paginated.
    :param api_url: The Github API endpoint as string.
    :param organization: The name of the target Github organization as string.
    :param query: The GraphQL query, e.g. `GITHUB_ORG_USERS_PAGINATED_GRAPHQL`
    :param cursor: The GraphQL cursor string (behaves like a page number) for Github objects in the given
    organization. If None, the Github API will return the first page of repos.
    :param kwargs: Other keyword args to add as key-value pairs to the GraphQL query.
    :return: The raw response object from the requests.get().json() call.
    """
    gql_vars = {
        **kwargs,
        "login": organization,
        "cursor": cursor,
    }
    gql_vars_json = json.dumps(gql_vars)
    response = call_github_api(query, gql_vars_json, token, api_url)
    return response


def fetch_all(
    token: str,
    api_url: str,
    organization: str,
    query: str,
    resource_type: str,
    retries: int = 5,
    resource_inner_type: Optional[str] = None,
    **kwargs: Any,
) -> Tuple[PaginatedGraphqlData, Dict[str, Any]]:
    """
    Fetch and return all data items of the given `resource_type` and `field_name` from Github's paginated GraphQL API as
    a list, along with information on the organization that they belong to.
    :param token: The Github API token as string.
    :param api_url: The Github v4 API endpoint as string.
    :param organization: The name of the target Github organization as string.
    :param query: The GraphQL query, e.g. `GITHUB_ORG_USERS_PAGINATED_GRAPHQL`
    :param resource_type: The name of the paginated resource under the organization e.g. `membersWithRole` or
    `repositories`. See the fields under https://docs.github.com/en/graphql/reference/objects#organization for a full
    list.
    :param retries: Number of retries to perform.  Github APIs are often flakey and retrying the request helps.
    :param resource_inner_type: Optional str. Default = None. Sometimes we need to paginate a field that is inside
    `resource_type` - for example: organization['team']['repositories']. In this case, we specify 'repositories' as the
    `resource_inner_type`.
    :param kwargs: Additional key-value args (other than `login` and `cursor`) to pass to the GraphQL query variables.
    :return: A 2-tuple containing 1. A list of data items of the given `resource_type` and `field_name`,  and 2. a dict
    containing the `url` and the `login` fields of the organization that the items belong to.
    """
    cursor = None
    has_next_page = True
    org_data: Dict[str, Any] = {}
    data: PaginatedGraphqlData = PaginatedGraphqlData(nodes=[], edges=[])
    retry = 0

    while has_next_page:
        exc: Any = None
        try:
            # In the future, we may use also use the rateLimit object from the graphql response.
            # But we still need at least one call to the REST endpoint in case the graphql remaining is already 0
            handle_rate_limit_sleep(token)
            resp = fetch_page(token, api_url, organization, query, cursor, **kwargs)
            retry = 0
        except requests.exceptions.Timeout as err:
            retry += 1
            exc = err
        except requests.exceptions.HTTPError as err:
            if (
                err.response is not None
                and err.response.status_code == 502
                and kwargs.get("count")
                and kwargs["count"] > 1
            ):
                kwargs["count"] = max(1, kwargs["count"] // 2)
                logger.warning(
                    "GitHub: Received 502 response. Reducing page size to %s and retrying.",
                    kwargs["count"],
                )
                continue
            retry += 1
            exc = err
        except requests.exceptions.ChunkedEncodingError as err:
            retry += 1
            exc = err

        if retry >= retries:
            logger.error(
                f"GitHub: Could not retrieve page of resource `{resource_type}` due to HTTP error "
                f"after {retry} retries. Raising exception.",
                exc_info=True,
            )
            raise exc
        elif retry > 0:
            time.sleep(2**retry)
            continue

        if "data" not in resp:
            logger.warning(
                f'Got no "data" attribute in response: {resp}. '
                f"Stopping requests for organization: {organization} and "
                f"resource_type: {resource_type}",
            )
            has_next_page = False
            continue

        resource = resp["data"]["organization"][resource_type]
        if resource_inner_type:
            resource = resp["data"]["organization"][resource_type][resource_inner_type]

        # Allow for paginating both nodes and edges fields of the GitHub GQL structure.
        data.nodes.extend(resource.get("nodes", []))
        data.edges.extend(resource.get("edges", []))

        cursor = resource["pageInfo"]["endCursor"]
        has_next_page = resource["pageInfo"]["hasNextPage"]
        if not org_data:
            org_data = {
                "url": resp["data"]["organization"]["url"],
                "login": resp["data"]["organization"]["login"],
            }

    if not org_data:
        raise ValueError(
            f"Didn't get any organization data for organization: {organization} and resource_type: {resource_type}",
        )
    return data, org_data


def _get_rest_api_base_url(graphql_url: str) -> str:
    """
    Convert a GitHub GraphQL API URL to a REST API base URL.

    For github.com: https://api.github.com/graphql -> https://api.github.com
    For GitHub Enterprise: https://github.example.com/api/graphql -> https://github.example.com/api/v3

    :param graphql_url: The GitHub GraphQL API URL
    :return: The REST API base URL
    """
    if "api.github.com" in graphql_url:
        return "https://api.github.com"
    # GitHub Enterprise URL format
    # e.g., https://github.example.com/api/graphql -> https://github.example.com/api/v3
    base = graphql_url.replace("/graphql", "").rstrip("/")
    if not base.endswith("/v3"):
        base = f"{base}/v3"
    return base


def handle_rest_rate_limit_sleep(token: str, base_url: str) -> None:
    """
    Check the remaining REST API rate limit and sleep if remaining is below threshold.

    :param token: The GitHub API token as string.
    :param base_url: The REST API base URL.
    """
    rate_limit_url = f"{base_url}/rate_limit"
    response = requests.get(
        rate_limit_url,
        headers={"Authorization": f"token {token}"},
        timeout=_TIMEOUT,
    )
    response.raise_for_status()
    response_json = response.json()
    rate_limit_obj = response_json["resources"]["core"]
    remaining = rate_limit_obj["remaining"]
    threshold = _REST_RATE_LIMIT_REMAINING_THRESHOLD
    if remaining > threshold:
        return
    reset_at = datetime.fromtimestamp(rate_limit_obj["reset"], tz=tz.utc)
    now = datetime.now(tz.utc)
    sleep_duration = reset_at - now + timedelta(minutes=1)
    logger.warning(
        f"GitHub REST API rate limit has {remaining} remaining and is under threshold {threshold}, "
        f"sleeping until reset at {reset_at} for {sleep_duration}",
    )
    time.sleep(sleep_duration.total_seconds())


def fetch_all_rest_api_pages(
    token: str,
    base_url: str,
    endpoint: str,
    result_key: str,
    retries: int = 5,
) -> list[dict[str, Any]]:
    """
    Fetch all pages from a GitHub REST API endpoint using Link header pagination.

    :param token: The GitHub API token as string.
    :param base_url: The REST API base URL (e.g., https://api.github.com).
    :param endpoint: The API endpoint path (e.g., /repos/{owner}/{repo}/actions/workflows).
    :param result_key: The key in the response JSON that contains the list of results
                       (e.g., 'workflows', 'secrets', 'variables').
    :param retries: Number of retries to perform on transient errors.
    :return: A list of all items from all pages.
    """
    results: list[dict[str, Any]] = []
    url: str | None = f"{base_url}{endpoint}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    retry = 0

    while url:
        exc: Any = None
        try:
            handle_rest_rate_limit_sleep(token, base_url)
            response = requests.get(url, headers=headers, timeout=_TIMEOUT)
            response.raise_for_status()
            retry = 0
        except requests.exceptions.Timeout as err:
            retry += 1
            exc = err
        except requests.exceptions.HTTPError as err:
            # Handle 404 gracefully - resource may not exist (e.g., no environments)
            if err.response is not None and err.response.status_code == 404:
                logger.debug(f"GitHub REST API: 404 for {url}, returning empty list")
                return []
            # Handle 403 gracefully
            if err.response is not None and err.response.status_code == 403:
                logger.warning(
                    f"GitHub REST API: 403 Forbidden for {url}. "
                    "This is likely due to insufficient permissions. "
                    "Skipping this resource and continuing.",
                )
                return []
            retry += 1
            exc = err
        except requests.exceptions.ChunkedEncodingError as err:
            retry += 1
            exc = err

        if retry >= retries:
            logger.error(
                f"GitHub REST API: Could not retrieve {url} after {retry} retries. Raising exception.",
                exc_info=True,
            )
            raise exc
        elif retry > 0:
            time.sleep(2**retry)
            continue

        response_json = response.json()

        # Some endpoints return a list directly, others wrap in an object
        if isinstance(response_json, list):
            results.extend(response_json)
        elif result_key in response_json:
            results.extend(response_json[result_key])
        else:
            logger.warning(
                f"GitHub REST API: Expected key '{result_key}' not found in response from {url}",
            )

        # Parse Link header for pagination
        url = None
        link_header = response.headers.get("Link", "")
        if link_header:
            for link in link_header.split(","):
                if 'rel="next"' in link:
                    # Extract URL from <url>; rel="next"
                    url = link.split(";")[0].strip().strip("<>")
                    break

    return results
