# See: https://d3fend.mitre.org/dao/artifact/d3f:ClientComputer/
from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class ClientComputerNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("hostname")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    hostname: PropertyRef = PropertyRef("hostname", extra_index=True)
    os: PropertyRef = PropertyRef("os")
    os_version: PropertyRef = PropertyRef("os_version")
    model: PropertyRef = PropertyRef("model")
    platform: PropertyRef = PropertyRef("platform")
    serial_number: PropertyRef = PropertyRef("serial_number", extra_index=True)


@dataclass(frozen=True)
class ClientComputerToNodeRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:ClientComputer)-[:HAS_OBSERVATION]->(:DuoEndpoint)
class ClientComputerToDuoEndpointRel(CartographyRelSchema):
    target_node_label: str = "DuoEndpoint"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"device_name": PropertyRef("hostname")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_OBSERVATION"
    properties: ClientComputerToNodeRelProperties = ClientComputerToNodeRelProperties()


# (:ClientComputer)-[:HAS_OBSERVATION]->(:DuoPhone)
class ClientComputerToDuoPhoneRel(CartographyRelSchema):
    target_node_label: str = "DuoPhone"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"name": PropertyRef("hostname")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_OBSERVATION"
    properties: ClientComputerToNodeRelProperties = ClientComputerToNodeRelProperties()


# (:ClientComputer)-[:HAS_OBSERVATION]->(:KandjiDevice)
class ClientComputerToKandjiDeviceRel(CartographyRelSchema):
    target_node_label: str = "KandjiDevice"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"device_name": PropertyRef("hostname")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_OBSERVATION"
    properties: ClientComputerToNodeRelProperties = ClientComputerToNodeRelProperties()


# (:ClientComputer)-[:HAS_OBSERVATION]->(:SnipeitAsset)
class ClientComputerToSnipeitAssetRel(CartographyRelSchema):
    target_node_label: str = "SnipeitAsset"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"name": PropertyRef("hostname")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_OBSERVATION"
    properties: ClientComputerToNodeRelProperties = ClientComputerToNodeRelProperties()


# (:ClientComputer)-[:HAS_OBSERVATION]->(:TailscaleDevice)
class ClientComputerToTailscaleDeviceRel(CartographyRelSchema):
    target_node_label: str = "TailscaleDevice"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"hostname": PropertyRef("hostname")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_OBSERVATION"
    properties: ClientComputerToNodeRelProperties = ClientComputerToNodeRelProperties()


# (:ClientComputer)-[:HAS_OBSERVATION]->(:CrowdstrikeHost)
class ClientComputerToCrowdstrikeHostRel(CartographyRelSchema):
    target_node_label: str = "CrowdstrikeHost"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"hostname": PropertyRef("hostname")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_OBSERVATION"
    properties: ClientComputerToNodeRelProperties = ClientComputerToNodeRelProperties()


# (:ClientComputer)-[:RESOURCE]->(:BigfixComputer)
class ClientComputerToBigfixComputerRel(CartographyRelSchema):
    target_node_label: str = "BigfixComputer"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"computername": PropertyRef("hostname")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RESOURCE"
    properties: ClientComputerToNodeRelProperties = ClientComputerToNodeRelProperties()


@dataclass(frozen=True)
class ClientComputerSchema(CartographyNodeSchema):
    label: str = "ClientComputer"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Ontology"])
    properties: ClientComputerNodeProperties = ClientComputerNodeProperties()
    scoped_cleanup: bool = False
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[
            ClientComputerToDuoEndpointRel(),
            ClientComputerToDuoPhoneRel(),
            ClientComputerToKandjiDeviceRel(),
            ClientComputerToSnipeitAssetRel(),
            ClientComputerToTailscaleDeviceRel(),
            ClientComputerToCrowdstrikeHostRel(),
            ClientComputerToBigfixComputerRel(),
        ],
    )
