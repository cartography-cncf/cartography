from typing import Any, Dict, List, Type

import neo4j

from cartography.client.core.tx import load
from cartography.models.common.human import HumanSchema
from cartography.models.core.nodes import CartographyNodeSchema


def _load_abstracted_nodes(
    neo4j_session: neo4j.Session,
    schema: Type[CartographyNodeSchema],
    update_tag: int,
    data: List[Dict[str, Any]],
    mapping: Dict[str, str],
):
    # Because the schema can be different for each node, we need to reformat the data
    # to match the abstract node schema.
    formated_data: List[Dict[str, Any]] = []
    for entity in data:
        formated_entity = {}
        for k, v in entity.items():
            formated_entity[mapping.get(k, k)] = v
        formated_data.append(formated_entity)

    load(
        neo4j_session,
        schema(),
        formated_data,
        lastupdated=update_tag,
    )


def load_human_from_users(
    neo4j_session: neo4j.Session,
    update_tag: int,
    data: List[Dict[str, Any]],
    email_field: str = "email",
):
    """
    Load human abstract nodes from a list of users.

    Args:
        neo4j_session: The Neo4j session to use.
        update_tag: The update tag to use.
        data: The list of users to load.
        email_field: The field to use for the email address. Defaults to "email".
    """
    _load_abstracted_nodes(
        neo4j_session,
        HumanSchema,
        update_tag,
        data,
        {"email": email_field},
    )
