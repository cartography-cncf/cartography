from dataclasses import dataclass

from cartography.models.aws.extra_labels import ENDPOINT
from cartography.models.aws.extra_labels import LEGACY_ELB_LISTENER
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
class ELBListenerNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Unique identifier for this `AWSELBListener` node."
    )
    port: PropertyRef = PropertyRef(
        "port",
        description="Load balancer port on which the listener accepts connections.",
    )
    protocol: PropertyRef = PropertyRef(
        "protocol", description="Protocol used by the load balancer listener."
    )
    instance_port: PropertyRef = PropertyRef(
        "instance_port",
        description="Backend instance port to which the listener forwards traffic.",
    )
    instance_protocol: PropertyRef = PropertyRef(
        "instance_protocol",
        description="Protocol used to forward listener traffic to backend instances.",
    )
    policy_names: PropertyRef = PropertyRef(
        "policy_names",
        description="Names of load balancer policies enabled on the listener.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ELBListenerToLoadBalancerRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ELBListenerToLoadBalancerRel(CartographyRelSchema):
    target_node_label: str = "AWSLoadBalancer"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("LoadBalancerId")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "ELB_LISTENER"
    properties: ELBListenerToLoadBalancerRelRelProperties = (
        ELBListenerToLoadBalancerRelRelProperties()
    )


@dataclass(frozen=True)
class ELBListenerToAWSAccountRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ELBListenerToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ELBListenerToAWSAccountRelRelProperties = (
        ELBListenerToAWSAccountRelRelProperties()
    )


@dataclass(frozen=True)
class ELBListenerSchema(CartographyNodeSchema):
    """Representation of an AWS Elastic Load Balancer [Listener](https://docs.aws.amazon.com/elasticloadbalancing/2012-06-01/APIReference/API_Listener.html).  Here, an AWSELBListener is a more specific type of Endpoint.  Here'a [good introduction](https://docs.aws.amazon.com/elasticloadbalancing/2012-06-01/APIReference/Welcome.html)."""

    label: str = "AWSELBListener"
    properties: ELBListenerNodeProperties = ELBListenerNodeProperties()
    # DEPRECATED: legacy ELBListener node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [LEGACY_ELB_LISTENER, ENDPOINT]
    )
    sub_resource_relationship: ELBListenerToAWSAccountRel = ELBListenerToAWSAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ELBListenerToLoadBalancerRel(),
        ],
    )
