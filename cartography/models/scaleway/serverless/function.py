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
class ScalewayServerlessFunctionProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", extra_index=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    status: PropertyRef = PropertyRef("status")
    runtime: PropertyRef = PropertyRef("runtime")
    handler: PropertyRef = PropertyRef("handler")
    # Exposure signal: `public` lets anyone invoke the function without auth.
    privacy: PropertyRef = PropertyRef("privacy")
    domain_name: PropertyRef = PropertyRef("domain_name", extra_index=True)
    # `enabled` allows plain HTTP; `redirected` forces HTTPS.
    http_option: PropertyRef = PropertyRef("http_option")
    sandbox: PropertyRef = PropertyRef("sandbox")
    min_scale: PropertyRef = PropertyRef("min_scale")
    max_scale: PropertyRef = PropertyRef("max_scale")
    memory_limit: PropertyRef = PropertyRef("memory_limit")
    cpu_limit: PropertyRef = PropertyRef("cpu_limit")
    timeout: PropertyRef = PropertyRef("timeout")
    region: PropertyRef = PropertyRef("region")
    tags: PropertyRef = PropertyRef("tags")
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ScalewayServerlessFunctionToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayServerlessFunction)
class ScalewayServerlessFunctionToProjectRel(CartographyRelSchema):
    target_node_label: str = "ScalewayProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ScalewayServerlessFunctionToProjectRelProperties = (
        ScalewayServerlessFunctionToProjectRelProperties()
    )


@dataclass(frozen=True)
class ScalewayServerlessFunctionToNamespaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayServerlessFunctionNamespace)-[:HAS]->(:ScalewayServerlessFunction)
class ScalewayServerlessFunctionToNamespaceRel(CartographyRelSchema):
    target_node_label: str = "ScalewayServerlessFunctionNamespace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("namespace_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS"
    properties: ScalewayServerlessFunctionToNamespaceRelProperties = (
        ScalewayServerlessFunctionToNamespaceRelProperties()
    )


@dataclass(frozen=True)
class ScalewayServerlessFunctionToPrivateNetworkRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayServerlessFunction)-[:ATTACHED_TO]->(:ScalewayPrivateNetwork)
class ScalewayServerlessFunctionToPrivateNetworkRel(CartographyRelSchema):
    target_node_label: str = "ScalewayPrivateNetwork"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("private_network_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ATTACHED_TO"
    properties: ScalewayServerlessFunctionToPrivateNetworkRelProperties = (
        ScalewayServerlessFunctionToPrivateNetworkRelProperties()
    )


@dataclass(frozen=True)
class ScalewayServerlessFunctionSchema(CartographyNodeSchema):
    label: str = "ScalewayServerlessFunction"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Function"])
    properties: ScalewayServerlessFunctionProperties = (
        ScalewayServerlessFunctionProperties()
    )
    sub_resource_relationship: ScalewayServerlessFunctionToProjectRel = (
        ScalewayServerlessFunctionToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ScalewayServerlessFunctionToNamespaceRel(),
            ScalewayServerlessFunctionToPrivateNetworkRel(),
        ]
    )
