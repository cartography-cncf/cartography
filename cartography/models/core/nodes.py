import abc
from dataclasses import dataclass
from dataclasses import field
from typing import List
from typing import Optional

from cartography.models.core.common import PropertyRef
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import OtherRelationships


@dataclass(frozen=True)
class CartographyNodeProperties(abc.ABC):
    """
    Abstract base dataclass that represents the properties on a CartographyNodeSchema.

    This class is abstract to enforce that all subclasses have an id and a lastupdated field.
    These fields are assigned to the node in the `SET` clause during Neo4j ingestion.

    Attributes:
        id (PropertyRef): The unique identifier for the node, set automatically.
        lastupdated (PropertyRef): The timestamp of the last update, set automatically.

    Examples:
        >>> @dataclass(frozen=True)
        ... class AWSUserProperties(CartographyNodeProperties):
        ...     id: PropertyRef = PropertyRef('Arn')
        ...     lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)
        ...     name: PropertyRef = PropertyRef('UserName')
        ...     path: PropertyRef = PropertyRef('Path')

        >>> # Cannot instantiate abstract class directly
        >>> CartographyNodeProperties()  # Raises TypeError

        >>> # Cannot use reserved word 'firstseen'
        >>> @dataclass(frozen=True)
        ... class BadProperties(CartographyNodeProperties):
        ...     firstseen: PropertyRef = PropertyRef('firstseen')  # Raises TypeError

    Note:
        - The `firstseen` attribute is reserved and automatically set by the querybuilder
        - All subclasses must define both `id` and `lastupdated` fields
        - This class cannot be instantiated directly
    """

    id: PropertyRef = field(init=False)
    lastupdated: PropertyRef = field(init=False)

    def __post_init__(self):
        """
        Perform data validation on the CartographyNodeProperties instance.

        This method enforces important constraints to ensure proper usage of the
        CartographyNodeProperties class and prevent common errors.

        Raises:
            TypeError: If attempting to instantiate the abstract class directly.
            TypeError: If the reserved word 'firstseen' is used as an attribute name.
        """
        if self.__class__ == CartographyNodeProperties:
            raise TypeError("Cannot instantiate abstract class.")

        if hasattr(self, "firstseen"):
            raise TypeError(
                "`firstseen` is a reserved word and is automatically set by the querybuilder on cartography nodes, so "
                f'it cannot be used on class "{type(self).__name__}(CartographyNodeProperties)". Please either choose '
                "a different name for `firstseen` or omit altogether.",
            )


@dataclass(frozen=True)
class ExtraNodeLabels:
    """
    Encapsulates a list of strings representing additional labels for the CartographyNodeSchema.

    This wrapper class is used to ensure dataclass immutability for the CartographyNodeSchema
    while providing additional Neo4j labels beyond the primary node label.

    Attributes:
        labels (List[str]): A list of string labels to be applied to the node.

    Examples:
        >>> # AWS resources with additional labels
        >>> extra_labels = ExtraNodeLabels(['Resource', 'AWSResource'])
    """

    labels: List[str]


@dataclass(frozen=True)
class CartographyNodeSchema(abc.ABC):
    """
    Abstract base dataclass that represents a graph node in cartography.

    This class is used to dynamically generate graph ingestion queries for Neo4j.
    It defines the structure and relationships of nodes in the cartography graph,
    providing a declarative way to specify how data should be ingested.

    Note:
        - Subclasses must implement the abstract properties: `label` and `properties`
        - Optional properties can be overridden to specify relationships and labels
    """

    @property
    @abc.abstractmethod
    def label(self) -> str:
        """
        Primary string label of the node.

        This property defines the main Neo4j label that will be applied to nodes
        of this type. It's used in the MERGE clause during ingestion.

        Returns:
            The primary label for the node (e.g., 'AWSUser', 'EC2Instance').
        """

    @property
    @abc.abstractmethod
    def properties(self) -> CartographyNodeProperties:
        """
        Properties of the node.

        This property defines all the properties that will be set on the node
        during ingestion, including how they map to the source data.

        Returns:
            CartographyNodeProperties: The properties definition for the node.
        """

    @property
    def sub_resource_relationship(self) -> Optional[CartographyRelSchema]:
        """
        The optional sub resource relationship for the node.

        Allows subclasses to specify a subresource relationship for the given node.
        "Sub resource" is a cartography term for the billing or organizational unit
        that contains the resource.

        Returns:
            Optional[CartographyRelSchema]: The sub resource relationship schema,
                or None if no sub resource relationship is defined.

        Examples:
            Sub resource examples by cloud provider:
            - AWS: AWSAccount
            - Azure: Subscription
            - GCP: GCPProject
            - Okta: OktaOrganization
        """
        return None

    @property
    def other_relationships(self) -> Optional[OtherRelationships]:
        """
        Optional additional cartography relationships on the node.

        Allows subclasses to specify additional relationships beyond the sub resource
        relationship. These relationships connect the node to other nodes in the graph.

        Returns:
            Optional[OtherRelationships]: The additional relationships for the node,
                or None if no additional relationships are defined.
        """
        return None

    @property
    def extra_node_labels(self) -> Optional[ExtraNodeLabels]:
        """
        Optional extra labels to be applied to the node.

        Allows specifying additional Neo4j labels beyond the primary label.
        This is useful for creating taxonomies or adding classification labels.

        Returns:
            Optional[ExtraNodeLabels]: The extra labels for the node,
                or None if no extra labels are defined.
        """
        return None

    @property
    def scoped_cleanup(self) -> bool:
        """
        Whether cleanups of this node must be scoped to the sub resource relationship.

        This property controls the cleanup behavior for nodes of this type during
        synchronization operations.

        Returns:
            bool: True if cleanups should be scoped to the sub resource (default),
                False if cleanups should be global.

        Note:
            - If True (default): Only delete stale nodes in the current sub resource
              (e.g., only clean up EC2 instances in the current AWS account)
            - If False: Delete all stale nodes globally (designed for resource types
              that don't have a "tenant"-like entity)
            - This affects how the cleanup queries are generated
        """
        return True
