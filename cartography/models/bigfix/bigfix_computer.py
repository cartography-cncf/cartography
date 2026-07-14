from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class BigfixComputerNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("ID", description="Internal BigFix ID.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last update.",
    )
    activedirectorypath: PropertyRef = PropertyRef(
        "ActiveDirectoryPath",
        description="Active Directory path.",
    )
    agenttype: PropertyRef = PropertyRef(
        "AgentType",
        description="BigFix agent type.",
    )
    agentversion: PropertyRef = PropertyRef(
        "AgentVersion",
        description="BigFix agent version.",
    )
    averageevaluationcycle: PropertyRef = PropertyRef(
        "AverageEvaluationCycle",
        description="Average evaluation cycle.",
    )
    besrelayselectionmethod: PropertyRef = PropertyRef(
        "BESRelaySelectionMethod",
        description="BES relay selection method.",
    )
    besrootserver: PropertyRef = PropertyRef(
        "BESRootServer",
        description="BES root server.",
    )
    bios: PropertyRef = PropertyRef("BIOS", description="BIOS information.")
    computertype: PropertyRef = PropertyRef(
        "ComputerType",
        description="Computer type, such as virtual or physical.",
    )
    computername: PropertyRef = PropertyRef(
        "ComputerName",
        extra_index=True,
        description="Computer name.",
    )
    cpu: PropertyRef = PropertyRef("CPU", description="CPU information.")
    devicetype: PropertyRef = PropertyRef(
        "DeviceType",
        description="Device type, such as server.",
    )
    distancetobesrelay: PropertyRef = PropertyRef(
        "DistanceToBESRelay",
        description="Distance to the BES relay.",
    )
    dnsname: PropertyRef = PropertyRef("DNSName", description="DNS name.")
    enrollmentdatetime: PropertyRef = PropertyRef(
        "EnrollmentDateTime",
        description="Timestamp when the computer enrolled in BigFix.",
    )
    freespaceonsystemdrive: PropertyRef = PropertyRef(
        "FreeSpaceOnSystemDrive",
        description="Free space on the system drive.",
    )
    ipaddress: PropertyRef = PropertyRef("IPAddress", description="IPv4 address.")
    ipv6address: PropertyRef = PropertyRef(
        "IPv6Address",
        description="IPv6 address.",
    )
    islocked: PropertyRef = PropertyRef(
        "IsLocked",
        description="Whether the computer is locked.",
    )
    lastreporttime: PropertyRef = PropertyRef(
        "LastReportDateTime",
        description="Timestamp of the computer's last report.",
    )
    locationbyiprange: PropertyRef = PropertyRef(
        "LocationByIPRange",
        description="Location derived from the IP range.",
    )
    loggedonuser: PropertyRef = PropertyRef(
        "LoggedonUser",
        description="Currently logged-on username.",
    )
    macaddress: PropertyRef = PropertyRef(
        "MACAddress",
        description="MAC address.",
    )
    os: PropertyRef = PropertyRef(
        "OS",
        description="Operating system information.",
    )
    providername: PropertyRef = PropertyRef(
        "ProviderName",
        description="Infrastructure provider name.",
    )
    ram: PropertyRef = PropertyRef("RAM", description="Installed memory.")
    relay: PropertyRef = PropertyRef("Relay", description="Assigned BigFix relay.")
    remotedesktopisenabled: PropertyRef = PropertyRef(
        "RemoteDesktopIsEnabled",
        description="Whether remote desktop is enabled.",
    )
    subnetaddress: PropertyRef = PropertyRef(
        "SubnetAddress",
        description="Subnet address.",
    )
    totalsizeofsystemdrive: PropertyRef = PropertyRef(
        "TotalSizeOfSystemDrive",
        description="Total size of the system drive.",
    )
    username: PropertyRef = PropertyRef(
        "UserName",
        description="Reported username.",
    )


@dataclass(frozen=True)
class BigfixComputerToBigfixRootRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class BigfixComputerToBigfixRootRel(CartographyRelSchema):
    """The BigFix root contains the computer."""

    target_node_label: str = "BigfixRoot"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ROOT_URL", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: BigfixComputerToBigfixRootRelProperties = (
        BigfixComputerToBigfixRootRelProperties()
    )


@dataclass(frozen=True)
class BigfixComputerSchema(CartographyNodeSchema):
    """A computer tracked by BigFix."""

    label: str = "BigfixComputer"
    properties: BigfixComputerNodeProperties = BigfixComputerNodeProperties()
    sub_resource_relationship: BigfixComputerToBigfixRootRel = (
        BigfixComputerToBigfixRootRel()
    )
