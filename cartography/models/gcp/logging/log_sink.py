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
class GCPLogSinkNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Full resource name of this Cloud Logging sink."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Full resource name of this sink."
    )
    sink_name: PropertyRef = PropertyRef(
        "sink_name", description="Short sink name without the parent prefix."
    )
    destination: PropertyRef = PropertyRef(
        "destination", description="Export destination configured for this sink."
    )
    filter: PropertyRef = PropertyRef(
        "filter", description="Advanced logs filter configured for this sink."
    )
    description: PropertyRef = PropertyRef(
        "description", description="Optional description of this sink."
    )
    disabled: PropertyRef = PropertyRef(
        "disabled", description="Whether this sink is disabled."
    )
    include_children: PropertyRef = PropertyRef(
        "include_children",
        description="Whether this sink includes child resources under the parent.",
    )
    writer_identity: PropertyRef = PropertyRef(
        "writer_identity", description="Writer identity used by this sink."
    )
    output_version_format: PropertyRef = PropertyRef(
        "output_version_format",
        description="Output version format configured for this sink, when present.",
    )
    parent_type: PropertyRef = PropertyRef(
        "parent_type", description="Sink parent type: organization, folder, or project."
    )
    parent_id: PropertyRef = PropertyRef(
        "parent_id", description="Full resource name of the sink parent."
    )


@dataclass(frozen=True)
class GCPLogSinkToOrgRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPLogSinkToOrgRel(CartographyRelSchema):
    target_node_label: str = "GCPOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_RESOURCE_NAME", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPLogSinkToOrgRelProperties = GCPLogSinkToOrgRelProperties()


@dataclass(frozen=True)
class GCPLogSinkToFolderRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPLogSinkToFolderRel(CartographyRelSchema):
    target_node_label: str = "GCPFolder"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("FOLDER_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPLogSinkToFolderRelProperties = GCPLogSinkToFolderRelProperties()


@dataclass(frozen=True)
class GCPLogSinkToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPLogSinkToProjectRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPLogSinkToProjectRelProperties = GCPLogSinkToProjectRelProperties()


@dataclass(frozen=True)
class GCPOrgLogSinkSchema(CartographyNodeSchema):
    """Representation of an organization-scoped GCP [Cloud Logging Sink](https://cloud.google.com/logging/docs/reference/v2/rest/v2/sinks)."""

    label: str = "GCPLogSink"
    properties: GCPLogSinkNodeProperties = GCPLogSinkNodeProperties()
    sub_resource_relationship: GCPLogSinkToOrgRel = GCPLogSinkToOrgRel()


@dataclass(frozen=True)
class GCPFolderLogSinkSchema(CartographyNodeSchema):
    """Representation of a folder-scoped GCP Cloud Logging Sink."""

    label: str = "GCPLogSink"
    properties: GCPLogSinkNodeProperties = GCPLogSinkNodeProperties()
    sub_resource_relationship: GCPLogSinkToFolderRel = GCPLogSinkToFolderRel()


@dataclass(frozen=True)
class GCPProjectLogSinkSchema(CartographyNodeSchema):
    """Representation of a project-scoped GCP Cloud Logging Sink."""

    label: str = "GCPLogSink"
    properties: GCPLogSinkNodeProperties = GCPLogSinkNodeProperties()
    sub_resource_relationship: GCPLogSinkToProjectRel = GCPLogSinkToProjectRel()
