import logging
from typing import Any, Dict, List

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.activedirectory.organizational_unit import ADOrganizationalUnitSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get(ldap_conn: Any, domain: Dict[str, Any]) -> List[Dict[str, Any]]:
    if ldap_conn is None:
        raise ValueError("ldap_conn is None; Active Directory connection not established.")
    base = f"DC={domain['dns_name'].replace('.', ',DC=')}"
    ldap_conn.search(
        search_base=base,
        search_filter="(objectClass=organizationalUnit)",
        attributes=["objectGUID", "distinguishedName", "name", "gPLink"],
        paged_size=1000,
    )
    out: List[Dict[str, Any]] = []
    for e in ldap_conn.entries:
        out.append({
            "objectGUID": bytes(e.objectGUID.value) if hasattr(e.objectGUID, "value") else e.objectGUID.value,
            "distinguishedName": str(e.distinguishedName.value),
            "name": str(e.name.value) if getattr(e, "name", None) else None,
            "gPLink": str(e.gPLink.value) if getattr(e, "gPLink", None) else None,
        })
    return out


def _guid_bytes_to_str(guid_bytes: bytes) -> str:
    import uuid
    return str(uuid.UUID(bytes_le=bytes(guid_bytes)))


def _parent_dn(dn: str) -> str | None:
    parts = dn.split(",")
    return ",".join(parts[1:]) if len(parts) > 1 else None


def _parse_gplink_ids(gplink: str | None) -> List[str]:
    if not gplink:
        return []
    # gPLink is like: [LDAP://<GUID=...>;<options>][LDAP://{...};<options>]
    import re
    ids: List[str] = []
    for m in re.finditer(r"GUID=([0-9A-Fa-f\-]{36})", gplink):
        ids.append(m.group(1).lower())
    for m in re.finditer(r"LDAP://\{([0-9A-Fa-f\-]{36})\}", gplink):
        ids.append(m.group(1).lower())
    return ids


@timeit
def transform(raw_ous: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for ou in raw_ous:
        dn = ou["distinguishedName"]
        out.append({
            "id": _guid_bytes_to_str(ou["objectGUID"]),
            "distinguishedname": dn,
            "name": ou.get("name"),
            "parent_dn": _parent_dn(dn),
            "gpo_ids": _parse_gplink_ids(ou.get("gPLink")),
        })
    return out


def load_ous(neo4j_session: neo4j.Session, data: List[Dict[str, Any]], domain_id: str, update_tag: int) -> None:
    load(neo4j_session, ADOrganizationalUnitSchema(), data, lastupdated=update_tag, DOMAIN_ID=domain_id)


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]) -> None:
    GraphJob.from_node_schema(ADOrganizationalUnitSchema(), common_job_parameters).run(neo4j_session)
