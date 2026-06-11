import json
import logging
import re

import neo4j

from cartography.client.core.tx import load
from cartography.client.core.tx import load_matchlinks
from cartography.client.core.tx import run_write_query
from cartography.graph.job import GraphJob
from cartography.models.terraform.matchlinks import RESOURCE_TYPE_ID_ATTR
from cartography.models.terraform.matchlinks import RESOURCE_TYPE_MATCHLINKS
from cartography.models.terraform.matchlinks import (
    TerraformWorkspaceToGitLabStateMatchLink,
)
from cartography.models.terraform.output import TerraformOutputSchema
from cartography.models.terraform.resource import TerraformResourceInstanceSchema
from cartography.models.terraform.resource import TerraformResourceSchema
from cartography.models.terraform.workspace import TerraformWorkspaceSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


def _normalize_provider(raw: str) -> str:
    m = re.search(r'registry\.terraform\.io/(.+?)(?:"|$)', raw)
    return m.group(1) if m else raw


def _make_resource_id(resource: dict) -> str:
    parts = []
    if module := resource.get("module"):
        parts.append(module)
    parts.append(resource["type"])
    parts.append(resource["name"])
    return ".".join(parts)


def _make_instance_id(resource_id: str, instance: dict) -> str:
    index = instance.get("index_key")
    if index is None:
        return resource_id
    return f"{resource_id}[{index}]"


def transform_workspace(document: dict, source_uri: str) -> dict:
    return {
        "lineage": document["lineage"],
        "terraform_version": document.get("terraform_version"),
        "serial": document.get("serial"),
        "workspace_name": (
            source_uri.rstrip("/")
            .rsplit("/", 1)[-1]
            .replace(".tfstate", "")
            .replace(".json", "")
        ),
    }


def transform_resources(document: dict, workspace_lineage: str) -> list[dict]:
    rows = []
    for res in document.get("resources", []):
        resource_id = _make_resource_id(res)
        rows.append(
            {
                "id": f"{workspace_lineage}/{resource_id}",
                "resource_type": res["type"],
                "resource_name": res["name"],
                "module_path": res.get("module", ""),
                "mode": res.get("mode", "managed"),
                "provider": _normalize_provider(res.get("provider", "")),
            }
        )
    return rows


def transform_instances(document: dict, workspace_lineage: str) -> list[dict]:
    rows = []
    for res in document.get("resources", []):
        resource_id = _make_resource_id(res)
        scoped_resource_id = f"{workspace_lineage}/{resource_id}"
        for inst in res.get("instances", []):
            attrs = inst.get("attributes") or {}
            tags = attrs.get("tags") or attrs.get("tags_all") or {}
            rows.append(
                {
                    "id": f"{workspace_lineage}/{_make_instance_id(resource_id, inst)}",
                    "resource_id": scoped_resource_id,
                    "index_key": (
                        str(inst["index_key"])
                        if inst.get("index_key") is not None
                        else None
                    ),
                    "attributes_id": attrs.get(
                        RESOURCE_TYPE_ID_ATTR.get(res["type"], "id")
                    )
                    or attrs.get("arn"),
                    "resource_type": res["type"],
                    "tags_json": json.dumps(tags) if tags else None,
                }
            )
    return rows


def transform_depends_on(document: dict, workspace_lineage: str) -> list[dict]:
    rows = []
    for res in document.get("resources", []):
        resource_id = _make_resource_id(res)
        scoped_source_id = f"{workspace_lineage}/{resource_id}"
        for inst in res.get("instances", []):
            for dep in inst.get("dependencies", []):
                # Target is external - use same scoping if it was a scoped ID
                rows.append(
                    {
                        "source_id": scoped_source_id,
                        "target_id": f"{workspace_lineage}/{dep}",
                    }
                )
    return rows


def transform_outputs(document: dict) -> list[dict]:
    lineage = document["lineage"]
    rows = []
    for name, output in document.get("outputs", {}).items():
        sensitive = bool(output.get("sensitive", False))
        value = output.get("value")
        tf_type = output.get("type")
        if isinstance(tf_type, list):
            value_type = tf_type[0]
        else:
            value_type = str(tf_type) if tf_type else "unknown"
        rows.append(
            {
                "id": f"{lineage}::{name}",
                "output_name": name,
                "value_type": value_type,
                "sensitive": sensitive,
                "value_json": json.dumps(value) if not sensitive else None,
            }
        )
    return rows


def _transform_cross_links(instances: list[dict]) -> dict[str, list[dict]]:
    by_type: dict[str, list[dict]] = {}
    for inst in instances:
        rt = inst.get("resource_type")
        if rt and rt in RESOURCE_TYPE_MATCHLINKS and inst.get("attributes_id"):
            by_type.setdefault(rt, []).append(inst)
    return by_type


@timeit
def load_workspace(
    neo4j_session: neo4j.Session,
    workspace_data: dict,
    source_uri: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        TerraformWorkspaceSchema(),
        [workspace_data],
        lastupdated=update_tag,
        source_uri=source_uri,
    )


