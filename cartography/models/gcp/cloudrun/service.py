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
class GCPCloudRunServiceProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Stable identifier for this resource."
    )
    name: PropertyRef = PropertyRef("name", description="Short name of the service.")
    description: PropertyRef = PropertyRef(
        "description", description="User-provided description of the service."
    )
    location: PropertyRef = PropertyRef(
        "location", description="The GCP location where the service is deployed."
    )
    uri: PropertyRef = PropertyRef(
        "uri", description="Default URL serving the service."
    )
    latest_ready_revision: PropertyRef = PropertyRef(
        "latest_ready_revision",
        description="Full resource name of the latest ready revision for this service.",
    )
    service_account_email: PropertyRef = PropertyRef(
        "service_account_email",
        description="The email of the service account configured on the service template (used by new revisions created from this service).",
    )
    project_id: PropertyRef = PropertyRef(
        "project_id", description="Google Cloud project that owns this resource."
    )
    ingress: PropertyRef = PropertyRef(
        "ingress",
        description="The ingress setting for the service. Values: `INGRESS_TRAFFIC_ALL`, `INGRESS_TRAFFIC_INTERNAL_ONLY`, `INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER`, `INGRESS_TRAFFIC_NONE`.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )


@dataclass(frozen=True)
class ProjectToCloudRunServiceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
class ProjectToCloudRunServiceRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("project_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ProjectToCloudRunServiceRelProperties = (
        ProjectToCloudRunServiceRelProperties()
    )


@dataclass(frozen=True)
class CloudRunServiceToServiceAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
# DEPRECATED: replaced by the canonical (:ComputeService)-[:RUNS_AS]->(:ServiceAccount)
# edge (CloudRunServiceToServiceAccountRunsAsRel). Kept for backward
# compatibility, will be removed in v1.0.0.
class CloudRunServiceToServiceAccountRel(CartographyRelSchema):
    target_node_label: str = "GCPServiceAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"email": PropertyRef("service_account_email")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_SERVICE_ACCOUNT"
    properties: CloudRunServiceToServiceAccountRelProperties = (
        CloudRunServiceToServiceAccountRelProperties()
    )


@dataclass(frozen=True)
class CloudRunServiceToServiceAccountRunsAsRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
# Canonical ontology edge: (:ComputeService)-[:RUNS_AS]->(:ServiceAccount)
class CloudRunServiceToServiceAccountRunsAsRel(CartographyRelSchema):
    target_node_label: str = "GCPServiceAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"email": PropertyRef("service_account_email")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RUNS_AS"
    properties: CloudRunServiceToServiceAccountRunsAsRelProperties = (
        CloudRunServiceToServiceAccountRunsAsRelProperties()
    )


@dataclass(frozen=True)
class GCPCloudRunServiceSchema(CartographyNodeSchema):
    """Representation of a GCP [Cloud Run Service](https://cloud.google.com/run/docs/reference/rest/v2/projects.locations.services)."""

    label: str = "GCPCloudRunService"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["ComputeService"])
    properties: GCPCloudRunServiceProperties = GCPCloudRunServiceProperties()
    sub_resource_relationship: ProjectToCloudRunServiceRel = (
        ProjectToCloudRunServiceRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            CloudRunServiceToServiceAccountRel(),
            CloudRunServiceToServiceAccountRunsAsRel(),
        ],
    )
