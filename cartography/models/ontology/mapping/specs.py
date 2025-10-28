from dataclasses import dataclass
from dataclasses import field


@dataclass(frozen=True)
class OntologyFieldMapping:
    ontology_field: str
    node_field: str


@dataclass(frozen=True)
class OntologyNodeMapping:
    node_label: str
    fields: list[OntologyFieldMapping]


@dataclass(frozen=True)
class OntologyRelMapping:
    query: str
    interative: bool = False
    __comment__: str | None = None


@dataclass(frozen=True)
class OntologyMapping:
    module_name: str
    nodes: list[OntologyNodeMapping]
    rels: list[OntologyRelMapping] = field(default_factory=list)
