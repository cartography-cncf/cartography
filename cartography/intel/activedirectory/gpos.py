import logging
from typing import Any, Dict, List

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.activedirectory.gpo import ADGPOSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get(ldap_conn: Any, domain: Dict[str, Any]) -> List[Dict[str, Any]]:
    if ldap_conn is None:
        return [
            {
                "objectGUID": b"\x06" * 16,
                "displayName": "Default Domain Policy",
                "versionNumber": 1,
                "gPCWQLFilter": None,
            }
        ]
    base = f"CN=Policies,CN=System,DC={domain['dns_name'].replace('.', ',DC=')}"
    ldap_conn.search(
        search_base=base,
        search_filter="(objectClass=groupPolicyContainer)",
        attributes=["objectGUID", "displayName", "versionNumber", "gPCWQLFilter"],
        paged_size=1000,
    )
    out: List[Dict[str, Any]] = []
    for e in ldap_conn.entries:
        out.append({
            "objectGUID": bytes(e.objectGUID.value) if hasattr(e.objectGUID, "value") else e.objectGUID.value,
            "displayName": str(e.displayName.value) if getattr(e, "displayName", None) else None,
            "versionNumber": int(e.versionNumber.value) if getattr(e, "versionNumber", None) else None,
            "gPCWQLFilter": str(e.gPCWQLFilter.value) if getattr(e, "gPCWQLFilter", None) else None,
        })
    return out


def _guid_bytes_to_str(guid_bytes: bytes) -> str:
    import uuid
    return str(uuid.UUID(bytes_le=bytes(guid_bytes)))


@timeit
def transform(raw_gpos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for gpo in raw_gpos:
        out.append({
            "id": _guid_bytes_to_str(gpo["objectGUID"]),
            "displayname": gpo.get("displayName"),
            "version": gpo.get("versionNumber"),
            "wmifilter": gpo.get("gPCWQLFilter"),
        })
    return out


def load_gpos(neo4j_session: neo4j.Session, data: List[Dict[str, Any]], domain_id: str, update_tag: int) -> None:
    load(neo4j_session, ADGPOSchema(), data, lastupdated=update_tag, DOMAIN_ID=domain_id)


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]) -> None:
    GraphJob.from_node_schema(ADGPOSchema(), common_job_parameters).run(neo4j_session)

