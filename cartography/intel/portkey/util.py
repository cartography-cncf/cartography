import json
from collections.abc import Generator
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry

# Connect and read timeouts of 60 seconds each.
_TIMEOUT = (60, 60)


def create_api_session(api_key: str) -> requests.Session:
    api_session = requests.session()
    retry_policy = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    api_session.mount("https://", HTTPAdapter(max_retries=retry_policy))
    api_session.headers.update({"x-portkey-api-key": api_key})
    return api_session


def json_dumps(value: Any) -> str | None:
    if value is None:
        return None
    return json.dumps(value, sort_keys=True)


def paginated_get(
    api_session: requests.Session,
    url: str,
    timeout: tuple[int, int],
    *,
    current_page_param: str = "current_page",
    page_size_param: str = "page_size",
    page_size: int = 100,
    extra_params: dict[str, Any] | None = None,
    data_key: str = "data",
) -> Generator[dict[str, Any], None, None]:
    current_page = 0
    while True:
        params = {
            current_page_param: current_page,
            page_size_param: page_size,
        }
        if extra_params:
            params.update(extra_params)
        req = api_session.get(url, params=params, timeout=timeout)
        req.raise_for_status()
        result = req.json()
        items = result.get(data_key, [])
        if not items:
            break
        yield from items
        total = result.get("total")
        if total is None:
            if len(items) < page_size:
                break
        elif (current_page + 1) * page_size >= total:
            break
        current_page += 1


def list_admin_users(
    api_session: requests.Session,
    base_url: str,
) -> list[dict[str, Any]]:
    return list(
        paginated_get(
            api_session,
            f"{base_url}/admin/users",
            _TIMEOUT,
            current_page_param="currentPage",
            page_size_param="pageSize",
            page_size=100,
        )
    )


def list_user_invites(
    api_session: requests.Session,
    base_url: str,
) -> list[dict[str, Any]]:
    return list(
        paginated_get(
            api_session,
            f"{base_url}/admin/users/invites",
            _TIMEOUT,
            current_page_param="currentPage",
            page_size_param="pageSize",
            page_size=100,
        )
    )


def list_workspaces(
    api_session: requests.Session,
    base_url: str,
) -> list[dict[str, Any]]:
    return list(
        paginated_get(
            api_session,
            f"{base_url}/admin/workspaces",
            _TIMEOUT,
            page_size=100,
        )
    )


def list_workspace_members(
    api_session: requests.Session,
    base_url: str,
    workspace_id: str,
) -> list[dict[str, Any]]:
    return list(
        paginated_get(
            api_session,
            f"{base_url}/admin/workspaces/{workspace_id}/users",
            _TIMEOUT,
            page_size=100,
        )
    )


def list_api_keys(
    api_session: requests.Session,
    base_url: str,
) -> list[dict[str, Any]]:
    return list(paginated_get(api_session, f"{base_url}/api-keys", _TIMEOUT))


def retrieve_api_key(
    api_session: requests.Session,
    base_url: str,
    api_key_id: str,
) -> dict[str, Any]:
    req = api_session.get(f"{base_url}/api-keys/{api_key_id}", timeout=_TIMEOUT)
    req.raise_for_status()
    return req.json()


def list_virtual_keys(
    api_session: requests.Session,
    base_url: str,
) -> list[dict[str, Any]]:
    return list(paginated_get(api_session, f"{base_url}/virtual-keys", _TIMEOUT))


def list_configs(
    api_session: requests.Session,
    base_url: str,
) -> list[dict[str, Any]]:
    return list(
        paginated_get(
            api_session,
            f"{base_url}/configs",
            _TIMEOUT,
            data_key="data",
        )
    )


def list_integrations(
    api_session: requests.Session,
    base_url: str,
) -> list[dict[str, Any]]:
    return list(paginated_get(api_session, f"{base_url}/integrations", _TIMEOUT))


def list_mcp_integrations(
    api_session: requests.Session,
    base_url: str,
    organisation_id: str,
) -> list[dict[str, Any]]:
    return list(
        paginated_get(
            api_session,
            f"{base_url}/mcp-integrations",
            _TIMEOUT,
            extra_params={"organisation_id": organisation_id},
        )
    )


def list_mcp_servers(
    api_session: requests.Session,
    base_url: str,
    workspace_id: str,
) -> list[dict[str, Any]]:
    return list(
        paginated_get(
            api_session,
            f"{base_url}/mcp-servers",
            _TIMEOUT,
            extra_params={"workspace_id": workspace_id},
        )
    )


def list_providers(
    api_session: requests.Session,
    base_url: str,
    workspace_id: str,
) -> list[dict[str, Any]]:
    return list(
        paginated_get(
            api_session,
            f"{base_url}/providers",
            _TIMEOUT,
            extra_params={"workspace_id": workspace_id},
        )
    )


def list_guardrails(
    api_session: requests.Session,
    base_url: str,
) -> list[dict[str, Any]]:
    return list(paginated_get(api_session, f"{base_url}/guardrails", _TIMEOUT))


def list_prompt_collections(
    api_session: requests.Session,
    base_url: str,
    workspace_id: str,
) -> list[dict[str, Any]]:
    return list(
        paginated_get(
            api_session,
            f"{base_url}/collections",
            _TIMEOUT,
            extra_params={"workspace_id": workspace_id},
        )
    )


def list_prompts(
    api_session: requests.Session,
    base_url: str,
    workspace_id: str,
) -> list[dict[str, Any]]:
    return list(
        paginated_get(
            api_session,
            f"{base_url}/prompts",
            _TIMEOUT,
            extra_params={"workspace_id": workspace_id},
        )
    )


def list_secret_references(
    api_session: requests.Session,
    base_url: str,
) -> list[dict[str, Any]]:
    return list(
        paginated_get(
            api_session,
            f"{base_url}/secret-references",
            _TIMEOUT,
        )
    )
