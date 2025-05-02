from string import Template
from typing import Any
from typing import List
from typing import Optional
from typing import Set
from typing import Tuple

import neo4j


def check_nodes(
    neo4j_session: neo4j.Session,
    node_label: str,
    attrs: List[str],
) -> Optional[Set[Tuple[Any, ...]]]:
    """
    Helper function for checking nodes in cartography integration tests.
    Returns the result of a neo4j match query on the given node label and the given list of attributes as a set of
    tuples.
    """
    if not attrs:
        raise ValueError(
            "`attrs` passed to check_nodes() must have at least one element.",
        )

    attrs = ", ".join(f"n.{attr}" for attr in attrs)
    query_template = Template("MATCH (n:$NodeLabel) RETURN $Attrs")
    result = neo4j_session.run(
        query_template.safe_substitute(NodeLabel=node_label, Attrs=attrs),
    )
    return {tuple(row.values()) for row in result}


def check_rels(
    neo4j_session: neo4j.Session,
    node_1_label: str,
    node_1_attr: str,
    node_2_label: str,
    node_2_attr: str,
    rel_label: str,
    rel_direction_right: Optional[bool] = True,
) -> Set[Tuple]:
    """
    Helper function to test a given relationship between node 1 and node 2.
    Returns the result of a neo4j match query as a set of tuples when given the node labels of 2 nodes, an attribute to
    return from each of them, the label of the relationship between them, and the direction of that relationship.
    :param neo4j_session: The neo4j session
    :param node_1_label: The label of the first node to check
    :param node_1_attr: The attribute of the first node to check
    :param node_2_label: The label of the second node to check
    :param node_2_attr: The attribute of the second node to check
    :param rel_label: The str label of the relationship between node 1 and node 2.
    :param rel_direction_right: The direction of the node is to the right (default=True). Else it is to the left.
    :return: A set of tuples with the shape {(n1.node_1_attr, n2.node_2_attr), ...}
    """
    relationship = (
        f"-[r:{rel_label}]->" if rel_direction_right else f"<-[r:{rel_label}]-"
    )

    query_template = Template(
        "MATCH (n1:$Node1Label)$Rel(n2:$Node2Label) RETURN n1.$Node1Attr, n2.$Node2Attr;",
    )
    query = query_template.safe_substitute(
        Node1Label=node_1_label,
        Rel=relationship,
        Node2Label=node_2_label,
        Node1Attr=node_1_attr,
        Node2Attr=node_2_attr,
    )
    result = neo4j_session.run(query)
    return {(r[f"n1.{node_1_attr}"], r[f"n2.{node_2_attr}"]) for r in result}
