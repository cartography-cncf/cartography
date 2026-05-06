import copy
from collections import defaultdict
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.portkey import util
from cartography.models.portkey.resources import PortkeyAPIKeySchema
from cartography.models.portkey.resources import PortkeyConfigSchema
from cartography.models.portkey.resources import PortkeyGuardrailSchema
from cartography.models.portkey.resources import PortkeyIntegrationSchema
from cartography.models.portkey.resources import PortkeyInviteSchema
from cartography.models.portkey.resources import PortkeyMCPIntegrationSchema
from cartography.models.portkey.resources import PortkeyMCPServerSchema
from cartography.models.portkey.resources import PortkeyPromptCollectionSchema
from cartography.models.portkey.resources import PortkeyPromptSchema
from cartography.models.portkey.resources import PortkeyProviderSchema
from cartography.models.portkey.resources import PortkeySecretReferenceSchema
from cartography.models.portkey.resources import PortkeyVirtualKeySchema
from cartography.util import timeit


def _jsonify(data: dict[str, Any], field_map: dict[str, str]) -> dict[str, Any]:
    result = copy.deepcopy(data)
    for source_field, target_field in field_map.items():
        result[target_field] = util.json_dumps(result.get(source_field))
    return result


def _load_resource(
    neo4j_session: neo4j.Session,
    schema: Any,
    data: list[dict[str, Any]],
    common_job_parameters: dict[str, Any],
) -> None:
    load(
        neo4j_session,
        schema,
        data,
        lastupdated=common_job_parameters["UPDATE_TAG"],
        PORTKEY_ORG_ID=common_job_parameters["PORTKEY_ORG_ID"],
    )


