import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.databricks._account_scope import account_scoped_id
from cartography.intel.databricks.util import DatabricksAccountClient
from cartography.models.databricks.account_setting import DatabricksAccountSettingSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

# Account-level settings that carry a security signal. Personal compute
# enablement is the key one: when enabled, every user can spin up a
# single-node cluster, widening the attack surface. Keyed by the human name we
# store on the node and the setting-type/name path segments the API expects.
_SETTINGS = [
    ("personal_compute", "dcp_acct_enable", "default"),
]


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: DatabricksAccountClient,
    account_id: str,
    common_job_parameters: dict[str, Any],
) -> None:
    settings = get(api_session)
    transformed = transform(settings, account_id)
    load_account_settings(
        neo4j_session, transformed, account_id, common_job_parameters["UPDATE_TAG"]
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(api_session: DatabricksAccountClient) -> list[dict[str, Any]]:
    """Fetch account settings that carry a security signal.

    Each setting is a separate GET; the endpoints are best-effort (a setting may
    404/400 if never configured or unavailable on the account tier), so skip an
    individual setting on error rather than aborting the whole sync.
    """
    results: list[dict[str, Any]] = []
    for setting_name, setting_type, name in _SETTINGS:
        uri = api_session.account_uri(f"/settings/types/{setting_type}/names/{name}")
        try:
            data = api_session.get(uri) or {}
        except requests.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else None
            if status in (400, 404):
                logger.info(
                    "Databricks account setting %s not available; skipping.",
                    setting_name,
                )
                continue
            raise
        data["_setting_name"] = setting_name
        results.append(data)
    return results


def _setting_value(data: dict[str, Any]) -> str | None:
    """Stringify whichever typed value field the setting returned.

    Different account settings wrap the value differently. Personal compute
    returns ``personal_compute: {"value": "ON"|"DELEGATE"}``; the generic typed
    settings use ``boolean_val`` / ``string_val`` / ``integer_val`` blocks. Scan
    the known keys, then fall back to any nested ``{"value": ...}`` block so a
    setting-specific wrapper (like personal_compute) is still captured.
    """
    for key in ("personal_compute", "boolean_val", "string_val", "integer_val"):
        block = data.get(key)
        if isinstance(block, dict) and "value" in block:
            return str(block["value"])
    if "enabled" in data:
        return str(data["enabled"])
    # Fallback: some settings nest the value under a setting-named key we do not
    # enumerate; take the first nested {"value": ...} that is not metadata.
    for key, block in data.items():
        if key in ("etag", "setting_name", "_setting_name"):
            continue
        if isinstance(block, dict) and "value" in block:
            return str(block["value"])
    return None


@timeit
def transform(settings: list[dict[str, Any]], account_id: str) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for s in settings:
        setting_name = s["_setting_name"]
        result.append(
            {
                "id": account_scoped_id(account_id, setting_name),
                "setting_name": setting_name,
                "value": _setting_value(s),
            }
        )
    return result


@timeit
def load_account_settings(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        DatabricksAccountSettingSchema(),
        data,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(
        DatabricksAccountSettingSchema(), common_job_parameters
    ).run(neo4j_session)
