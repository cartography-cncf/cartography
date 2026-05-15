import json
import logging
from datetime import datetime
from typing import Any
from urllib.parse import quote

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.github.util import fetch_all_rest_api_pages
from cartography.intel.github.util import github_org_url
from cartography.intel.github.util import rest_api_base_url
from cartography.models.github.personal_access_tokens import (
    GitHubPersonalAccessTokenSchema,
)
from cartography.util import timeit

logger = logging.getLogger(__name__)


def _to_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        logger.debug("Could not parse GitHub timestamp %r as ISO 8601.", value)
        return None


def _owner_user_url(
    org_url: str, owner: dict[str, Any] | None, login: str | None
) -> str | None:
    if owner:
        html_url = owner.get("html_url")
        if isinstance(html_url, str) and html_url:
            return html_url
    if not login:
        return None
    return f"{org_url.rsplit('/', 1)[0]}/{quote(login, safe='')}"


@timeit
def get_fine_grained_personal_access_tokens(
    token: Any,
    api_url: str,
    organization: str,
) -> list[dict[str, Any]]:
    """
    Fetch approved fine-grained PATs that can access organization resources.

    GitHub exposes this inventory only to GitHub Apps with the
    "Personal access tokens" organization read permission. A missing
    permission returns an empty list and no PATs are persisted for this run.
    """
    base_url = rest_api_base_url(api_url)
    endpoint = f"/orgs/{quote(organization, safe='')}/personal-access-tokens"
    try:
        return fetch_all_rest_api_pages(
            token,
            base_url,
            endpoint,
            "",
            params={"per_page": 100},
            raise_on_status=(403, 404),
        )
    except requests.exceptions.HTTPError as err:
        status = err.response.status_code if err.response is not None else None
        if status in (403, 404):
            logger.warning(
                "Skipping fine-grained personal access token inventory for "
                "GitHub org %s due to HTTP %s. This endpoint requires GitHub "
                "App authentication with Personal access tokens organization "
                "read permission.",
                organization,
                status,
            )
            return []
        raise


@timeit
def get_fine_grained_personal_access_token_repositories(
    token: Any,
    api_url: str,
    organization: str,
    pat_id: int,
) -> list[dict[str, Any]]:
    base_url = rest_api_base_url(api_url)
    endpoint = (
        f"/orgs/{quote(organization, safe='')}/personal-access-tokens/"
        f"{pat_id}/repositories"
    )
    try:
        return fetch_all_rest_api_pages(
            token,
            base_url,
            endpoint,
            "",
            params={"per_page": 100},
            raise_on_status=(403, 404),
        )
    except requests.exceptions.HTTPError as err:
        status = err.response.status_code if err.response is not None else None
        if status in (403, 404):
            logger.warning(
                "Skipping repository access for fine-grained personal access "
                "token %s in GitHub org %s due to HTTP %s.",
                pat_id,
                organization,
                status,
            )
            return []
        raise


@timeit
def get_saml_credential_authorizations(
    token: Any,
    api_url: str,
    organization: str,
) -> list[dict[str, Any]]:
    """
    Fetch classic PAT metadata exposed via SAML SSO credential authorizations.

    Only available for SAML SSO-enabled organizations. Returns an empty list
    when the endpoint is unavailable.
    """
    base_url = rest_api_base_url(api_url)
    endpoint = f"/orgs/{quote(organization, safe='')}/credential-authorizations"
    try:
        return fetch_all_rest_api_pages(
            token,
            base_url,
            endpoint,
            "",
            params={"per_page": 100},
            raise_on_status=(403, 404),
        )
    except requests.exceptions.HTTPError as err:
        status = err.response.status_code if err.response is not None else None
        if status in (403, 404):
            logger.warning(
                "Skipping SAML credential authorizations for GitHub org %s due "
                "to HTTP %s. Classic PAT inventory is only available through "
                "this endpoint for SAML SSO-enabled organizations.",
                organization,
                status,
            )
            return []
        raise


