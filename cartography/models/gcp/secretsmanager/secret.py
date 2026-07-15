from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class GCPSecretManagerSecretNodeProperties(CartographyNodeProperties):
    """
    Properties for GCP Secret Manager Secret
    """

    id: PropertyRef = PropertyRef(
        "id", description="Stable identifier for this resource."
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="The short name of the secret."
    )
    project_id: PropertyRef = PropertyRef(
        "project_id", description="The GCP project ID that owns this secret."
    )
    rotation_enabled: PropertyRef = PropertyRef(
        "rotation_enabled",
        description="Boolean indicating if automatic rotation is configured.",
    )
    rotation_period: PropertyRef = PropertyRef(
        "rotation_period",
        description="The rotation period in seconds (if rotation is enabled).",
    )
    rotation_next_time: PropertyRef = PropertyRef(
        "rotation_next_time",
        description="Epoch timestamp of the next scheduled rotation.",
    )
    created_date: PropertyRef = PropertyRef(
        "created_date", description="Epoch timestamp when the secret was created."
    )
    expire_time: PropertyRef = PropertyRef(
        "expire_time",
        description="Epoch timestamp when the secret will automatically expire and be deleted.",
    )
    replication_type: PropertyRef = PropertyRef(
        "replication_type",
        description="The replication policy type: `automatic` or `user_managed`.",
    )
    etag: PropertyRef = PropertyRef(
        "etag", description="Used to perform consistent read-modify-write updates."
    )
    labels: PropertyRef = PropertyRef(
        "labels", description="JSON string of user-defined labels."
    )
    topics: PropertyRef = PropertyRef(
        "topics",
        description="JSON string of Pub/Sub topics for rotation notifications.",
    )
    version_aliases: PropertyRef = PropertyRef(
        "version_aliases",
        description="JSON string mapping alias names to version numbers.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )


@dataclass(frozen=True)
class GCPSecretManagerSecretRelProperties(CartographyRelProperties):
    """
    Properties for relationships between Secret and other nodes
    """

    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
class GCPSecretManagerSecretToProjectRel(CartographyRelSchema):
    """
    Relationship between Secret and GCP Project
    (:GCPProject)-[:RESOURCE]->(:GCPSecretManagerSecret)
    """

    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPSecretManagerSecretRelProperties = (
        GCPSecretManagerSecretRelProperties()
    )


@dataclass(frozen=True)
class GCPSecretManagerSecretSchema(CartographyNodeSchema):
    """Representation of a GCP [Secret Manager Secret](https://cloud.google.com/secret-manager/docs/reference/rest/v1/projects.secrets). A Secret is a logical container for secret data that can have multiple versions."""

    label: str = "GCPSecretManagerSecret"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        ["Secret"]
    )  # Secret label is used for ontology mapping
    properties: GCPSecretManagerSecretNodeProperties = (
        GCPSecretManagerSecretNodeProperties()
    )
    sub_resource_relationship: GCPSecretManagerSecretToProjectRel = (
        GCPSecretManagerSecretToProjectRel()
    )
