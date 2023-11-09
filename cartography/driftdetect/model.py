import logging
from typing import List

logger = logging.getLogger(__name__)


class State:
    """
    The default object which stores query information.

    :type name: String
    :param name: Name of the query.
    :type validation_query: String
    :param validation_query: Actual Cypher query being run.
    :type properties: List of Strings
    :param properties: List of keys in order that the cypher query will return.
    :type results: List of List of Strings
    :param results: List of all results of running the validation query
    """

    def __init__(
            self,
            name: str,
            validation_query: str,
            properties: List[str],
            results: List[List[str]],
    ):

        self.name: str = name
        self.validation_query: str = validation_query
        self.properties: List[str] = properties
        self.results: List[List[str]] = results
