from typing import cast

import neo4j

from cartography.client.core.tx import read_list_of_values_tx
from cartography.client.core.tx import read_single_value_tx
from cartography.util import timeit


@timeit
def list_entra_application_ids(neo4j_session: neo4j.Session) -> list[str]:
    """
    Return Entra application IDs currently present in the graph.

    :param neo4j_session: The neo4j session object.
    :return: A list of Entra application app_id values.
    """
    query = """
    MATCH (app:EntraApplication)
    RETURN app.app_id
    """
    return cast(list[str], neo4j_session.execute_read(read_list_of_values_tx, query))


@timeit
def get_entra_service_principal_id_for_app(
    neo4j_session: neo4j.Session,
    app_id: str,
) -> str | None:
    """
    Return the Entra service principal ID associated with an application.

    :param neo4j_session: The neo4j session object.
    :param app_id: The Entra application app_id value.
    :return: The Entra service principal node ID, if present.
    """
    query = """
    MATCH (sp:EntraServicePrincipal {app_id: $app_id})
    RETURN sp.id as service_principal_id
    """
    return cast(
        str | None,
        neo4j_session.execute_read(
            read_single_value_tx,
            query,
            app_id=app_id,
        ),
    )
