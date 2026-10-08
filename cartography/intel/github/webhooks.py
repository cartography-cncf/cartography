import logging
from typing import Any
from urllib.parse import quote
from urllib.parse import urlsplit

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.github.util import fetch_all_rest_api_pages
from cartography.intel.github.util import github_org_url
from cartography.intel.github.util import rest_api_base_url
from cartography.models.github.webhooks import GitHubWebhookSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


def _get_hooks(
    token: Any,
    api_url: str,
    endpoint: str,
) -> list[dict[str, Any]] | None:
    """
    Return the webhooks listed at `endpoint`, or None when GitHub denies the
    listing. GitHub answers 403 or 404 when the credential lacks the Webhooks
    permission or administrator access. Other failures propagate.
    """
    try:
        return fetch_all_rest_api_pages(
            token,
            rest_api_base_url(api_url),
            endpoint,
            "",
            params={"per_page": 100},
            raise_on_status=(403, 404),
        )
    except requests.exceptions.HTTPError as err:
        status = err.response.status_code if err.response is not None else None
        if status not in (403, 404):
            raise
        logger.debug("Could not list GitHub webhooks at %s: HTTP %s", endpoint, status)
        return None


@timeit
def get_organization_webhooks(
    token: Any,
    api_url: str,
    organization: str,
) -> list[dict[str, Any]] | None:
    """
    Fetch organization webhooks. Requires organization owner access with the
    organization **Webhooks: Read** permission or the classic `admin:org_hook`
    scope.
    """
    hooks = _get_hooks(token, api_url, f"/orgs/{quote(organization, safe='')}/hooks")
    if hooks is None:
        logger.warning(
            "Skipping GitHub organization webhooks for org %s. This endpoint "
            "requires organization owner access with the organization "
            "Webhooks: Read permission.",
            organization,
        )
    return hooks


@timeit
def get_repository_webhooks(
    token: Any,
    api_url: str,
    repo_fullname: str,
) -> list[dict[str, Any]] | None:
    """
    Fetch a repository's webhooks. Requires repository administrator access with
    the repository **Webhooks: Read** permission.
    """
    owner, _, name = repo_fullname.partition("/")
    return _get_hooks(
        token,
        api_url,
        f"/repos/{quote(owner, safe='')}/{quote(name, safe='')}/hooks",
    )


def transform(
    hook: dict[str, Any],
    organization_id: str | None = None,
    repository_id: str | None = None,
) -> dict[str, Any]:
    config = hook.get("config") or {}
    target = config.get("url")
    parsed = urlsplit(target) if target else None
    last_response = hook.get("last_response") or {}
    return {
        "id": hook["url"],
        "hook_id": hook.get("id"),
        "scope": "repository" if repository_id else "organization",
        "name": hook.get("name"),
        "active": hook.get("active"),
        "events": hook.get("events") or [],
        "content_type": config.get("content_type"),
        "target_scheme": parsed.scheme.lower() if parsed else None,
        "target_host": parsed.hostname if parsed else None,
        "uses_https": parsed.scheme.lower() == "https" if parsed else None,
        "insecure_ssl": (
            str(config["insecure_ssl"]) == "1" if "insecure_ssl" in config else None
        ),
        # GitHub masks a configured secret as "********" and omits it otherwise.
        "has_secret": bool(config.get("secret")),
        "last_response_code": last_response.get("code"),
        "last_response_status": last_response.get("status"),
        "created_at": hook.get("created_at"),
        "updated_at": hook.get("updated_at"),
        "organization_id": organization_id,
        "repository_id": repository_id,
    }


@timeit
def get(
    token: Any,
    api_url: str,
    organization: str,
    repos: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], bool]:
    """
    Return transformed organization and repository webhooks, and whether the
    inventory is complete enough to safely clean up stale webhooks.
    """
    org_url = github_org_url(api_url, organization)
    webhooks: list[dict[str, Any]] = []
    complete = True

    org_hooks = get_organization_webhooks(token, api_url, organization)
    if org_hooks is None:
        complete = False
    for hook in org_hooks or []:
        webhooks.append(transform(hook, organization_id=org_url))

    unavailable_repos = 0
    for repo in repos:
        fullname = repo.get("fullname")
        repo_url = repo.get("url")
        if not fullname or not repo_url:
            continue
        repo_hooks = get_repository_webhooks(token, api_url, fullname)
        if repo_hooks is None:
            unavailable_repos += 1
            continue
        for hook in repo_hooks:
            webhooks.append(transform(hook, repository_id=repo_url))
    if unavailable_repos:
        complete = False
        logger.warning(
            "Could not list webhooks for %d of %d GitHub repositories in org %s. "
            "Repository webhooks require the repository Webhooks: Read permission.",
            unavailable_repos,
            len(repos),
            organization,
        )
    return webhooks, complete


@timeit
def load_webhooks(
    neo4j_session: neo4j.Session,
    webhooks: list[dict[str, Any]],
    org_url: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        GitHubWebhookSchema(),
        webhooks,
        lastupdated=update_tag,
        org_url=org_url,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    org_url: str,
    update_tag: int,
) -> None:
    GraphJob.from_node_schema(
        GitHubWebhookSchema(),
        {"UPDATE_TAG": update_tag, "org_url": org_url},
    ).run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
    token: Any,
    api_url: str,
    organization: str,
    repos: list[dict[str, Any]],
) -> None:
    org_url = github_org_url(api_url, organization)
    update_tag = common_job_parameters["UPDATE_TAG"]
    webhooks, complete = get(token, api_url, organization, repos)
    load_webhooks(neo4j_session, webhooks, org_url, update_tag)
    if complete:
        cleanup(neo4j_session, org_url, update_tag)
    else:
        logger.warning(
            "Skipping GitHub webhook cleanup for org %s because the webhook "
            "inventory is incomplete.",
            organization,
        )
