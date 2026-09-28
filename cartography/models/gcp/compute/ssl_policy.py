from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.ontology.labels import NETWORK_ACCESS_CONTROL


@dataclass(frozen=True)
class GCPSslPolicyNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "partial_uri", description="Stable identifier for this resource."
    )
    partial_uri: PropertyRef = PropertyRef("partial_uri", description="Same as `id`.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="The name of the SSL policy."
    )
    self_link: PropertyRef = PropertyRef(
        "self_link", description="Server-defined URL for the resource."
    )
    project_id: PropertyRef = PropertyRef(
        "project_id", description="The project ID that this SSL policy belongs to."
    )
    region: PropertyRef = PropertyRef(
        "region",
        description="The region of this SSL policy, or `null` for global SSL policies.",
    )
    description: PropertyRef = PropertyRef(
        "description", description="An optional description of this SSL policy."
    )
    profile: PropertyRef = PropertyRef(
        "profile",
        description="The compatibility profile (`COMPATIBLE`, `MODERN`, `RESTRICTED`, or `CUSTOM`).",
    )
    min_tls_version: PropertyRef = PropertyRef(
        "min_tls_version",
        description="The minimum TLS version this SSL policy accepts (e.g. `TLS_1_2`).",
    )
    enabled_features: PropertyRef = PropertyRef(
        "enabled_features",
        description="The list of features enabled in this SSL policy, given its profile and custom features.",
    )
    custom_features: PropertyRef = PropertyRef(
        "custom_features",
        description="The list of features explicitly enabled when `profile` is `CUSTOM`.",
    )
    creation_timestamp: PropertyRef = PropertyRef(
        "creation_timestamp", description="Creation timestamp of the resource."
    )


@dataclass(frozen=True)
class GCPSslPolicyToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPSslPolicyToProjectRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("PROJECT_ID", set_in_kwargs=True),
        },
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPSslPolicyToProjectRelProperties = (
        GCPSslPolicyToProjectRelProperties()
    )


@dataclass(frozen=True)
class GCPSslPolicySchema(CartographyNodeSchema):
    """Representation of a GCP [SSL Policy](https://cloud.google.com/compute/docs/reference/rest/v1/sslPolicies). SSL policies control the TLS versions and cipher suites that HTTPS/SSL proxy load balancers negotiate with clients."""

    label: str = "GCPSslPolicy"
    properties: GCPSslPolicyNodeProperties = GCPSslPolicyNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([NETWORK_ACCESS_CONTROL])
    sub_resource_relationship: GCPSslPolicyToProjectRel = GCPSslPolicyToProjectRel()
