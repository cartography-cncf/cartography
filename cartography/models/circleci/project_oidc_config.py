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
class CircleCIProjectOidcConfigNodeProperties(CartographyNodeProperties):
    # One project-level custom-claims config per project; id is the project id.
    id: PropertyRef = PropertyRef(
        "id", description="Owning project ID used as the configuration ID."
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
        "project_id", description="Owning project ID."
    )


@dataclass(frozen=True)
class CircleCIProjectOidcConfigToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:CircleCIProject)-[:RESOURCE]->(:CircleCIProjectOidcConfig)
class CircleCIProjectOidcConfigToProjectRel(CartographyRelSchema):
    """The CircleCI project contains its OIDC configuration."""

    target_node_label: str = "CircleCIProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: CircleCIProjectOidcConfigToProjectRelProperties = (
        CircleCIProjectOidcConfigToProjectRelProperties()
    )


@dataclass(frozen=True)
class CircleCIProjectOidcConfigSchema(CartographyNodeSchema):
    """A project-level CircleCI OIDC custom-claims configuration."""

    label: str = "CircleCIProjectOidcConfig"
    properties: CircleCIProjectOidcConfigNodeProperties = (
        CircleCIProjectOidcConfigNodeProperties()
    )
    sub_resource_relationship: CircleCIProjectOidcConfigToProjectRel = (
        CircleCIProjectOidcConfigToProjectRel()
    )
