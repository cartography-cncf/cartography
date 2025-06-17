# See: https://d3fend.mitre.org/dao/artifact/d3f:Host/
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
class HostNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("hostname")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    hostname: PropertyRef = PropertyRef("hostname", extra_index=True)
    # WIP: is_server: PropertyRef = PropertyRef("is_server")
    # WIP: is_virtual: PropertyRef = PropertyRef("is_virtual")
    os: PropertyRef = PropertyRef("os")
    os_version: PropertyRef = PropertyRef("os_version")
    model: PropertyRef = PropertyRef("model")
    platform: PropertyRef = PropertyRef("platform")
    serial_number: PropertyRef = PropertyRef("serial_number", extra_index=True)


@dataclass(frozen=True)
class HostToNodeRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:Host)-[:HAS_OBSERVATION]->(:DuoEndpoint)
class HostToDuoEndpointRel(CartographyRelSchema):
    target_node_label: str = "DuoEndpoint"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"device_name": PropertyRef("hostname")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_OBSERVATION"
    properties: HostToNodeRelProperties = HostToNodeRelProperties()


# (:Host)-[:HAS_OBSERVATION]->(:DuoPhone)
class HostToDuoPhoneRel(CartographyRelSchema):
    target_node_label: str = "DuoPhone"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"name": PropertyRef("hostname")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_OBSERVATION"
    properties: HostToNodeRelProperties = HostToNodeRelProperties()


# (:Host)-[:HAS_OBSERVATION]->(:KandjiDevice)
class HostToKandjiDeviceRel(CartographyRelSchema):
    target_node_label: str = "KandjiDevice"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"device_name": PropertyRef("hostname")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_OBSERVATION"
    properties: HostToNodeRelProperties = HostToNodeRelProperties()


# (:Host)-[:HAS_OBSERVATION]->(:SnipeitAsset)
class HostToSnipeitAssetRel(CartographyRelSchema):
    target_node_label: str = "SnipeitAsset"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"name": PropertyRef("hostname")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_OBSERVATION"
    properties: HostToNodeRelProperties = HostToNodeRelProperties()


# (:Host)-[:HAS_OBSERVATION]->(:TailscaleDevice)
class HostToTailscaleDeviceRel(CartographyRelSchema):
    target_node_label: str = "TailscaleDevice"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"hostname": PropertyRef("hostname")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_OBSERVATION"
    properties: HostToNodeRelProperties = HostToNodeRelProperties()


# (:Host)-[:HAS_OBSERVATION]->(:CrowdstrikeHost)
class HostToCrowdstrikeHostRel(CartographyRelSchema):
    target_node_label: str = "CrowdstrikeHost"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"hostname": PropertyRef("hostname")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_OBSERVATION"
    properties: HostToNodeRelProperties = HostToNodeRelProperties()


# (:Host)-[:RESOURCE]->(:BigfixComputer)
class HostToBigfixComputerRel(CartographyRelSchema):
    target_node_label: str = "BigfixComputer"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"computername": PropertyRef("hostname")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RESOURCE"
    properties: HostToNodeRelProperties = HostToNodeRelProperties()


@dataclass(frozen=True)
class HostSchema(CartographyNodeSchema):
    label: str = "Host"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Ontology"])
    properties: HostNodeProperties = HostNodeProperties()
    scoped_cleanup: bool = False
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[
            HostToDuoEndpointRel(),
            HostToDuoPhoneRel(),
            HostToKandjiDeviceRel(),
            HostToSnipeitAssetRel(),
            HostToTailscaleDeviceRel(),
            HostToCrowdstrikeHostRel(),
            HostToBigfixComputerRel(),
        ],
    )
