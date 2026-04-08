import logging
from typing import Any

import neo4j
from falconpy.oauth2 import OAuth2
from falconpy.spotlight_vulnerabilities import Spotlight_Vulnerabilities

from cartography.client.core.tx import load
from cartography.models.crowdstrike.spotlight import CrowdstrikeCVESchema
from cartography.models.crowdstrike.spotlight import SpotlightVulnerabilitySchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync_vulnerabilities(
    neo4j_session: neo4j.Session,
    update_tag: int,
    authorization: OAuth2,
) -> None:
    client = Spotlight_Vulnerabilities(auth_object=authorization)
    all_ids = get_spotlight_vulnerability_ids(client)
    for ids in all_ids:
        vulnerability_data = get_spotlight_vulnerabilities(client, ids)
        vulns, cves = transform(vulnerability_data)
        load_vulnerability_data(neo4j_session, vulns, update_tag)
        load_cve_data(neo4j_session, cves, update_tag)


def transform(data: list[dict]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    vulns: list[dict[str, Any]] = []
    cves: list[dict[str, Any]] = []
    for item in data:
        vuln: dict[str, Any] = {}
        for key in [
            "id",
            "aid",
            "cid",
            "status",
            "created_timestamp",
            "closed_timestamp",
            "updated_timestamp",
        ]:
            vuln[key] = item.get(key)
        vuln["remediation_ids"] = item.get("remediation", {}).get("ids", [])
        vuln["app_product_name_version"] = item.get("app", {}).get(
            "product_name_version",
        )
        cve = item.get("cve", {})
        vuln["cve_id"] = cve.get("id")
        if cve:
            cve["vuln_id"] = vuln["id"]
            cves.append(cve)
        vuln["host_info_local_ip"] = item.get("host_info", {}).get("local_ip")
        vulns.append(vuln)
    return vulns, cves


def load_vulnerability_data(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SpotlightVulnerabilitySchema(),
        data,
        lastupdated=update_tag,
    )


def load_cve_data(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        CrowdstrikeCVESchema(),
        data,
        lastupdated=update_tag,
    )


def get_spotlight_vulnerability_ids(
    client: Spotlight_Vulnerabilities,
) -> list[list[str]]:
    ids = []
    parameters = {"filter": 'status:!"closed"', "limit": 400}
    response = client.queryVulnerabilities(parameters=parameters)
    body = response.get("body", {})
    resources = body.get("resources", [])
    if not resources:
        logger.warning("No vulnerability IDs in spotlight queryVulnerabilities.")
        return []
    ids.append(resources)
    after = body.get("meta", {}).get("pagination", {}).get("after")
    while after:
        parameters["after"] = after
        response = client.queryVulnerabilities(parameters=parameters)
        body = response.get("body", {})
        resources = body.get("resources", [])
        if not resources:
            break
        ids.append(resources)
        after = body.get("meta", {}).get("pagination", {}).get("after")
    return ids


def get_spotlight_vulnerabilities(
    client: Spotlight_Vulnerabilities,
    ids: list[str],
) -> list[dict]:
    response = client.getVulnerabilities(ids=",".join(ids))
    body = response.get("body", {})
    return body.get("resources", [])
