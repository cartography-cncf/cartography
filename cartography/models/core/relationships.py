import abc
from dataclasses import dataclass
from dataclasses import field
from dataclasses import make_dataclass
from enum import auto
from enum import Enum
from typing import Dict
from typing import List

from cartography.models.core.common import PropertyRef


class LinkDirection(Enum):
    """
    Enum defining the direction of relationships in CartographyRelSchema.

    Each CartographyRelSchema has a LinkDirection that determines whether the relationship
    points toward the original node ("INWARD") or away from the original node ("OUTWARD").
    This controls the directionality of the Neo4j relationship arrows.

    Attributes:
        INWARD: The relationship points toward the original node (incoming).
        OUTWARD: The relationship points away from the original node (outgoing).
    """

    INWARD = auto()
    OUTWARD = auto()


@dataclass(frozen=True)
class CartographyRelProperties(abc.ABC):
    """
    Abstract base class representing properties on a CartographyRelSchema.

    This abstract class enforces that all subclasses will have a lastupdated field
    defined on their resulting relationships. These fields are assigned to the
    relationship in the Neo4j SET clause during graph operations.

    Attributes:
        lastupdated: A PropertyRef to the update tag of the relationship.

    Required Properties for MatchLink Usage:
        When the CartographyRelSchema is used as a MatchLink, the following
        properties must be defined in subclasses:

        - lastupdated: A PropertyRef to the update tag of the relationship.
        - _sub_resource_label: A PropertyRef to the label of the sub-resource
          that the relationship is associated with.
        - _sub_resource_id: A PropertyRef to the id of the sub-resource that
          the relationship is associated with.

    Examples:
        >>> @dataclass(frozen=True)
        ... class MyRelProperties(CartographyRelProperties):
        ...     lastupdated: PropertyRef = PropertyRef('lastupdated')
        ...     custom_field: PropertyRef = PropertyRef('custom_field')

    Note:
        This class cannot be instantiated directly. It must be subclassed.
        The `firstseen` attribute is reserved and automatically set by the
        querybuilder, so it cannot be used as a custom attribute name.
    """

    lastupdated: PropertyRef = field(init=False)

    def __post_init__(self):
        """
        Perform data validation on CartographyRelProperties instances.

        This method enforces two important validation rules:
        1. Prevents direct instantiation of the abstract base class
        2. Prevents use of reserved attribute names

        Raises:
            TypeError: If attempting to instantiate the abstract base class directly,
                      or if using reserved attribute names like 'firstseen'.

        Note:
            This workaround is needed since this is both a dataclass and an abstract
            class without an abstract method defined. See https://stackoverflow.com/q/60590442.

            The `firstseen` attribute is reserved because it's automatically set by
            the querybuilder on cartography relationships.
        """
        if self.__class__ == CartographyRelProperties:
            raise TypeError("Cannot instantiate abstract class.")

        if hasattr(self, "firstseen"):
            raise TypeError(
                "`firstseen` is a reserved word and is automatically set by the querybuilder on cartography rels, so "
                f'it cannot be used on class "{type(self).__name__}(CartographyRelProperties)". Please either choose '
                "a different name for `firstseen` or omit altogether.",
            )


@dataclass(frozen=True)
class TargetNodeMatcher:
    """
    Encapsulates node matching criteria for target nodes in relationships.

    This dataclass is used to define the mapping between attribute names on the
    target node and their corresponding PropertyRef values. It ensures immutability
    when composed as part of a CartographyNodeSchema object.

    The class serves as a base template that is dynamically extended by
    `make_target_node_matcher()` to create specific matching criteria.

    Attributes:
        Dynamically created by `make_target_node_matcher()` based on the
        key_ref_dict parameter. Each key becomes an attribute with a PropertyRef value.

    Examples:
        Creating a matcher for AWS Account nodes:
        >>> from cartography.models.core.common import PropertyRef
        >>> matcher = make_target_node_matcher({
        ...     'id': PropertyRef('AccountId'),
        ...     'arn': PropertyRef('Arn')
        ... })

        The resulting matcher will have `id` and `arn` attributes with
        the corresponding PropertyRef values.

    Note:
        This class is not meant to be instantiated directly. Use
        `make_target_node_matcher()` to create instances with the required
        attributes for specific use cases.
    """

    pass


