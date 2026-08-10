import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.unikraft.util import list_resources
from cartography.intel.unikraft.util import METRO_BASE_URLS
from cartography.intel.unikraft.util import require_non_empty
from cartography.models.unikraft.certificate import UnikraftCertificateSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get(session: requests.Session, base_url: str) -> list[dict[str, Any]]:
    return list_resources(session, f"{base_url}/v1/certificates", "certificates")


def transform(certificates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "uuid": require_non_empty(certificate.get("uuid"), "certificate uuid"),
            "name": certificate.get("name"),
            "created_at": certificate.get("created_at"),
            "common_name": certificate.get("common_name"),
            "subject": certificate.get("subject"),
            "issuer": certificate.get("issuer"),
            "serial_number": certificate.get("serial_number"),
            "not_before": certificate.get("not_before"),
            "not_after": certificate.get("not_after"),
            "state": certificate.get("state"),
            "status": certificate.get("status"),
            "message": certificate.get("message"),
        }
        for certificate in certificates
    ]


@timeit
def load_certificates(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    account_id: str,
    metro: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        UnikraftCertificateSchema(),
        data,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
        METRO=metro,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(UnikraftCertificateSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    session: requests.Session,
    account_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    for metro, base_url in METRO_BASE_URLS.items():
        certificates = get(session, base_url)
        transformed = transform(certificates)
        load_certificates(neo4j_session, transformed, account_id, metro, update_tag)
    cleanup(neo4j_session, common_job_parameters)
