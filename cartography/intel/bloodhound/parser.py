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
from collections import Counter
from collections import defaultdict
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
SAME_FOREST_TRUST = "SAME_FOREST_TRUST"
CROSS_FOREST_TRUST = "CROSS_FOREST_TRUST"

GENERIC_ALL = "GENERIC_ALL"
GENERIC_WRITE = "GENERIC_WRITE"
WRITE_DACL = "WRITE_DACL"
WRITE_OWNER = "WRITE_OWNER"
OWNS = "OWNS"
FORCE_CHANGE_PASSWORD = "FORCE_CHANGE_PASSWORD"
ADD_MEMBER = "ADD_MEMBER"
ALL_EXTENDED_RIGHTS = "ALL_EXTENDED_RIGHTS"
ADD_KEY_CREDENTIAL_LINK = "ADD_KEY_CREDENTIAL_LINK"
READ_LAPS_PASSWORD = "READ_LAPS_PASSWORD"
READ_GMSA_PASSWORD = "READ_GMSA_PASSWORD"
ADD_SELF = "ADD_SELF"
WRITE_SPN = "WRITE_SPN"
DC_SYNC = "DC_SYNC"
ADMIN_TO = "ADMIN_TO"
CAN_RDP = "CAN_RDP"
CAN_PS_REMOTE = "CAN_PS_REMOTE"
HAS_SESSION = "HAS_SESSION"
ALLOWED_TO_DELEGATE = "ALLOWED_TO_DELEGATE"
ALLOWED_TO_ACT = "ALLOWED_TO_ACT"
HAS_SID_HISTORY = "HAS_SID_HISTORY"

# ACE right name -> relationship. Rights not listed here are counted and logged.
ACL_RIGHTS: dict[str, str] = {
    "GenericAll": GENERIC_ALL,
    "GenericWrite": GENERIC_WRITE,
    "WriteDacl": WRITE_DACL,
    "WriteOwner": WRITE_OWNER,
    "Owns": OWNS,
    "ForceChangePassword": FORCE_CHANGE_PASSWORD,
    "AddMember": ADD_MEMBER,
    "AllExtendedRights": ALL_EXTENDED_RIGHTS,
    "AddKeyCredentialLink": ADD_KEY_CREDENTIAL_LINK,
    "ReadLAPSPassword": READ_LAPS_PASSWORD,
    "ReadGMSAPassword": READ_GMSA_PASSWORD,
    "AddSelf": ADD_SELF,
    "WriteSPN": WRITE_SPN,
}
# A principal holding both replication rights on a domain can DCSync it.
_DCSYNC_RIGHTS = frozenset({"GetChanges", "GetChangesAll"})
# OWNER RIGHTS stands for whoever owns the object; it is not a principal.
_OWNER_RIGHTS_SID = "S-1-3-4"

# Local group RID -> relationship to the computer that holds the group.
_LOCAL_GROUP_EDGES = {"544": ADMIN_TO, "555": CAN_RDP, "580": CAN_PS_REMOTE}
_GPO_LOCAL_GROUP_EDGES = {
    "LocalAdmins": ADMIN_TO,
    "RemoteDesktopUsers": CAN_RDP,
    "PSRemoteUsers": CAN_PS_REMOTE,
}
_RDP_LOGON_RIGHT = "SeRemoteInteractiveLogonRight"
_SESSION_LISTS = ("Sessions", "PrivilegedSessions", "RegistrySessions")
# Accounts local to one computer, which have no AD object.
_LOCAL_PRINCIPAL_TYPES = frozenset({"LocalUser", "LocalGroup"})

