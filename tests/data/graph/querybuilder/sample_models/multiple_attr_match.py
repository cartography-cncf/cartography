from dataclasses import dataclass
from typing import Optional

from cartography.graph.model import CartographyNodeProperties
from cartography.graph.model import CartographyNodeSchema
from cartography.graph.model import CartographyRelProperties
from cartography.graph.model import CartographyRelSchema
from cartography.graph.model import LinkDirection
from cartography.graph.model import OtherRelationships
from cartography.graph.model import PropertyRef
from cartography.graph.model import TargetNodeMatcher


@dataclass
class TestComputerToPersonRelProps(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass
class TestComputerToPersonRel(CartographyRelSchema):
    """
    (:TestComputer)<-[:OWNS]-(:Person)
    """
    target_node_label: str = 'Person'
    target_node_matcher: TargetNodeMatcher = TargetNodeMatcher(
        {
            'first_name': PropertyRef('FirstName'),
            'last_name': PropertyRef('LastName'),
        },
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "OWNS"
    properties: TestComputerToPersonRelProps = TestComputerToPersonRelProps()


# Test defining a simple node with no relationships.
@dataclass
class TestComputerProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('Id')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)
    ram_gb: PropertyRef = PropertyRef('RAM_GB')
    num_cores: PropertyRef = PropertyRef('NumCores')
    name: PropertyRef = PropertyRef('name')


@dataclass
class TestComputer(CartographyNodeSchema):
    label: str = 'TestComputer'
    properties: TestComputerProperties = TestComputerProperties()
    other_relationships: Optional[OtherRelationships] = OtherRelationships([TestComputerToPersonRel()])
