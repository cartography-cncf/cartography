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
class ModalProxyNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    created_at: PropertyRef = PropertyRef("created_at")
    region: PropertyRef = PropertyRef("region", extra_index=True)
    environment_name: PropertyRef = PropertyRef("environment_name", extra_index=True)


@dataclass(frozen=True)
class ModalProxyToEnvironmentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ModalEnvironment)-[:RESOURCE]->(:ModalProxy)
class ModalProxyToEnvironmentRel(CartographyRelSchema):
    target_node_label: str = "ModalEnvironment"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ENVIRONMENT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ModalProxyToEnvironmentRelProperties = (
        ModalProxyToEnvironmentRelProperties()
    )


@dataclass(frozen=True)
# A Modal proxy, which gives workloads a stable set of egress IPs so a third party can
# allowlist them.
#
# Which functions route through it is not graphable: `Function.proxy_id` is write-only in
# Modal's API, like every other deploy-time function setting.
class ModalProxySchema(CartographyNodeSchema):
    label: str = "ModalProxy"
    properties: ModalProxyNodeProperties = ModalProxyNodeProperties()
    sub_resource_relationship: ModalProxyToEnvironmentRel = ModalProxyToEnvironmentRel()


@dataclass(frozen=True)
class ModalProxyIPNodeProperties(CartographyNodeProperties):
    # Modal gives proxy IPs no id, so it is synthesised as "<proxy_id>/<ip>".
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    ip_address: PropertyRef = PropertyRef("ip_address", extra_index=True)
    # Raw PROXY_IP_STATUS_* value: CREATING, ONLINE, TERMINATED or UNHEALTHY.
    status: PropertyRef = PropertyRef("status", extra_index=True)
    created_at: PropertyRef = PropertyRef("created_at")
    proxy_id: PropertyRef = PropertyRef("proxy_id")
    environment_name: PropertyRef = PropertyRef("environment_name", extra_index=True)


@dataclass(frozen=True)
class ModalProxyIPToEnvironmentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ModalEnvironment)-[:RESOURCE]->(:ModalProxyIP)
class ModalProxyIPToEnvironmentRel(CartographyRelSchema):
    target_node_label: str = "ModalEnvironment"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ENVIRONMENT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ModalProxyIPToEnvironmentRelProperties = (
        ModalProxyIPToEnvironmentRelProperties()
    )


@dataclass(frozen=True)
class ModalProxyToIPRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ModalProxy)-[:HAS_IP]->(:ModalProxyIP)
class ModalProxyToIPRel(CartographyRelSchema):
    target_node_label: str = "ModalProxy"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("proxy_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_IP"
    properties: ModalProxyToIPRelProperties = ModalProxyToIPRelProperties()


@dataclass(frozen=True)
# One egress IP of a Modal proxy.
#
# Not promoted to the canonical ontology PublicIP in this version: that would mean editing the
# shared cartography/models/ontology/publicip.py to add a RESERVED_BY relationship, which does
# not belong in a new-provider change. Worth a follow-up, since egress-allowlist questions are
# exactly what a canonical PublicIP is for.
class ModalProxyIPSchema(CartographyNodeSchema):
    label: str = "ModalProxyIP"
    properties: ModalProxyIPNodeProperties = ModalProxyIPNodeProperties()
    sub_resource_relationship: ModalProxyIPToEnvironmentRel = (
        ModalProxyIPToEnvironmentRel()
    )
    other_relationships: OtherRelationships = OtherRelationships([ModalProxyToIPRel()])
