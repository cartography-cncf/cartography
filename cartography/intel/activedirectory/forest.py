import logging
from typing import Any, Dict, Optional

from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get(ldap_conn: Any, base_dn: Optional[str]) -> Dict[str, Any]:
    """
    Thin collector to discover forest information via rootDSE.
    Returns a dict with at least: {"id": <forest_guid_str>, "name": <root domain FQDN>, "functional_level": <str>}
    """
    if ldap_conn is None:
        raise ValueError("ldap_conn is None; Active Directory connection not established.")

    # rootDSE read
    ldap_conn.search(search_base="", search_filter="(objectClass=*)", search_scope="BASE", attributes=[
        "objectGUID",
        "rootDomainNamingContext",
        "forestFunctionality",
    ])
    if not ldap_conn.entries:
        raise RuntimeError("AD: rootDSE search returned no entries")
    entry = ldap_conn.entries[0]
    return {
        "objectGUID": bytes(entry.objectGUID.value) if hasattr(entry.objectGUID, "value") else entry.objectGUID.value,
        "rootDomainNamingContext": str(entry.rootDomainNamingContext.value),
        "forestFunctionality": str(entry.forestFunctionality.value),
    }


def _guid_bytes_to_str(guid_bytes: bytes) -> str:
    if not isinstance(guid_bytes, (bytes, bytearray)):
        return str(guid_bytes)
    # Convert little-endian GUID bytes to standard GUID string
    import uuid
    return str(uuid.UUID(bytes_le=bytes(guid_bytes)))


def _dn_to_fqdn(dn: str) -> str:
    # dc=example,dc=com -> example.com
    parts = [p.split("=")[-1] for p in dn.split(",") if p.strip().lower().startswith("dc=")]
    return ".".join(parts)


@timeit
def transform(raw: Dict[str, Any]) -> Dict[str, Any]:
    forest_id = _guid_bytes_to_str(raw["objectGUID"]) if raw.get("objectGUID") is not None else _dn_to_fqdn(raw["rootDomainNamingContext"])  # fallback
    return {
        "id": forest_id,
        "name": _dn_to_fqdn(raw["rootDomainNamingContext"]),
        "functional_level": raw.get("forestFunctionality"),
    }
