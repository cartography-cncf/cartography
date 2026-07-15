from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class GCPCloudRunRevisionProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Stable identifier for this resource."
    )
    name: PropertyRef = PropertyRef("name", description="Short name of the revision.")
    service: PropertyRef = PropertyRef(
        "service", description="Full resource name of the parent service."
    )
    service_account_email: PropertyRef = PropertyRef(
        "service_account_email",
        description="The email of the service account used by this revision.",
    )
    log_uri: PropertyRef = PropertyRef(
        "log_uri", description="URI to Cloud Logging for this revision."
    )
    project_id: PropertyRef = PropertyRef(
        "project_id", description="The GCP project ID this revision belongs to."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )


@dataclass(frozen=True)
class ProjectToCloudRunRevisionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
class ProjectToCloudRunRevisionRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("project_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ProjectToCloudRunRevisionRelProperties = (
        ProjectToCloudRunRevisionRelProperties()
    )


@dataclass(frozen=True)
class CloudRunServiceToRevisionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
class CloudRunServiceToRevisionRel(CartographyRelSchema):
    target_node_label: str = "GCPCloudRunService"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("service")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_REVISION"
    properties: CloudRunServiceToRevisionRelProperties = (
        CloudRunServiceToRevisionRelProperties()
    )


@dataclass(frozen=True)
class CloudRunRevisionToServiceAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
class CloudRunRevisionToServiceAccountRel(CartographyRelSchema):
    target_node_label: str = "GCPServiceAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"email": PropertyRef("service_account_email")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_SERVICE_ACCOUNT"
    properties: CloudRunRevisionToServiceAccountRelProperties = (
        CloudRunRevisionToServiceAccountRelProperties()
    )


@dataclass(frozen=True)
class GCPCloudRunRevisionSchema(CartographyNodeSchema):
    """A Google Cloud Cloud Run Revision resource."""

    label: str = "GCPCloudRunRevision"
    properties: GCPCloudRunRevisionProperties = GCPCloudRunRevisionProperties()
    sub_resource_relationship: ProjectToCloudRunRevisionRel = (
        ProjectToCloudRunRevisionRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            CloudRunServiceToRevisionRel(),
            CloudRunRevisionToServiceAccountRel(),
        ],
    )
