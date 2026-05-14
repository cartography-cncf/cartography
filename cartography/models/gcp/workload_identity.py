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
class GCPWorkloadIdentityPoolNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", extra_index=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    display_name: PropertyRef = PropertyRef("displayName")
    description: PropertyRef = PropertyRef("description")
    state: PropertyRef = PropertyRef("state")
    disabled: PropertyRef = PropertyRef("disabled")
    mode: PropertyRef = PropertyRef("mode")
    session_duration: PropertyRef = PropertyRef("sessionDuration")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    project_id: PropertyRef = PropertyRef("projectId", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPWorkloadIdentityPoolToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPWorkloadIdentityPoolToProjectRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("projectId", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPWorkloadIdentityPoolToProjectRelProperties = (
        GCPWorkloadIdentityPoolToProjectRelProperties()
    )


@dataclass(frozen=True)
class GCPWorkloadIdentityPoolSchema(CartographyNodeSchema):
    label: str = "GCPWorkloadIdentityPool"
    properties: GCPWorkloadIdentityPoolNodeProperties = (
        GCPWorkloadIdentityPoolNodeProperties()
    )
    sub_resource_relationship: GCPWorkloadIdentityPoolToProjectRel = (
        GCPWorkloadIdentityPoolToProjectRel()
    )


@dataclass(frozen=True)
class GCPWorkloadIdentityProviderNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", extra_index=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    display_name: PropertyRef = PropertyRef("displayName")
    description: PropertyRef = PropertyRef("description")
    state: PropertyRef = PropertyRef("state")
    disabled: PropertyRef = PropertyRef("disabled")
    enabled: PropertyRef = PropertyRef("enabled")
    protocol: PropertyRef = PropertyRef("protocol")
    attribute_condition: PropertyRef = PropertyRef("attributeCondition")
    oidc_issuer_uri: PropertyRef = PropertyRef("oidcIssuerUri")
    oidc_allowed_audiences: PropertyRef = PropertyRef("oidcAllowedAudiences")
    aws_account_id: PropertyRef = PropertyRef("awsAccountId")
    saml_idp_metadata_xml: PropertyRef = PropertyRef("samlIdpMetadataXml")
    pool_name: PropertyRef = PropertyRef("poolName")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    project_id: PropertyRef = PropertyRef("projectId", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPWorkloadIdentityProviderToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPWorkloadIdentityProviderToProjectRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("projectId", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPWorkloadIdentityProviderToProjectRelProperties = (
        GCPWorkloadIdentityProviderToProjectRelProperties()
    )


@dataclass(frozen=True)
class GCPWorkloadIdentityProviderToPoolRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPWorkloadIdentityProviderToPoolRel(CartographyRelSchema):
    target_node_label: str = "GCPWorkloadIdentityPool"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("poolName")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF"
    properties: GCPWorkloadIdentityProviderToPoolRelProperties = (
        GCPWorkloadIdentityProviderToPoolRelProperties()
    )


@dataclass(frozen=True)
class GCPWorkloadIdentityProviderSchema(CartographyNodeSchema):
    label: str = "GCPWorkloadIdentityProvider"
    properties: GCPWorkloadIdentityProviderNodeProperties = (
        GCPWorkloadIdentityProviderNodeProperties()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["IdentityProvider"])
    sub_resource_relationship: GCPWorkloadIdentityProviderToProjectRel = (
        GCPWorkloadIdentityProviderToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GCPWorkloadIdentityProviderToPoolRel(),
        ],
    )
