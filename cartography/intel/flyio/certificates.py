import logging
from typing import Any
from urllib.parse import quote

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.flyio.util import get_json
from cartography.intel.flyio.util import require_non_empty
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
    skipped_certificate_details = response.get("skipped_certificate_details") or []
    if skipped_certificate_details:
        logger.warning(
            "Skipping Fly.io certificate cleanup for app %r because detail "
            "requests failed for certificate hostnames: %s.",
            common_job_parameters["APP_NAME"],
            skipped_certificate_details,
        )
    else:
        cleanup(neo4j_session, common_job_parameters)
    return certificates


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
    app_name: str,
) -> dict[str, Any]:
    certificates: list[dict[str, Any]] = []
    skipped_certificate_details: list[str] = []
    next_cursor: str | None = None
    while True:
        current_cursor: str | None = next_cursor
        params: dict[str, str] = {}
        if current_cursor:
            params["cursor"] = current_cursor
        response = get_json(
            api_session,
            f"{base_url}/v1/apps/{app_name}/certificates",
            **params,
        )
        for cert in response["certificates"]:
            hostname = require_non_empty(cert.get("hostname"), "certificate hostname")
            encoded_hostname = quote(hostname, safe="")
            try:
                detail = get_json(
                    api_session,
                    f"{base_url}/v1/apps/{app_name}/certificates/{encoded_hostname}",
                )
            except requests.HTTPError as e:
                status_code = e.response.status_code if e.response is not None else None
                if status_code not in (403, 404, 410):
                    raise
                logger.warning(
                    "Skipping Fly.io certificate detail for app %r hostname %r "
                    "after HTTP %s. Certificate cleanup for this app will be skipped.",
                    app_name,
                    hostname,
                    status_code,
                )
                skipped_certificate_details.append(hostname)
                continue
            certificates.append({**cert, **detail})
        new_cursor = response.get("next_cursor")
        if new_cursor and new_cursor == current_cursor:
            raise ValueError(
                "Fly.io certificates pagination returned a repeated next_cursor.",
            )
        next_cursor = new_cursor
        if not next_cursor:
            return {
                "certificates": certificates,
                "total_count": response.get("total_count", len(certificates)),
                "skipped_certificate_details": skipped_certificate_details,
            }


def transform(response: dict[str, Any], app_id: str) -> list[dict[str, Any]]:
    certificates: list[dict[str, Any]] = []
    for cert in response["certificates"]:
        hostname = require_non_empty(cert.get("hostname"), "certificate hostname")
        issued_certificates: list[dict[str, Any]] = []
        sources: list[str] = []
        issuers: list[str] = []
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
