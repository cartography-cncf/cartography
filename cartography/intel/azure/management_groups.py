import logging
from typing import Any

import neo4j
from azure.core.exceptions import HttpResponseError
from azure.mgmt.managementgroups import ManagementGroupsAPI

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.azure.management_group import AzureManagementGroupSchema
from cartography.util import timeit

from .util.credentials import Credentials

logger = logging.getLogger(__name__)


def _get_value(data: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in data:
            return data[key]
    return None


def _management_group_parent(
    management_group: dict[str, Any],
    inherited_parent: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    details = management_group.get("details") or {}
    parent = details.get("parent")
    if parent:
        return parent
    return inherited_parent


def _transform_one_management_group(
    management_group: dict[str, Any],
    inherited_parent: dict[str, Any] | None = None,
) -> dict[str, Any]:
    tenant_id = _get_value(management_group, "tenant_id", "tenantId")
    parent = _management_group_parent(management_group, inherited_parent) or {}
    parent_id = _get_value(parent, "id")
    parent_name = _get_value(parent, "name")

    parent_tenant_id = None
    parent_management_group_id = None
    if tenant_id and (
        parent_name == tenant_id
        or parent_id == f"/providers/Microsoft.Management/managementGroups/{tenant_id}"
    ):
        parent_tenant_id = tenant_id
    elif parent_id:
        parent_management_group_id = parent_id

    details = management_group.get("details") or {}
    return {
        "id": _get_value(management_group, "id"),
        "name": _get_value(management_group, "name"),
        "displayName": _get_value(management_group, "display_name", "displayName"),
        "tenantId": tenant_id,
        "type": _get_value(management_group, "type"),
        "updatedBy": _get_value(details, "updated_by", "updatedBy"),
        "updatedTime": _get_value(details, "updated_time", "updatedTime"),
        "version": _get_value(details, "version"),
        "parent_tenant_id": parent_tenant_id,
        "parent_management_group_id": parent_management_group_id,
    }


def _merge_non_null_values(
    base: dict[str, Any],
    update: dict[str, Any],
) -> dict[str, Any]:
    merged = dict(base)
    for key, value in update.items():
        if value is not None:
            merged[key] = value
    return merged


def _walk_management_group_tree(
    management_group: dict[str, Any],
    transformed_by_id: dict[str, dict[str, Any]],
    inherited_parent: dict[str, Any] | None = None,
) -> None:
    transformed = _transform_one_management_group(
        management_group,
        inherited_parent=inherited_parent,
    )
    management_group_id = transformed.get("id")
    if not management_group_id:
        return

    existing = transformed_by_id.get(management_group_id)
    if existing:
        transformed_by_id[management_group_id] = _merge_non_null_values(
            existing,
            transformed,
        )
    else:
        transformed_by_id[management_group_id] = transformed

    child_parent = {
        "id": management_group_id,
        "name": transformed.get("name"),
        "displayName": transformed.get("displayName"),
    }
    for child in management_group.get("children") or []:
        child_type = _get_value(child, "type")
        if child_type == "Microsoft.Management/managementGroups":
            _walk_management_group_tree(
                child,
                transformed_by_id,
                inherited_parent=child_parent,
            )


@timeit
def get_azure_management_groups(credentials: Credentials) -> list[dict[str, Any]]:
    client = ManagementGroupsAPI(credentials.credential)
    try:
        management_groups = list(client.management_groups.list())
    except HttpResponseError as e:
        raise RuntimeError(
            "Failed to fetch Azure management groups for tenant "
            f"'{credentials.tenant_id}': {e}"
        ) from e

    results: list[dict[str, Any]] = []
    for management_group in management_groups:
        group_name = management_group.name
        try:
            expanded_group = client.management_groups.get(
                group_id=group_name,
                expand="children",
                recurse=True,
            )
            results.append(expanded_group.as_dict())
        except HttpResponseError as e:
            logger.warning(
                "Failed to fetch expanded Azure management group '%s'. "
                "Falling back to basic payload. Details: %s",
                group_name,
                e,
            )
            results.append(management_group.as_dict())
    return results


def transform_azure_management_groups(
    management_groups: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    transformed_by_id: dict[str, dict[str, Any]] = {}
    for management_group in management_groups:
        _walk_management_group_tree(
            management_group,
            transformed_by_id,
        )
    return list(transformed_by_id.values())


@timeit
def load_azure_management_groups(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    tenant_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AzureManagementGroupSchema(),
        data,
        lastupdated=update_tag,
        TENANT_ID=tenant_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(AzureManagementGroupSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    credentials: Credentials,
    tenant_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> list[dict[str, Any]]:
    logger.info("Syncing Azure management groups for tenant '%s'.", tenant_id)
    management_groups = get_azure_management_groups(credentials)
    transformed_management_groups = transform_azure_management_groups(
        management_groups,
    )
    if transformed_management_groups:
        load_azure_management_groups(
            neo4j_session,
            transformed_management_groups,
            tenant_id,
            update_tag,
        )
    cleanup(neo4j_session, common_job_parameters)
    return transformed_management_groups
