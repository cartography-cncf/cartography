import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.circleci.util import _TIMEOUT
from cartography.intel.circleci.util import parse_iso
from cartography.models.circleci.policy import CircleCIPolicySchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

# ponytail: only the "config" policy context is queried - it's the only context
# CircleCI config policies use today. Add others here if CircleCI introduces them.
_POLICY_CONTEXT = "config"


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
    org_id: str,
) -> None:
    base_url = common_job_parameters["BASE_URL"]
    settings = get_decision_settings(api_session, base_url, org_id, _POLICY_CONTEXT)
    enabled = settings.get("enabled") if settings else None
    bundle = get_policy_bundle(api_session, base_url, org_id, _POLICY_CONTEXT)
    policies = transform(bundle, org_id, _POLICY_CONTEXT, enabled)
    load_policies(
        neo4j_session,
        policies,
        org_id,
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get_decision_settings(
    api_session: requests.Session,
    base_url: str,
    org_id: str,
    context: str,
) -> dict[str, Any] | None:
    req = api_session.get(
        f"{base_url}/owner/{org_id}/context/{context}/decision/settings",
        timeout=_TIMEOUT,
    )
    if req.status_code == 404:
        return None
    req.raise_for_status()
    return req.json()


@timeit
def get_policy_bundle(
    api_session: requests.Session,
    base_url: str,
    org_id: str,
    context: str,
) -> dict[str, Any]:
    req = api_session.get(
        f"{base_url}/owner/{org_id}/context/{context}/policy-bundle",
        timeout=_TIMEOUT,
    )
    # 404 means policies are not enabled / no bundle for this owner+context.
    if req.status_code == 404:
        return {}
    req.raise_for_status()
    return req.json() or {}


def transform(
    bundle: dict[str, Any],
    org_id: str,
    context: str,
    enabled: bool | None,
) -> list[dict[str, Any]]:
    # The bundle is a map of policy-name -> list of policy documents. Be
    # defensive about a single-object value too, since the per-policy endpoint
    # returns a bare object.
    policies = []
    for name, value in bundle.items():
        docs = value if isinstance(value, list) else [value]
        for doc in docs:
            doc = doc or {}
            policy_name = doc.get("name") or name
            policies.append(
                {
                    "id": f"{org_id}:{context}:{policy_name}",
                    "name": policy_name,
                    "context": context,
                    "content": doc.get("content"),
                    "created_at": parse_iso(doc.get("created_at")),
                    "created_by": doc.get("created_by"),
                    "decision_enabled": enabled,
                }
            )
    return policies


@timeit
def load_policies(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    org_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        CircleCIPolicySchema(),
        data,
        lastupdated=update_tag,
        ORG_ID=org_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(CircleCIPolicySchema(), common_job_parameters).run(
        neo4j_session,
    )
