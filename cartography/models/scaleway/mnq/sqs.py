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
from cartography.models.ontology.labels import SECRET


@dataclass(frozen=True)
class ScalewayMnqSqsNamespaceProperties(CartographyNodeProperties):
    # SQS activation has no provider-side ID of its own - it's per (project, region)
    # - so a synthetic `<project id>/<region>` id is used instead.
    id: PropertyRef = PropertyRef(
        "id", description="Synthetic id: `<project id>/<region>`."
    )
    status: PropertyRef = PropertyRef(
        "status", description="SQS activation status (`enabled`, `disabled`, ...)."
    )
    sqs_endpoint_url: PropertyRef = PropertyRef(
        "sqs_endpoint_url", description="SQS-compatible endpoint URL for this project."
    )
    region: PropertyRef = PropertyRef(
        "region", description="Region this SQS namespace lives in."
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Time SQS was activated for this project."
    )
    updated_at: PropertyRef = PropertyRef("updated_at", description="Last update time.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ScalewayMnqSqsNamespaceToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayMnqSqsNamespace)
class ScalewayMnqSqsNamespaceToProjectRel(CartographyRelSchema):
    """Connects `ScalewayProject` to `ScalewayMnqSqsNamespace` through `RESOURCE`."""

    target_node_label: str = "ScalewayProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ScalewayMnqSqsNamespaceToProjectRelProperties = (
        ScalewayMnqSqsNamespaceToProjectRelProperties()
    )


@dataclass(frozen=True)
class ScalewayMnqSqsNamespaceSchema(CartographyNodeSchema):
    """Represents a project's Scaleway Messaging & Queuing SQS-compatible namespace."""

    label: str = "ScalewayMnqSqsNamespace"
    properties: ScalewayMnqSqsNamespaceProperties = ScalewayMnqSqsNamespaceProperties()
    sub_resource_relationship: ScalewayMnqSqsNamespaceToProjectRel = (
        ScalewayMnqSqsNamespaceToProjectRel()
    )


@dataclass(frozen=True)
class ScalewayMnqSqsCredentialProperties(CartographyNodeProperties):
    # The credential's secret_key (its actual bearer credential) is intentionally
    # never read into this node - see cartography/intel/scaleway/mnq/sqs.py.
    id: PropertyRef = PropertyRef(
        "id", extra_index=True, description="Credential unique ID."
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Credential name."
    )
    access_key: PropertyRef = PropertyRef(
        "access_key",
        extra_index=True,
        description="Access key (public identifier, not sensitive alone).",
    )
    can_publish: PropertyRef = PropertyRef(
        "can_publish", description="Whether this credential can publish messages."
    )
    can_receive: PropertyRef = PropertyRef(
        "can_receive", description="Whether this credential can receive messages."
    )
    can_manage: PropertyRef = PropertyRef(
        "can_manage", description="Whether this credential can manage queues."
    )
    region: PropertyRef = PropertyRef(
        "region", description="Region this credential lives in."
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Credential creation date."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="Credential last update date."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ScalewayMnqSqsCredentialToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayMnqSqsCredential)
class ScalewayMnqSqsCredentialToProjectRel(CartographyRelSchema):
    """Connects `ScalewayProject` to `ScalewayMnqSqsCredential` through `RESOURCE`."""

    target_node_label: str = "ScalewayProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ScalewayMnqSqsCredentialToProjectRelProperties = (
        ScalewayMnqSqsCredentialToProjectRelProperties()
    )


@dataclass(frozen=True)
class ScalewayMnqSqsCredentialToNamespaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayMnqSqsNamespace)-[:HAS]->(:ScalewayMnqSqsCredential)
class ScalewayMnqSqsCredentialToNamespaceRel(CartographyRelSchema):
    """Connects `ScalewayMnqSqsNamespace` to `ScalewayMnqSqsCredential` through `HAS`."""

    target_node_label: str = "ScalewayMnqSqsNamespace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("namespace_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS"
    properties: ScalewayMnqSqsCredentialToNamespaceRelProperties = (
        ScalewayMnqSqsCredentialToNamespaceRelProperties()
    )


@dataclass(frozen=True)
class ScalewayMnqSqsCredentialSchema(CartographyNodeSchema):
    """
    An SQS-compatible access credential for Scaleway Messaging & Queuing.

    Scaleway's list API returns each credential's full secret_key alongside its
    metadata. Cartography deliberately ingests only the metadata - see
    cartography/intel/scaleway/mnq/sqs.py for where that secret_key is dropped.
    """

    label: str = "ScalewayMnqSqsCredential"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([SECRET])
    properties: ScalewayMnqSqsCredentialProperties = (
        ScalewayMnqSqsCredentialProperties()
    )
    sub_resource_relationship: ScalewayMnqSqsCredentialToProjectRel = (
        ScalewayMnqSqsCredentialToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [ScalewayMnqSqsCredentialToNamespaceRel()],
    )
