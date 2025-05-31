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
    Abstract base dataclass that represents the properties on a CartographyNodeSchema. This class is abstract so that we
    can enforce that all subclasses have an id and a lastupdated field. These fields are assigned to the node in the
    `SET` clause.
    """

    id: PropertyRef = field(init=False)
    lastupdated: PropertyRef = field(init=False)

    def __post_init__(self):
        """
        Data validation.
        1. Prevents direct instantiation. This workaround is needed since this is a dataclass and an abstract
        class without an abstract method defined. See https://stackoverflow.com/q/60590442.
        2. Stops reserved words from being used as attribute names. See https://github.com/cartography-cncf/cartography/issues/1064.
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
    Encapsulates a list of str representing additional labels for the CartographyNodeSchema that this is composed on.
    This wrapping is used to ensure dataclass immutability for the CartographyNodeSchema.
    """

    labels: List[str]


@dataclass(frozen=True)
class CartographyNodeSchema(abc.ABC):
    """
    Abstract base dataclass that represents a graph node in cartography. This is used to dynamically generate graph
    ingestion queries.
    """

    @property
    @abc.abstractmethod
    def label(self) -> str:
        """
        :return: The primary str label of the node.
        """
        pass

    @property
    @abc.abstractmethod
    def properties(self) -> CartographyNodeProperties:
        """
        :return: The properties of the node.
        """
        pass

    @property
    def sub_resource_relationship(self) -> Optional[CartographyRelSchema]:
        """
        Optional.
        Allows subclasses to specify a subresource relationship for the given node. "Sub resource" is a term we made up
        best defined by examples:
        - In the AWS module, the subresource is an AWSAccount
        - In Azure, the subresource is a Subscription
        - In GCP, the subresource is a GCPProject
        - In Okta, the subresource is an OktaOrganization
        ... and so on and so forth.
        :return:
        """
        return None

    @property
    def other_relationships(self) -> Optional[OtherRelationships]:
        """
        Optional.
        Allows subclasses to specify additional cartography relationships on the node.
        :return: None if not overridden. Else return the node's OtherRelationships.
        """
        return None

    @property
    def extra_node_labels(self) -> Optional[ExtraNodeLabels]:
        """
        Optional.
        Allows specifying extra labels on the node.
        :return: None if not overridden. Else return the ExtraNodeLabels specified on the node.
        """
        return None

    @property
    def scoped_cleanup(self) -> bool:
        """
        Optional.
        Allows specifying whether cleanups of this node must be scoped to the sub resource relationship.
        If True (default), when we clean up nodes of this type, we will only delete stale nodes in the current sub
        resource. This is how our AWS sync behaves.
        If False, when we clean up node of this type, we will delete all stale nodes. This is designed for resource
        types that don't have a "tenant"-like entity.
        :return: True if not overridden. Else return the boolean value specified on the node.
        """
        return True
