from dataclasses import dataclass
from typing import ClassVar

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_source_node_matcher
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import MatchLinkSubResource
from cartography.models.core.relationships import SourceNodeMatcher
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.ontology.labels import TAG


@dataclass(frozen=True)
class AWSTagNodeProperties(CartographyNodeProperties):
    """
    Properties for AWSTag nodes.

    The id is computed as "Key:Value" during ingestion, so one tag node is shared by
    every resource, in every account, that carries the same key and value.
    """

    id: PropertyRef = PropertyRef(
        "id", description="Unique identifier for this `AWSTag` node."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    key: PropertyRef = PropertyRef("key", extra_index=True, description="Tag key.")
    value: PropertyRef = PropertyRef("value", description="Tag value.")


@dataclass(frozen=True)
class AWSTagSchema(CartographyNodeSchema):
    """
    Representation of an AWS [Tag](https://docs.aws.amazon.com/resourcegroupstagging/latest/APIReference/API_Tag.html). AWS Tags can be applied to many objects.

    AWSTag has no sub resource because one node is shared across accounts. Its
    TAGGED relationships are loaded with `AWSResourceToTagMatchLink`, which records
    the owning account on each relationship so cleanup stays scoped to one account.

    The TAGGED relationship goes FROM the resource TO the AWSTag:
    (resource)-[:TAGGED]->(AWSTag)
    """

    label: str = "AWSTag"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([TAG])
    properties: AWSTagNodeProperties = AWSTagNodeProperties()
    sub_resource_relationship: None = None


@dataclass(frozen=True)
class AWSResourceToTagRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSResourceToTagMatchLink(CartographyRelSchema):
    """
    An AWS resource is tagged with an `AWSTag`.

    This is a runtime template: the resource label and matcher are filled in from
    `cartography.models.aws_tagging.AWS_TAGGABLE_RESOURCES`, which is also where the
    concrete TAGGED edges are documented.
    """

    __cartography_introspection_exclude__: ClassVar[bool] = True

    source_node_label: str = "AWSEC2Instance"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("resource_id")},
    )
    # Only tag resources owned by the account being synced. Some taggable resources
    # (load balancers) are keyed by a name that is not unique across accounts.
    source_node_sub_resource: MatchLinkSubResource = MatchLinkSubResource(
        target_node_label="AWSAccount",
        target_node_matcher=make_target_node_matcher(
            {"id": PropertyRef("_sub_resource_id", set_in_kwargs=True)},
        ),
        direction=LinkDirection.INWARD,
        rel_label="RESOURCE",
    )
    target_node_label: str = "AWSTag"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("tag_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "TAGGED"
    properties: AWSResourceToTagRelProperties = AWSResourceToTagRelProperties()
