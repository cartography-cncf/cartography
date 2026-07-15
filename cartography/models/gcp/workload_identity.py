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
    id: PropertyRef = PropertyRef(
        "id",
        extra_index=True,
        description="The full resource name, e.g. `projects/{number}/locations/global/workloadIdentityPools/{pool_id}`.",
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Same as `id`."
    )
    display_name: PropertyRef = PropertyRef(
        "displayName", description="The friendly name of the pool."
    )
    description: PropertyRef = PropertyRef(
        "description", description="A description of the pool."
    )
    state: PropertyRef = PropertyRef(
        "state", description="Pool state (`ACTIVE`, `DELETED`)."
    )
    disabled: PropertyRef = PropertyRef(
        "disabled", description="Whether the pool is disabled."
    )
    mode: PropertyRef = PropertyRef(
        "mode",
        description="Pool mode. `SYSTEM_TRUST_DOMAIN` indicates a GKE-managed pool (`*.svc.id.goog`) whose providers are managed by Google and not enumerated by Cartography. Otherwise the field is unset or carries a user-managed mode.",
    )
    session_duration: PropertyRef = PropertyRef(
        "sessionDuration",
        description="Default session duration for federated tokens issued via this pool.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )
    project_id: PropertyRef = PropertyRef(
        "projectId",
        set_in_kwargs=True,
        description="Google Cloud project that owns this resource.",
    )


@dataclass(frozen=True)
class GCPWorkloadIdentityPoolToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


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
    """Representation of a GCP [Workload Identity Pool](https://cloud.google.com/iam/docs/reference/rest/v1/projects.locations.workloadIdentityPools). A pool groups external identities that can impersonate GCP service accounts via federation."""

    label: str = "GCPWorkloadIdentityPool"
    properties: GCPWorkloadIdentityPoolNodeProperties = (
        GCPWorkloadIdentityPoolNodeProperties()
    )
    sub_resource_relationship: GCPWorkloadIdentityPoolToProjectRel = (
        GCPWorkloadIdentityPoolToProjectRel()
    )


@dataclass(frozen=True)
class GCPWorkloadIdentityProviderNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", extra_index=True, description="The full provider resource name."
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Same as `id`."
    )
    display_name: PropertyRef = PropertyRef(
        "displayName", description="The friendly name of the provider."
    )
    description: PropertyRef = PropertyRef(
        "description", description="A description of the provider."
    )
    state: PropertyRef = PropertyRef(
        "state", description="Provider state (`ACTIVE`, `DELETED`)."
    )
    disabled: PropertyRef = PropertyRef(
        "disabled", description="Whether the provider is explicitly disabled."
    )
    enabled: PropertyRef = PropertyRef(
        "enabled",
        description="Effective enabled flag: true only when both the provider and its parent pool are `state == ACTIVE` and not disabled. Used for the `IdentityProvider` ontology mapping.",
    )
    protocol: PropertyRef = PropertyRef(
        "protocol",
        description="One of `OIDC`, `AWS`, `SAML`, `X509`, depending on which sub-object is populated.",
    )
    attribute_condition: PropertyRef = PropertyRef(
        "attributeCondition",
        description="CEL expression that gates token claims before federation.",
    )
    oidc_issuer_uri: PropertyRef = PropertyRef(
        "oidcIssuerUri",
        description="OIDC issuer URI (only set when `protocol = OIDC`).",
    )
    oidc_allowed_audiences: PropertyRef = PropertyRef(
        "oidcAllowedAudiences",
        description="OIDC allowed audiences (only set when `protocol = OIDC`).",
    )
    aws_account_id: PropertyRef = PropertyRef(
        "awsAccountId",
        description="AWS account ID this provider trusts (only set when `protocol = AWS`).",
    )
    saml_idp_metadata_xml: PropertyRef = PropertyRef(
        "samlIdpMetadataXml",
        description="SAML IdP metadata XML (only set when `protocol = SAML`).",
    )
    pool_name: PropertyRef = PropertyRef(
        "poolName",
        description="The resource name of the parent GCPWorkloadIdentityPool.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )
    project_id: PropertyRef = PropertyRef(
        "projectId",
        set_in_kwargs=True,
        description="Google Cloud project that owns this resource.",
    )


@dataclass(frozen=True)
class GCPWorkloadIdentityProviderToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


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
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


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
    """A Google Cloud Workload Identity Provider resource."""

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
