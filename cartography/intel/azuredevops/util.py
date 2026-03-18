import base64
import logging
import time
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

import requests
from azure.identity import ClientSecretCredential

logger = logging.getLogger(__name__)
TIMEOUT = (60, 60)
MAX_RETRIES = 3
RETRY_DELAY = 1


def get_access_token(
    tenant_id: str, client_id: str, client_secret: str, refresh_token: str = None,
) -> str:
    """
    Exchanges client credentials for an OAuth 2.0 access token using Microsoft Entra ID.
    """
    credential = ClientSecretCredential(
        tenant_id=tenant_id,
        client_id=client_id,
        client_secret=client_secret,
    )
    access_token = credential.get_token("499b84ac-1321-427f-aa17-267ca6975798/.default")
    return access_token.token


def call_azure_devops_api(
    url: str,
    access_token: str,
    method: str = "GET",
    params: Optional[Dict] = None,
    json_data: Optional[Dict] = None,
) -> Tuple[Optional[Dict], Optional[Dict]]:
    """
    Calls the Azure DevOps REST API with Microsoft Entra ID OAuth authentication.
    """
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {access_token}"
    }

    for attempt in range(MAX_RETRIES):
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=json_data,
                timeout=TIMEOUT,
            )
            response.raise_for_status()

            if response.status_code == 204:  # No Content
                return None, None
            return response.json(), response.headers

        except requests.exceptions.HTTPError as e:
            if (
                e.response.status_code in [429, 500, 502, 503, 504] and
                attempt < MAX_RETRIES - 1
            ):
                # Retry on rate limiting and server errors
                retry_after = int(e.response.headers.get("Retry-After", RETRY_DELAY))
                logger.warning(
                    f"HTTP {e.response.status_code} error, retrying in {retry_after} seconds (attempt {attempt + 1}/{MAX_RETRIES})",
                )
                time.sleep(retry_after)
                continue
            else:
                # Log detailed error information for debugging
                error_details = {
                    "status_code": e.response.status_code,
                    "url": url,
                    "response_text": e.response.text[
                        :500
                    ],  # Limit response text length
                    "headers": dict(e.response.headers),
                }
                logger.error(
                    f"HTTP error calling Azure DevOps API: {e}. "
                    f"Details: {error_details}",
                )
                return None, None

        except requests.exceptions.RequestException as e:
            if attempt < MAX_RETRIES - 1:
                logger.warning(
                    f"Request error, retrying in {RETRY_DELAY} seconds (attempt {attempt + 1}/{MAX_RETRIES}): {e}",
                )
                time.sleep(RETRY_DELAY)
                continue
            else:
                logger.error(
                    f"Failed to call Azure DevOps API at {url} after {MAX_RETRIES} attempts: {e}",
                )
                return None, None

    return None, None


def call_azure_devops_api_pagination(
    url: str,
    access_token: str,
    params: Optional[Dict] = None,
) -> List[Dict]:
    """
    Calls the Azure DevOps REST API and handles pagination for list endpoints.
    """
    results: List[Dict] = []
    current_url = url
    current_params = params.copy() if params else {}

    while current_url:
        response, headers = call_azure_devops_api(
            current_url, access_token, params=current_params,
        )
        if not response:
            break

        page_results = response.get("value", response.get("items", []))
        if not isinstance(page_results, list):
            logger.warning(
                f"Pagination call did not return a list for URL {current_url}. Stopping pagination.",
            )
            if page_results:  # If it's a single dict, wrap it in a list
                results.append(page_results)
            break

        results.extend(page_results)

        # Check for continuation token in the headers
        continuation_token = headers.get("x-ms-continuationtoken")
        if continuation_token:
            from urllib.parse import urlencode, urlparse, parse_qs, urlunparse

            parsed_url = urlparse(current_url)
            query_params = parse_qs(parsed_url.query)
            query_params["continuationToken"] = [continuation_token]

            # Ensure api-version is preserved
            if (
                "api-version" not in query_params and
                current_params and
                current_params.get("api-version")
            ):
                query_params["api-version"] = [current_params["api-version"]]

            new_query = urlencode(query_params, doseq=True)
            current_url = urlunparse(parsed_url._replace(query=new_query))
            current_params = None  # Params are now embedded in the URL
        else:
            # If no continuation token, assume the API returned all results.
            current_url = None

    return results


def validate_organization_data(data: Dict) -> bool:
    """
    Validates organization data from Azure DevOps API.

    Required fields:
    - name: Organization name
    - url: Organization URL
    """
    required_fields = ["name", "url"]
    return all(field in data and data[field] for field in required_fields)


def validate_project_data(data: Dict) -> bool:
    """
    Validates project data from Azure DevOps API.

    Required fields:
    - id: Project ID
    - name: Project name
    - url: Project URL
    """
    required_fields = ["id", "name", "url"]
    return all(field in data and data[field] for field in required_fields)


def validate_repository_data(data: Dict) -> bool:
    """
    Validates repository data from Azure DevOps API.

    Required fields:
    - id: Repository ID
    - name: Repository name
    - url: Repository URL
    """
    required_fields = ["id", "name", "url"]
    return all(field in data and data[field] for field in required_fields)


def validate_user_data(data: Dict) -> bool:
    """
    Validates user data from Azure DevOps API.

    Required fields:
    - id: User ID
    - user: User object containing displayName and principalName
    """
    required_fields = ["id", "user"]
    if not all(field in data and data[field] for field in required_fields):
        return False

    user = data.get("user", {})
    user_required_fields = ["displayName", "principalName"]
    return all(field in user and user[field] for field in user_required_fields)