def _cleanup_resource(
    neo4j_session: neo4j.Session,
    schema: Any,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(schema, common_job_parameters).run(neo4j_session)


def _group_by_workspace(data: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in data:
        workspace_id = item.get("workspace_id")
        if workspace_id:
            grouped[workspace_id].append(item)
    return grouped


def _load_workspace_resource(
    neo4j_session: neo4j.Session,
    schema: Any,
    data: list[dict[str, Any]],
    workspace_id: str,
    common_job_parameters: dict[str, Any],
) -> None:
    load(
        neo4j_session,
        schema,
        data,
        lastupdated=common_job_parameters["UPDATE_TAG"],
        WORKSPACE_ID=workspace_id,
    )


def _cleanup_workspace_resource(
    neo4j_session: neo4j.Session,
    schema: Any,
    workspace_id: str,
    common_job_parameters: dict[str, Any],
) -> None:
    workspace_job_parameters = {
        **common_job_parameters,
        "WORKSPACE_ID": workspace_id,
    }
    GraphJob.from_node_schema(schema, workspace_job_parameters).run(neo4j_session)


@timeit
def sync_invites(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    invites = []
    for invite in util.list_user_invites(
        api_session, common_job_parameters["BASE_URL"]
    ):
        invite["workspace_ids"] = [
            workspace["workspace_id"]
            for workspace in invite.get("workspaces", [])
            if workspace.get("workspace_id")
        ]
        invite["workspaces_json"] = util.json_dumps(invite.get("workspaces"))
        invites.append(invite)
    _load_resource(
        neo4j_session,
        PortkeyInviteSchema(),
        invites,
        common_job_parameters,
    )
    _cleanup_resource(neo4j_session, PortkeyInviteSchema(), common_job_parameters)


@timeit
def sync_api_keys(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    data = []
    for item in util.list_api_keys(api_session, common_job_parameters["BASE_URL"]):
        details = util.retrieve_api_key(
            api_session,
            common_job_parameters["BASE_URL"],
            item["id"],
        )
        details.pop("key", None)
        data.append(
            _jsonify(
                details,
                {
                    "rate_limits": "rate_limits_json",
                    "usage_limits": "usage_limits_json",
                    "defaults": "defaults_json",
                },
            )
        )
    _load_resource(neo4j_session, PortkeyAPIKeySchema(), data, common_job_parameters)
    _cleanup_resource(neo4j_session, PortkeyAPIKeySchema(), common_job_parameters)


@timeit
def sync_virtual_keys(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    data = []
    for item in util.list_virtual_keys(api_session, common_job_parameters["BASE_URL"]):
        item["id"] = item.get("id") or item["slug"]
        data.append(
            _jsonify(
                item,
                {
                    "model_config": "model_config_json",
                    "rate_limits": "rate_limits_json",
                    "usage_limits": "usage_limits_json",
                },
            )
        )
    _load_resource(
        neo4j_session, PortkeyVirtualKeySchema(), data, common_job_parameters
    )
    _cleanup_resource(neo4j_session, PortkeyVirtualKeySchema(), common_job_parameters)


@timeit
def sync_configs(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    workspaces: list[dict[str, Any]],
    common_job_parameters: dict[str, Any],
) -> None:
    data = util.list_configs(api_session, common_job_parameters["BASE_URL"])
    data_by_workspace = _group_by_workspace(data)
    schema = PortkeyConfigSchema()
    for workspace in workspaces:
        workspace_id = workspace["id"]
        workspace_data = data_by_workspace.get(workspace_id, [])
        if workspace_data:
            _load_workspace_resource(
                neo4j_session,
                schema,
                workspace_data,
                workspace_id,
                common_job_parameters,
            )
        _cleanup_workspace_resource(
            neo4j_session,
            schema,
            workspace_id,
            common_job_parameters,
        )


@timeit
def sync_secret_references(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    data = []
    for item in util.list_secret_references(
        api_session,
        common_job_parameters["BASE_URL"],
    ):
        item["auth_config_json"] = util.json_dumps(item.get("auth_config"))
        data.append(item)
    _load_resource(
        neo4j_session,
        PortkeySecretReferenceSchema(),
        data,
        common_job_parameters,
    )
    _cleanup_resource(
        neo4j_session,
        PortkeySecretReferenceSchema(),
        common_job_parameters,
    )


@timeit
def sync_integrations(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    data = []
    for item in util.list_integrations(api_session, common_job_parameters["BASE_URL"]):
        item["secret_mappings_json"] = util.json_dumps(item.get("secret_mappings"))
        item["secret_reference_ids"] = [
            mapping["secret_reference_id"]
            for mapping in item.get("secret_mappings", [])
            if mapping.get("secret_reference_id")
        ]
        data.append(item)
    _load_resource(
        neo4j_session,
        PortkeyIntegrationSchema(),
        data,
        common_job_parameters,
    )
    _cleanup_resource(
        neo4j_session,
        PortkeyIntegrationSchema(),
        common_job_parameters,
    )


@timeit
def sync_mcp_integrations(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    data = []
    for item in util.list_mcp_integrations(
        api_session,
        common_job_parameters["BASE_URL"],
        common_job_parameters["PORTKEY_ORG_ID"],
    ):
        item["configurations_json"] = util.json_dumps(item.get("configurations"))
        data.append(item)
    _load_resource(
        neo4j_session,
        PortkeyMCPIntegrationSchema(),
        data,
        common_job_parameters,
    )
    _cleanup_resource(
        neo4j_session,
        PortkeyMCPIntegrationSchema(),
        common_job_parameters,
    )


@timeit
def sync_mcp_servers(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    workspaces: list[dict[str, Any]],
    common_job_parameters: dict[str, Any],
) -> None:
    data_by_workspace: dict[str, list[dict[str, Any]]] = {
        workspace["id"]: [] for workspace in workspaces
    }
    seen_ids: set[str] = set()
    for workspace in workspaces:
        workspace_id = workspace["id"]
        for item in util.list_mcp_servers(
            api_session,
            common_job_parameters["BASE_URL"],
            workspace_id,
        ):
            if item["id"] in seen_ids:
                continue
            seen_ids.add(item["id"])
            item["workspace_id"] = item.get("workspace_id") or workspace_id
            data_by_workspace.setdefault(item["workspace_id"], []).append(item)
    schema = PortkeyMCPServerSchema()
    for workspace_id, workspace_data in data_by_workspace.items():
        if workspace_data:
            _load_workspace_resource(
                neo4j_session,
                schema,
                workspace_data,
                workspace_id,
                common_job_parameters,
            )
        _cleanup_workspace_resource(
            neo4j_session,
            schema,
            workspace_id,
            common_job_parameters,
        )


@timeit
def sync_providers(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    workspaces: list[dict[str, Any]],
    common_job_parameters: dict[str, Any],
) -> None:
    data = []
    seen_ids: set[str] = set()
    for workspace in workspaces:
        for item in util.list_providers(
            api_session,
            common_job_parameters["BASE_URL"],
            workspace["id"],
        ):
            provider_id = item.get("id") or item["slug"]
            if provider_id in seen_ids:
                continue
            seen_ids.add(provider_id)
            item["id"] = provider_id
            item["workspace_id"] = item.get("workspace_id") or workspace["id"]
            item["rate_limits_json"] = util.json_dumps(item.get("rate_limits"))
            item["usage_limits_json"] = util.json_dumps(item.get("usage_limits"))
            data.append(item)
    _load_resource(neo4j_session, PortkeyProviderSchema(), data, common_job_parameters)
    _cleanup_resource(neo4j_session, PortkeyProviderSchema(), common_job_parameters)


@timeit
def sync_guardrails(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    workspaces: list[dict[str, Any]],
    common_job_parameters: dict[str, Any],
) -> None:
    data = []
    for item in util.list_guardrails(api_session, common_job_parameters["BASE_URL"]):
        item["checks_json"] = util.json_dumps(item.get("checks"))
        item["actions_json"] = util.json_dumps(item.get("actions"))
        data.append(item)
    data_by_workspace = _group_by_workspace(data)
    schema = PortkeyGuardrailSchema()
    for workspace in workspaces:
        workspace_id = workspace["id"]
        workspace_data = data_by_workspace.get(workspace_id, [])
        if workspace_data:
            _load_workspace_resource(
                neo4j_session,
                schema,
                workspace_data,
                workspace_id,
                common_job_parameters,
            )
        _cleanup_workspace_resource(
            neo4j_session,
            schema,
            workspace_id,
            common_job_parameters,
        )


@timeit
def sync_prompt_collections_and_prompts(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    workspaces: list[dict[str, Any]],
    common_job_parameters: dict[str, Any],
) -> None:
    for workspace in workspaces:
        workspace_id = workspace["id"]
        collections = []
        prompts = []
        for collection in util.list_prompt_collections(
            api_session,
            common_job_parameters["BASE_URL"],
            workspace_id,
        ):
            collection["workspace_id"] = collection.get("workspace_id") or workspace_id
            collection["collection_details_json"] = util.json_dumps(
                collection.get("collection_details")
            )
            collections.append(collection)
        for prompt in util.list_prompts(
            api_session,
            common_job_parameters["BASE_URL"],
            workspace_id,
        ):
            prompt["workspace_id"] = workspace_id
            if not prompt.get("collection_id"):
                prompt["collection_id"] = None
            prompts.append(prompt)
        collection_schema = PortkeyPromptCollectionSchema()
        prompt_schema = PortkeyPromptSchema()
        _load_workspace_resource(
            neo4j_session,
            collection_schema,
            collections,
            workspace_id,
            common_job_parameters,
        )
        _load_workspace_resource(
            neo4j_session,
            prompt_schema,
            prompts,
            workspace_id,
            common_job_parameters,
        )
        _cleanup_workspace_resource(
            neo4j_session,
            collection_schema,
            workspace_id,
            common_job_parameters,
        )
        _cleanup_workspace_resource(
            neo4j_session,
            prompt_schema,
            workspace_id,
            common_job_parameters,
        )
