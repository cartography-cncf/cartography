import logging
from typing import Any, Dict, List

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.activedirectory.group import ADGroupSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get(ldap_conn: Any, domain: Dict[str, Any]) -> List[Dict[str, Any]]:
    if ldap_conn is None:
        raise ValueError("ldap_conn is None; Active Directory connection not established.")
    base = f"DC={domain['dns_name'].replace('.', ',DC=')}"
    ldap_conn.search(
        search_base=base,
        search_filter="(objectClass=group)",
        attributes=["objectGUID", "distinguishedName", "sAMAccountName", "objectSid", "groupType", "member", "memberOf"],
        paged_size=1000,
    )
    out: List[Dict[str, Any]] = []
    for e in ldap_conn.entries:
        out.append({
            "objectGUID": bytes(e.objectGUID.value) if hasattr(e.objectGUID, "value") else e.objectGUID.value,
            "distinguishedName": str(e.distinguishedName.value),
            "sAMAccountName": str(e.sAMAccountName.value) if getattr(e, "sAMAccountName", None) else None,
            "objectSid": bytes(e.objectSid.value) if getattr(e, "objectSid", None) else None,
            "groupType": int(e.groupType.value) if getattr(e, "groupType", None) else None,
            "member": [str(m) for m in e.member.values] if getattr(e, "member", None) else [],
            "memberOf": [str(m) for m in e.memberOf.values] if getattr(e, "memberOf", None) else [],
        })
    return out


def _guid_bytes_to_str(guid_bytes: bytes) -> str:
    import uuid
    return str(uuid.UUID(bytes_le=bytes(guid_bytes)))


def _sid_bytes_to_str(sid: bytes | None) -> str | None:
    if sid is None:
        return None
    import struct
    rev = sid[0]
    subcnt = sid[1]
    auth = int.from_bytes(sid[2:8], byteorder="big")
    subs: List[int] = []
    offset = 8
    for _ in range(subcnt):
        subs.append(struct.unpack("<I", sid[offset:offset + 4])[0])
        offset += 4
    return "S-{}-{}-{}".format(rev, auth, "-".join(str(s) for s in subs))


@timeit
def transform(raw_groups: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for g in raw_groups:
        out.append({
            "id": _guid_bytes_to_str(g["objectGUID"]),
            "distinguishedname": g["distinguishedName"],
            "samaccountname": g.get("sAMAccountName"),
            "objectsid": _sid_bytes_to_str(g.get("objectSid")),
            "scope": None,
            "type": g.get("groupType"),
            "is_builtin": None,
            "member_dns": g.get("member") or [],
            "memberof_dns": g.get("memberOf") or [],
        })
    return out


def load_groups(neo4j_session: neo4j.Session, data: List[Dict[str, Any]], domain_id: str, update_tag: int) -> None:
    load(neo4j_session, ADGroupSchema(), data, lastupdated=update_tag, DOMAIN_ID=domain_id)


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]) -> None:
    GraphJob.from_node_schema(ADGroupSchema(), common_job_parameters).run(neo4j_session)