def make_target_node_matcher(key_ref_dict: Dict[str, PropertyRef]) -> TargetNodeMatcher:
    """
    Create a TargetNodeMatcher with dynamically generated attributes.

    This function creates a specialized TargetNodeMatcher dataclass with attributes
    corresponding to the keys in the provided dictionary. Each attribute is
    initialized with its corresponding PropertyRef value.

    Args:
        key_ref_dict: A dictionary mapping attribute names to PropertyRef objects.
                     The keys become attribute names on the target node, and the
                     values are PropertyRef objects that define how to extract
                     the matching values from the data.

    Returns:
        A TargetNodeMatcher instance with dynamically created attributes
        corresponding to the provided key_ref_dict.

    Examples:
        Creating a matcher for AWS EC2 instances:
        >>> from cartography.models.core.common import PropertyRef
        >>> matcher = make_target_node_matcher({
        ...     'instanceid': PropertyRef('InstanceId'),
        ...     'region': PropertyRef('Region')
        ... })
        >>> # The resulting matcher has instanceid and region attributes

        Creating a matcher for a single key:
        >>> matcher = make_target_node_matcher({
        ...     'id': PropertyRef('Id')
        ... })
        >>> # The resulting matcher has an id attribute
    """
    fields = [
        (key, PropertyRef, field(default=prop_ref))
        for key, prop_ref in key_ref_dict.items()
    ]
    return make_dataclass(TargetNodeMatcher.__name__, fields, frozen=True)()


@dataclass(frozen=True)
class SourceNodeMatcher:
    """
    Encapsulates node matching criteria for source nodes in relationships.

    This dataclass is identical to TargetNodeMatcher but specifically designed
    for matching source nodes. It is used exclusively with load_matchlinks()
    operations where relationships are created between existing nodes.

    The class serves as a base template that is dynamically extended by
    `make_source_node_matcher()` to create specific matching criteria.

    Examples:
        Creating a matcher for EC2 instance source nodes:
        >>> from cartography.models.core.common import PropertyRef
        >>> matcher = make_source_node_matcher({
        ...     'instanceid': PropertyRef('InstanceId'),
        ...     'account_id': PropertyRef('AccountId')
        ... })

        The resulting matcher will have `instanceid` and `account_id` attributes
        with the corresponding PropertyRef values.

    Note:
        This class is only used for load_matchlinks() operations where we match
        on and connect existing nodes. It has no effect on CartographyRelSchema
        objects that are included in CartographyNodeSchema.

        Use `make_source_node_matcher()` to create instances with the required
        attributes for specific use cases.
    """

    pass


def make_source_node_matcher(key_ref_dict: Dict[str, PropertyRef]) -> SourceNodeMatcher:
    """
    Create a SourceNodeMatcher with dynamically generated attributes.

    This function creates a specialized SourceNodeMatcher dataclass with attributes
    corresponding to the keys in the provided dictionary. Each attribute is
    initialized with its corresponding PropertyRef value.

    Args:
        key_ref_dict: A dictionary mapping attribute names to PropertyRef objects.
                     The keys become attribute names on the source node, and the
                     values are PropertyRef objects that define how to extract
                     the matching values from the data.

    Returns:
        A SourceNodeMatcher instance with dynamically created attributes
        corresponding to the provided key_ref_dict.
    """
    fields = [
        (key, PropertyRef, field(default=prop_ref))
        for key, prop_ref in key_ref_dict.items()
    ]
    return make_dataclass(SourceNodeMatcher.__name__, fields, frozen=True)()


