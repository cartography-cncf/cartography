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
    id: PropertyRef = PropertyRef("id", description="Instance template unique ID.")
    name: PropertyRef = PropertyRef("name", description="Instance template name.")
    commercial_type: PropertyRef = PropertyRef(
        "commercial_type", description="Instance commercial type."
    )
    image_id: PropertyRef = PropertyRef(
        "image_id", description="Image ID used for created Instances."
    )
    security_group_id: PropertyRef = PropertyRef(
        "security_group_id",
        description="Security Group ID applied to created Instances.",
    )
    placement_group_id: PropertyRef = PropertyRef(
        "placement_group_id",
        description="Placement Group ID applied to created Instances.",
    )
    public_ips_v4_count: PropertyRef = PropertyRef(
        "public_ips_v4_count", description="Number of IPv4 addresses to attach."
    )
    public_ips_v6_count: PropertyRef = PropertyRef(
        "public_ips_v6_count", description="Number of IPv6 addresses to attach."
    )
    private_network_ids: PropertyRef = PropertyRef(
        "private_network_ids",
        description="Private Networks to attach to created Instances.",
    )
    status: PropertyRef = PropertyRef(
        "status", description="Template status, such as `ready` or `error`."
    )
    tags: PropertyRef = PropertyRef(
        "tags", description="Tags associated with the template."
    )
    zone: PropertyRef = PropertyRef(
        "zone", description="Zone in which the template is located."
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Template creation date."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="Template last update date."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ScalewayInstanceTemplateToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayInstanceTemplate)
class ScalewayInstanceTemplateToProjectRel(CartographyRelSchema):
    """Connects `ScalewayProject` to `ScalewayInstanceTemplate` through `RESOURCE`."""

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
    """Connects `ScalewayInstanceTemplate` to `ScalewayPrivateNetwork`."""

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
    """Defines how Instances are created for an autoscaling Instance Group."""

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
    id: PropertyRef = PropertyRef("id", description="Instance group unique ID.")
    name: PropertyRef = PropertyRef("name", description="Instance group name.")
    tags: PropertyRef = PropertyRef(
        "tags", description="Tags associated with the group."
    )
    instance_template_id: PropertyRef = PropertyRef(
        "instance_template_id",
        description="Instance Template used to create Instances.",
    )
    capacity_max_replicas: PropertyRef = PropertyRef(
        "capacity.max_replicas",
        description="Maximum number of Instances in the group.",
    )
    capacity_min_replicas: PropertyRef = PropertyRef(
        "capacity.min_replicas",
        description="Minimum number of Instances in the group.",
    )
    capacity_cooldown_delay: PropertyRef = PropertyRef(
        "capacity.cooldown_delay",
        description="Cooldown duration between scaling actions.",
    )
    loadbalancer_id: PropertyRef = PropertyRef(
        "loadbalancer_id", description="Load Balancer attached to the group."
    )
    loadbalancer_backend_ids: PropertyRef = PropertyRef(
        "loadbalancer_backend_ids",
        description="Load Balancer backends maintained by the group.",
    )
    loadbalancer_private_network_id: PropertyRef = PropertyRef(
        "loadbalancer_private_network_id",
        description="Private Network shared with the Load Balancer.",
    )
    error_messages: PropertyRef = PropertyRef(
        "error_messages", description="Configuration error messages."
    )
    zone: PropertyRef = PropertyRef(
        "zone", description="Zone in which the group is located."
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Group creation date."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="Group last update date."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ScalewayInstanceGroupToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayInstanceGroup)
class ScalewayInstanceGroupToProjectRel(CartographyRelSchema):
    """Connects `ScalewayProject` to `ScalewayInstanceGroup` through `RESOURCE`."""

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
    """Connects `ScalewayInstanceGroup` to the Instance Template it uses."""

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
    """Connects `ScalewayInstanceGroup` to the Load Balancer it uses."""

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
    """Manages a fleet of Instances using a template, capacity, and policies."""

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
    id: PropertyRef = PropertyRef("id", description="Scaling policy unique ID.")
    name: PropertyRef = PropertyRef("name", description="Scaling policy name.")
    action: PropertyRef = PropertyRef(
        "action", description="Scaling action, such as `scale_up` or `scale_down`."
    )
    type: PropertyRef = PropertyRef(
        "type_", description="How the value is applied to group capacity."
    )
    value: PropertyRef = PropertyRef(
        "value", description="Magnitude of the scaling action."
    )
    priority: PropertyRef = PropertyRef(
        "priority", description="Policy priority; lower values are evaluated first."
    )
    instance_group_id: PropertyRef = PropertyRef(
        "instance_group_id", description="Instance Group the policy applies to."
    )
    metric_name: PropertyRef = PropertyRef(
        "metric.name", description="Metric name or description."
    )
    metric_operator: PropertyRef = PropertyRef(
        "metric.operator",
        description="Operator used to compare the metric to the threshold.",
    )
    metric_aggregate: PropertyRef = PropertyRef(
        "metric.aggregate",
        description="Aggregation method for sampled metric values.",
    )
    metric_sampling_range_min: PropertyRef = PropertyRef(
        "metric.sampling_range_min", description="Sampling window in minutes."
    )
    metric_threshold: PropertyRef = PropertyRef(
        "metric.threshold", description="Threshold value for the scaling condition."
    )
    metric_managed_metric: PropertyRef = PropertyRef(
        "metric.managed_metric", description="Scaleway managed metric identifier."
    )
    metric_cockpit_metric_name: PropertyRef = PropertyRef(
        "metric.cockpit_metric_name", description="Custom Cockpit metric name."
    )
    zone: PropertyRef = PropertyRef(
        "zone", description="Zone in which the policy is located."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ScalewayScalingPolicyToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayScalingPolicy)
class ScalewayScalingPolicyToProjectRel(CartographyRelSchema):
    """Connects `ScalewayProject` to `ScalewayScalingPolicy` through `RESOURCE`."""

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
    """Connects `ScalewayScalingPolicy` to the Instance Group it applies to."""

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
    """Defines a metric condition and scaling action for an Instance Group."""

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