# BloodHound object type -> label of the placeholder created for a principal
# that an edge references but the import does not contain.
PLACEHOLDER_LABELS: dict[str, str] = {
    "User": "ADUser",
    "Group": "ADGroup",
    "Computer": "ADComputer",
}

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
# BloodHound CE's rule: every other trust type is a cross-forest trust.
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
    # Domain SID -> merged node row for every imported domain.
    domain_rows: dict[str, dict[str, Any]] = field(default_factory=dict)
    # (data type, domain SID) pairs with at least one object, live or deleted, in
    # the import.
    collected_types: set[tuple[str, str]] = field(default_factory=set)
    # Domain SID -> OR of meta.methods over the files holding its objects.
    domain_methods: dict[str, int] = field(default_factory=dict)
    # Principal ID -> placeholder label, for every principal an edge references.
    referenced_principals: dict[str, str] = field(default_factory=dict)
    # (edge kind, domain SID) -> computers whose host data for that edge kind
    # was not collected, so their existing edges are kept.
    uncollected_hosts: dict[tuple[str, str], set[str]] = field(
        default_factory=lambda: defaultdict(set),
    )
    # Computer ID -> principals holding the remote interactive logon right, for
    # computers where membership of Remote Desktop Users does not grant it.
    rdp_logon_grantees: dict[str, set[str]] = field(default_factory=dict)

    def allows_rdp(self, principal_id: str, computer_id: str) -> bool:
        """Whether the computer's collected user rights let the principal RDP."""
        grantees = self.rdp_logon_grantees.get(computer_id)
        return grantees is None or principal_id in grantees

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


_PROVENANCE_FIELDS = frozenset({"source_uri", "collected_at", "collector_version"})


def merge_domain_row(
    rows: dict[str, dict[str, Any]],
    row: dict[str, Any],
) -> dict[str, Any]:
    """Merge a repeated record of the same domain into ``rows``.

    A collection can describe one domain more than once, for example a partial
    record without a name next to the full one. Missing values are filled in;
    two different non-empty values for the same property are rejected, so the
    result never depends on record order.
    """
    existing = rows.setdefault(row["id"], dict(row))
    if existing is row or existing == row:
        return existing
    for key, value in row.items():
        if value is None or key in _PROVENANCE_FIELDS:
            continue
        current = existing.get(key)
        if current is None:
            existing[key] = value
        elif current != value:
            raise ValueError(
                f"domain {row['id']} has conflicting {key} values "
                f"{current!r} and {value!r}",
            )
    return existing


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

    node["collected"] = True
    if data_type == DOMAINS:
        node["forest_root_id"] = _upper(obj.get("ForestRootIdentifier"))
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
    skipped_rights: Counter[str] | None = None,
) -> Iterator[tuple[str, dict[str, Any]]]:
    """Yield ``(edge kind, row)`` for every relationship declared by one object.

    A row's ``source_type`` or ``target_type`` holds the BloodHound object type
    of an endpoint other than the object itself, when the output records it.
    ACE rights that map to no relationship are counted in ``skipped_rights``.
    """
    oid = object_id(obj)

    if data_type == GROUPS:
        for member_id, member_type in _typed_principals(obj.get("Members"), "Members"):
            yield MEMBER_OF, _edge(member_id, oid, provenance, source_type=member_type)

    if data_type in (USERS, COMPUTERS):
        primary_group = _upper(obj.get("PrimaryGroupSID"))
        if primary_group:
            yield MEMBER_OF, _edge(oid, primary_group, provenance, target_type="Group")

    # Current SharpHound records containment on the child (ContainedBy) and
    # leaves ChildObjects empty; older output fills ChildObjects instead.
    parent = obj.get("ContainedBy")
    if parent is not None:
        if not isinstance(parent, dict):
            raise ValueError("ContainedBy must be an object")
        yield CONTAINS, _edge(
            object_id(parent),
            oid,
            provenance,
            source_type=parent.get("ObjectType"),
        )
    if data_type in (DOMAINS, OUS, CONTAINERS):
        for child_id, child_type in _typed_principals(
            obj.get("ChildObjects"),
            "ChildObjects",
        ):
            yield CONTAINS, _edge(oid, child_id, provenance, target_type=child_type)

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
        yield from _gpo_local_group_edges(obj, provenance)

    if data_type == DOMAINS:
        for trust in obj.get("Trusts") or []:
            yield from _trust_edges(oid, trust, provenance)

    yield from _ace_edges(data_type, oid, obj, provenance, skipped_rights)

    if data_type in (USERS, COMPUTERS):
        for target_id, target_type in _typed_principals(
            obj.get("AllowedToDelegate"),
            "AllowedToDelegate",
        ):
            yield ALLOWED_TO_DELEGATE, _edge(
                oid,
                target_id,
                provenance,
                target_type=target_type,
            )
        for target_id, target_type in _typed_principals(
            obj.get("HasSIDHistory"),
            "HasSIDHistory",
        ):
            yield HAS_SID_HISTORY, _edge(
                oid,
                target_id,
                provenance,
                target_type=target_type,
            )

    if data_type == COMPUTERS:
        for actor_id, actor_type in _typed_principals(
            obj.get("AllowedToAct"),
            "AllowedToAct",
        ):
            yield ALLOWED_TO_ACT, _edge(
                actor_id, oid, provenance, source_type=actor_type
            )
        yield from _local_group_edges(oid, obj, provenance)
        yield from _session_edges(oid, obj, provenance)


