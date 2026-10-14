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
# Principals from the trusted domain, which the import does not contain.
PARTNER_ADMINS_SID = f"{PARTNER_SID}-519"
PARTNER_USER_SID = f"{PARTNER_SID}-1500"
# Local account on WS01, which has no AD object.
WS01_LOCAL_ADMIN_SID = "S-1-5-21-3000000001-3000000002-3000000003-500"

COLLECTION_TIMESTAMP = "20261012143015"
COLLECTED_AT = "2026-10-12T14:30:15"
COLLECTOR_VERSION = "2.5.0.0"
# Group | LocalAdmin | GPOLocalGroup | Session | Trusts | ACL | Container | RDP |
# ObjectProps | DCOM | PSRemote | UserRights
ALL_METHODS = 1 | 2 | 4 | 8 | 32 | 64 | 128 | 256 | 512 | 4096 | 16384 | 32768


def _principal(oid: str, object_type: str) -> dict[str, str]:
    return {"ObjectIdentifier": oid, "ObjectType": object_type}


def _ace(
    principal_sid: str,
    principal_type: str,
    right: str,
    inherited: bool = False,
) -> dict[str, Any]:
    return {
        "PrincipalSID": principal_sid,
        "PrincipalType": principal_type,
        "RightName": right,
        "IsInherited": inherited,
    }


def _props(name: str, dn: str, **extra: Any) -> dict[str, Any]:
    return {
        "name": name,
        "domain": DOMAIN_NAME,
        "domainsid": DOMAIN_SID,
        "distinguishedname": dn,
        "whencreated": 1700000000,
        **extra,
    }


def _sessions(*user_sids: str) -> dict[str, Any]:
    return {
        "Collected": True,
        "FailureReason": None,
        "Results": [{"UserSID": sid, "ComputerSID": WS01_SID} for sid in user_sids],
    }


def _local_group(
    name: str,
    rid: str,
    members: list[dict[str, str]],
) -> dict[str, Any]:
    return {
        "ObjectIdentifier": f"{WS01_SID}-{rid}",
        "Name": f"{name}@WS01.{DOMAIN_NAME}",
        "Results": members,
        "LocalNames": [],
        "Collected": True,
        "FailureReason": None,
    }


DOMAINS = [
    {
        "ObjectIdentifier": DOMAIN_SID,
        "Properties": {
            **_props(DOMAIN_NAME, "DC=EXAMPLE,DC=TEST"),
            "functionallevel": "2016",
        },
        "Aces": [
            # Both replication rights: DCSync.
            _ace(PARTNER_ADMINS_SID, "Group", "GetChanges"),
            _ace(PARTNER_ADMINS_SID, "Group", "GetChangesAll"),
            # Only one of them: no DCSync.
            _ace(SVC_SID, "User", "GetChanges"),
            _ace(PARTNER_ADMINS_SID, "Group", "GenericAll", inherited=True),
            # Not a principal, and not imported.
            _ace("S-1-3-4", "User", "GenericAll"),
            # A right this module does not import.
            _ace(HELPDESK_SID, "Group", "WriteGPLink"),
        ],
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
        "Aces": [
            # Granted both directly and by inheritance: reads as direct.
            _ace(HELPDESK_SID, "Group", "ForceChangePassword", inherited=True),
            _ace(HELPDESK_SID, "Group", "ForceChangePassword"),
            _ace(HELPDESK_SID, "Group", "GenericWrite", inherited=True),
            # An object's rights over itself grant nothing.
            _ace(ALICE_SID, "User", "WriteSPN"),
        ],
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
        "Aces": [_ace(ALICE_SID, "User", "AddKeyCredentialLink")],
        "IsDeleted": False,
        "IsACLProtected": False,
        "ContainedBy": _principal(USERS_CONTAINER, "Container"),
        "PrimaryGroupSID": DOMAIN_USERS_SID,
        "AllowedToDelegate": [_principal(WS01_SID, "Computer")],
        "HasSIDHistory": [_principal(PARTNER_USER_SID, "User")],
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
        "Aces": [
            _ace(ALICE_SID, "User", "AddSelf"),
            _ace(SVC_SID, "User", "AddMember"),
        ],
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
        "Aces": [_ace(HELPDESK_SID, "Group", "ReadLAPSPassword")],
        "IsDeleted": False,
        "IsACLProtected": False,
        "ContainedBy": _principal(WORKSTATIONS_OU, "OU"),
        "PrimaryGroupSID": DOMAIN_COMPUTERS_SID,
        "AllowedToDelegate": [],
        "AllowedToAct": [_principal(SVC_SID, "User")],
        "HasSIDHistory": [],
        "DumpSMSAPassword": [],
        "Sessions": _sessions(ALICE_SID),
        "PrivilegedSessions": _sessions(SVC_SID),
        # The same session seen twice yields one edge.
        "RegistrySessions": _sessions(ALICE_SID),
        "LocalGroups": [
            _local_group(
                "ADMINISTRATORS",
                "544",
                [
                    _principal(HELPDESK_SID, "Group"),
                    _principal(WS01_LOCAL_ADMIN_SID, "LocalUser"),
                ],
            ),
            _local_group(
                "REMOTE DESKTOP USERS",
                "555",
                [
                    _principal(DOMAIN_USERS_SID, "Group"),
                    _principal(ALICE_SID, "User"),
                ],
            ),
            _local_group(
                "REMOTE MANAGEMENT USERS",
                "580",
                [_principal(SVC_SID, "User")],
            ),
        ],
        # Remote Desktop Users lacks the logon right here, so only Alice, who
        # holds it directly, can RDP.
        "UserRights": [
            {
                "Privilege": "SeRemoteInteractiveLogonRight",
                "Results": [
                    _principal(f"{WS01_SID}-544", "LocalGroup"),
                    _principal(ALICE_SID, "User"),
                ],
                "LocalNames": [],
                "Collected": True,
                "FailureReason": None,
            },
        ],
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
        # A GPO linked here adds svc_app to the local Administrators group.
        "GPOChanges": {
            "LocalAdmins": [_principal(SVC_SID, "User")],
            "RemoteDesktopUsers": [],
            "DcomUsers": [],
            "PSRemoteUsers": [],
            "AffectedComputers": [_principal(WS01_SID, "Computer")],
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