@dataclass(frozen=True)
class CartographyRelSchema(abc.ABC):
    """
    Abstract base class representing a cartography relationship schema.

    This class defines the structure and behavior of relationships in the cartography
    data model. It contains all the necessary properties to connect a CartographyNodeSchema
    to other existing nodes in the Neo4j graph database.

    The CartographyRelSchema is used to define how nodes should be connected,
    including the direction of the relationship, the target node criteria,
    and the properties to be set on the relationship.

    Note:
        This is an abstract base class and cannot be instantiated directly.
        All abstract properties must be implemented by concrete subclasses.

        The dataclass is frozen to ensure immutability when used in
        CartographyNodeSchema objects.
    """

    @property
    @abc.abstractmethod
    def properties(self) -> CartographyRelProperties:
        """
        Properties to be set on the relationship.

        This property defines the CartographyRelProperties instance that contains
        all the attributes to be assigned to the relationship in the Neo4j SET clause.

        Returns:
            A CartographyRelProperties instance containing the relationship properties.
        """
        pass

    @property
    @abc.abstractmethod
    def target_node_label(self) -> str:
        """
        Label of the target node for this relationship.

        This property defines the Neo4j node label that this relationship will
        connect to. The target node must already exist in the graph database.

        Returns:
            The string label of the target node type.
        """
        pass

    @property
    @abc.abstractmethod
    def target_node_matcher(self) -> TargetNodeMatcher:
        """
        Matcher used to identify target nodes for this relationship.

        This property defines the TargetNodeMatcher that specifies how to find
        the target nodes that this relationship should connect to. The matcher
        contains the keys and PropertyRef values used to identify unique target nodes.

        Returns:
            A TargetNodeMatcher instance with the matching criteria.

        Note:
            Use `make_target_node_matcher()` to create the matcher with the appropriate
            key-value pairs for your specific use case.
        """
        pass

    @property
    @abc.abstractmethod
    def rel_label(self) -> str:
        """
        Label of the relationship.

        This property defines the Neo4j relationship type that will be created
        between the source and target nodes. The label appears in the Neo4j
        relationship syntax as [:LABEL].

        Returns:
            The string label of the relationship type.
        """
        pass

    @property
    @abc.abstractmethod
    def direction(self) -> LinkDirection:
        """
        Direction of the relationship.

        This property defines the LinkDirection that determines whether the
        relationship arrow points toward the source node (INWARD) or away
        from the source node (OUTWARD).

        Returns:
            A LinkDirection enum value specifying the relationship direction.

        Note:
            Please see the LinkDirection enum documentation for detailed explanations
            of how direction affects the resulting Neo4j relationship patterns.
        """
        pass

    @property
    def source_node_label(self) -> str | None:
        """
        Source node label for load_matchlinks() operations.

        This optional property is only used with load_matchlinks() operations
        where relationships are created between existing nodes. It specifies
        the Neo4j node label of the source node for the relationship.

        Returns:
            The string label of the source node type, or None if not applicable.
            Default implementation returns None.

        Note:
            This property does not affect CartographyRelSchema objects that are
            included in CartographyNodeSchema objects. It is only relevant for
            standalone relationship creation using load_matchlinks().
        """
        return None

    @property
    def source_node_matcher(self) -> SourceNodeMatcher | None:
        """
        Source node matcher for load_matchlinks() operations.

        This optional property is only used with load_matchlinks() operations
        where relationships are created between existing nodes. It specifies
        the SourceNodeMatcher that defines how to identify the source nodes
        for the relationship.

        Note:
            This property does not affect CartographyRelSchema objects that are
            included in CartographyNodeSchema objects. It is only relevant for
            standalone relationship creation using load_matchlinks().

            Use `make_source_node_matcher()` to create the matcher with the
            appropriate key-value pairs for your specific use case.
        """
        return None


@dataclass(frozen=True)
class OtherRelationships:
    """
    Encapsulates a list of CartographyRelSchema objects for additional relationships.

    This dataclass is used to group multiple CartographyRelSchema objects together
    while ensuring dataclass immutability when composed as part of a CartographyNodeSchema
    object. It allows a node schema to define multiple additional relationships
    beyond the primary sub_resource_relationship.

    Attributes:
        rels: A list of CartographyRelSchema objects representing additional relationships.

    Examples:
        Creating additional relationships for an EC2 instance:
        >>> other_rels = OtherRelationships(rels=[
        ...     EC2InstanceToVPCRel(),
        ...     EC2InstanceToSecurityGroupRel(),
        ...     EC2InstanceToSubnetRel()
        ... ])

        Using in a CartographyNodeSchema:
        >>> class EC2InstanceSchema(CartographyNodeSchema):
        ...     other_relationships: OtherRelationships = other_rels
    """

    rels: List[CartographyRelSchema]
