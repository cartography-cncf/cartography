"""Validate and transform BloodHound CE (v6) collector JSON.

Every SharpHound CE output file has the shape
``{"data": [<object>, ...], "meta": {"type", "count", "version", "methods", "collectorversion"}}``
with ``meta`` written after ``data``. Files are streamed with ijson because a
large forest produces millions of ACEs.
"""

import datetime
import enum
import logging
import zipfile
import zlib
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from dataclasses import field
from typing import Any
from typing import IO

import ijson

from cartography.intel.bloodhound.collection import BloodHoundImportError
from cartography.intel.bloodhound.collection import CollectionFile
from cartography.intel.common.object_store import ObjectStoreError

logger = logging.getLogger(__name__)

SUPPORTED_VERSION = 6

DOMAINS = "domains"
USERS = "users"
GROUPS = "groups"
COMPUTERS = "computers"
OUS = "ous"
GPOS = "gpos"
CONTAINERS = "containers"

NODE_TYPES = (DOMAINS, USERS, GROUPS, COMPUTERS, OUS, GPOS, CONTAINERS)
REQUIRED_TYPES = frozenset({DOMAINS, USERS, GROUPS, COMPUTERS})

MEMBER_OF = "MEMBER_OF"
CONTAINS = "CONTAINS"
GP_LINK = "GP_LINK"
TRUSTED_BY = "TRUSTED_BY"

_BOM = b"\xef\xbb\xbf"
_READ_ERRORS = (
    ijson.JSONError,
    zipfile.BadZipFile,
    zlib.error,
    EOFError,
    OSError,
    UnicodeDecodeError,
    ObjectStoreError,
)
_TRUST_DIRECTIONS = ("Disabled", "Inbound", "Outbound", "Bidirectional")
_TRUST_TYPES = (
    "TreeRoot",
    "ParentChild",
    "CrossLink",
    "External",
    "Forest",
    "Kerberos",
    "Unknown",
)
_SAME_FOREST_TRUST_TYPES = frozenset({"TreeRoot", "ParentChild", "CrossLink"})

# Allowlist of BloodHound properties copied onto nodes. Attributes that can hold
# cleartext secrets (userpassword, unixpassword, unicodepassword, sfupassword)
# are deliberately absent.
_COMMON_PROPERTIES = (
    "name",
    "domain",
    "distinguishedname",
    "description",
    "whencreated",
)
_TYPE_PROPERTIES: dict[str, tuple[str, ...]] = {
    DOMAINS: ("functionallevel",),
    USERS: (
        "samaccountname",
        "displayname",
        "email",
        "title",
        "enabled",
        "lastlogon",
        "lastlogontimestamp",
        "pwdlastset",
        "pwdneverexpires",
        "passwordnotreqd",
        "dontreqpreauth",
        "hasspn",
        "serviceprincipalnames",
        "admincount",
        "sensitive",
        "unconstraineddelegation",
        "trustedtoauth",
        "sidhistory",
    ),
    GROUPS: ("samaccountname", "admincount"),
    COMPUTERS: (
        "samaccountname",
        "operatingsystem",
        "enabled",
        "haslaps",
        "lastlogon",
        "lastlogontimestamp",
        "pwdlastset",
        "serviceprincipalnames",
        "unconstraineddelegation",
        "trustedtoauth",
        "sidhistory",
    ),
    OUS: ("blocksinheritance",),
    GPOS: ("gpcpath",),
    CONTAINERS: (),
}


class CollectionMethod(enum.IntFlag):
    """SharpHound's ``meta.methods`` bitmask (SharpHoundCommon ``CollectionMethod``)."""

    GROUP = 1
    LOCAL_ADMIN = 1 << 1
    GPO_LOCAL_GROUP = 1 << 2
    SESSION = 1 << 3
    LOGGED_ON = 1 << 4
    TRUSTS = 1 << 5
    ACL = 1 << 6
    CONTAINER = 1 << 7
    RDP = 1 << 8
    OBJECT_PROPS = 1 << 9
    DCOM = 1 << 12
    SPN_TARGETS = 1 << 13
    PS_REMOTE = 1 << 14
    USER_RIGHTS = 1 << 15