def _typed_principals(value: Any, field_name: str) -> list[tuple[str, str | None]]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list")
    return [(object_id(item), item.get("ObjectType")) for item in value]


def _is_owner_rights(principal_id: str) -> bool:
    return principal_id == _OWNER_RIGHTS_SID or principal_id.endswith(
        f"-{_OWNER_RIGHTS_SID}",
    )


def _ace_edges(
    data_type: str,
    oid: str,
    obj: dict[str, Any],
    provenance: Provenance,
    skipped_rights: Counter[str] | None,
) -> Iterator[tuple[str, dict[str, Any]]]:
    aces = obj.get("Aces")
    if aces is None:
        return
    if not isinstance(aces, list):
        raise ValueError("Aces must be a list")
    # (kind, principal) -> whether every ACE granting it is inherited, so a
    # right granted both directly and by inheritance reads as direct.
    granted: dict[tuple[str, str], bool] = {}
    principal_types: dict[str, str | None] = {}
    replication: dict[str, set[str]] = defaultdict(set)
    for ace in aces:
        principal_id = _upper(ace["PrincipalSID"])
        right = ace["RightName"]
        # SharpHound lists an object's rights over itself and rights held by
        # OWNER RIGHTS; neither grants another principal anything.
        if (
            principal_id is None
            or principal_id == oid
            or _is_owner_rights(principal_id)
        ):
            continue
        principal_types.setdefault(principal_id, ace.get("PrincipalType"))
        kind = ACL_RIGHTS.get(right)
        if kind is not None:
            inherited = bool(ace.get("IsInherited"))
            key = (kind, principal_id)
            granted[key] = granted.get(key, True) and inherited
        elif data_type == DOMAINS and right in _DCSYNC_RIGHTS:
            replication[principal_id].add(right)
        elif skipped_rights is not None:
            skipped_rights[str(right)] += 1
    for (kind, principal_id), inherited in granted.items():
        yield kind, _edge(
            principal_id,
            oid,
            provenance,
            is_inherited=inherited,
            source_type=principal_types[principal_id],
        )
    for principal_id, rights in replication.items():
        if rights == _DCSYNC_RIGHTS:
            yield DC_SYNC, _edge(
                principal_id,
                oid,
                provenance,
                source_type=principal_types[principal_id],
            )


def _local_group_members(obj: dict[str, Any]) -> dict[str, dict[str, str | None]]:
    """Edge kind -> {principal ID: type} for the collected local groups of a computer."""
    members: dict[str, dict[str, str | None]] = {}
    for group in obj.get("LocalGroups") or []:
        if not group.get("Collected"):
            continue
        rid = object_id(group).rsplit("-", 1)[-1]
        kind = _LOCAL_GROUP_EDGES.get(rid)
        if kind is None:
            continue
        principals = members.setdefault(kind, {})
        for member_id, member_type in _typed_principals(
            group.get("Results"), "Results"
        ):
            if member_type not in _LOCAL_PRINCIPAL_TYPES:
                principals[member_id] = member_type
    return members


