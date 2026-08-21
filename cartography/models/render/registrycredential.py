from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class RenderRegistryCredentialNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="ID of the Render registry credential."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Name of the registry credential."
    )
    owner_id: PropertyRef = PropertyRef(
        "ownerId", description="ID of the owning Render workspace."
    )
    username: PropertyRef = PropertyRef(
        "username", description="Username associated with the credential."
    )
    registry: PropertyRef = PropertyRef(
        "registry",
        description="Registry type: GITHUB, GITLAB, DOCKER, GOOGLE_ARTIFACT, or AWS_ECR.",
    )
    updated_at: PropertyRef = PropertyRef(
        "updatedAt", description="Time when the credential was last modified."
    )


@dataclass(frozen=True)
class RenderRegistryCredentialToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:RenderTenant)-[:RESOURCE]->(:RenderRegistryCredential)
class RenderRegistryCredentialToTenantRel(CartographyRelSchema):
    """Connects a Render workspace to a registry credential that it contains."""

    target_node_label: str = "RenderTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("OWNER_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: RenderRegistryCredentialToTenantRelProperties = (
        RenderRegistryCredentialToTenantRelProperties()
    )


@dataclass(frozen=True)
class RenderRegistryCredentialSchema(CartographyNodeSchema):
    """
    A Render registry credential used to pull private container images.

    Only metadata is ingested. Render's list API never returns the actual
    credential/password value - confirmed in the API docs - so there is nothing
    sensitive to discard here.
    """

    label: str = "RenderRegistryCredential"
    properties: RenderRegistryCredentialNodeProperties = (
        RenderRegistryCredentialNodeProperties()
    )
    sub_resource_relationship: RenderRegistryCredentialToTenantRel = (
        RenderRegistryCredentialToTenantRel()
    )
