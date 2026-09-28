import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.netlify.util import get_list
from cartography.models.netlify.form import NetlifyFormSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync_netlify_forms(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    base_url: str,
    account_id: str,
    sites: list[dict[str, Any]],
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    raw_forms = []
    for site in sites:
        raw_forms.extend(get_netlify_forms(api_session, base_url, site["id"]))
    forms = transform_netlify_forms(raw_forms)
    load_netlify_forms(neo4j_session, forms, account_id, update_tag)
    cleanup_netlify_forms(neo4j_session, common_job_parameters)


@timeit
def get_netlify_forms(
    api_session: requests.Session,
    base_url: str,
    site_id: str,
) -> list[dict[str, Any]]:
    return get_list(api_session, f"{base_url}/sites/{site_id}/forms")


def transform_netlify_forms(forms: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Reduce the field descriptors to their names.

    `fields` is a list of objects describing each input. Only the names are kept: they say what
    kind of data the form collects, which is the point for a data-inventory rule, while the rest
    of the descriptor is presentation detail Neo4j cannot store as a scalar anyway.
    """
    transformed = []
    for form in forms:
        fields = form.get("fields") or []
        transformed.append(
            {
                **{k: v for k, v in form.items() if k != "fields"},
                "field_names": [field["name"] for field in fields if field.get("name")],
            },
        )
    return transformed


@timeit
def load_netlify_forms(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        NetlifyFormSchema(),
        data,
        lastupdated=update_tag,
        NETLIFY_ACCOUNT_ID=account_id,
    )


@timeit
def cleanup_netlify_forms(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(NetlifyFormSchema(), common_job_parameters).run(
        neo4j_session,
    )
