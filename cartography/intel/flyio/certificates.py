import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.flyio.util import get_json
from cartography.models.flyio.certificate import FlyCertificateSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
) -> list[dict[str, Any]]:
    response = get(
        api_session,
        common_job_parameters["BASE_URL"],
        common_job_parameters["APP_NAME"],
    )
    certificates = transform(response, common_job_parameters["APP_ID"])
    load_certificates(
        neo4j_session,
        certificates,
        common_job_parameters["APP_ID"],
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)
    return certificates


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
    app_name: str,
) -> dict[str, Any]:
    certificates = []
    next_cursor = None
    while True:
        params = {}
        if next_cursor:
            params["cursor"] = next_cursor
        response = get_json(
            api_session,
            f"{base_url}/v1/apps/{app_name}/certificates",
            **params,
        )
        certificates.extend(response["certificates"])
        next_cursor = response.get("next_cursor")
        if not next_cursor:
            return {
                "certificates": certificates,
                "total_count": response.get("total_count", len(certificates)),
            }


def transform(response: dict[str, Any], app_id: str) -> list[dict[str, Any]]:
    certificates = []
    for cert in response["certificates"]:
        hostname = cert["hostname"]
        issued_certificates = []
        sources = []
        issuers = []
        for issued_cert in cert.get("certificates") or []:
            if issued_cert.get("source"):
                sources.append(issued_cert["source"])
            if issued_cert.get("issuer"):
                issuers.append(issued_cert["issuer"])
            issued_certificates.extend(issued_cert.get("issued") or [])
        certificates.append(
            {
                "id": f"{app_id}/{hostname}",
                "hostname": hostname,
                "status": cert.get("status"),
                "dns_provider": cert.get("dns_provider"),
                "configured": cert.get("configured"),
                "acme_dns_configured": cert.get("acme_dns_configured"),
                "acme_alpn_configured": cert.get("acme_alpn_configured"),
                "acme_http_configured": cert.get("acme_http_configured"),
                "ownership_txt_configured": cert.get("ownership_txt_configured"),
                "acme_requested": cert.get("acme_requested"),
                "has_custom_certificate": cert.get("has_custom_certificate"),
                "has_fly_certificate": cert.get("has_fly_certificate"),
                "certificate_authorities": [
                    issued["certificate_authority"]
                    for issued in issued_certificates
                    if issued.get("certificate_authority")
                ],
                "sources": sources,
                "issuers": issuers,
                "created_at": cert.get("created_at"),
                "updated_at": cert.get("updated_at"),
            }
        )
    return certificates


@timeit
def load_certificates(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    app_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        FlyCertificateSchema(),
        data,
        lastupdated=update_tag,
        APP_ID=app_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(FlyCertificateSchema(), common_job_parameters).run(
        neo4j_session,
    )