def _transform_fine_grained_token(
    raw_token: dict[str, Any],
    org_url: str,
    repository_urls: list[str],
) -> dict[str, Any] | None:
    pat_id = raw_token.get("id")
    if pat_id is None:
        logger.debug("Skipping fine-grained GitHub PAT without id.")
        return None
    owner = raw_token.get("owner") if isinstance(raw_token.get("owner"), dict) else None
    owner_login = owner.get("login") if owner else None
    owner_user_id = _owner_user_url(org_url, owner, owner_login)
    permissions = raw_token.get("permissions")
    return {
        "id": f"{org_url}/personal-access-tokens/{pat_id}",
        "token_kind": "fine_grained",
        "token_id": raw_token.get("token_id"),
        "token_name": raw_token.get("token_name"),
        "owner_login": owner_login,
        "owner_user_id": owner_user_id,
        "repository_selection": raw_token.get("repository_selection"),
        "permissions": (
            json.dumps(permissions, sort_keys=True) if permissions is not None else None
        ),
        "scopes": None,
        "access_granted_at": _to_datetime(raw_token.get("access_granted_at")),
        "credential_authorized_at": None,
        "credential_accessed_at": None,
        "expires_at": _to_datetime(raw_token.get("token_expires_at")),
        "last_used_at": _to_datetime(raw_token.get("token_last_used_at")),
        "repository_urls": repository_urls,
    }


def _transform_saml_credential_authorization(
    raw_credential: dict[str, Any],
    org_url: str,
) -> dict[str, Any] | None:
    if raw_credential.get("credential_type") != "personal access token":
        return None
    credential_id = raw_credential.get("credential_id")
    if credential_id is None:
        logger.debug("Skipping GitHub credential authorization without credential_id.")
        return None
    owner_login = raw_credential.get("login")
    owner_user_id = _owner_user_url(org_url, None, owner_login)
    # GitHub's SAML credential authorization endpoint reports credential_accessed_at
    # (auth events), which is not semantically equivalent to the fine-grained
    # token_last_used_at (API calls). Leave last_used_at unset for classic PATs;
    # credential_accessed_at remains available on its own property.
    return {
        "id": f"{org_url}/credential-authorizations/{credential_id}",
        "token_kind": "classic",
        "token_id": None,
        "token_name": None,
        "owner_login": owner_login,
        "owner_user_id": owner_user_id,
        "repository_selection": None,
        "permissions": None,
        "scopes": raw_credential.get("scopes") or [],
        "access_granted_at": None,
        "credential_authorized_at": _to_datetime(
            raw_credential.get("credential_authorized_at")
        ),
        "credential_accessed_at": _to_datetime(
            raw_credential.get("credential_accessed_at")
        ),
        "expires_at": _to_datetime(
            raw_credential.get("authorized_credential_expires_at")
        ),
        "last_used_at": None,
        "repository_urls": [],
    }


@timeit
def get(
    token: Any,
    api_url: str,
    organization: str,
) -> list[dict[str, Any]]:
    org_url = github_org_url(api_url, organization)
    transformed_tokens: list[dict[str, Any]] = []

    for raw_pat in get_fine_grained_personal_access_tokens(
        token, api_url, organization
    ):
        pat_id = raw_pat.get("id")
        if pat_id is None:
            continue
        repositories = get_fine_grained_personal_access_token_repositories(
            token,
            api_url,
            organization,
            pat_id,
        )
        repository_urls = [
            repo["html_url"]
            for repo in repositories
            if isinstance(repo.get("html_url"), str)
        ]
        transformed = _transform_fine_grained_token(raw_pat, org_url, repository_urls)
        if transformed:
            transformed_tokens.append(transformed)

    for raw_credential in get_saml_credential_authorizations(
        token, api_url, organization
    ):
        transformed = _transform_saml_credential_authorization(raw_credential, org_url)
        if transformed:
            transformed_tokens.append(transformed)

    return transformed_tokens


@timeit
def load_personal_access_tokens(
    neo4j_session: neo4j.Session,
    tokens: list[dict[str, Any]],
    org_url: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        GitHubPersonalAccessTokenSchema(),
        tokens,
        lastupdated=update_tag,
        org_url=org_url,
    )


@timeit
def cleanup_personal_access_tokens(
    neo4j_session: neo4j.Session,
    org_url: str,
    update_tag: int,
) -> None:
    GraphJob.from_node_schema(
        GitHubPersonalAccessTokenSchema(),
        {"UPDATE_TAG": update_tag, "org_url": org_url},
    ).run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
    token: Any,
    api_url: str,
    organization: str,
) -> None:
    org_url = github_org_url(api_url, organization)
    tokens = get(token, api_url, organization)
    load_personal_access_tokens(
        neo4j_session,
        tokens,
        org_url,
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup_personal_access_tokens(
        neo4j_session,
        org_url,
        common_job_parameters["UPDATE_TAG"],
    )
