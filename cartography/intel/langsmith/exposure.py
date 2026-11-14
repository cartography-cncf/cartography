"""
Ways a workspace's data leaves LangSmith: public share links, public prompt and agent
repos, webhooks that receive runs or prompt changes, and bulk exports to object storage.

Only metadata is kept. A share token is the credential for its public URL, a webhook URL
often embeds a secret (a Slack incoming-webhook URL is one), and webhook headers carry
auth, so none of them reach the graph: a share keeps the id of what it exposes, and a
webhook keeps only its URL's scheme and host.
"""

import logging
from typing import Any
from urllib.parse import urlsplit

from cartography.intel.langsmith.util import LangSmithClient
from cartography.intel.langsmith.util import LangSmithFetchError
from cartography.util import timeit

logger = logging.getLogger(__name__)

_SHARED_ENTITY_FIELDS = {
    "run": ("run_id", "run_name"),
    "dataset": ("dataset_id", "dataset_name"),
    "thread": ("thread_id", None),
}


@timeit
def get_public_shares(
    client: LangSmithClient, org_id: str, workspace_id: str
) -> tuple[list[dict[str, Any]], bool]:
    """List the workspace's public share links and its public prompt and agent repos."""
    try:
        shared = client.get_paginated_envelope(
            "/api/v1/workspaces/current/shared",
            key="entities",
            org_id=org_id,
            tenant_id=workspace_id,
        )
        repos = client.get_paginated_envelope(
            "/api/v1/repos",
            key="repos",
            params={"is_public": "true", "tenant_id": workspace_id},
            org_id=org_id,
            tenant_id=workspace_id,
        )
    except LangSmithFetchError as err:
        logger.warning(
            "Skipping LangSmith public shares for workspace %s: %s", workspace_id, err
        )
        return [], err.not_found
    shares = [transform_shared_entity(entity, workspace_id) for entity in shared]
    shares.extend(
        transform_public_repo(repo, workspace_id)
        for repo in repos
        # The public listing spans every organization's repos; keep this workspace's.
        if repo.get("tenant_id") == workspace_id and repo.get("is_public")
    )
    return shares, True


def transform_shared_entity(
    entity: dict[str, Any], workspace_id: str
) -> dict[str, Any]:
    share_type = entity["type"]
    id_field, name_field = _SHARED_ENTITY_FIELDS[share_type]
    return {
        "id": f"{share_type}|{entity[id_field]}",
        "share_type": share_type,
        "entity_id": entity[id_field],
        "entity_name": entity.get(name_field) if name_field else None,
        "project_id": entity.get("session_id"),
        "project_name": entity.get("session_name"),
        "created_at": entity.get("created_at"),
        "workspace_id": workspace_id,
    }


def transform_public_repo(repo: dict[str, Any], workspace_id: str) -> dict[str, Any]:
    return {
        "id": f"repo|{repo['id']}",
        "share_type": "repo",
        "entity_id": repo["id"],
        "entity_name": repo.get("full_name") or repo.get("repo_handle"),
        "repo_type": repo.get("repo_type"),
        "created_at": repo.get("created_at"),
        "workspace_id": workspace_id,
    }


@timeit
def get_webhooks(
    client: LangSmithClient, org_id: str, workspace_id: str
) -> tuple[list[dict[str, Any]], bool]:
    """List the webhooks automation rules send runs to, and the prompt webhooks."""
    try:
        rules = client.get("/api/v1/runs/rules", org_id=org_id, tenant_id=workspace_id)
        prompt_webhooks = client.get(
            "/api/v1/prompt-webhooks", org_id=org_id, tenant_id=workspace_id
        )
    except LangSmithFetchError as err:
        logger.warning(
            "Skipping LangSmith webhooks for workspace %s: %s", workspace_id, err
        )
        return [], err.not_found
    webhooks = [
        {
            **_webhook_target(webhook["url"]),
            "id": f"{rule['id']}|{index}",
            "source": "run_rule",
            "rule_name": rule.get("display_name"),
            "project_name": rule.get("session_name"),
            "dataset_name": rule.get("dataset_name"),
            "enabled": rule.get("is_enabled"),
            "created_at": rule.get("created_at"),
            "workspace_id": workspace_id,
        }
        for rule in rules
        for index, webhook in enumerate(rule.get("webhooks") or [])
    ]
    webhooks.extend(
        {
            **_webhook_target(webhook["url"]),
            "id": webhook["id"],
            "source": "prompt",
            "enabled": True,
            "created_at": webhook.get("created_at"),
            "workspace_id": workspace_id,
        }
        for webhook in prompt_webhooks
    )
    return webhooks, True


def _webhook_target(url: str) -> dict[str, Any]:
    parts = urlsplit(url)
    host = parts.hostname
    if host and parts.port:
        host = f"{host}:{parts.port}"
    return {"scheme": parts.scheme or None, "host": host}


@timeit
def get_bulk_export_destinations(
    client: LangSmithClient, org_id: str, workspace_id: str
) -> tuple[list[dict[str, Any]], bool]:
    try:
        destinations = client.get(
            "/api/v1/bulk-exports/destinations", org_id=org_id, tenant_id=workspace_id
        )
    except LangSmithFetchError as err:
        logger.warning(
            "Skipping LangSmith bulk export destinations for workspace %s: %s",
            workspace_id,
            err,
        )
        return [], err.not_found
    return [
        transform_bulk_export_destination(destination, workspace_id)
        for destination in destinations
    ], True


def transform_bulk_export_destination(
    destination: dict[str, Any], workspace_id: str
) -> dict[str, Any]:
    config = destination.get("config") or {}
    on_amazon_s3 = not config.get("endpoint_url")
    return {
        "id": destination["id"],
        "display_name": destination.get("display_name"),
        "destination_type": destination.get("destination_type"),
        "bucket_name": config.get("bucket_name"),
        # An S3-compatible endpoint elsewhere can reuse an Amazon bucket's name, so only a
        # destination on Amazon S3 links to the S3Bucket of that name.
        "aws_bucket_name": config.get("bucket_name") if on_amazon_s3 else None,
        "prefix": config.get("prefix"),
        "region": config.get("region"),
        "endpoint_url": config.get("endpoint_url"),
        "aws_role_arn": config.get("aws_role_arn"),
        "credential_fields": sorted(destination.get("credentials_keys") or []),
        "created_at": destination.get("created_at"),
        "workspace_id": workspace_id,
    }
