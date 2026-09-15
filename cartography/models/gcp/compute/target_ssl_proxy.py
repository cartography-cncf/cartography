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
class GCPTargetSslProxyNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "partial_uri", description="Stable identifier for this resource."
    )
    partial_uri: PropertyRef = PropertyRef("partial_uri", description="Same as `id`.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="The name of the target SSL proxy."
    )
    self_link: PropertyRef = PropertyRef(
        "self_link", description="Server-defined URL for the resource."
    )
    project_id: PropertyRef = PropertyRef(
        "project_id",
        description="The project ID that this target SSL proxy belongs to.",
    )
    description: PropertyRef = PropertyRef(
        "description", description="An optional description of this target proxy."
    )
    service: PropertyRef = PropertyRef(
        "service_partial_uri",
        description="A partial resource URI of the backend service this target proxy forwards to.",
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
class GCPTargetSslProxyToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPTargetSslProxyToProjectRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("PROJECT_ID", set_in_kwargs=True),
        },
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPTargetSslProxyToProjectRelProperties = (
        GCPTargetSslProxyToProjectRelProperties()
    )


@dataclass(frozen=True)
class GCPTargetSslProxyToSslPolicyRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPTargetSslProxyToSslPolicyRel(CartographyRelSchema):
    target_node_label: str = "GCPSslPolicy"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("ssl_policy_partial_uri"),
        },
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES"
    properties: GCPTargetSslProxyToSslPolicyRelProperties = (
        GCPTargetSslProxyToSslPolicyRelProperties()
    )


@dataclass(frozen=True)
class GCPTargetSslProxyToBackendServiceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPTargetSslProxyToBackendServiceRel(CartographyRelSchema):
    target_node_label: str = "GCPBackendService"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("service_partial_uri"),
        },
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ROUTES_TO"
    properties: GCPTargetSslProxyToBackendServiceRelProperties = (
        GCPTargetSslProxyToBackendServiceRelProperties()
    )


# No `LoadBalancer` ontology label, for the same reason as GCPTargetHttpsProxySchema: the
# proxy is a component inside a load balancer, and GCPForwardingRule is the labelled entry
# point for this provider.
@dataclass(frozen=True)
class GCPTargetSslProxySchema(CartographyNodeSchema):
    """Representation of a GCP [Target SSL Proxy](https://cloud.google.com/compute/docs/reference/rest/v1/targetSslProxies), used by SSL proxy load balancers to terminate TLS for non-HTTP TCP traffic."""

    label: str = "GCPTargetSslProxy"
    properties: GCPTargetSslProxyNodeProperties = GCPTargetSslProxyNodeProperties()
    sub_resource_relationship: GCPTargetSslProxyToProjectRel = (
        GCPTargetSslProxyToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GCPTargetSslProxyToSslPolicyRel(),
            GCPTargetSslProxyToBackendServiceRel(),
        ],
    )
