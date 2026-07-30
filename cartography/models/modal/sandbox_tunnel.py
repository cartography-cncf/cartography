from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class ModalSandboxTunnelNodeProperties(CartographyNodeProperties):
    # Modal gives tunnels no id of their own, so it is synthesised as
    # "<sandbox_id>/<container_port>", which is unique per sandbox.
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    sandbox_id: PropertyRef = PropertyRef("sandbox_id")
    # Public TLS hostname the tunnel is reachable at.
    host: PropertyRef = PropertyRef("host", extra_index=True)
    port: PropertyRef = PropertyRef("port")
    # Populated only for a tunnel opened on an *unencrypted* port. Traffic to it is
    # cleartext over the public internet, which is why it is indexed.
    unencrypted_host: PropertyRef = PropertyRef("unencrypted_host", extra_index=True)
    unencrypted_port: PropertyRef = PropertyRef("unencrypted_port")
    has_unencrypted_endpoint: PropertyRef = PropertyRef(
        "has_unencrypted_endpoint", extra_index=True
    )
    container_port: PropertyRef = PropertyRef("container_port")
    environment_name: PropertyRef = PropertyRef("environment_name", extra_index=True)


@dataclass(frozen=True)
class ModalSandboxTunnelToEnvironmentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ModalEnvironment)-[:RESOURCE]->(:ModalSandboxTunnel)
class ModalSandboxTunnelToEnvironmentRel(CartographyRelSchema):
    target_node_label: str = "ModalEnvironment"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ENVIRONMENT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ModalSandboxTunnelToEnvironmentRelProperties = (
        ModalSandboxTunnelToEnvironmentRelProperties()
    )


@dataclass(frozen=True)
class ModalSandboxToTunnelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ModalSandbox)-[:EXPOSES]->(:ModalSandboxTunnel)
class ModalSandboxToTunnelRel(CartographyRelSchema):
    target_node_label: str = "ModalSandbox"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("sandbox_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "EXPOSES"
    properties: ModalSandboxToTunnelRelProperties = ModalSandboxToTunnelRelProperties()


@dataclass(frozen=True)
# A forwarded port on a running sandbox, reachable from the public internet. This is the
# main inbound exposure surface of a Modal sandbox.
class ModalSandboxTunnelSchema(CartographyNodeSchema):
    label: str = "ModalSandboxTunnel"
    properties: ModalSandboxTunnelNodeProperties = ModalSandboxTunnelNodeProperties()
    sub_resource_relationship: ModalSandboxTunnelToEnvironmentRel = (
        ModalSandboxTunnelToEnvironmentRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [ModalSandboxToTunnelRel()],
    )
