import logging
from typing import Any, Dict, List, Tuple

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.activedirectory.site import ADSiteSchema
from cartography.models.activedirectory.subnet import ADSubnetSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get(ldap_conn: Any, forest_info: Dict[str, Any]) -> Dict[str, Any]:
    if ldap_conn is None:
        raise ValueError("ldap_conn is None; Active Directory connection not established.")

    ldap_conn.search(search_base="", search_filter="(objectClass=*)", search_scope="BASE", attributes=["configurationNamingContext"])
    cfg_nc = str(ldap_conn.entries[0].configurationNamingContext.value)

    sites_base = f"CN=Sites,{cfg_nc}"
    ldap_conn.search(search_base=sites_base, search_filter="(objectClass=site)", attributes=["cn"], paged_size=1000)
    sites = [str(e.cn.value) for e in ldap_conn.entries]

    subnets_base = f"CN=Subnets,{sites_base}"
    ldap_conn.search(search_base=subnets_base, search_filter="(objectClass=subnet)", attributes=["cn", "siteObject"])
    site_to_subnets: Dict[str, List[str]] = {name: [] for name in sites}
    for e in ldap_conn.entries:
        subnet_name = str(e.cn.value)
        site_dn = str(e.siteObject.value) if getattr(e, "siteObject", None) else None
        if site_dn:
            # extract CN=SiteName
            site_name = site_dn.split(",")[0].split("=")[-1]
            site_to_subnets.setdefault(site_name, []).append(subnet_name)

    # Replication topology omitted in thin collector; callers may add if needed
    return {"sites": [{"name": s, "subnets": site_to_subnets.get(s, []), "replicates_with": []} for s in sites]}


@timeit
def transform(raw: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    sites_out: List[Dict[str, Any]] = []
    subnets_out: List[Dict[str, Any]] = []
    for s in raw.get("sites", []):
        sites_out.append({
            "id": s["name"],
            "subnet_ids": s.get("subnets", []),
            "replicate_site_names": s.get("replicates_with", []),
        })
        for sub in s.get("subnets", []):
            subnets_out.append({"id": sub})
    return sites_out, subnets_out


def load_sites_and_subnets(
    neo4j_session: neo4j.Session,
    sites: List[Dict[str, Any]],
    subnets: List[Dict[str, Any]],
    forest_id: str,
    update_tag: int,
) -> None:
    load(neo4j_session, ADSubnetSchema(), subnets, lastupdated=update_tag, FOREST_ID=forest_id)
    load(neo4j_session, ADSiteSchema(), sites, lastupdated=update_tag, FOREST_ID=forest_id)


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]) -> None:
    GraphJob.from_node_schema(ADSubnetSchema(), common_job_parameters).run(neo4j_session)
    GraphJob.from_node_schema(ADSiteSchema(), common_job_parameters).run(neo4j_session)
