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
class CircleCIOidcConfigNodeProperties(CartographyNodeProperties):
    # One org-level custom-claims config per org; id is the org id.
    id: PropertyRef = PropertyRef(
        "id", description="Owning organization ID used as the configuration ID."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last update.",
    )
    scope: PropertyRef = PropertyRef("scope", description="OIDC configuration scope.")
    audience: PropertyRef = PropertyRef(
        "audience", description="Trusted OIDC token audiences."
    )
    audience_updated_at: PropertyRef = PropertyRef(
        "audience_updated_at", description="Timestamp of the last audience change."
    )
    ttl: PropertyRef = PropertyRef("ttl", description="OIDC token time to live.")
    ttl_updated_at: PropertyRef = PropertyRef(
        "ttl_updated_at", description="Timestamp of the last token TTL change."
    )
    org_id: PropertyRef = PropertyRef("org_id", description="Owning organization ID.")
    project_id: PropertyRef = PropertyRef(
        "project_id", description="Owning project ID when present."
    )


@dataclass(frozen=True)
class CircleCIOidcConfigToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:CircleCIOrganization)-[:RESOURCE]->(:CircleCIOidcConfig)
class CircleCIOidcConfigToOrganizationRel(CartographyRelSchema):
    """The CircleCI organization contains its OIDC configuration."""

    target_node_label: str = "CircleCIOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: CircleCIOidcConfigToOrganizationRelProperties = (
        CircleCIOidcConfigToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class CircleCIOidcConfigSchema(CartographyNodeSchema):
    """An organization-level CircleCI OIDC custom-claims configuration."""

    label: str = "CircleCIOidcConfig"
    properties: CircleCIOidcConfigNodeProperties = CircleCIOidcConfigNodeProperties()
    sub_resource_relationship: CircleCIOidcConfigToOrganizationRel = (
        CircleCIOidcConfigToOrganizationRel()
    )
