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
from cartography.models.ontology.labels import IDENTITY_PROVIDER


@dataclass(frozen=True)
class LangSmithSSOProviderNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="SSO settings UUID.")
    name: PropertyRef = PropertyRef(
        "provider_id",
        extra_index=True,
        description="Identifier of the upstream SSO provider.",
    )
    metadata_url: PropertyRef = PropertyRef(
        "metadata_url",
        description="URL of the provider's SAML or OIDC metadata document.",
    )
    has_metadata_xml: PropertyRef = PropertyRef(
        "has_metadata_xml",
        description=(
            "True if SSO metadata was supplied inline as XML rather than by URL. The XML "
            "itself is not ingested."
        ),
    )
    attribute_mapping_load_error: PropertyRef = PropertyRef(
        "attribute_mapping_load_error",
        description="Error reported while loading the provider's attribute mapping, if any.",
    )
    sso_groups_enabled: PropertyRef = PropertyRef(
        "sso_groups_enabled",
        description="True if group claims from the provider are consumed.",
    )
    sso_groups_claim_field: PropertyRef = PropertyRef(
        "sso_groups_claim_field",
        description="Name of the assertion claim carrying the user's groups.",
    )
    sso_groups_required: PropertyRef = PropertyRef(
        "sso_groups_required",
        description="True if a user must carry a matching group claim in order to log in.",
    )
    sso_groups_role_sync_enabled: PropertyRef = PropertyRef(
        "sso_groups_role_sync_enabled",
        description="True if workspace roles are synchronized from provider group claims.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class LangSmithSSOProviderToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:LangSmithOrganization)-[:RESOURCE]->(:LangSmithSSOProvider)
class LangSmithSSOProviderToOrganizationRel(CartographyRelSchema):
    """Links an organization to its configured SSO provider."""

    target_node_label: str = "LangSmithOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: LangSmithSSOProviderToOrganizationRelProperties = (
        LangSmithSSOProviderToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class LangSmithSSOProviderToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:LangSmithSSOProvider)-[:PROVISIONS_INTO]->(:LangSmithWorkspace)
class LangSmithSSOProviderToWorkspaceRel(CartographyRelSchema):
    """A workspace that just-in-time provisioned users are placed into by default."""

    target_node_label: str = "LangSmithWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("default_workspace_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "PROVISIONS_INTO"
    properties: LangSmithSSOProviderToWorkspaceRelProperties = (
        LangSmithSSOProviderToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class LangSmithSSOProviderToRoleRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:LangSmithSSOProvider)-[:DEFAULT_ROLE]->(:LangSmithRole)
class LangSmithSSOProviderToRoleRel(CartographyRelSchema):
    """The workspace role granted to users provisioned through this provider."""

    target_node_label: str = "LangSmithRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("default_workspace_role_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "DEFAULT_ROLE"
    properties: LangSmithSSOProviderToRoleRelProperties = (
        LangSmithSSOProviderToRoleRelProperties()
    )


@dataclass(frozen=True)
class LangSmithSSOProviderSchema(CartographyNodeSchema):
    """An SSO identity provider configured for a LangSmith organization."""

    label: str = "LangSmithSSOProvider"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [IDENTITY_PROVIDER]
    )  # IdentityProvider label is used for ontology mapping
    properties: LangSmithSSOProviderNodeProperties = (
        LangSmithSSOProviderNodeProperties()
    )
    sub_resource_relationship: LangSmithSSOProviderToOrganizationRel = (
        LangSmithSSOProviderToOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            LangSmithSSOProviderToWorkspaceRel(),
            LangSmithSSOProviderToRoleRel(),
        ],
    )