@dataclass(frozen=True)
class Provenance:
    source_uri: str
    collected_at: str
    collector_version: str | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "source_uri": self.source_uri,
            "collected_at": self.collected_at,
            "collector_version": self.collector_version,
        }


@dataclass(frozen=True)
class ValidatedFile:
    file: CollectionFile
    data_type: str
    provenance: Provenance


@dataclass
class ValidatedCollection:
    files: list[ValidatedFile] = field(default_factory=list)
    # Domain SID -> name, for every domain whose own object was imported.
    domains: dict[str, str | None] = field(default_factory=dict)
    # Domain SID -> name, for every domain an imported domain has a trust with.
    trust_targets: dict[str, str | None] = field(default_factory=dict)
    # (data type, domain SID) pairs with at least one object, live or deleted, in
    # the import.
    collected_types: set[tuple[str, str]] = field(default_factory=set)
    # Domain SID -> OR of meta.methods over the files holding its objects.
    domain_methods: dict[str, int] = field(default_factory=dict)

    def files_of(self, *data_types: str) -> list[ValidatedFile]:
        return [f for f in self.files if f.data_type in data_types]

    def was_collected(self, domain_sid: str, methods: CollectionMethod) -> bool:
        """Whether any of ``methods`` ran for the domain.

        A zero bitmask means the collector did not report its methods, which is
        treated as a full collection.
        """
        mask = self.domain_methods.get(domain_sid, 0)
        return mask == 0 or bool(mask & methods)


@contextmanager
def _json_stream(file: CollectionFile) -> Iterator[IO[bytes]]:
    with file.open() as fp:
        peek = getattr(fp, "peek", None)
        if peek is not None and peek(len(_BOM))[: len(_BOM)] == _BOM:
            fp.read(len(_BOM))
        yield fp


def read_meta(file: CollectionFile) -> Any:
    with _json_stream(file) as fp:
        return next(ijson.items(fp, "meta", use_float=True), None)


def has_data_array(file: CollectionFile) -> bool:
    """Whether the document has a top-level ``data`` array.

    SharpHound writes ``data`` first, so this stops after a few events.
    """
    with _json_stream(file) as fp:
        events = ijson.parse(fp, use_float=True)
        for prefix, event, value in events:
            if prefix == "" and event == "map_key" and value == "data":
                _, next_event, _ = next(events)
                return next_event == "start_array"
    return False


def iter_objects(file: CollectionFile) -> Iterator[dict[str, Any]]:
    with _json_stream(file) as fp:
        yield from ijson.items(fp, "data.item", use_float=True)


def _upper(value: Any) -> str | None:
    if value is None or value == "":
        return None
    if not isinstance(value, str):
        raise ValueError(f"expected an identifier string, got {value!r}")
    return value.upper()


def object_id(obj: dict[str, Any]) -> str:
    oid = obj.get("ObjectIdentifier")
    if not isinstance(oid, str) or not oid:
        raise ValueError("object has no ObjectIdentifier")
    return oid.upper()


def object_domain_sid(data_type: str, obj: dict[str, Any]) -> str:
    if data_type == DOMAINS:
        return object_id(obj)
    sid = _upper(obj["Properties"].get("domainsid") or obj.get("DomainSID"))
    if sid is None:
        raise ValueError(f"object {object_id(obj)} has no domainsid")
    return sid


def is_deleted(obj: dict[str, Any]) -> bool:
    return bool(obj.get("IsDeleted"))


def _typed_principal_ids(value: Any, field_name: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list")
    return [object_id(item) for item in value]


def _enum_name(value: Any, names: tuple[str, ...], field_name: str) -> str:
    if isinstance(value, str) and value in names:
        return value
    if (
        isinstance(value, int)
        and not isinstance(value, bool)
        and 0 <= value < len(names)
    ):
        return names[value]
    raise ValueError(f"unrecognized {field_name} {value!r}")


_EPOCH_PROPERTIES = frozenset(
    {"whencreated", "lastlogon", "lastlogontimestamp", "pwdlastset"},
)


def _epoch_to_datetime(value: Any) -> datetime.datetime | None:
    """Convert SharpHound's epoch seconds to a UTC datetime.

    SharpHound writes 0 or -1 for "never". Any other value that is not a
    representable number of seconds raises ValueError, which validation reports
    as a malformed object.
    """
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"expected epoch seconds, got {value!r}")
    try:
        seconds = int(value)
        if seconds <= 0:
            return None
        return datetime.datetime.fromtimestamp(seconds, tz=datetime.timezone.utc)
    except (OverflowError, OSError, ValueError) as exc:
        raise ValueError(f"epoch seconds out of range: {value!r}") from exc


