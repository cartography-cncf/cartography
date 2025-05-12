from dataclasses import dataclass
from typing import Optional

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
class TestComputerToPersonRelProps(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class TestComputerToPersonRel(CartographyRelSchema):
    """
    (:TestComputer)<-[:OWNS]-(:Person)
    """

    target_node_label: str = "Person"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "first_name": PropertyRef("FirstName"),
            "last_name": PropertyRef("LastName"),
        },
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "OWNS"
    properties: TestComputerToPersonRelProps = TestComputerToPersonRelProps()


# Test defining a simple node with no relationships.
@dataclass(frozen=True)
class TestComputerProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("Id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    ram_gb: PropertyRef = PropertyRef("RAM_GB")
    num_cores: PropertyRef = PropertyRef("NumCores")
    name: PropertyRef = PropertyRef("name")


@dataclass(frozen=True)
class TestComputer(CartographyNodeSchema):
    label: str = "TestComputer"
    properties: TestComputerProperties = TestComputerProperties()
    other_relationships: Optional[OtherRelationships] = OtherRelationships(
        [TestComputerToPersonRel()],
    )
