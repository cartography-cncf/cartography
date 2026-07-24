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
class ScalewayInstanceTemplateProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    commercial_type: PropertyRef = PropertyRef("commercial_type")
    image_id: PropertyRef = PropertyRef("image_id")
    security_group_id: PropertyRef = PropertyRef("security_group_id")
    placement_group_id: PropertyRef = PropertyRef("placement_group_id")
    public_ips_v4_count: PropertyRef = PropertyRef("public_ips_v4_count")
    public_ips_v6_count: PropertyRef = PropertyRef("public_ips_v6_count")
    private_network_ids: PropertyRef = PropertyRef("private_network_ids")
    status: PropertyRef = PropertyRef("status")
    tags: PropertyRef = PropertyRef("tags")
    zone: PropertyRef = PropertyRef("zone")
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ScalewayInstanceTemplateToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayInstanceTemplate)
class ScalewayInstanceTemplateToProjectRel(CartographyRelSchema):
    target_node_label: str = "ScalewayProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ScalewayInstanceTemplateToProjectRelProperties = (
        ScalewayInstanceTemplateToProjectRelProperties()
    )


@dataclass(frozen=True)
class ScalewayInstanceTemplateToPrivateNetworkRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayInstanceTemplate)-[:ATTACHED_TO]->(:ScalewayPrivateNetwork)
class ScalewayInstanceTemplateToPrivateNetworkRel(CartographyRelSchema):
    target_node_label: str = "ScalewayPrivateNetwork"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("private_network_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ATTACHED_TO"
    properties: ScalewayInstanceTemplateToPrivateNetworkRelProperties = (
        ScalewayInstanceTemplateToPrivateNetworkRelProperties()
    )


@dataclass(frozen=True)
class ScalewayInstanceTemplateSchema(CartographyNodeSchema):
    label: str = "ScalewayInstanceTemplate"
    properties: ScalewayInstanceTemplateProperties = (
        ScalewayInstanceTemplateProperties()
    )
    sub_resource_relationship: ScalewayInstanceTemplateToProjectRel = (
        ScalewayInstanceTemplateToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ScalewayInstanceTemplateToPrivateNetworkRel(),
        ]
    )


@dataclass(frozen=True)
class ScalewayInstanceGroupProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    tags: PropertyRef = PropertyRef("tags")
    instance_template_id: PropertyRef = PropertyRef("instance_template_id")
    capacity_max_replicas: PropertyRef = PropertyRef("capacity.max_replicas")
    capacity_min_replicas: PropertyRef = PropertyRef("capacity.min_replicas")
    capacity_cooldown_delay: PropertyRef = PropertyRef("capacity.cooldown_delay")
    loadbalancer_id: PropertyRef = PropertyRef("loadbalancer_id")
    loadbalancer_backend_ids: PropertyRef = PropertyRef("loadbalancer_backend_ids")
    loadbalancer_private_network_id: PropertyRef = PropertyRef(
        "loadbalancer_private_network_id"
    )
    error_messages: PropertyRef = PropertyRef("error_messages")
    zone: PropertyRef = PropertyRef("zone")
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ScalewayInstanceGroupToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayInstanceGroup)
class ScalewayInstanceGroupToProjectRel(CartographyRelSchema):
    target_node_label: str = "ScalewayProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ScalewayInstanceGroupToProjectRelProperties = (
        ScalewayInstanceGroupToProjectRelProperties()
    )


@dataclass(frozen=True)
class ScalewayInstanceGroupToTemplateRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayInstanceGroup)-[:USES]->(:ScalewayInstanceTemplate)
class ScalewayInstanceGroupToTemplateRel(CartographyRelSchema):
    target_node_label: str = "ScalewayInstanceTemplate"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("instance_template_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES"
    properties: ScalewayInstanceGroupToTemplateRelProperties = (
        ScalewayInstanceGroupToTemplateRelProperties()
    )


@dataclass(frozen=True)
class ScalewayInstanceGroupToLoadBalancerRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayInstanceGroup)-[:USES]->(:ScalewayLoadBalancer)
class ScalewayInstanceGroupToLoadBalancerRel(CartographyRelSchema):
    target_node_label: str = "ScalewayLoadBalancer"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("loadbalancer_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES"
    properties: ScalewayInstanceGroupToLoadBalancerRelProperties = (
        ScalewayInstanceGroupToLoadBalancerRelProperties()
    )


@dataclass(frozen=True)
class ScalewayInstanceGroupSchema(CartographyNodeSchema):
    label: str = "ScalewayInstanceGroup"
    properties: ScalewayInstanceGroupProperties = ScalewayInstanceGroupProperties()
    sub_resource_relationship: ScalewayInstanceGroupToProjectRel = (
        ScalewayInstanceGroupToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ScalewayInstanceGroupToTemplateRel(),
            ScalewayInstanceGroupToLoadBalancerRel(),
        ]
    )


@dataclass(frozen=True)
class ScalewayScalingPolicyProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    action: PropertyRef = PropertyRef("action")
    type: PropertyRef = PropertyRef("type_")
    value: PropertyRef = PropertyRef("value")
    priority: PropertyRef = PropertyRef("priority")
    instance_group_id: PropertyRef = PropertyRef("instance_group_id")
    metric_name: PropertyRef = PropertyRef("metric.name")
    metric_operator: PropertyRef = PropertyRef("metric.operator")
    metric_aggregate: PropertyRef = PropertyRef("metric.aggregate")
    metric_sampling_range_min: PropertyRef = PropertyRef("metric.sampling_range_min")
    metric_threshold: PropertyRef = PropertyRef("metric.threshold")
    metric_managed_metric: PropertyRef = PropertyRef("metric.managed_metric")
    metric_cockpit_metric_name: PropertyRef = PropertyRef("metric.cockpit_metric_name")
    zone: PropertyRef = PropertyRef("zone")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ScalewayScalingPolicyToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayScalingPolicy)
class ScalewayScalingPolicyToProjectRel(CartographyRelSchema):
    target_node_label: str = "ScalewayProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ScalewayScalingPolicyToProjectRelProperties = (
        ScalewayScalingPolicyToProjectRelProperties()
    )


@dataclass(frozen=True)
class ScalewayScalingPolicyToInstanceGroupRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayScalingPolicy)-[:APPLIES_TO]->(:ScalewayInstanceGroup)
class ScalewayScalingPolicyToInstanceGroupRel(CartographyRelSchema):
    target_node_label: str = "ScalewayInstanceGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("instance_group_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "APPLIES_TO"
    properties: ScalewayScalingPolicyToInstanceGroupRelProperties = (
        ScalewayScalingPolicyToInstanceGroupRelProperties()
    )


@dataclass(frozen=True)
class ScalewayScalingPolicySchema(CartographyNodeSchema):
    label: str = "ScalewayScalingPolicy"
    properties: ScalewayScalingPolicyProperties = ScalewayScalingPolicyProperties()
    sub_resource_relationship: ScalewayScalingPolicyToProjectRel = (
        ScalewayScalingPolicyToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ScalewayScalingPolicyToInstanceGroupRel(),
        ]
    )