def _rdp_logon_grantees(obj: dict[str, Any]) -> set[str] | None:
    """Principals granted remote interactive logon, or None when not collected."""
    for user_right in obj.get("UserRights") or []:
        if user_right.get("Privilege") == _RDP_LOGON_RIGHT and user_right.get(
            "Collected",
        ):
            return {
                principal_id
                for principal_id, _ in _typed_principals(
                    user_right.get("Results"),
                    "Results",
                )
            }
    return None


def rdp_logon_restriction(oid: str, obj: dict[str, Any]) -> set[str] | None:
    """Principals allowed to RDP to a computer by its collected user rights.

    None when user rights were not collected, or when Remote Desktop Users
    holds the remote interactive logon right, so membership alone suffices.
    """
    grantees = _rdp_logon_grantees(obj)
    if grantees is None or f"{oid}-555" in grantees:
        return None
    return grantees


def _local_group_edges(
    oid: str,
    obj: dict[str, Any],
    provenance: Provenance,
) -> Iterator[tuple[str, dict[str, Any]]]:
    members = _local_group_members(obj)
    # Membership of Remote Desktop Users only allows RDP when the group also
    # holds the remote interactive logon right. When user rights were collected
    # and the group lacks it, only members granted the right directly qualify.
    grantees = rdp_logon_restriction(oid, obj)
    if grantees is not None and CAN_RDP in members:
        members[CAN_RDP] = {
            principal_id: principal_type
            for principal_id, principal_type in members[CAN_RDP].items()
            if principal_id in grantees
        }
    for kind, principals in members.items():
        for principal_id, principal_type in principals.items():
            yield kind, _edge(principal_id, oid, provenance, source_type=principal_type)


def _gpo_local_group_edges(
    obj: dict[str, Any],
    provenance: Provenance,
) -> Iterator[tuple[str, dict[str, Any]]]:
    """Local group membership that GPOs linked to a domain or OU push to computers."""
    changes = obj.get("GPOChanges")
    if not changes:
        return
    if not isinstance(changes, dict):
        raise ValueError("GPOChanges must be an object")
    computers = _typed_principal_ids(
        changes.get("AffectedComputers"),
        "AffectedComputers",
    )
    for field_name, kind in _GPO_LOCAL_GROUP_EDGES.items():
        for member_id, member_type in _typed_principals(
            changes.get(field_name),
            field_name,
        ):
            if member_type in _LOCAL_PRINCIPAL_TYPES:
                continue
            for computer_id in computers:
                yield kind, _edge(
                    member_id,
                    computer_id,
                    provenance,
                    source_type=member_type,
                    target_type="Computer",
                )


def _session_edges(
    oid: str,
    obj: dict[str, Any],
    provenance: Provenance,
) -> Iterator[tuple[str, dict[str, Any]]]:
    seen: set[tuple[str, str]] = set()
    for list_name in _SESSION_LISTS:
        sessions = obj.get(list_name) or {}
        if not sessions.get("Collected"):
            continue
        for session in sessions.get("Results") or []:
            computer_id = _upper(session.get("ComputerSID")) or oid
            user_id = _upper(session["UserSID"])
            if user_id is None or (computer_id, user_id) in seen:
                continue
            seen.add((computer_id, user_id))
            yield HAS_SESSION, _edge(
                computer_id,
                user_id,
                provenance,
                source_type=None if computer_id == oid else "Computer",
                target_type="User",
            )


def uncollected_host_edges(obj: dict[str, Any]) -> list[str]:
    """Host edge kinds a computer's output holds no data for.

    SharpHound cannot reach every computer. Its existing edges of these kinds
    are kept rather than cleaned up.
    """
    collected_rids = {
        object_id(group).rsplit("-", 1)[-1]
        for group in obj.get("LocalGroups") or []
        if group.get("Collected")
    }
    kinds = [
        kind for rid, kind in _LOCAL_GROUP_EDGES.items() if rid not in collected_rids
    ]
    if not any((obj.get(name) or {}).get("Collected") for name in _SESSION_LISTS):
        kinds.append(HAS_SESSION)
    return kinds


