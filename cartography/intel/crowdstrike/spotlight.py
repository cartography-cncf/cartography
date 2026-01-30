import logging
from typing import Dict
from typing import List

import neo4j
from falconpy.oauth2 import OAuth2
from falconpy.spotlight_vulnerabilities import Spotlight_Vulnerabilities

from cartography.client.core.tx import run_write_query
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
        load_vulnerability_data(neo4j_session, vulnerability_data, update_tag)


def load_vulnerability_data(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    update_tag: int,
) -> None:
    """
    Transform and load scan information
    """
    ingestion_cypher_query = """
    UNWIND $Vulnerabilities AS vuln
        MERGE (v:SpotlightVulnerability{id: vuln.id})
        ON CREATE SET v.aid = vuln.aid,
            v.cid = vuln.cid,
            v.firstseen = timestamp()
        SET v.status = vuln.status,
            v.created_timestamp = vuln.created_timestamp,
            v.closed_timestamp = vuln.closed_timestamp,
            v.updated_timestamp = vuln.updated_timestamp,
            v.cve_id = vuln.cve_id,
            v.host_info_local_ip = vuln.host_info_local_ip,
            v.remediation_ids = vuln.remediation_ids,
            v.app_product_name_version = vuln.app_product_name_version,
            v.lastupdated = $update_tag
        WITH v
        MATCH (h:CrowdstrikeHost{id: v.aid})
        MERGE (h)-[hv:HAS_VULNERABILITY]->(v)
        ON CREATE SET hv.firstseen = timestamp()
        SET hv.lastupdated = $update_tag
    """
    logger.info(f"Loading {len(data)} crowdstrike spotlight vulnerabilities.")
    vulns = []
    cves = []
    for item in data:
        vuln = {}
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
    run_write_query(
        neo4j_session,
        ingestion_cypher_query,
        Vulnerabilities=vulns,
        update_tag=update_tag,
    )
    _load_cves(neo4j_session, cves, update_tag)


def _load_cves(neo4j_session: neo4j.Session, data: List[Dict], update_tag: int) -> None:
    """
    Transform and load cve information
    """
    ingestion_cypher_query = """
    UNWIND $cves AS cve
        MERGE (c:CVE:CrowdstrikeFinding{id: cve.id})
        ON CREATE SET c.id = cve.id,
            c.firstseen = timestamp()
        SET c.base_score = cve.base_score,
            c.base_severity = cve.severity,
            c.exploitability_score = cve.exploit_status,
            c.lastupdated = $update_tag
        WITH c, cve
        MATCH (v:SpotlightVulnerability{id: cve.vuln_id})
        MERGE (v)-[hc:HAS_CVE]->(c)
        ON CREATE SET hc.firstseen = timestamp()
        SET hc.lastupdated = $update_tag
    """
    run_write_query(
        neo4j_session,
        ingestion_cypher_query,
        cves=data,
        update_tag=update_tag,
    )


def get_spotlight_vulnerability_ids(
    client: Spotlight_Vulnerabilities,
) -> List[List[str]]:
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
    ids: List[str],
) -> List[Dict]:
    response = client.getVulnerabilities(ids=",".join(ids))
    body = response.get("body", {})
    return body.get("resources", [])
