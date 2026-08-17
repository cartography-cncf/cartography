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
class GCPTargetHttpsProxyNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "partial_uri", description="Stable identifier for this resource."
    )
    partial_uri: PropertyRef = PropertyRef("partial_uri", description="Same as `id`.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="The name of the target HTTPS proxy."
    )
    self_link: PropertyRef = PropertyRef(
        "self_link", description="Server-defined URL for the resource."
    )
    project_id: PropertyRef = PropertyRef(
        "project_id",
        description="The project ID that this target HTTPS proxy belongs to.",
    )
    region: PropertyRef = PropertyRef(
        "region",
        description="The region of this proxy, or `null` for global target HTTPS proxies.",
    )
    description: PropertyRef = PropertyRef(
        "description", description="An optional description of this target proxy."
    )
    url_map: PropertyRef = PropertyRef(
        "url_map_partial_uri",
        description="A partial resource URI of the URL map this target proxy uses.",
    )
    ssl_policy: PropertyRef = PropertyRef(
        "ssl_policy_partial_uri",
        description="A partial resource URI of the SSL policy attached to this target proxy. "
        "Absent means no SSL policy is configured on the proxy.",
    )
    creation_timestamp: PropertyRef = PropertyRef(
        "creation_timestamp", description="Creation timestamp of the resource."
    )


@dataclass(frozen=True)
class GCPTargetHttpsProxyToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPTargetHttpsProxyToProjectRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("PROJECT_ID", set_in_kwargs=True),
        },
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPTargetHttpsProxyToProjectRelProperties = (
        GCPTargetHttpsProxyToProjectRelProperties()
    )


@dataclass(frozen=True)
class GCPTargetHttpsProxyToSslPolicyRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPTargetHttpsProxyToSslPolicyRel(CartographyRelSchema):
    target_node_label: str = "GCPSslPolicy"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("ssl_policy_partial_uri"),
        },
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES"
    properties: GCPTargetHttpsProxyToSslPolicyRelProperties = (
        GCPTargetHttpsProxyToSslPolicyRelProperties()
    )


# No `LoadBalancer` ontology label: a target proxy is a component inside a GCP load
# balancer rather than the load balancer itself, the same way AzureLoadBalancerRule and
# AzureLoadBalancerFrontendIP carry no label while AzureLoadBalancer does. GCPForwardingRule
# is the labelled entry point for this provider.
@dataclass(frozen=True)
class GCPTargetHttpsProxySchema(CartographyNodeSchema):
    """Representation of a GCP [Target HTTPS Proxy](https://cloud.google.com/compute/docs/reference/rest/v1/targetHttpsProxies), used by external and internal HTTPS load balancers to terminate TLS."""

    label: str = "GCPTargetHttpsProxy"
    properties: GCPTargetHttpsProxyNodeProperties = GCPTargetHttpsProxyNodeProperties()
    sub_resource_relationship: GCPTargetHttpsProxyToProjectRel = (
        GCPTargetHttpsProxyToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GCPTargetHttpsProxyToSslPolicyRel(),
        ],
    )
