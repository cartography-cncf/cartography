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
class GCPSecretManagerSecretVersionNodeProperties(CartographyNodeProperties):
    """
    Properties for GCP Secret Manager Secret Version
    """

    id: PropertyRef = PropertyRef(
        "id", description="Stable identifier for this resource."
    )
    secret_id: PropertyRef = PropertyRef(
        "secret_id", description="Full resource name of the parent secret."
    )
    version: PropertyRef = PropertyRef(
        "version", description='The version number (e.g., "1", "2").'
    )
    state: PropertyRef = PropertyRef(
        "state",
        description="The current state of the version: `ENABLED`, `DISABLED`, or `DESTROYED`.",
    )

    # Date properties (epoch timestamps)
    created_date: PropertyRef = PropertyRef(
        "created_date", description="Epoch timestamp when the version was created."
    )
    destroy_time: PropertyRef = PropertyRef(
        "destroy_time",
        description="Epoch timestamp when the version was destroyed (only present if state is `DESTROYED`).",
    )

    # Other properties
    etag: PropertyRef = PropertyRef(
        "etag", description="Used to perform consistent read-modify-write updates."
    )

    # Standard cartography properties
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )


@dataclass(frozen=True)
class GCPSecretManagerSecretVersionRelProperties(CartographyRelProperties):
    """
    Properties for relationships between Secret Version and other nodes
    """

    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
class GCPSecretManagerSecretVersionToProjectRel(CartographyRelSchema):
    """Indicates that a GCP project contains this Secret Manager secret version as a resource."""

    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPSecretManagerSecretVersionRelProperties = (
        GCPSecretManagerSecretVersionRelProperties()
    )


@dataclass(frozen=True)
class GCPSecretManagerSecretVersionToSecretRel(CartographyRelSchema):
    """Indicates that this Secret Manager secret version is a version of its parent secret."""

    target_node_label: str = "GCPSecretManagerSecret"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("secret_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "VERSION_OF"
    properties: GCPSecretManagerSecretVersionRelProperties = (
        GCPSecretManagerSecretVersionRelProperties()
    )


@dataclass(frozen=True)
class GCPSecretManagerSecretVersionSchema(CartographyNodeSchema):
    """Representation of a GCP [Secret Manager Secret Version](https://cloud.google.com/secret-manager/docs/reference/rest/v1/projects.secrets.versions). A SecretVersion stores a specific version of secret data within a Secret."""

    label: str = "GCPSecretManagerSecretVersion"
    properties: GCPSecretManagerSecretVersionNodeProperties = (
        GCPSecretManagerSecretVersionNodeProperties()
    )
    sub_resource_relationship: GCPSecretManagerSecretVersionToProjectRel = (
        GCPSecretManagerSecretVersionToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GCPSecretManagerSecretVersionToSecretRel(),
        ],
    )
