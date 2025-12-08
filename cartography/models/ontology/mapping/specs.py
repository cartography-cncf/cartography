from dataclasses import dataclass
from dataclasses import field
from typing import Any


@dataclass(frozen=True)
class OntologyFieldMapping:
    """Mapping between an ontology field and a module's node field.

    Attributes:
        ontology_field: The field name in the ontology.
        node_field: The corresponding field name in the module's node.
        required: Whether this field is required to create an ontology node or not.
        special_handling: Any special handling required for this field (e.g., "invert_boolean").
        extra: Additional info that may be relevant for this mapping (only used for specific special_handling).

    Available special_handling options:
        - "invert_boolean": Inverts the boolean value of the field (e.g., True becomes False and vice versa).
        - "to_boolean": Converts the field value to a boolean, treating any non-null value as True.
        - "or_boolean": Combines multiple boolean fields (provided in extra['fields']) using a logical OR operation .
        - "nor_boolean": Combines multiple boolean fields (provided in extra['fields']) using a logical NOR operation .
        - "equal_boolean": Compares the field value to a specified boolean value (True/False) provided in extra['value'].
        - "static_value": Sets a static value for the ontology field (provided in extra['value']), ignoring node_field.

    Example:
        OntologyFieldMapping(ontology_field="email", node_field="email_address", required=True)
        This mapping indicates that the 'email' field in the ontology corresponds to the 'email_address' field in the module's node and is required.
        So {"id": "123", "email_address": "<email_value>"} can be mapped to an ontology node, but {"id": "123"} cannot.
    """

    ontology_field: str
    node_field: str
    required: bool = False
    special_handling: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class OntologyNodeMapping:
    """Mapping for a node in the ontology.

    Attributes:
        node_label: The label of the ontology node.
        fields: A list of OntologyFieldMapping defining the field mappings for this node.
        eligible_for_source: Whether this node mapping is eligible to create a new node.

    Note:
        By default, all node mappings are eligible to create new nodes unless specified otherwise.
        Eligibility should be set to False if required fields are not sufficient to create a valid ontology node.
        For instance if a AccountUser node does not have an email field mapped, it cannot be created as an ontology User node.
    """

    node_label: str
    fields: list[OntologyFieldMapping]
    eligible_for_source: bool = True


@dataclass(frozen=True)
class OntologyRelMapping:
    """Mapping for a relationship in the ontology.

    Attributes:
        query: The query used to retrieve this relationship.
        iterative: Whether this relationship requires batch processing (iterative) or can be created in a single query.
        __comment__: An optional comment about this relationship.
    """

    query: str
    iterative: bool = False
    __comment__: str | None = None


@dataclass(frozen=True)
class OntologyMapping:
    """Ontology mapping for a specific module.

    Attributes:
        module_name: The name of the module.
        nodes: A list of OntologyNodeMapping defining the nodes for this module.
        rels: A list of OntologyRelMapping defining the relationships for this module.
    """

    module_name: str
    nodes: list[OntologyNodeMapping]
    rels: list[OntologyRelMapping] = field(default_factory=list)
