import logging
import re
from collections.abc import Iterator
from datetime import datetime
from datetime import timezone
from typing import Any
from urllib.parse import parse_qs
from urllib.parse import quote
from urllib.parse import urljoin
from urllib.parse import urlsplit

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.jira.access import resource_id
from cartography.intel.jira.util import JiraClient
from cartography.intel.jira.util import require_array
from cartography.models.jira.automation import JiraAutomationRuleSchema
from cartography.util import DEFAULT_MAX_PAGES
from cartography.util import timeit

logger = logging.getLogger(__name__)

_GITHUB_REPO_PATH_RE = re.compile(r"^/repos/([^/]+)/([^/]+)(?:/.*)?$")
# Jira-global rules use the Jira site ARI. Project-type rules use a product site ARI
# such as ari:cloud:jira-software::site/<cloudId>, so they are not global.
_JIRA_SITE_SCOPE_RE = re.compile(r"^ari:cloud:jira:[^:]*:site/[^/]+$")
_SLACK_WEBHOOK_PATH_RE = re.compile(r"^/services/(T[A-Z0-9]+)/[^/]+/[^/]+(?:/.*)?$")
_OUTGOING_COMPONENT_TYPES = frozenset(
    {"jira.issue.outgoing.webhook", "slack.notification"}
)


def parse_outgoing_target(url: str) -> tuple[str, str | None, str | None]:
    """Extract only the lowercase host and non-secret GitHub/Slack target IDs from a URL."""
    if not isinstance(url, str) or not url.strip():
        return ("", None, None)
    try:
        parsed = urlsplit(url.strip())
    except ValueError:
        return ("", None, None)
    if parsed.scheme.lower() not in ("http", "https"):
        return ("", None, None)
    if (
        "{{" in parsed.netloc
        or "}}" in parsed.netloc
        or "{{" in parsed.path
        or "}}" in parsed.path
    ):
        return ("", None, None)
    host = (parsed.hostname or "").lower()
    if not host:
        return ("", None, None)

    github_repository_id: str | None = None
    slack_team_id: str | None = None

    if host == "api.github.com":
        match = _GITHUB_REPO_PATH_RE.match(parsed.path)
        if match:
            github_repository_id = (
                f"https://github.com/{match.group(1)}/{match.group(2)}"
            )
    elif host == "hooks.slack.com":
        match = _SLACK_WEBHOOK_PATH_RE.match(parsed.path)
        if match:
            slack_team_id = match.group(1)

    return (host, github_repository_id, slack_team_id)


def _iter_components(node: Any) -> Iterator[dict[str, Any]]:
    if isinstance(node, list):
        for item in node:
            yield from _iter_components(item)
        return
    if not isinstance(node, dict):
        return
    if "type" in node or "component" in node:
        yield node
    for key in ("children", "conditions", "branches", "components"):
        nested = node.get(key)
        if nested:
            yield from _iter_components(nested)


def _epoch_ms_to_datetime(value: Any) -> datetime | None:
    if value is None or isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return datetime.fromtimestamp(value / 1000, tz=timezone.utc)


def _extract_project_id(ari: str) -> str | None:
    if not isinstance(ari, str) or ":project/" not in ari:
        return None
    project_id = ari.split(":project/", 1)[1]
    if not project_id or "/" in project_id:
        return None
    return project_id


@timeit
def get(client: JiraClient) -> tuple[list[dict[str, Any]], bool] | None:
    """
    Return (rules, is_complete), or None when the token cannot read Automation rules.

    is_complete is False when a rule listed in the summary could not be read, for
    example because it was deleted between the summary and detail calls.
    """
    summary_url = f"{client.automation_base_url}/rule/summary"
    base_parts = urlsplit(summary_url)
    summaries: list[dict[str, Any]] = []
    seen_cursors: set[str] = set()
    next_url: str | None = summary_url

    for page_index in range(DEFAULT_MAX_PAGES):
        try:
            if page_index == 0:
                page = client.get_automation(summary_url, limit=100)
            else:
                assert next_url is not None
                page = client.get_automation(next_url)
        except requests.HTTPError as e:
            if (
                page_index == 0
                and e.response is not None
                and e.response.status_code in (401, 403, 404)
            ):
                logger.warning(
                    "Skipping Jira Automation rules sync (HTTP %s): a classic API token "
                    "of a Jira admin is required to read Automation rules; scoped tokens "
                    "are not accepted.",
                    e.response.status_code,
                )
                return None
            raise

        data = require_array(page["data"], "automation rule summary data")
        summaries.extend(data)

        links = page.get("links") or {}
        raw_next = links.get("next")
        if not raw_next:
            break

        resolved_next = urljoin(summary_url, raw_next)
        next_parts = urlsplit(resolved_next)
        if (next_parts.scheme, next_parts.netloc) != (
            base_parts.scheme,
            base_parts.netloc,
        ):
            raise ValueError(
                "Jira Automation pagination URL pointed to an unexpected origin"
            )
        cursor_values = parse_qs(next_parts.query).get("cursor")
        cursor_key = cursor_values[0] if cursor_values else resolved_next
        if cursor_key in seen_cursors:
            raise ValueError("Jira Automation pagination repeated cursor")
        seen_cursors.add(cursor_key)
        next_url = resolved_next
    else:
        raise RuntimeError(
            f"Jira Automation pagination exceeded {DEFAULT_MAX_PAGES} pages"
        )

    rules: list[dict[str, Any]] = []
    is_complete = True
    for summary in summaries:
        rule_uuid = summary["uuid"]
        detail_url = (
            f"{client.automation_base_url}/rule/{quote(str(rule_uuid), safe='')}"
        )
        try:
            detail = client.get_automation(detail_url, redactSensitiveFields="true")
        except requests.HTTPError as e:
            if e.response is not None and e.response.status_code in (403, 404):
                logger.warning(
                    "Skipping Jira Automation rule %s (HTTP %s)",
                    rule_uuid,
                    e.response.status_code,
                )
                is_complete = False
                continue
            raise
        rules.append(detail["rule"])
    return rules, is_complete


