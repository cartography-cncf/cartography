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
from cartography.models.ontology.labels import API_GATEWAY


@dataclass(frozen=True)
class GCPApiGatewayApiNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", extra_index=True, description="Stable identifier for this resource."
    )
    name: PropertyRef = PropertyRef(
        "name",
        description="Full resource name, projects/*/locations/global/apis/*. Same as id.",
    )
    display_name: PropertyRef = PropertyRef(
        "displayName", description="Human-readable display name of the API."
    )
    # The managed service is the Service Management name that backs this API. It is
    # the join key to servicemanagement.googleapis.com, where the normalized service
    # config lives.
    managed_service: PropertyRef = PropertyRef(
        "managedService",
        description="Name of the associated Service Management service.",
    )
    state: PropertyRef = PropertyRef(
        "state",
        description="Provider-native lifecycle state, for example ACTIVE, CREATING, FAILED.",
    )
    create_time: PropertyRef = PropertyRef(
        "createTime", description="RFC 3339 timestamp when the API was created."
    )
    update_time: PropertyRef = PropertyRef(
        "updateTime", description="RFC 3339 timestamp when the API was last updated."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPApiGatewayApiToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPApiGatewayApiToProjectRel(CartographyRelSchema):
    """The GCP project that contains this API."""

    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPApiGatewayApiToProjectRelProperties = (
        GCPApiGatewayApiToProjectRelProperties()
    )


@dataclass(frozen=True)
class GCPApiGatewayApiSchema(CartographyNodeSchema):
    """A Google Cloud API Gateway Api: the logical API, not a deployed endpoint."""

    label: str = "GCPApiGatewayApi"
    properties: GCPApiGatewayApiNodeProperties = GCPApiGatewayApiNodeProperties()
    sub_resource_relationship: GCPApiGatewayApiToProjectRel = (
        GCPApiGatewayApiToProjectRel()
    )


@dataclass(frozen=True)
class GCPApiGatewayApiConfigNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", extra_index=True, description="Stable identifier for this resource."
    )
    name: PropertyRef = PropertyRef(
        "name",
        description="Full resource name, projects/*/locations/global/apis/*/configs/*. Same as id.",
    )
    display_name: PropertyRef = PropertyRef(
        "displayName", description="Human-readable display name of the config."
    )
    state: PropertyRef = PropertyRef(
        "state",
        description="Provider-native lifecycle state, for example ACTIVE, CREATING, FAILED.",
    )
    service_config_id: PropertyRef = PropertyRef(
        "serviceConfigId",
        description="ID of the associated Service Management service config.",
    )
    gateway_service_account: PropertyRef = PropertyRef(
        "gatewayServiceAccount",
        description="Service account the gateway uses when calling backends.",
    )
    # configs.list omits openapiDocuments entirely and configs.get defaults to
    # view=BASIC, which also omits it. Both of these are only populated when the
    # module successfully fetched the config with view=FULL.
    has_openapi_document: PropertyRef = PropertyRef(
        "hasOpenapiDocument",
        description="Whether an OpenAPI document was returned for this config. False for gRPC-backed configs.",
    )
    openapi_document_path: PropertyRef = PropertyRef(
        "openapiDocumentPath",
        description="Path of the first OpenAPI document attached to this config, if any.",
    )
    create_time: PropertyRef = PropertyRef(
        "createTime", description="RFC 3339 timestamp when the config was created."
    )
    update_time: PropertyRef = PropertyRef(
        "updateTime", description="RFC 3339 timestamp when the config was last updated."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPApiGatewayApiConfigToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPApiGatewayApiConfigToProjectRel(CartographyRelSchema):
    """The GCP project that contains this API config."""

    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPApiGatewayApiConfigToProjectRelProperties = (
        GCPApiGatewayApiConfigToProjectRelProperties()
    )


@dataclass(frozen=True)
class GCPApiGatewayApiConfigToApiRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPApiGatewayApiConfigToApiRel(CartographyRelSchema):
    """The API that this configuration belongs to."""

    target_node_label: str = "GCPApiGatewayApi"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("apiId")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_CONFIG"
    properties: GCPApiGatewayApiConfigToApiRelProperties = (
        GCPApiGatewayApiConfigToApiRelProperties()
    )


@dataclass(frozen=True)
class GCPApiGatewayApiConfigSchema(CartographyNodeSchema):
    """A Google Cloud API Gateway ApiConfig: the deployable configuration for an Api."""

    label: str = "GCPApiGatewayApiConfig"
    properties: GCPApiGatewayApiConfigNodeProperties = (
        GCPApiGatewayApiConfigNodeProperties()
    )
    sub_resource_relationship: GCPApiGatewayApiConfigToProjectRel = (
        GCPApiGatewayApiConfigToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [GCPApiGatewayApiConfigToApiRel()]
    )


@dataclass(frozen=True)
class GCPApiGatewayGatewayNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", extra_index=True, description="Stable identifier for this resource."
    )
    name: PropertyRef = PropertyRef(
        "name",
        description="Full resource name, projects/*/locations/*/gateways/*. Same as id.",
    )
    display_name: PropertyRef = PropertyRef(
        "displayName", description="Human-readable display name of the gateway."
    )
    state: PropertyRef = PropertyRef(
        "state",
        description="Provider-native lifecycle state, for example ACTIVE, CREATING, FAILED.",
    )
    # The hostname is the address clients actually call. A gateway is reachable
    # from the internet whenever this is set; API Gateway has no private
    # deployment mode.
    default_hostname: PropertyRef = PropertyRef(
        "defaultHostname",
        description="Auto-generated public hostname serving this gateway. Absent until the gateway is ACTIVE.",
    )
    api_config: PropertyRef = PropertyRef(
        "apiConfig",
        description="Resource name of the ApiConfig this gateway currently serves.",
    )
    region: PropertyRef = PropertyRef(
        "region",
        description="Region the gateway is deployed in, parsed from the resource name.",
    )
    create_time: PropertyRef = PropertyRef(
        "createTime", description="RFC 3339 timestamp when the gateway was created."
    )
    update_time: PropertyRef = PropertyRef(
        "updateTime",
        description="RFC 3339 timestamp when the gateway was last updated.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPApiGatewayGatewayToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPApiGatewayGatewayToProjectRel(CartographyRelSchema):
    """The GCP project that contains this gateway."""

    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPApiGatewayGatewayToProjectRelProperties = (
        GCPApiGatewayGatewayToProjectRelProperties()
    )


@dataclass(frozen=True)
class GCPApiGatewayGatewayToApiConfigRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPApiGatewayGatewayToApiConfigRel(CartographyRelSchema):
    """The API configuration this gateway currently serves."""

    target_node_label: str = "GCPApiGatewayApiConfig"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("apiConfig")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_CONFIG"
    properties: GCPApiGatewayGatewayToApiConfigRelProperties = (
        GCPApiGatewayGatewayToApiConfigRelProperties()
    )


@dataclass(frozen=True)
class GCPApiGatewayGatewaySchema(CartographyNodeSchema):
    """A deployed Google Cloud API Gateway: the address clients call."""

    label: str = "GCPApiGatewayGateway"
    # The Gateway, not the Api, carries the ontology label: it is the node that
    # terminates client requests at a hostname, which is what the cross-provider
    # APIGateway concept means.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([API_GATEWAY])
    properties: GCPApiGatewayGatewayNodeProperties = (
        GCPApiGatewayGatewayNodeProperties()
    )
    sub_resource_relationship: GCPApiGatewayGatewayToProjectRel = (
        GCPApiGatewayGatewayToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [GCPApiGatewayGatewayToApiConfigRel()]
    )