def _optional_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def transform_node(
    data_type: str,
    obj: dict[str, Any],
    provenance: Provenance,
) -> dict[str, Any]:
    props = obj["Properties"]
    if not isinstance(props, dict):
        raise ValueError("Properties must be an object")
    node: dict[str, Any] = {
        "id": object_id(obj),
        "domainsid": object_domain_sid(data_type, obj),
        "isaclprotected": obj.get("IsACLProtected", props.get("isaclprotected")),
        **provenance.as_dict(),
    }
    for name in _COMMON_PROPERTIES + _TYPE_PROPERTIES[data_type]:
        value = props.get(name)
        node[name] = _epoch_to_datetime(value) if name in _EPOCH_PROPERTIES else value

    if data_type == DOMAINS:
        node["forest_root_id"] = _upper(obj.get("ForestRootIdentifier"))
        node["collected"] = True
    elif data_type in (USERS, COMPUTERS):
        node["primarygroupsid"] = _upper(obj.get("PrimaryGroupSID"))
        if not node["sidhistory"]:
            node["sidhistory"] = (
                _typed_principal_ids(obj.get("HasSIDHistory"), "HasSIDHistory") or None
            )
        node["unconstraineddelegation"] = obj.get(
            "UnconstrainedDelegation",
            props.get("unconstraineddelegation"),
        )
    if data_type == COMPUTERS:
        name = node["name"]
        node["hostname"] = name.split(".")[0] if isinstance(name, str) else None
        node["isdc"] = obj.get("IsDC", props.get("isdc"))
    return node


def _edge(
    source_id: str,
    target_id: str,
    provenance: Provenance,
    **extra: Any,
) -> dict[str, Any]:
    return {
        "source_id": source_id,
        "target_id": target_id,
        **provenance.as_dict(),
        **extra,
    }


def iter_edges(
    data_type: str,
    obj: dict[str, Any],
    provenance: Provenance,
) -> Iterator[tuple[str, dict[str, Any]]]:
    """Yield ``(edge kind, row)`` for every relationship declared by one object."""
    oid = object_id(obj)

    if data_type == GROUPS:
        for member_id in _typed_principal_ids(obj.get("Members"), "Members"):
            yield MEMBER_OF, _edge(member_id, oid, provenance)

    if data_type in (USERS, COMPUTERS):
        primary_group = _upper(obj.get("PrimaryGroupSID"))
        if primary_group:
            yield MEMBER_OF, _edge(oid, primary_group, provenance)

    # Current SharpHound records containment on the child (ContainedBy) and
    # leaves ChildObjects empty; older output fills ChildObjects instead.
    parent = obj.get("ContainedBy")
    if parent is not None:
        if not isinstance(parent, dict):
            raise ValueError("ContainedBy must be an object")
        yield CONTAINS, _edge(object_id(parent), oid, provenance)
    if data_type in (DOMAINS, OUS, CONTAINERS):
        for child_id in _typed_principal_ids(obj.get("ChildObjects"), "ChildObjects"):
            yield CONTAINS, _edge(oid, child_id, provenance)

    if data_type in (DOMAINS, OUS):
        for link in obj.get("Links") or []:
            gpo_id = _upper(link["GUID"])
            if gpo_id:
                yield GP_LINK, _edge(
                    gpo_id,
                    oid,
                    provenance,
                    enforced=bool(link.get("IsEnforced")),
                )

    if data_type == DOMAINS:
        for trust in obj.get("Trusts") or []:
            yield from _trust_edges(oid, trust, provenance)


