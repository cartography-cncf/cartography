from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_source_node_matcher
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import SourceNodeMatcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class ELBV2TargetGroupToKubernetesServiceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)
    binding_name: PropertyRef = PropertyRef(
        "binding_name",
        description="Name of the `TargetGroupBinding` that declares this relationship.",
    )
    target_type: PropertyRef = PropertyRef(
        "target_type",
        description="`ip` when pod IPs are registered in the target group, `instance` when node ports are.",
    )
    service_port: PropertyRef = PropertyRef(
        "service_port",
        description="Service port from `spec.serviceRef.port`, either a port number or a port name.",
    )


@dataclass(frozen=True)
# (:AWSELBV2TargetGroup)-[:TARGETS]->(:KubernetesService)
class ELBV2TargetGroupToKubernetesServiceMatchLink(CartographyRelSchema):
    """Links an AWS ELBv2 target group to the Kubernetes service whose endpoints the AWS Load Balancer Controller registers in it, as declared by an `elbv2.k8s.aws` `TargetGroupBinding`. Covers target groups created outside the cluster as well as those the controller creates for Ingresses and LoadBalancer Services."""

    target_node_label: str = "KubernetesService"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "cluster_name": PropertyRef("cluster_name"),
            "qualified_name": PropertyRef("service_qualified_name"),
        },
    )
    source_node_label: str = "AWSELBV2TargetGroup"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("target_group_arn")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "TARGETS"
    properties: ELBV2TargetGroupToKubernetesServiceRelProperties = (
        ELBV2TargetGroupToKubernetesServiceRelProperties()
    )
