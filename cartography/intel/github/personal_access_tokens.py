import json
import logging
from dataclasses import dataclass
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
    GitHubClassicPersonalAccessTokenCleanupSchema,
)
from cartography.models.github.personal_access_tokens import (
    GitHubFineGrainedPersonalAccessTokenCleanupSchema,
)
from cartography.models.github.personal_access_tokens import (
    GitHubPersonalAccessTokenSchema,
)
from cartography.util import timeit

logger = logging.getLogger(__name__)

FINE_GRAINED_PAT_SOURCE = "fine_grained_personal_access_tokens"
CLASSIC_PAT_SOURCE = "saml_credential_authorizations"


@dataclass(frozen=True)
class PersonalAccessTokensFetchResult:
    tokens: list[dict[str, Any]]
    cleanup_safe_sources: set[str]


def _owner_url_from_login(org_url: str, login: str | None) -> str | None:
    if not login:
        return None
    return f"{org_url.rsplit('/', 1)[0]}/{quote(login, safe='')}"


def _owner_user_id(owner: dict[str, Any] | None, org_url: str) -> str | None:
    if not owner:
        return None
    html_url = owner.get("html_url")
    if isinstance(html_url, str) and html_url:
        return html_url
    login = owner.get("login")
    return _owner_url_from_login(org_url, login if isinstance(login, str) else None)