def _trust_edges(
    domain_id: str,
    trust: dict[str, Any],
    provenance: Provenance,
) -> Iterator[tuple[str, dict[str, Any]]]:
    target_id = _upper(trust["TargetDomainSid"])
    direction = _enum_name(
        trust.get("TrustDirection"), _TRUST_DIRECTIONS, "trust direction"
    )
    if target_id is None or direction == "Disabled":
        return
    trust_type = _enum_name(trust.get("TrustType"), _TRUST_TYPES, "trust type")
    props = {
        "trust_type": trust_type,
        "same_forest": trust_type in _SAME_FOREST_TRUST_TYPES,
        "is_transitive": trust.get("IsTransitive"),
        "sid_filtering_enabled": trust.get("SidFilteringEnabled"),
        "tgt_delegation_enabled": trust.get("TGTDelegationEnabled"),
        "trust_attributes": _optional_int(trust.get("TrustAttributes")),
    }
    # An inbound trust means the target domain trusts this one; an outbound
    # trust means this domain trusts the target. TRUSTED_BY runs from the trusted
    # domain to the trusting one, the direction in which access flows.
    if direction in ("Inbound", "Bidirectional"):
        yield TRUSTED_BY, _edge(domain_id, target_id, provenance, **props)
    if direction in ("Outbound", "Bidirectional"):
        yield TRUSTED_BY, _edge(target_id, domain_id, provenance, **props)


def trust_targets(obj: dict[str, Any]) -> dict[str, str | None]:
    targets: dict[str, str | None] = {}
    for trust in obj.get("Trusts") or []:
        target_id = _upper(trust["TargetDomainSid"])
        if target_id:
            targets[target_id] = trust.get("TargetDomainName")
    return targets


def parse_collected_at(value: str) -> str:
    try:
        return datetime.datetime.fromisoformat(value).isoformat()
    except ValueError as exc:
        raise BloodHoundImportError(
            f"Invalid BloodHound collection timestamp {value!r}: expected ISO 8601, "
            "for example 2026-10-12T14:30:15.",
        ) from exc


def validate_collection(
    files: list[CollectionFile],
    collected_at_override: str | None = None,
) -> ValidatedCollection:
    """Read every file once and reject the collection if anything is wrong.

    Runs the same transforms the load uses, so a malformed object fails here,
    before any write, rather than half way through the load.
    """
    if not files:
        raise BloodHoundImportError(
            "No BloodHound JSON files were found in the source."
        )

    collected_at = (
        parse_collected_at(collected_at_override) if collected_at_override else None
    )
    collection = ValidatedCollection()
    type_sources: dict[tuple[str, str], str] = {}
    referenced_domains: dict[str, str] = {}
    unreported_methods: list[str] = []
    empty_files: list[_FileResult] = []

    for file in files:
        try:
            result = _validate_file(file, collected_at)
        except BloodHoundImportError:
            raise
        except _READ_ERRORS as exc:
            raise BloodHoundImportError(
                f"Failed to read {file.source_uri}: {exc}",
            ) from exc
        if result is None:
            continue
        validated = result.file
        if result.methods == 0:
            unreported_methods.append(file.source_uri)
        if not result.domain_sids:
            empty_files.append(result)
        collection.files.append(validated)
        for domain_sid, domain_name in result.domains.items():
            if domain_name or domain_sid not in collection.domains:
                collection.domains[domain_sid] = domain_name
        for target_id, target_name in result.trust_targets.items():
            collection.trust_targets.setdefault(target_id, target_name)
        for domain_sid in result.domain_sids:
            key = (validated.data_type, domain_sid)
            previous = type_sources.get(key)
            if previous is not None:
                raise BloodHoundImportError(
                    f"Domain {domain_sid} has {validated.data_type} in both {previous} "
                    f"and {file.source_uri}. Import one collection per domain.",
                )
            type_sources[key] = file.source_uri
            referenced_domains.setdefault(domain_sid, file.source_uri)
            collection.collected_types.add(key)
            collection.domain_methods[domain_sid] = (
                collection.domain_methods.get(domain_sid, 0) | result.methods
            )

    # An empty file names no domain. With a single domain in the import it can
    # only describe that domain, so it marks the type as collected and lets
    # cleanup remove the domain's previous objects of that type. With several
    # domains it is ambiguous and the existing data is kept.
    if len(collection.domains) == 1:
        (only_domain,) = collection.domains
        for result in empty_files:
            collection.collected_types.add((result.file.data_type, only_domain))
            collection.domain_methods[only_domain] = (
                collection.domain_methods.get(only_domain, 0) | result.methods
            )
    elif empty_files:
        logger.warning(
            "Keeping existing data for empty BloodHound files in a multi-domain "
            "import: %s",
            ", ".join(r.file.provenance.source_uri for r in empty_files),
        )

    present_types = {f.data_type for f in collection.files}
    missing = sorted(REQUIRED_TYPES - present_types)
    if missing:
        raise BloodHoundImportError(
            f"BloodHound collection is missing {', '.join(missing)} data. "
            "Collect with SharpHound -c All or -c Default.",
        )
    for domain_sid, source in sorted(referenced_domains.items()):
        if domain_sid not in collection.domains:
            raise BloodHoundImportError(
                f"{source} has objects from domain {domain_sid}, which is not in the "
                "collection's domains data.",
            )
    if unreported_methods:
        logger.warning(
            "BloodHound files did not report their collection methods; treating them "
            "as full collections: %s",
            ", ".join(unreported_methods),
        )
    return collection


