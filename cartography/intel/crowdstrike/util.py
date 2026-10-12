from typing import Any

from falconpy.oauth2 import OAuth2


class CrowdstrikeAPIError(RuntimeError):
    pass


def get_authorization(client_id: str, client_secret: str, api_url: str) -> OAuth2:
    authorization = OAuth2(
        creds={"client_id": client_id, "client_secret": client_secret},
        base_url=api_url,
    )
    return authorization


def get_response_body(response: dict[str, Any], operation: str) -> dict[str, Any]:
    """
    Return the body of a falconpy response, raising if the call failed.

    falconpy returns a failed call as an ordinary response whose `resources` list
    is empty. Reading that as the end of the results lets a rate-limited or failed
    page truncate the sync, and the cleanup that follows then deletes everything
    the truncated sync did not see.
    """
    status_code = response.get("status_code")
    body = response.get("body")
    if status_code is None or not 200 <= status_code < 300:
        messages = [error.get("message") for error in (body or {}).get("errors") or []]
        raise CrowdstrikeAPIError(
            f"CrowdStrike {operation} failed with HTTP {status_code}: {messages}",
        )
    if not body:
        raise CrowdstrikeAPIError(
            f"CrowdStrike {operation} returned HTTP {status_code} with no body",
        )
    return body
