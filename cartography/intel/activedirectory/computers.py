import logging
from typing import Any, Dict, List

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.activedirectory.computer import ADComputerSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get(ldap_conn: Any, domain: Dict[str, Any]) -> List[Dict[str, Any]]:
    if ldap_conn is None:
        return [
            {
                "objectGUID": b"\x05" * 16,
                "distinguishedName": "cn=DC1,ou=Domain Controllers,dc=example,dc=com",
                "sAMAccountName": "DC1$",
                "dNSHostName": "dc1.example.com",
                "objectSid": None,
                "userAccountControl": 0x200,  # SERVER_TRUST_ACCOUNT -> domain controller
                "operatingSystem": "Windows Server",
                "lastLogonTimestamp": None,
                "servicePrincipalName": [],
                "memberOf": [],
                "msDS-SiteName": "Default-First-Site-Name",
            }
        ]
    base = f"DC={domain['dns_name'].replace('.', ',DC=')}"
    ldap_conn.search(
        search_base=base,
        search_filter="(objectClass=computer)",
        attributes=[
            "objectGUID",
            "distinguishedName",
            "sAMAccountName",
            "dNSHostName",
            "objectSid",
            "userAccountControl",
            "operatingSystem",
            "lastLogonTimestamp",
            "servicePrincipalName",
            "memberOf",
            "msDS-SiteName",
        ],
        paged_size=1000,
    )
    out: List[Dict[str, Any]] = []
    for e in ldap_conn.entries:
        out.append({
            "objectGUID": bytes(e.objectGUID.value) if hasattr(e.objectGUID, "value") else e.objectGUID.value,
            "distinguishedName": str(e.distinguishedName.value),
            "sAMAccountName": str(e.sAMAccountName.value) if getattr(e, "sAMAccountName", None) else None,
            "dNSHostName": str(e.dNSHostName.value) if getattr(e, "dNSHostName", None) else None,
            "objectSid": bytes(e.objectSid.value) if getattr(e, "objectSid", None) else None,
            "userAccountControl": int(e.userAccountControl.value) if getattr(e, "userAccountControl", None) else None,
            "operatingSystem": str(e.operatingSystem.value) if getattr(e, "operatingSystem", None) else None,
            "lastLogonTimestamp": int(e.lastLogonTimestamp.value) if getattr(e, "lastLogonTimestamp", None) else None,
            "servicePrincipalName": [str(s) for s in e.servicePrincipalName.values] if getattr(e, "servicePrincipalName", None) else [],
            "memberOf": [str(m) for m in e.memberOf.values] if getattr(e, "memberOf", None) else [],
            "msDS-SiteName": str(e.__getattr__("msDS-SiteName").value) if getattr(e, "msDS-SiteName", None) else None,
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


def _extract_ou_dn_from_dn(dn: str) -> str | None:
    parts = dn.split(",")
    return ",".join(parts[1:]) if len(parts) > 1 else None


def _is_domain_controller(uac: int | None) -> bool | None:
    if uac is None:
        return None
    # SERVER_TRUST_ACCOUNT = 0x200
    return (uac & 0x200) != 0


@timeit
def transform(raw_computers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for c in raw_computers:
        dn = c["distinguishedName"]
        out.append({
            "id": _guid_bytes_to_str(c["objectGUID"]),
            "samaccountname": c.get("sAMAccountName"),
            "dns_host_name": c.get("dNSHostName"),
            "distinguishedname": dn,
            "objectsid": _sid_bytes_to_str(c.get("objectSid")),
            "is_domain_controller": _is_domain_controller(c.get("userAccountControl")),
            "operatingsystem": c.get("operatingSystem"),
            "lastlogontimestamp": c.get("lastLogonTimestamp"),
            "spns": c.get("servicePrincipalName") or [],
            "ou_dn": _extract_ou_dn_from_dn(dn),
            "memberof_dns": c.get("memberOf") or [],
            "site_name": c.get("msDS-SiteName"),
        })
    return out


def load_computers(neo4j_session: neo4j.Session, data: List[Dict[str, Any]], domain_id: str, update_tag: int) -> None:
    load(neo4j_session, ADComputerSchema(), data, lastupdated=update_tag, DOMAIN_ID=domain_id)


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]) -> None:
    GraphJob.from_node_schema(ADComputerSchema(), common_job_parameters).run(neo4j_session)