@dataclass
class _FileResult:
    file: ValidatedFile
    methods: int
    domain_sids: set[str] = field(default_factory=set)
    domains: dict[str, str | None] = field(default_factory=dict)
    trust_targets: dict[str, str | None] = field(default_factory=dict)


def _validate_file(
    file: CollectionFile,
    collected_at_override: str | None,
) -> _FileResult | None:
    meta = read_meta(file)
    if not isinstance(meta, dict):
        raise BloodHoundImportError(
            f"{file.source_uri} has no meta block. The file is truncated or is not "
            "BloodHound collector output.",
        )
    data_type = meta.get("type")
    if not isinstance(data_type, str) or not data_type:
        raise BloodHoundImportError(
            f"{file.source_uri} has no data type in its meta block.",
        )
    if data_type not in NODE_TYPES:
        logger.info(
            "Skipping BloodHound %s data in %s: not supported by this module.",
            data_type,
            file.source_uri,
        )
        return None
    version = meta.get("version")
    if version != SUPPORTED_VERSION:
        raise BloodHoundImportError(
            f"{file.source_uri} is BloodHound data version {version}; only version "
            f"{SUPPORTED_VERSION} (BloodHound CE / SharpHound CE) is supported.",
        )
    expected_count = meta.get("count")
    collected_at = collected_at_override or file.collected_at
    if collected_at is None:
        raise BloodHoundImportError(
            f"Cannot tell when {file.source_uri} was collected: its name has no "
            "SharpHound timestamp prefix. Set --bloodhound-collected-at.",
        )
    provenance = Provenance(
        source_uri=file.source_uri,
        collected_at=collected_at,
        collector_version=meta.get("collectorversion"),
    )
    methods = meta.get("methods", 0)
    if isinstance(methods, bool) or not isinstance(methods, int) or methods < 0:
        raise BloodHoundImportError(
            f"{file.source_uri} has an invalid collection-method mask {methods!r}.",
        )
    if not has_data_array(file):
        raise BloodHoundImportError(
            f"{file.source_uri} has no data array. The file is truncated or is not "
            "BloodHound collector output.",
        )
    result = _FileResult(
        file=ValidatedFile(file, data_type, provenance),
        methods=methods,
    )

    count = 0
    for obj in iter_objects(file):
        count += 1
        try:
            if not isinstance(obj, dict):
                raise ValueError("data entries must be objects")
            result.domain_sids.add(object_domain_sid(data_type, obj))
            if is_deleted(obj):
                continue
            node = transform_node(data_type, obj, provenance)
            if data_type == DOMAINS:
                result.domains[node["id"]] = node["name"] or result.domains.get(
                    node["id"],
                )
                result.trust_targets.update(trust_targets(obj))
            for _ in iter_edges(data_type, obj, provenance):
                pass
        except (KeyError, TypeError, ValueError, AttributeError) as exc:
            raise BloodHoundImportError(
                f"Malformed {data_type} object #{count} in {file.source_uri}: {exc!r}",
            ) from exc

    if count != expected_count:
        raise BloodHoundImportError(
            f"{file.source_uri} contains {count} objects but its meta block declares "
            f"{expected_count}. The file is incomplete.",
        )
    return result
