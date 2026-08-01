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
class ModalQueueNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Queue ID, e.g. `qu-kbM1N097wnpOSJgRjiwXvk`."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", extra_index=True, description="Queue name.")
    created_at: PropertyRef = PropertyRef(
        "created_at", description="When the Queue was created."
    )
    num_partitions: PropertyRef = PropertyRef(
        "num_partitions", description="Number of partitions, if reported."
    )
    total_size: PropertyRef = PropertyRef(
        "total_size", description="Current queue depth, if reported."
    )
    environment_name: PropertyRef = PropertyRef(
        "environment_name",
        extra_index=True,
        description="Name of the owning environment.",
    )


@dataclass(frozen=True)
class ModalQueueToEnvironmentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ModalEnvironment)-[:RESOURCE]->(:ModalQueue)
class ModalQueueToEnvironmentRel(CartographyRelSchema):
    target_node_label: str = "ModalEnvironment"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ENVIRONMENT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ModalQueueToEnvironmentRelProperties = (
        ModalQueueToEnvironmentRelProperties()
    )


@dataclass(frozen=True)
# A Modal Queue: a distributed FIFO queue scoped to an environment. It carries no ontology
# label; the ontology has no queue/messaging concept, so there is nothing to normalise it to.
# Contents are not enumerated: only the container is inventoried.
class ModalQueueSchema(CartographyNodeSchema):
    """Represents a Modal Queue: a distributed FIFO queue scoped to an environment. Only the container is inventoried; its contents are not enumerated. It carries no ontology label, the ontology having no queue or messaging concept to normalise it to."""

    label: str = "ModalQueue"
    properties: ModalQueueNodeProperties = ModalQueueNodeProperties()
    sub_resource_relationship: ModalQueueToEnvironmentRel = ModalQueueToEnvironmentRel()
