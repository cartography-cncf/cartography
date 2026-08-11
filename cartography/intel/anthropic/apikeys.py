from typing import Any
from typing import Tuple

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.anthropic.util import paginated_get
from cartography.intel.anthropic.util import resolve_org_id
from cartography.models.anthropic.apikey import AnthropicApiKeySchema
from cartography.util import timeit

# Connect and read timeouts of 60 seconds each; see https://requests.readthedocs.io/en/master/user/advanced/#timeouts
_TIMEOUT = (60, 60)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    header_org_id, apikeys = get(
        api_session,
        common_job_parameters["BASE_URL"],
    )
    org_id = resolve_org_id(common_job_parameters, header_org_id)
    common_job_parameters["ORG_ID"] = org_id
    for apikey in apikeys:
        transform_apikey(apikey)
    load_apikeys(
        neo4j_session,
        apikeys,
        org_id,
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
) -> Tuple[str, list[dict[str, Any]]]:
    return paginated_get(
        api_session, f"{base_url}/organizations/api_keys", timeout=_TIMEOUT
    )


def transform_apikey(apikey: dict[str, Any]) -> None:
    """Resolve the single owner the canonical OWNED_BY edge points at.

    A key acting as a service account still records the human who created it, so
    deriving ownership from `created_by` alone would attribute the key to both a user
    and a service account and make ownership queries double-count. The principal is
    what the key acts as, so it wins; `created_by` remains the fallback, and stays on
    the deprecated OWNS edge either way as creation attribution.
    """
    principal = apikey.get("principal") or {}
    if principal.get("type") == "service_account":
        apikey["owner_user_id"] = None
        apikey["owner_service_account_id"] = principal.get("id")
        return
    apikey["owner_user_id"] = principal.get("id") or (
        apikey.get("created_by") or {}
    ).get("id")
    apikey["owner_service_account_id"] = None


@timeit
def load_apikeys(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    ORG_ID: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AnthropicApiKeySchema(),
        data,
        lastupdated=update_tag,
        ORG_ID=ORG_ID,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(AnthropicApiKeySchema(), common_job_parameters).run(
        neo4j_session
    )
