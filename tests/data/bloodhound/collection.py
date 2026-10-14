"""A synthetic BloodHound CE (v6) collection for one small domain.

Every name, SID and GUID here is made up.
"""

import copy
import json
import zipfile
from pathlib import Path
from typing import Any

DOMAIN_SID = "S-1-5-21-1000000001-1000000002-1000000003"
DOMAIN_NAME = "EXAMPLE.TEST"
PARTNER_SID = "S-1-5-21-2000000001-2000000002-2000000003"
PARTNER_NAME = "PARTNER.TEST"

ALICE_SID = f"{DOMAIN_SID}-1105"
SVC_SID = f"{DOMAIN_SID}-1106"
WS01_SID = f"{DOMAIN_SID}-1201"
DOMAIN_USERS_SID = f"{DOMAIN_SID}-513"
DOMAIN_COMPUTERS_SID = f"{DOMAIN_SID}-515"
HELPDESK_SID = f"{DOMAIN_SID}-1110"
WORKSTATIONS_OU = "0B6F3B0C-0000-4000-8000-000000000001"
USERS_CONTAINER = "0B6F3B0C-0000-4000-8000-000000000002"
DEFAULT_GPO = "31B2F340-016D-11D2-945F-00C04FB984F9"

COLLECTION_TIMESTAMP = "20261012143015"
COLLECTED_AT = "2026-10-12T14:30:15"
COLLECTOR_VERSION = "2.5.0.0"
# Group | LocalAdmin | Session | Trusts | ACL | Container | RDP | ObjectProps | DCOM | PSRemote
ALL_METHODS = 1 | 2 | 8 | 32 | 64 | 128 | 256 | 512 | 4096 | 16384


def _principal(oid: str, object_type: str) -> dict[str, str]:
    return {"ObjectIdentifier": oid, "ObjectType": object_type}


def _props(name: str, dn: str, **extra: Any) -> dict[str, Any]:
    return {
        "name": name,
        "domain": DOMAIN_NAME,
        "domainsid": DOMAIN_SID,
        "distinguishedname": dn,
        "whencreated": 1700000000,
        **extra,
    }


DOMAINS = [
    {
        "ObjectIdentifier": DOMAIN_SID,
        "Properties": {
            **_props(DOMAIN_NAME, "DC=EXAMPLE,DC=TEST"),
            "functionallevel": "2016",
        },
        "Aces": [],
        "IsDeleted": False,
        "IsACLProtected": False,
        "ContainedBy": None,
        "ForestRootIdentifier": DOMAIN_SID,
        "ChildObjects": [
            _principal(WORKSTATIONS_OU, "OU"),
            _principal(USERS_CONTAINER, "Container"),
        ],
        "Links": [{"IsEnforced": False, "GUID": DEFAULT_GPO}],
        "Trusts": [
            {
                "TargetDomainSid": PARTNER_SID,
                "TargetDomainName": PARTNER_NAME,
                "IsTransitive": False,
                "SidFilteringEnabled": True,
                "TGTDelegationEnabled": False,
                "TrustAttributes": 4,
                "TrustDirection": "Outbound",
                "TrustType": "External",
            },
        ],
        "GPOChanges": {
            "LocalAdmins": [],
            "RemoteDesktopUsers": [],
            "DcomUsers": [],
            "PSRemoteUsers": [],
            "AffectedComputers": [],
        },
    },
]

