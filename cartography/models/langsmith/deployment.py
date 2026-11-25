from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_source_node_matcher
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import SourceNodeMatcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class LangSmithDeploymentNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Deployment UUID.")
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Deployment name."
    )
    display_name: PropertyRef = PropertyRef(
        "display_name", description="Human-readable deployment name."
    )
    status: PropertyRef = PropertyRef("status", description="Deployment status.")
    url: PropertyRef = PropertyRef(
        "url", description="Serving URL of the deployment, once provisioned."
    )
    source: PropertyRef = PropertyRef(
        "source",
        description="Where the deployment image comes from, for example github or external_docker.",
    )
    image_version: PropertyRef = PropertyRef(
        "image_version", description="Image version currently deployed."
    )
    shareable: PropertyRef = PropertyRef(
        "shareable",
        description="True if the deployment can be shared with LangSmith users outside the organization.",
    )
    route_through_gateway: PropertyRef = PropertyRef(
        "route_through_gateway",
        description="True if OpenAI and Anthropic model calls are routed through the LangSmith LLM gateway.",
    )
    is_managed_deep_agent: PropertyRef = PropertyRef(
        "is_managed_deep_agent",
        description="True if this is a Managed Deep Agent deployment.",
    )
    is_preview: PropertyRef = PropertyRef(
        "is_preview", description="True if this is a preview-build deployment."
    )
    secret_names: PropertyRef = PropertyRef(
        "secret_names",
        description=(
            "Names of the environment secrets configured on the deployment. Secret values are "
            "discarded during transform and are never written to the graph."
        ),
    )
    secret_reference_names: PropertyRef = PropertyRef(
        "secret_reference_names",
        description="Names of the Kubernetes Secret references configured on the deployment.",
    )
    tracer_session_id: PropertyRef = PropertyRef(
        "tracer_session_id",
        extra_index=True,
        description="UUID of the LangSmith tracing project the deployment writes runs to.",
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Timestamp when the deployment was created."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="Timestamp when the deployment was last updated."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class LangSmithDeploymentToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:LangSmithOrganization)-[:RESOURCE]->(:LangSmithDeployment)
class LangSmithDeploymentToOrganizationRel(CartographyRelSchema):
    """Links an organization to a deployment running within it."""

    target_node_label: str = "LangSmithOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: LangSmithDeploymentToOrganizationRelProperties = (
        LangSmithDeploymentToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class LangSmithDeploymentToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:LangSmithWorkspace)-[:CONTAINS]->(:LangSmithDeployment)
class LangSmithDeploymentToWorkspaceRel(CartographyRelSchema):
    """Links a deployment to the workspace that owns it."""

    target_node_label: str = "LangSmithWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("tenant_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: LangSmithDeploymentToWorkspaceRelProperties = (
        LangSmithDeploymentToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class LangSmithDeploymentToResourceTagRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)


# Deployments load before resource tags and taggings, so this edge is a matchlink loaded
# with the workspace resources rather than a relationship on the deployment schema.
@dataclass(frozen=True)
# (:LangSmithDeployment)-[:TAGGED]->(:LangSmithResourceTag)
class LangSmithDeploymentToResourceTagRel(CartographyRelSchema):
    """
    A resource tag applied to the deployment. Access policies for the deployment
    resource type match on these tags.
    """

    source_node_label: str = "LangSmithDeployment"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("deployment_id")},
    )
    target_node_label: str = "LangSmithResourceTag"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("tag_value_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "TAGGED"
    properties: LangSmithDeploymentToResourceTagRelProperties = (
        LangSmithDeploymentToResourceTagRelProperties()
    )


@dataclass(frozen=True)
class LangSmithDeploymentSchema(CartographyNodeSchema):
    """A LangGraph Platform deployment serving an agent."""

    label: str = "LangSmithDeployment"
    properties: LangSmithDeploymentNodeProperties = LangSmithDeploymentNodeProperties()
    sub_resource_relationship: LangSmithDeploymentToOrganizationRel = (
        LangSmithDeploymentToOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            LangSmithDeploymentToWorkspaceRel(),
        ],
    )
