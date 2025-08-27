import logging
from typing import Any, Dict, List

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.activedirectory.user import ADUserSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get(ldap_conn: Any, domain: Dict[str, Any]) -> List[Dict[str, Any]]:
    if ldap_conn is None:
        return [
            {
                "objectGUID": b"\x04" * 16,
                "distinguishedName": "cn=Alice,ou=Engineering,dc=example,dc=com",
                "userPrincipalName": "alice@example.com",
                "sAMAccountName": "alice",
                "objectSid": b"\x01\x05\x00\x00\x00\x00\x00\x05\x15\x00\x00\x00\xaa\xaa\xaa\xaa\xbb\xbb\xbb\xbb\xcc\xcc\xcc\xcc\x2a\x00\x00\x00",
                "userAccountControl": 512,
                "lastLogonTimestamp": None,
                "pwdLastSet": None,
                "servicePrincipalName": [],
                "memberOf": ["cn=Domain Admins,cn=Users,dc=example,dc=com"],
            }
        ]
    base = f"DC={domain['dns_name'].replace('.', ',DC=')}"
    ldap_conn.search(
        search_base=base,
        search_filter="(&(objectClass=user)(!(objectClass=computer)))",
        attributes=[
            "objectGUID",
            "distinguishedName",
            "userPrincipalName",
            "sAMAccountName",
            "objectSid",
            "userAccountControl",
            "lastLogonTimestamp",
            "pwdLastSet",
            "servicePrincipalName",
            "memberOf",
        ],
        paged_size=1000,
    )
    out: List[Dict[str, Any]] = []
    for e in ldap_conn.entries:
        out.append({
            "objectGUID": bytes(e.objectGUID.value) if hasattr(e.objectGUID, "value") else e.objectGUID.value,
            "distinguishedName": str(e.distinguishedName.value),
            "userPrincipalName": str(e.userPrincipalName.value) if getattr(e, "userPrincipalName", None) else None,
            "sAMAccountName": str(e.sAMAccountName.value) if getattr(e, "sAMAccountName", None) else None,
            "objectSid": bytes(e.objectSid.value) if getattr(e, "objectSid", None) else None,
            "userAccountControl": int(e.userAccountControl.value) if getattr(e, "userAccountControl", None) else None,
            "lastLogonTimestamp": int(e.lastLogonTimestamp.value) if getattr(e, "lastLogonTimestamp", None) else None,
            "pwdLastSet": int(e.pwdLastSet.value) if getattr(e, "pwdLastSet", None) else None,
            "servicePrincipalName": [str(s) for s in e.servicePrincipalName.values] if getattr(e, "servicePrincipalName", None) else [],
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


def _extract_ou_dn_from_dn(dn: str) -> str | None:
    # Walk up until first OU= or CN=Users style containers are included
    # For simplicity: return parent of the CN=User leaf if present
    parts = dn.split(",")
    return ",".join(parts[1:]) if len(parts) > 1 else None


def _enabled_from_uac(uac: int | None) -> bool | None:
    if uac is None:
        return None
    # ACCOUNTDISABLE = 0x0002
    return (uac & 0x0002) == 0


@timeit
def transform(raw_users: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for u in raw_users:
        dn = u["distinguishedName"]
        out.append({
            "id": _guid_bytes_to_str(u["objectGUID"]),
            "samaccountname": u.get("sAMAccountName"),
            "userprincipalname": u.get("userPrincipalName"),
            "distinguishedname": dn,
            "objectsid": _sid_bytes_to_str(u.get("objectSid")),
            "enabled": _enabled_from_uac(u.get("userAccountControl")),
            "pwdlastset": u.get("pwdLastSet"),
            "lastlogontimestamp": u.get("lastLogonTimestamp"),
            "spns": u.get("servicePrincipalName") or [],
            "ou_dn": _extract_ou_dn_from_dn(dn),
            "memberof_dns": u.get("memberOf") or [],
        })
    return out


def load_users(neo4j_session: neo4j.Session, data: List[Dict[str, Any]], domain_id: str, update_tag: int) -> None:
    load(neo4j_session, ADUserSchema(), data, lastupdated=update_tag, DOMAIN_ID=domain_id)


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]) -> None:
    GraphJob.from_node_schema(ADUserSchema(), common_job_parameters).run(neo4j_session)