@timeit
def get_fine_grained_personal_access_tokens(
    token: Any,
    api_url: str,
    organization: str,
) -> tuple[list[dict[str, Any]], bool]:
    """
    Fetch approved fine-grained PATs that can access organization resources.

    GitHub currently exposes this inventory only to GitHub Apps with the
    "Personal access tokens" organization read permission. Missing permission
    or endpoint availability is not cleanup-safe.
    """
    base_url = rest_api_base_url(api_url)
    endpoint = f"/orgs/{quote(organization, safe='')}/personal-access-tokens"
    params: dict[str, Any] = {"per_page": 100}
    try:
        return (
            fetch_all_rest_api_pages(
                token,
                base_url,
                endpoint,
                "",
                params=params,
                raise_on_status=(403, 404),
            ),
            True,
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
            return [], False
        raise


@timeit
def get_fine_grained_personal_access_token_repositories(
    token: Any,
    api_url: str,
    organization: str,
    pat_id: int,
) -> tuple[list[dict[str, Any]], bool]:
    """
    Fetch repositories a fine-grained PAT can access.

    A per-token repository fetch failure means the fine-grained PAT source was
    not fully refreshed, so source cleanup must be skipped for this run.
    """
    base_url = rest_api_base_url(api_url)
    endpoint = (
        f"/orgs/{quote(organization, safe='')}/personal-access-tokens/"
        f"{pat_id}/repositories"
    )
    params: dict[str, Any] = {"per_page": 100}
    try:
        return (
            fetch_all_rest_api_pages(
                token,
                base_url,
                endpoint,
                "",
                params=params,
                raise_on_status=(403, 404),
            ),
            True,
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
            return [], False
        raise


@timeit
def get_saml_credential_authorizations(
    token: Any,
    api_url: str,
    organization: str,
) -> tuple[list[dict[str, Any]], bool]:
    """
    Fetch classic PAT metadata exposed via SAML SSO credential authorizations.

    This endpoint exists for SAML SSO-enabled organizations and includes both
    PATs and SSH keys. Missing permission or endpoint availability is not
    cleanup-safe.
    """
    base_url = rest_api_base_url(api_url)
    endpoint = f"/orgs/{quote(organization, safe='')}/credential-authorizations"
    params: dict[str, Any] = {"per_page": 100}
    try:
        return (
            fetch_all_rest_api_pages(
                token,
                base_url,
                endpoint,
                "",
                params=params,
                raise_on_status=(403, 404),
            ),
            True,
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
            return [], False
        raise


def _transform_fine_grained_token(
    raw_token: dict[str, Any],
    org_url: str,
    repository_urls: list[str],
) -> dict[str, Any] | None:
    provider_id = raw_token.get("id")
    if provider_id is None:
        logger.debug("Skipping fine-grained GitHub PAT without id.")
        return None
    owner = raw_token.get("owner") if isinstance(raw_token.get("owner"), dict) else None
    permissions = raw_token.get("permissions")
    return {
        "id": f"{org_url}/personal-access-tokens/{provider_id}",
        "token_kind": "fine_grained",
        "source": FINE_GRAINED_PAT_SOURCE,
        "provider_id": str(provider_id),
        "token_id": raw_token.get("token_id"),
        "token_name": raw_token.get("token_name"),
        "owner_login": owner.get("login") if owner else None,
        "owner_user_id": _owner_user_id(owner, org_url),
        "repository_selection": raw_token.get("repository_selection"),
        "permissions": (
            json.dumps(permissions, sort_keys=True) if permissions is not None else None
        ),
        "scopes": None,
        "access_granted_at": raw_token.get("access_granted_at"),
        "credential_authorized_at": None,
        "credential_accessed_at": None,
        "expires_at": raw_token.get("token_expires_at"),
        "last_used_at": raw_token.get("token_last_used_at"),
        "expired": raw_token.get("token_expired"),
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
    if not isinstance(owner_login, str):
        owner_login = None
    return {
        "id": f"{org_url}/credential-authorizations/{credential_id}",
        "token_kind": "classic",
        "source": CLASSIC_PAT_SOURCE,
        "provider_id": str(credential_id),
        "token_id": None,
        "token_name": None,
        "owner_login": owner_login,
        "owner_user_id": _owner_url_from_login(org_url, owner_login),
        "repository_selection": None,
        "permissions": None,
        "scopes": raw_credential.get("scopes") or [],
        "access_granted_at": None,
        "credential_authorized_at": raw_credential.get("credential_authorized_at"),
        "credential_accessed_at": raw_credential.get("credential_accessed_at"),
        "expires_at": raw_credential.get("authorized_credential_expires_at"),
        "last_used_at": raw_credential.get("credential_accessed_at"),
        "expired": None,
        "repository_urls": [],
    }


@timeit
def get(
    token: Any,
    api_url: str,
    organization: str,
) -> PersonalAccessTokensFetchResult:
    org_url = github_org_url(api_url, organization)
    cleanup_safe_sources: set[str] = set()
    transformed_tokens: list[dict[str, Any]] = []

    fine_grained_tokens, fine_grained_cleanup_safe = (
        get_fine_grained_personal_access_tokens(token, api_url, organization)
    )
    if fine_grained_cleanup_safe:
        cleanup_safe_sources.add(FINE_GRAINED_PAT_SOURCE)

    for raw_pat in fine_grained_tokens:
        pat_id = raw_pat.get("id")
        if not isinstance(pat_id, int):
            logger.debug("Skipping repository access fetch for PAT without integer id.")
            fine_grained_cleanup_safe = False
            cleanup_safe_sources.discard(FINE_GRAINED_PAT_SOURCE)
            continue
        repositories, repositories_cleanup_safe = (
            get_fine_grained_personal_access_token_repositories(
                token,
                api_url,
                organization,
                pat_id,
            )
        )
        if not repositories_cleanup_safe:
            fine_grained_cleanup_safe = False
            cleanup_safe_sources.discard(FINE_GRAINED_PAT_SOURCE)
        repository_urls = [
            repo["html_url"]
            for repo in repositories
            if isinstance(repo.get("html_url"), str)
        ]
        transformed = _transform_fine_grained_token(raw_pat, org_url, repository_urls)
        if transformed:
            transformed_tokens.append(transformed)

    saml_credentials, saml_cleanup_safe = get_saml_credential_authorizations(
        token,
        api_url,
        organization,
    )
    if saml_cleanup_safe:
        cleanup_safe_sources.add(CLASSIC_PAT_SOURCE)

    for raw_credential in saml_credentials:
        transformed = _transform_saml_credential_authorization(raw_credential, org_url)
        if transformed:
            transformed_tokens.append(transformed)

    return PersonalAccessTokensFetchResult(
        tokens=transformed_tokens,
        cleanup_safe_sources=cleanup_safe_sources,
    )


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
    cleanup_safe_sources: set[str],
) -> None:
    common_job_parameters = {
        "UPDATE_TAG": update_tag,
        "org_url": org_url,
    }
    if FINE_GRAINED_PAT_SOURCE in cleanup_safe_sources:
        GraphJob.from_node_schema(
            GitHubFineGrainedPersonalAccessTokenCleanupSchema(),
            common_job_parameters,
        ).run(neo4j_session)
    if CLASSIC_PAT_SOURCE in cleanup_safe_sources:
        GraphJob.from_node_schema(
            GitHubClassicPersonalAccessTokenCleanupSchema(),
            common_job_parameters,
        ).run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
    token: Any,
    api_url: str,
    organization: str,
) -> PersonalAccessTokensFetchResult:
    org_url = github_org_url(api_url, organization)
    result = get(token, api_url, organization)
    load_personal_access_tokens(
        neo4j_session,
        result.tokens,
        org_url,
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup_personal_access_tokens(
        neo4j_session,
        org_url,
        common_job_parameters["UPDATE_TAG"],
        result.cleanup_safe_sources,
    )
    return result