@timeit
def load_resources(
    neo4j_session: neo4j.Session,
    resources: list[dict],
    workspace_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        TerraformResourceSchema(),
        resources,
        lastupdated=update_tag,
        workspace_id=workspace_id,
    )


@timeit
def load_instances(
    neo4j_session: neo4j.Session,
    instances: list[dict],
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        TerraformResourceInstanceSchema(),
        instances,
        lastupdated=update_tag,
    )


@timeit
def load_depends_on(
    neo4j_session: neo4j.Session,
    depends_on_rows: list[dict],
    update_tag: int,
) -> None:
    run_write_query(
        neo4j_session,
        """
        UNWIND $rows AS row
        MATCH (src:TerraformResource {id: row.source_id})
        MATCH (tgt:TerraformResource {id: row.target_id})
        MERGE (src)-[r:DEPENDS_ON]->(tgt)
        SET r.lastupdated = $lastupdated
        """,
        rows=depends_on_rows,
        lastupdated=update_tag,
    )


@timeit
def load_outputs(
    neo4j_session: neo4j.Session,
    outputs: list[dict],
    workspace_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        TerraformOutputSchema(),
        outputs,
        lastupdated=update_tag,
        workspace_id=workspace_id,
    )


@timeit
def load_sourced_from(
    neo4j_session: neo4j.Session,
    workspace_id: str,
    source_uri: str,
    update_tag: int,
) -> None:
    load_matchlinks(
        neo4j_session,
        TerraformWorkspaceToGitLabStateMatchLink(),
        [{"workspace_id": workspace_id, "source_uri": source_uri}],
        lastupdated=update_tag,
        _sub_resource_label="TerraformWorkspace",
        _sub_resource_id=workspace_id,
    )


@timeit
def load_cross_links(
    neo4j_session: neo4j.Session,
    instances: list[dict],
    workspace_lineage: str,
    update_tag: int,
) -> None:
    by_type = _transform_cross_links(instances)
    for resource_type, schema in RESOURCE_TYPE_MATCHLINKS.items():
        batch = by_type.get(resource_type, [])
        if not batch:
            continue
        logger.debug("Loading %d MANAGES edges for %s", len(batch), resource_type)
        load_matchlinks(
            neo4j_session,
            schema,
            batch,
            lastupdated=update_tag,
            _sub_resource_label="TerraformWorkspace",
            _sub_resource_id=workspace_lineage,
        )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict,
    workspace_lineage: str,
    update_tag: int,
) -> None:
    GraphJob.from_node_schema(TerraformWorkspaceSchema(), common_job_parameters).run(
        neo4j_session
    )
    update_tag_val = common_job_parameters["UPDATE_TAG"]

    def _cleanup_stale(label: str, max_per_batch: int = 10000) -> None:
        while True:
            result = neo4j_session.run(
                f"""
                MATCH (n:{label})
                WHERE n.lastupdated <> $UPDATE_TAG
                WITH n LIMIT $LIMIT_SIZE
                DETACH DELETE n
                RETURN count(n) AS deleted
                """,
                UPDATE_TAG=update_tag_val,
                LIMIT_SIZE=max_per_batch,
            )
            deleted = result.single()["deleted"]
            if deleted == 0:
                break
            logger.debug("Cleaned up %d stale %s nodes", deleted, label)

    _cleanup_stale("TerraformResource")
    _cleanup_stale("TerraformResourceInstance")
    _cleanup_stale("TerraformOutput")

    for schema in RESOURCE_TYPE_MATCHLINKS.values():
        GraphJob.from_matchlink(
            schema, "TerraformWorkspace", workspace_lineage, update_tag
        ).run(neo4j_session)

    GraphJob.from_matchlink(
        TerraformWorkspaceToGitLabStateMatchLink(),
        "TerraformWorkspace",
        workspace_lineage,
        update_tag,
    ).run(neo4j_session)


@timeit
def sync_state_file(
    neo4j_session: neo4j.Session,
    document: dict,
    source_uri: str,
    update_tag: int,
    common_job_parameters: dict,
) -> None:
    workspace_data = transform_workspace(document, source_uri)
    workspace_id = workspace_data["lineage"]

    load_workspace(neo4j_session, workspace_data, source_uri, update_tag)

    resources = transform_resources(document, workspace_id)
    load_resources(neo4j_session, resources, workspace_id, update_tag)

    instances = transform_instances(document, workspace_id)
    load_instances(neo4j_session, instances, update_tag)

    depends_on = transform_depends_on(document, workspace_id)
    if depends_on:
        load_depends_on(neo4j_session, depends_on, update_tag)

    outputs = transform_outputs(document)
    load_outputs(neo4j_session, outputs, workspace_id, update_tag)

    load_cross_links(neo4j_session, instances, workspace_id, update_tag)

    load_sourced_from(neo4j_session, workspace_id, source_uri, update_tag)

    cleanup(neo4j_session, common_job_parameters, workspace_id, update_tag)
