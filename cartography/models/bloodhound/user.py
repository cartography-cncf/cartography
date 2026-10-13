from dataclasses import dataclass

from cartography.models.bloodhound.common import AD_OBJECT
from cartography.models.bloodhound.common import ADDomainToObjectRel
from cartography.models.bloodhound.common import ADObjectNodeProperties
from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.ontology.labels import USER_ACCOUNT


@dataclass(frozen=True)
class ADUserNodeProperties(ADObjectNodeProperties):
    samaccountname: PropertyRef = PropertyRef(
        "samaccountname",
        extra_index=True,
        description="Pre-Windows 2000 logon name.",
    )
    displayname: PropertyRef = PropertyRef(
        "displayname",
        description="Display name.",
    )
    email: PropertyRef = PropertyRef(
        "email",
        extra_index=True,
        description="Email address from the `mail` attribute.",
    )
    title: PropertyRef = PropertyRef("title", description="Job title.")
    enabled: PropertyRef = PropertyRef(
        "enabled",
        description="Whether the account is enabled.",
    )
    lastlogon: PropertyRef = PropertyRef(
        "lastlogon",
        description="Last logon on the queried DC, in epoch seconds. Not replicated.",
    )
    lastlogontimestamp: PropertyRef = PropertyRef(
        "lastlogontimestamp",
        description="Replicated last logon time, in epoch seconds. Lags by up to 14 days.",
    )
    pwdlastset: PropertyRef = PropertyRef(
        "pwdlastset",
        description="Time the password was last set, in epoch seconds.",
    )
    pwdneverexpires: PropertyRef = PropertyRef(
        "pwdneverexpires",
        description="Whether the password never expires.",
    )
    passwordnotreqd: PropertyRef = PropertyRef(
        "passwordnotreqd",
        description="Whether the account may have an empty password.",
    )
    dontreqpreauth: PropertyRef = PropertyRef(
        "dontreqpreauth",
        description="Whether Kerberos pre-authentication is disabled (AS-REP roastable).",
    )
    hasspn: PropertyRef = PropertyRef(
        "hasspn",
        description="Whether the account has a service principal name (Kerberoastable).",
    )
    serviceprincipalnames: PropertyRef = PropertyRef(
        "serviceprincipalnames",
        description="Service principal names registered on the account.",
    )
    admincount: PropertyRef = PropertyRef(
        "admincount",
        description="Whether AdminSDHolder protects the account, which usually means it is or was privileged.",
    )
    sensitive: PropertyRef = PropertyRef(
        "sensitive",
        description="Whether the account is marked sensitive and cannot be delegated.",
    )
    unconstraineddelegation: PropertyRef = PropertyRef(
        "unconstraineddelegation",
        description="Whether the account is trusted for unconstrained delegation.",
    )
    trustedtoauth: PropertyRef = PropertyRef(
        "trustedtoauth",
        description="Whether the account may use protocol transition for constrained delegation.",
    )
    sidhistory: PropertyRef = PropertyRef(
        "sidhistory",
        description="SIDs in the account's SID history.",
    )
    primarygroupsid: PropertyRef = PropertyRef(
        "primarygroupsid",
        description="SID of the account's primary group.",
    )


@dataclass(frozen=True)
class ADUserSchema(CartographyNodeSchema):
    """An Active Directory user account, keyed by SID."""

    label: str = "ADUser"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([USER_ACCOUNT, AD_OBJECT])
    properties: ADUserNodeProperties = ADUserNodeProperties()
    sub_resource_relationship: ADDomainToObjectRel = ADDomainToObjectRel()
