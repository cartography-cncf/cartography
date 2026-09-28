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
from cartography.models.ontology.labels import LOAD_BALANCER


@dataclass(frozen=True)
class LoadBalancerNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="The load balancer's DNS name exactly as AWS returned it, case preserved. Unlike `dnsname` it is not lowercased, because listeners and target groups join against it.",
    )
    name: PropertyRef = PropertyRef("name", description="The name of the load balancer")
    dnsname: PropertyRef = PropertyRef(
        "dnsname",
        extra_index=True,
        description="The DNS name of the load balancer, lowercased at ingestion. AWS preserves the load balancer name's case here, while Route53 alias targets and Kubernetes load balancer status hostnames are lowercase, and those are matched against this property for equality.",
    )
    canonicalhostedzonename: PropertyRef = PropertyRef(
        "canonicalhostedzonename", description="The DNS name of the load balancer"
    )
    canonicalhostedzonenameid: PropertyRef = PropertyRef(
        "canonicalhostedzonenameid",
        description="The ID of the Amazon Route 53 hosted zone for the load balancer.",
    )
    scheme: PropertyRef = PropertyRef(
        "scheme",
        extra_index=True,
        description="The type of load balancer. Valid only for load balancers in a VPC. If scheme is `internet-facing`, the load balancer has a public DNS name that resolves to a public IP address.  If scheme is `internal`, the load balancer has a public DNS name that resolves to a private IP address.",
    )
    region: PropertyRef = PropertyRef(
        "Region", set_in_kwargs=True, description="The region of the load balancer"
    )
    createdtime: PropertyRef = PropertyRef(
        "createdtime", description="The date and time the load balancer was created."
    )
    exposed_internet: PropertyRef = PropertyRef(
        "exposed_internet",
        extra_index=True,
        description="`True` when the scheme is `internet-facing` and a source security group opens a listener port to `0.0.0.0/0`. `False` otherwise.",
    )  # Populated by the AWS_EC2_ASSET_EXPOSURE_LOAD_BALANCER analysis job.
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class LoadBalancerToAWSAccountRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class LoadBalancerToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: LoadBalancerToAWSAccountRelRelProperties = (
        LoadBalancerToAWSAccountRelRelProperties()
    )


@dataclass(frozen=True)
class LoadBalancerToSecurityGroupRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class LoadBalancerToSourceSecurityGroupRel(CartographyRelSchema):
    target_node_label: str = "AWSEC2SecurityGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"name": PropertyRef("GROUP_NAME")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "SOURCE_SECURITY_GROUP"
    properties: LoadBalancerToSecurityGroupRelProperties = (
        LoadBalancerToSecurityGroupRelProperties()
    )


@dataclass(frozen=True)
class LoadBalancerToEC2SecurityGroupRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class LoadBalancerToEC2SecurityGroupRel(CartographyRelSchema):
    target_node_label: str = "AWSEC2SecurityGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"groupid": PropertyRef("GROUP_IDS", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF_EC2_SECURITY_GROUP"
    properties: LoadBalancerToEC2SecurityGroupRelRelProperties = (
        LoadBalancerToEC2SecurityGroupRelRelProperties()
    )


@dataclass(frozen=True)
class LoadBalancerToEC2InstanceRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class LoadBalancerToEC2InstanceRel(CartographyRelSchema):
    target_node_label: str = "AWSEC2Instance"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"instanceid": PropertyRef("INSTANCE_IDS", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "EXPOSE"
    properties: LoadBalancerToEC2InstanceRelRelProperties = (
        LoadBalancerToEC2InstanceRelRelProperties()
    )


@dataclass(frozen=True)
class LoadBalancerSchema(CartographyNodeSchema):
    """Represents a classic [AWS Elastic Load Balancer](https://docs.aws.amazon.com/elasticloadbalancing/2012-06-01/APIReference/API_LoadBalancerDescription.html).  See [spec for details](https://docs.aws.amazon.com/elasticloadbalancing/2012-06-01/APIReference/API_LoadBalancerDescription.html).

    **Label rename:** in previous versions, classic ELB nodes used the label `LoadBalancer`. It was renamed to `AWSLoadBalancer` for consistency with other AWS resources, and existing nodes are relabeled automatically on upgrade.
    """

    label: str = "AWSLoadBalancer"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([LOAD_BALANCER])
    properties: LoadBalancerNodeProperties = LoadBalancerNodeProperties()
    sub_resource_relationship: LoadBalancerToAWSAccountRel = (
        LoadBalancerToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            LoadBalancerToSourceSecurityGroupRel(),
            LoadBalancerToEC2SecurityGroupRel(),
            LoadBalancerToEC2InstanceRel(),
        ],
    )
