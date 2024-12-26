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


class PaginatedGraphqlData(NamedTuple):
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]


def handle_rate_limit_sleep(token: str) -> None:
    '''
    Check the remaining rate limit and sleep if remaining is below threshold
    :param token: The Github API token as string.
    '''
    response = requests.get('https://api.github.com/rate_limit', headers={'Authorization': f"token {token}"})
    response.raise_for_status()
    response_json = response.json()
    rate_limit_obj = response_json['resources']['graphql']
    remaining = rate_limit_obj['remaining']
    threshold = _GRAPHQL_RATE_LIMIT_REMAINING_THRESHOLD
    if remaining > threshold:
        return
    reset_at = datetime.fromtimestamp(rate_limit_obj['reset'], tz=tz.utc)
    now = datetime.now(tz.utc)
    # add an extra minute for safety
    sleep_duration = reset_at - now + timedelta(minutes=1)
    logger.warning(
        f'Github graphql ratelimit has {remaining} remaining and is under threshold {threshold},'
        f' sleeping until reset at {reset_at} for {sleep_duration}',
    )
    time.sleep(sleep_duration.seconds)


def call_github_api(query: str, variables: str, token: str, api_url: str) -> Dict:
    """
    Calls the GitHub v4 API and executes a query
    :param query: the GraphQL query to run
    :param variables: parameters for the query
    :param token: the Oauth token for the API
    :param api_url: the URL to call for the API
    :return: query results json
    """
    headers = {'Authorization': f"token {token}"}
    try:
        response = requests.post(
            api_url,
            json={'query': query, 'variables': variables},
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
            f'continuing sync.',
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
        'login': organization,
        'cursor': cursor,
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
            time.sleep(2 ** retry)
            continue

        if 'data' not in resp:
            logger.warning(
                f'Got no "data" attribute in response: {resp}. '
                f'Stopping requests for organization: {organization} and '
                f'resource_type: {resource_type}',
            )
            has_next_page = False
            continue

        resource = resp['data']['organization'][resource_type]
        if resource_inner_type:
            resource = resp['data']['organization'][resource_type][resource_inner_type]

        # Allow for paginating both nodes and edges fields of the GitHub GQL structure.
        data.nodes.extend(resource.get('nodes', []))
        data.edges.extend(resource.get('edges', []))

        cursor = resource['pageInfo']['endCursor']
        has_next_page = resource['pageInfo']['hasNextPage']
        if not org_data:
            org_data = {
                'url': resp['data']['organization']['url'],
                'login': resp['data']['organization']['login'],
            }

    if not org_data:
        raise ValueError(
            f"Didn't get any organization data for organization: {organization} and resource_type: {resource_type}",
        )
    return data, org_data