USERS = [
    {
        "ObjectIdentifier": ALICE_SID,
        "Properties": _props(
            f"ALICE@{DOMAIN_NAME}",
            "CN=Alice,CN=Users,DC=EXAMPLE,DC=TEST",
            samaccountname="alice",
            displayname="Alice Example",
            email="alice@example.test",
            enabled=True,
            hasspn=False,
            pwdlastset=1700000100,
            lastlogontimestamp=1760000000,
            # Collected by SharpHound but never imported.
            userpassword="not-a-real-password",
        ),
        "Aces": [],
        "IsDeleted": False,
        "IsACLProtected": False,
        "ContainedBy": _principal(USERS_CONTAINER, "Container"),
        "PrimaryGroupSID": DOMAIN_USERS_SID,
        "AllowedToDelegate": [],
        "HasSIDHistory": [],
        "SPNTargets": [],
        "UnconstrainedDelegation": False,
        "DomainSID": DOMAIN_SID,
    },
    {
        "ObjectIdentifier": SVC_SID,
        "Properties": _props(
            f"SVC_APP@{DOMAIN_NAME}",
            "CN=svc_app,CN=Users,DC=EXAMPLE,DC=TEST",
            samaccountname="svc_app",
            enabled=True,
            hasspn=True,
            serviceprincipalnames=["HTTP/app.example.test"],
        ),
        "Aces": [],
        "IsDeleted": False,
        "IsACLProtected": False,
        "ContainedBy": _principal(USERS_CONTAINER, "Container"),
        "PrimaryGroupSID": DOMAIN_USERS_SID,
        "AllowedToDelegate": [],
        "HasSIDHistory": [],
        "SPNTargets": [],
        "UnconstrainedDelegation": False,
        "DomainSID": DOMAIN_SID,
    },
]

GROUPS = [
    {
        "ObjectIdentifier": DOMAIN_USERS_SID,
        "Properties": _props(
            f"DOMAIN USERS@{DOMAIN_NAME}",
            "CN=Domain Users,CN=Users,DC=EXAMPLE,DC=TEST",
            samaccountname="Domain Users",
        ),
        "Aces": [],
        "IsDeleted": False,
        "IsACLProtected": False,
        "ContainedBy": _principal(USERS_CONTAINER, "Container"),
        "Members": [],
        "HasSIDHistory": [],
    },
    {
        "ObjectIdentifier": DOMAIN_COMPUTERS_SID,
        "Properties": _props(
            f"DOMAIN COMPUTERS@{DOMAIN_NAME}",
            "CN=Domain Computers,CN=Users,DC=EXAMPLE,DC=TEST",
            samaccountname="Domain Computers",
        ),
        "Aces": [],
        "IsDeleted": False,
        "IsACLProtected": False,
        "ContainedBy": _principal(USERS_CONTAINER, "Container"),
        "Members": [],
        "HasSIDHistory": [],
    },
    {
        "ObjectIdentifier": HELPDESK_SID,
        "Properties": _props(
            f"HELPDESK@{DOMAIN_NAME}",
            "CN=Helpdesk,CN=Users,DC=EXAMPLE,DC=TEST",
            samaccountname="Helpdesk",
            description="Help desk staff",
        ),
        "Aces": [],
        "IsDeleted": False,
        "IsACLProtected": False,
        "ContainedBy": _principal(USERS_CONTAINER, "Container"),
        "Members": [_principal(ALICE_SID, "User")],
        "HasSIDHistory": [],
    },
]

COMPUTERS = [
    {
        "ObjectIdentifier": WS01_SID,
        "Properties": _props(
            f"WS01.{DOMAIN_NAME}",
            "CN=WS01,OU=Workstations,DC=EXAMPLE,DC=TEST",
            samaccountname="WS01$",
            operatingsystem="Windows 11 Enterprise",
            enabled=True,
            haslaps=True,
        ),
        "Aces": [],
        "IsDeleted": False,
        "IsACLProtected": False,
        "ContainedBy": _principal(WORKSTATIONS_OU, "OU"),
        "PrimaryGroupSID": DOMAIN_COMPUTERS_SID,
        "AllowedToDelegate": [],
        "AllowedToAct": [],
        "HasSIDHistory": [],
        "DumpSMSAPassword": [],
        "Sessions": {"Collected": True, "FailureReason": None, "Results": []},
        "PrivilegedSessions": {"Collected": True, "FailureReason": None, "Results": []},
        "RegistrySessions": {"Collected": True, "FailureReason": None, "Results": []},
        "LocalGroups": [],
        "UserRights": [],
        "Status": None,
        "IsDC": False,
        "UnconstrainedDelegation": False,
        "DomainSID": DOMAIN_SID,
    },
]

