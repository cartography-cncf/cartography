from typing import Any, Dict, List, Type
import logging

import neo4j

from cartography.client.core.tx import load
from cartography.models.common.human import HumanSchema
from cartography.models.core.nodes import CartographyNodeSchema

logger = logging.getLogger(__name__)


def _load_abstracted_nodes(
    neo4j_session: neo4j.Session,
    schema: Type[CartographyNodeSchema],
    update_tag: int,
    data: List[Dict[str, Any]],
    mapping: Dict[str, str],
    id_field: str = "id",
):
    # Because the schema can be different for each node, we need to reformat the data
    # to match the abstract node schema.
    formated_data: List[Dict[str, Any]] = []
    for entity in data:
        formated_entity = entity.copy()
        for k, v in mapping.items():
            if k == v:
                continue
            formated_entity[k] = entity.get(v)
        # We need to check if the id_field is in the mapping
        # For some intel, that field could be missing and lead to errors
        # e.g. Service account in Entra does not have mail
        # e.g. GitHub User could have a private email resulting in a None value
        if formated_entity.get(id_field) is None:
            logger.debug(
                f"Skipping {schema.__name__} node because {id_field} is None: {formated_entity}"
            )
            continue
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
        id_field="email",
    )
