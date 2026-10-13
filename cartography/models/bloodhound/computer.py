from dataclasses import dataclass

from cartography.models.bloodhound.common import AD_OBJECT
from cartography.models.bloodhound.common import ADDomainToObjectRel
from cartography.models.bloodhound.common import ADObjectNodeProperties
from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels


@dataclass(frozen=True)
class ADComputerNodeProperties(ADObjectNodeProperties):
    hostname: PropertyRef = PropertyRef(
        "hostname",
        extra_index=True,
        description="Host name: the first label of the computer's DNS name.",
    )
    samaccountname: PropertyRef = PropertyRef(
        "samaccountname",
        extra_index=True,
        description="Machine account name, ending in `$`.",
    )
    operatingsystem: PropertyRef = PropertyRef(
        "operatingsystem",
        description="Operating system reported in AD.",
    )
    enabled: PropertyRef = PropertyRef(
        "enabled",
        description="Whether the machine account is enabled.",
    )
    isdc: PropertyRef = PropertyRef(
        "isdc",
        description="Whether the computer is a domain controller.",
    )
    haslaps: PropertyRef = PropertyRef(
        "haslaps",
        description="Whether LAPS manages the local administrator password.",
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
        description="Time the machine password was last set, in epoch seconds.",
    )
    serviceprincipalnames: PropertyRef = PropertyRef(
        "serviceprincipalnames",
        description="Service principal names registered on the machine account.",
    )
    unconstraineddelegation: PropertyRef = PropertyRef(
        "unconstraineddelegation",
        description="Whether the computer is trusted for unconstrained delegation.",
    )
    trustedtoauth: PropertyRef = PropertyRef(
        "trustedtoauth",
        description="Whether the computer may use protocol transition for constrained delegation.",
    )
    sidhistory: PropertyRef = PropertyRef(
        "sidhistory",
        description="SIDs in the machine account's SID history.",
    )
    primarygroupsid: PropertyRef = PropertyRef(
        "primarygroupsid",
        description="SID of the machine account's primary group.",
    )


@dataclass(frozen=True)
class ADComputerSchema(CartographyNodeSchema):
    """An Active Directory computer account, keyed by SID."""

    label: str = "ADComputer"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([AD_OBJECT])
    properties: ADComputerNodeProperties = ADComputerNodeProperties()
    sub_resource_relationship: ADDomainToObjectRel = ADDomainToObjectRel()
