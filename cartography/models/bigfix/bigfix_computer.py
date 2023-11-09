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
    id: PropertyRef = PropertyRef('ID')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)
    activedirectorypath: PropertyRef = PropertyRef('ActiveDirectoryPath')
    agenttype: PropertyRef = PropertyRef('AgentType')
    agentversion: PropertyRef = PropertyRef('AgentVersion')
    averageevaluationcycle: PropertyRef = PropertyRef('AverageEvaluationCycle')
    besrelayselectionmethod: PropertyRef = PropertyRef('BESRelaySelectionMethod')
    besrootserver: PropertyRef = PropertyRef('BESRootServer')
    bios: PropertyRef = PropertyRef('BIOS')
    computertype: PropertyRef = PropertyRef('ComputerType')
    computername: PropertyRef = PropertyRef('ComputerName')
    cpu: PropertyRef = PropertyRef('CPU')
    devicetype: PropertyRef = PropertyRef('DeviceType')
    distancetobesrelay: PropertyRef = PropertyRef('DistanceToBESRelay')
    dnsname: PropertyRef = PropertyRef('DNSName')
    enrollmentdatetime: PropertyRef = PropertyRef('EnrollmentDateTime')
    freespaceonsystemdrive: PropertyRef = PropertyRef('FreeSpaceOnSystemDrive')
    ipaddress: PropertyRef = PropertyRef('IPAddress')
    ipv6address: PropertyRef = PropertyRef('IPv6Address')
    islocked: PropertyRef = PropertyRef('IsLocked')
    lastreporttime: PropertyRef = PropertyRef('LastReportDateTime')
    locationbyiprange: PropertyRef = PropertyRef('LocationByIPRange')
    loggedonuser: PropertyRef = PropertyRef('LoggedonUser')
    macaddress: PropertyRef = PropertyRef('MACAddress')
    os: PropertyRef = PropertyRef('OS')
    providername: PropertyRef = PropertyRef('ProviderName')
    ram: PropertyRef = PropertyRef('RAM')
    relay: PropertyRef = PropertyRef('Relay')
    remotedesktopisenabled: PropertyRef = PropertyRef('RemoteDesktopIsEnabled')
    subnetaddress: PropertyRef = PropertyRef('SubnetAddress')
    totalsizeofsystemdrive: PropertyRef = PropertyRef('TotalSizeOfSystemDrive')
    username: PropertyRef = PropertyRef('UserName')


@dataclass(frozen=True)
class BigfixComputerToBigfixRootRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class BigfixComputerToBigfixRootRel(CartographyRelSchema):
    target_node_label: str = 'BigfixRoot'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('ROOT_URL', set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: BigfixComputerToBigfixRootRelProperties = BigfixComputerToBigfixRootRelProperties()


@dataclass(frozen=True)
class BigfixComputerSchema(CartographyNodeSchema):
    label: str = 'BigfixComputer'
    properties: BigfixComputerNodeProperties = BigfixComputerNodeProperties()
    sub_resource_relationship: BigfixComputerToBigfixRootRel = BigfixComputerToBigfixRootRel()
