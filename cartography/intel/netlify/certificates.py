import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.netlify.util import get_one
from cartography.models.netlify.certificate import NetlifyCertificateSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync_netlify_certificates(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    base_url: str,
    account_id: str,
    sites: list[dict[str, Any]],
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    raw: list[tuple[str, dict[str, Any]]] = []
    for site in sites:
        certificate = get_netlify_certificate(api_session, base_url, site["id"])
        if certificate:
            raw.append((site["id"], certificate))
    certificates = transform_netlify_certificates(raw)
    load_netlify_certificates(neo4j_session, certificates, account_id, update_tag)
    cleanup_netlify_certificates(neo4j_session, common_job_parameters)


@timeit
def get_netlify_certificate(
    api_session: requests.Session,
    base_url: str,
    site_id: str,
) -> dict[str, Any] | None:
    """
    Fetch a site's TLS certificate, if it has one.

    A site with no custom domain answers with a JSON `null` body rather than a 404, which
    get_one() normalises to None.
    """
    return get_one(api_session, f"{base_url}/sites/{site_id}/ssl")


def transform_netlify_certificates(
    raw: list[tuple[str, dict[str, Any]]],
) -> list[dict[str, Any]]:
    """
    Attach the site id, synthesise an id, and pick out the primary domain.

    Netlify returns the certificate with no identifier of any kind, and a site has at most one,
    so `<site_id>_ssl` identifies it. The Certificate ontology mapping needs a scalar `domain`,
    so the first SAN entry is promoted; the full list stays in `domains`.
    """
    certificates = []
    for site_id, certificate in raw:
        domains = certificate.get("domains") or []
        certificates.append(
            {
                **certificate,
                "id": f"{site_id}_ssl",
                "site_id": site_id,
                "domain": domains[0] if domains else None,
            },
        )
    return certificates


@timeit
def load_netlify_certificates(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        NetlifyCertificateSchema(),
        data,
        lastupdated=update_tag,
        NETLIFY_ACCOUNT_ID=account_id,
    )


@timeit
def cleanup_netlify_certificates(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(NetlifyCertificateSchema(), common_job_parameters).run(
        neo4j_session,
    )