def placeholder_domain(principal_id: str) -> dict[str, str | None]:
    """Domain properties derivable from a principal identifier alone."""
    if principal_id.startswith("S-1-5-21-") and principal_id.count("-") == 7:
        return {"domainsid": principal_id.rsplit("-", 1)[0], "domain": None}
    prefix, sep, _ = principal_id.partition("-S-1-")
    if sep:
        return {"domainsid": None, "domain": prefix}
    return {"domainsid": None, "domain": None}


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
    # SharpHound writes the type as a name, and versions add names (Shortcut,
    # Realm), so any name is kept. Older output writes an enum value.
    raw_type = trust.get("TrustType")
    trust_type = (
        raw_type
        if isinstance(raw_type, str) and raw_type
        else _enum_name(raw_type, _TRUST_TYPES, "trust type")
    )
    kind = (
        SAME_FOREST_TRUST
        if trust_type in _SAME_FOREST_TRUST_TYPES
        else CROSS_FOREST_TRUST
    )
    props = {
        "trust_type": trust_type,
        "is_transitive": trust.get("IsTransitive"),
        "sid_filtering_enabled": trust.get("SidFilteringEnabled"),
        "tgt_delegation_enabled": trust.get("TGTDelegationEnabled"),
        "trust_attributes": _optional_int(trust.get("TrustAttributes")),
    }
    # An inbound trust means the target domain trusts this one; an outbound
    # trust means this domain trusts the target. As in BloodHound CE, trust
    # edges run from the trusting domain to the trusted one.
    if direction in ("Inbound", "Bidirectional"):
        yield kind, _edge(target_id, domain_id, provenance, **props)
    if direction in ("Outbound", "Bidirectional"):
        yield kind, _edge(domain_id, target_id, provenance, **props)


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
    skipped_rights: Counter[str] = Counter()

    for file in files:
        try:
            result = _validate_file(file, collected_at, skipped_rights)
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
        collection.domains.update(result.domains)
        collection.domain_rows.update(result.domain_rows)
        for principal_id, label in result.referenced_principals.items():
            collection.referenced_principals.setdefault(principal_id, label)
        for key, computer_ids in result.uncollected_hosts.items():
            collection.uncollected_hosts[key].update(computer_ids)
        collection.rdp_logon_grantees.update(result.rdp_logon_grantees)
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
    if skipped_rights:
        logger.info(
            "Skipped BloodHound ACEs with rights this module does not import: %s",
            ", ".join(f"{right} ({n})" for right, n in skipped_rights.most_common()),
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
    domain_rows: dict[str, dict[str, Any]] = field(default_factory=dict)
    referenced_principals: dict[str, str] = field(default_factory=dict)
    uncollected_hosts: dict[tuple[str, str], set[str]] = field(
        default_factory=lambda: defaultdict(set),
    )
    rdp_logon_grantees: dict[str, set[str]] = field(default_factory=dict)


def _record_references(
    result: _FileResult,
    oid: str,
    row: dict[str, Any],
) -> None:
    for side in ("source", "target"):
        label = PLACEHOLDER_LABELS.get(row.get(f"{side}_type") or "")
        principal_id = row[f"{side}_id"]
        if label is not None and principal_id != oid:
            result.referenced_principals.setdefault(principal_id, label)


def _validate_file(
    file: CollectionFile,
    collected_at_override: str | None,
    skipped_rights: Counter[str] | None = None,
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
            domain_sid = object_domain_sid(data_type, obj)
            result.domain_sids.add(domain_sid)
            if is_deleted(obj):
                continue
            node = transform_node(data_type, obj, provenance)
            if data_type == DOMAINS:
                merged = merge_domain_row(result.domain_rows, node)
                result.domains[node["id"]] = merged["name"]
                result.trust_targets.update(trust_targets(obj))
            oid = node["id"]
            for _, row in iter_edges(data_type, obj, provenance, skipped_rights):
                _record_references(result, oid, row)
            if data_type == COMPUTERS:
                for kind in uncollected_host_edges(obj):
                    result.uncollected_hosts[(kind, domain_sid)].add(oid)
                grantees = rdp_logon_restriction(oid, obj)
                if grantees is not None:
                    result.rdp_logon_grantees[oid] = grantees
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