OUS = [
    {
        "ObjectIdentifier": WORKSTATIONS_OU,
        "Properties": _props(
            f"WORKSTATIONS@{DOMAIN_NAME}",
            "OU=Workstations,DC=EXAMPLE,DC=TEST",
            blocksinheritance=False,
        ),
        "Aces": [],
        "IsDeleted": False,
        "IsACLProtected": False,
        "ContainedBy": _principal(DOMAIN_SID, "Domain"),
        "Links": [{"IsEnforced": True, "GUID": DEFAULT_GPO}],
        "ChildObjects": [_principal(WS01_SID, "Computer")],
        "GPOChanges": {
            "LocalAdmins": [],
            "RemoteDesktopUsers": [],
            "DcomUsers": [],
            "PSRemoteUsers": [],
            "AffectedComputers": [],
        },
    },
]

GPOS = [
    {
        "ObjectIdentifier": DEFAULT_GPO,
        "Properties": _props(
            f"DEFAULT DOMAIN POLICY@{DOMAIN_NAME}",
            f"CN={{{DEFAULT_GPO}}},CN=Policies,CN=System,DC=EXAMPLE,DC=TEST",
            gpcpath=f"\\\\EXAMPLE.TEST\\SYSVOL\\EXAMPLE.TEST\\POLICIES\\{{{DEFAULT_GPO}}}",
        ),
        "Aces": [],
        "IsDeleted": False,
        "IsACLProtected": False,
        "ContainedBy": None,
    },
]

CONTAINERS = [
    {
        "ObjectIdentifier": USERS_CONTAINER,
        "Properties": _props(f"USERS@{DOMAIN_NAME}", "CN=Users,DC=EXAMPLE,DC=TEST"),
        "Aces": [],
        "IsDeleted": False,
        "IsACLProtected": False,
        "ContainedBy": _principal(DOMAIN_SID, "Domain"),
        "ChildObjects": [
            _principal(ALICE_SID, "User"),
            _principal(SVC_SID, "User"),
            _principal(DOMAIN_USERS_SID, "Group"),
            _principal(DOMAIN_COMPUTERS_SID, "Group"),
            _principal(HELPDESK_SID, "Group"),
        ],
    },
]


def collection() -> dict[str, list[dict[str, Any]]]:
    """A deep copy of the collection, keyed by BloodHound data type."""
    return copy.deepcopy(
        {
            "domains": DOMAINS,
            "users": USERS,
            "groups": GROUPS,
            "computers": COMPUTERS,
            "ous": OUS,
            "gpos": GPOS,
            "containers": CONTAINERS,
        },
    )


def document(
    data_type: str,
    data: list[dict[str, Any]],
    *,
    methods: int = ALL_METHODS,
    version: int = 6,
    count: int | None = None,
) -> dict[str, Any]:
    """Wrap objects the way SharpHound does, with meta written after data."""
    return {
        "data": data,
        "meta": {
            "methods": methods,
            "type": data_type,
            "count": len(data) if count is None else count,
            "version": version,
            "collectorversion": COLLECTOR_VERSION,
        },
    }


def write_zip(
    path: Path,
    data: dict[str, list[dict[str, Any]]] | None = None,
    *,
    timestamp: str = COLLECTION_TIMESTAMP,
    methods: int = ALL_METHODS,
    raw_members: dict[str, bytes] | None = None,
) -> Path:
    """Write a SharpHound-style zip archive and return its path."""
    data = collection() if data is None else data
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        for data_type, objects in data.items():
            archive.writestr(
                f"{timestamp}_{data_type}.json",
                json.dumps(document(data_type, objects, methods=methods)),
            )
        for name, content in (raw_members or {}).items():
            archive.writestr(name, content)
    return path
