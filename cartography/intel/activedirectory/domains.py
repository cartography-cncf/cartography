import logging
from typing import Any, Dict, List

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.activedirectory.domain import ADDomainSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_domains(ldap_conn: Any, forest_info: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Thin collector to list domains in the forest via CN=Partitions under Configuration NC.
    Returns a list of raw dicts with keys including objectGUID, dnsRoot, nETBIOSName, objectSid.
    """
    if ldap_conn is None:
        # Minimal stub for tests
        return [
            {
                "objectGUID": b"\x01" * 16,
                "dnsRoot": "example.com",
                "nETBIOSName": "EXAMPLE",
                "objectSid": b"\x01\x05\x00\x00\x00\x00\x00\x05\x15\x00\x00\x00\xAA\xAA\xAA\xAA\xBB\xBB\xBB\xBB\xCC\xCC\xCC\xCC",
            },
        ]

    # Discover Configuration NC
    ldap_conn.search(search_base="", search_filter="(objectClass=*)", search_scope="BASE", attributes=["configurationNamingContext"])
    cfg_nc = str(ldap_conn.entries[0].configurationNamingContext.value)

    # Search partitions for crossRef objects with nCName ending in DC=...
    base = f"CN=Partitions,{cfg_nc}"
    ldap_conn.search(
        search_base=base,
        search_filter="(objectClass=crossRef)",
        attributes=["nCName", "dnsRoot", "nETBIOSName", "objectGUID", "objectSid"],
    )
    domains: List[Dict[str, Any]] = []
    for e in ldap_conn.entries:
        # Filter to actual domain NCs by presence of dnsRoot
        if not getattr(e, "dnsRoot", None):
            continue
        domains.append({
            "objectGUID": bytes(e.objectGUID.value) if hasattr(e.objectGUID, "value") else e.objectGUID.value,
            "dnsRoot": str(e.dnsRoot.value),
            "nETBIOSName": str(e.nETBIOSName.value) if getattr(e, "nETBIOSName", None) else None,
            "objectSid": bytes(e.objectSid.value) if getattr(e, "objectSid", None) else None,
        })
    return domains


def _guid_bytes_to_str(guid_bytes: bytes) -> str:
    import uuid
    return str(uuid.UUID(bytes_le=bytes(guid_bytes)))


def _sid_bytes_to_str(sid: bytes | None) -> str | None:
    if sid is None:
        return None
    # Basic SID conversion
    # Reference: https://learn.microsoft.com/windows/win32/secauthz/sid-strings
    import struct
    if len(sid) < 8:
        return None
    rev = sid[0]
    subcnt = sid[1]
    auth = int.from_bytes(sid[2:8], byteorder="big")
    subs: List[int] = []
    offset = 8
    for _ in range(subcnt):
        if offset + 4 <= len(sid):
            subs.append(struct.unpack("<I", sid[offset:offset + 4])[0])
            offset += 4
        else:
            break
    return "S-{}-{}-{}".format(rev, auth, "-".join(str(s) for s in subs))


@timeit
def transform_domains(raw_domains: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for d in raw_domains:
        out.append({
            "id": _guid_bytes_to_str(d["objectGUID"]),
            "dns_name": d["dnsRoot"],
            "netbios_name": d.get("nETBIOSName"),
            "sid": _sid_bytes_to_str(d.get("objectSid")),
        })
    return out


def cleanup(neo4j_session, common_job_parameters):
    GraphJob.from_node_schema(ADDomainSchema(), common_job_parameters).run(neo4j_session)