@timeit
def transform(rules: list[dict[str, Any]], cloud_id: str) -> list[dict[str, Any]]:
    transformed: list[dict[str, Any]] = []
    for rule in rules:
        uuid = rule["uuid"]
        trigger = rule.get("trigger") or {}
        trigger_type = trigger.get("type")

        actor = rule.get("actor") or {}
        actor_user_id: str | None = None
        if actor.get("type") == "ACCOUNT_ID" and actor.get("actor"):
            actor_user_id = resource_id(cloud_id, "user", actor["actor"])

        scope_aris = rule.get("ruleScopeARIs") or []
        project_ids: set[str] = set()
        for ari in scope_aris:
            project_id = _extract_project_id(ari)
            if project_id is not None:
                project_ids.add(resource_id(cloud_id, "project", project_id))

        hosts: set[str] = set()
        github_repository_ids: set[str] = set()
        slack_team_ids: set[str] = set()
        outgoing_request_count = 0

        for component in _iter_components(rule.get("components") or []):
            comp_type = component.get("type")
            if comp_type not in _OUTGOING_COMPONENT_TYPES:
                continue
            outgoing_request_count += 1
            raw_value = component.get("value")
            value = raw_value if isinstance(raw_value, dict) else {}
            raw_url = (
                value.get("webhookUrl")
                if comp_type == "slack.notification"
                else value.get("url")
            )
            host, github_repo_id, slack_team_id = parse_outgoing_target(raw_url or "")
            if host:
                hosts.add(host)
            if github_repo_id:
                github_repository_ids.add(github_repo_id)
            if slack_team_id:
                slack_team_ids.add(slack_team_id)

        transformed.append(
            {
                "id": resource_id(cloud_id, "automation_rule", uuid),
                "uuid": uuid,
                "name": rule.get("name"),
                "state": rule.get("state"),
                "description": rule.get("description"),
                "write_access_type": rule.get("writeAccessType"),
                "created": _epoch_ms_to_datetime(rule.get("created")),
                "updated": _epoch_ms_to_datetime(rule.get("updated")),
                "trigger_type": trigger_type,
                "has_incoming_webhook_trigger": (
                    trigger_type == "jira.incoming.webhook"
                ),
                "is_global": any(
                    isinstance(ari, str) and _JIRA_SITE_SCOPE_RE.match(ari)
                    for ari in scope_aris
                ),
                "outgoing_request_hosts": sorted(hosts),
                "outgoing_request_count": outgoing_request_count,
                "actor_user_id": actor_user_id,
                "project_ids": sorted(project_ids),
                "github_repository_ids": sorted(github_repository_ids),
                "slack_team_ids": sorted(slack_team_ids),
            }
        )
    return transformed


@timeit
def sync(neo4j_session: neo4j.Session, client: JiraClient, update_tag: int) -> None:
    result = get(client)
    if result is None:
        return
    rules, is_complete = result
    data = transform(rules, client.cloud_id)
    logger.info("Loading %d Jira Automation rules", len(data))
    load(
        neo4j_session,
        JiraAutomationRuleSchema(),
        data,
        lastupdated=update_tag,
        TENANT_ID=client.cloud_id,
    )
    if not is_complete:
        logger.warning(
            "Skipping Jira Automation rules cleanup because one or more rules could not be read",
        )
        return
    GraphJob.from_node_schema(
        JiraAutomationRuleSchema(),
        {"UPDATE_TAG": update_tag, "TENANT_ID": client.cloud_id},
    ).run(neo4j_session)
