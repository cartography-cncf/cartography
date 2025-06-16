from typing import List

import neo4j

from cartography.client.core.tx import read_list_of_values_tx
from cartography.util import timeit


@timeit
def list_accounts(neo4j_session: neo4j.Session) -> List[str]:
    """
    :param neo4j_session: The neo4j session object.
    :return: A list of all AWS account IDs in the graph
    """
    # See https://community.neo4j.com/t/extract-list-of-nodes-and-labels-from-path/13665/4
    query = """
    MATCH (a:AWSAccount) RETURN a.id
    """
    return neo4j_session.read_transaction(read_list_of_values_tx, query)
