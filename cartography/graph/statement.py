import json
import logging
import os
from pathlib import Path
from typing import Any
from typing import Dict
from typing import Optional
from typing import Union

import neo4j

from cartography.stats import get_stats_client

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)


class GraphStatementJSONEncoder(json.JSONEncoder):
    """
    Support JSON serialization for GraphStatement instances.

    This custom JSON encoder extends the default JSONEncoder to handle
    GraphStatement objects by converting them to dictionaries using their
    as_dict() method.

    Note:
        This encoder only handles GraphStatement objects. All other objects
        are passed to the default JSONEncoder, which may raise TypeError
        for non-serializable objects.
    """

    def default(self, obj):
        if isinstance(obj, GraphStatement):
            return obj.as_dict()
        else:
            # Let the default encoder roll up the exception.
            return json.JSONEncoder.default(self, obj)


# TODO move this cartography.util after we move util.run_*_job to cartography.graph.job.
def get_job_shortname(file_path: Union[Path, str]) -> str:
    """
    Extract the short name from a file path by removing the extension.

    This utility function takes a file path and returns the path without the
    file extension. Note that the directory path is preserved.

    Args:
        file_path (Union[Path, str]): The file path to process, can be a Path object or string.

    Returns:
        str: The file path without extension.

    Examples:
        >>> get_job_shortname("/path/to/my_job.json")
        '/path/to/my_job'
        >>> get_job_shortname("config.yaml")
        'config'
        >>> get_job_shortname(Path("/jobs/data_sync.py"))
        '/jobs/data_sync'

    Note:
        This function is planned to be moved to cartography.util after refactoring
        of the run_*_job functions to cartography.graph.job.
    """
    # Return file path without extension
    return os.path.splitext(file_path)[0]


class GraphStatement:
    """
    A statement that will run against the cartography graph. Statements can query or update the graph.

    This class encapsulates a Neo4j Cypher query along with its parameters and execution
    configuration. It supports both regular and iterative execution modes, and provides
    comprehensive logging and statistics tracking.

    Attributes:
        query (str): The Cypher query to run.
        parameters (Dict[Any, Any]): The parameters to use for the query.
        iterative (bool): Whether the statement is iterative. If True, the statement will be run
            in chunks of size `iterationsize` until no more records are returned.
        iterationsize (int): The size of each chunk for iterative statements.
        parent_job_name (Optional[str]): The name of the parent job this statement belongs to.
        parent_job_sequence_num (Optional[int]): The sequence number of this statement within the parent job.
            This is used for logging and tracking purposes.

    Examples:
        >>> # Simple query statement
        >>> stmt = GraphStatement("MATCH (n:User) RETURN count(n)")
        >>> stmt.run(session)

        >>> # Statement with parameters
        >>> stmt = GraphStatement(
        ...     "MATCH (n:User) WHERE n.name = $name RETURN n",
        ...     parameters={"name": "Alice"}
        ... )

        >>> # Iterative statement for large datasets
        >>> stmt = GraphStatement(
        ...     "MATCH (n:User) SET n.processed = true LIMIT $LIMIT_SIZE",
        ...     iterative=True,
        ...     iterationsize=1000
        ... )

    Note:
        For iterative statements, the query should include a LIMIT clause using the
        $LIMIT_SIZE parameter, which is automatically set to the iterationsize value.
    """

    def __init__(
        self,
        query: str,
        parameters: Optional[Dict[Any, Any]] = None,
        iterative: bool = False,
        iterationsize: int = 0,
        parent_job_name: Optional[str] = None,
        parent_job_sequence_num: Optional[int] = None,
    ):
        """
        Initialize a GraphStatement instance.

        Args:
            query (str): The Cypher query to execute.
            parameters (Optional[Dict[Any, Any]], optional): Parameters to pass to the query.
                Defaults to None (empty dict).
            iterative (bool, optional): Whether to run the statement iteratively in chunks.
                Defaults to False.
            iterationsize (int, optional): Size of each chunk for iterative execution.
                Defaults to 0. Must be > 0 if iterative=True.
            parent_job_name (Optional[str], optional): Name of the parent job for logging.
                Defaults to None.
            parent_job_sequence_num (Optional[int], optional): Sequence number within the parent job.
                Defaults to None (will be set to 1).
        """
        self.query = query
        self.parameters = parameters or {}
        self.iterative = iterative
        self.iterationsize = iterationsize
        if iterationsize < 0:
            raise ValueError(
                f"iterationsize must be a positive integer, got {iterationsize}",
            )
        self.parameters["LIMIT_SIZE"] = self.iterationsize

        self.parent_job_name = parent_job_name if parent_job_name else None
        self.parent_job_sequence_num = (
            parent_job_sequence_num if parent_job_sequence_num else 1
        )

    def merge_parameters(self, parameters: Dict) -> None:
        """
        Merge given parameters with existing parameters.

        This method updates the statement's parameters by merging the provided
        parameters with the existing ones. New parameters will override existing
        ones with the same key.

        Args:
            parameters (Dict): The parameters to merge into the existing parameters.

        Examples:
            >>> stmt = GraphStatement("MATCH (n) WHERE n.id = $id RETURN n", {"id": 1})
            >>> stmt.merge_parameters({"limit": 10, "id": 2})
            >>> # stmt.parameters is now {"id": 2, "limit": 10, "LIMIT_SIZE": 0}

        Note:
            This method creates a copy of the existing parameters before merging
            to avoid modifying the original dictionary reference.
        """
        tmp = self.parameters.copy()
        tmp.update(parameters)
        self.parameters = tmp

    def run(self, session: neo4j.Session) -> None:
        """
        Run the statement. This will execute the query against the graph.

        This method executes the Cypher query using either iterative or non-iterative
        execution based on the statement configuration. It handles logging and
        statistics collection automatically.

        Args:
            session (neo4j.Session): The Neo4j session to use for executing the query.

        Examples:
            >>> stmt = GraphStatement("MATCH (n:User) RETURN count(n)")
            >>> stmt.run(session)
            >>> # Query executed and results processed

            >>> # Iterative execution
            >>> stmt = GraphStatement(
            ...     "MATCH (n:User) SET n.processed = true LIMIT $LIMIT_SIZE",
            ...     iterative=True,
            ...     iterationsize=1000
            ... )
            >>> stmt.run(session)
            >>> # Query executed in chunks of 1000 until no more updates

        Note:
            For iterative statements, the method will continue running until
            the query returns no updates (summary.counters.contains_updates is False).
            Completion is logged with the parent job name and sequence number.
        """
        if self.iterative:
            self._run_iterative(session)
        else:
            session.write_transaction(self._run_noniterative)

        logger.info(
            "Completed %s statement #%s",
            self.parent_job_name,
            self.parent_job_sequence_num,
        )

    def as_dict(self) -> Dict[str, Any]:
        """
        Convert statement to a dictionary representation.

        This method serializes the GraphStatement instance into a dictionary
        containing all the essential information needed to recreate the statement.

        Returns:
            Dict[str, Any]: A dictionary representation of the statement containing:
                - query: The Cypher query string
                - parameters: The query parameters
                - iterative: Boolean indicating if the statement is iterative
                - iterationsize: The chunk size for iterative execution

        Examples:
            >>> stmt = GraphStatement(
            ...     "MATCH (n) RETURN count(n)",
            ...     parameters={"limit": 10},
            ...     iterative=True,
            ...     iterationsize=1000
            ... )
            >>> stmt_dict = stmt.as_dict()
            >>> # Returns:
            >>> # {
            >>> #     "query": "MATCH (n) RETURN count(n)",
            >>> #     "parameters": {"limit": 10, "LIMIT_SIZE": 1000},
            >>> #     "iterative": True,
            >>> #     "iterationsize": 1000
            >>> # }

        Note:
            This method is used by GraphStatementJSONEncoder for JSON serialization.
            Parent job information is not included in the dictionary representation.
        """
        return {
            "query": self.query,
            "parameters": self.parameters,
            "iterative": self.iterative,
            "iterationsize": self.iterationsize,
        }

    def _run_noniterative(self, tx: neo4j.Transaction) -> neo4j.ResultSummary:
        """
        Execute a non-iterative statement within a transaction.

        This method runs the query once within the provided transaction and collects
        statistics about the execution. It ensures the result is consumed within the
        transaction to avoid ResultConsumedError.

        Args:
            tx (neo4j.Transaction): The Neo4j transaction to use for executing the query.

        Returns:
            neo4j.ResultSummary: A ResultSummary containing the execution summary including
                statistics about nodes created/deleted, relationships created/deleted,
                properties set, indexes/constraints added/removed, etc.

        Note:
            This method automatically updates various statistics counters for monitoring
            and tracking purposes. The result is consumed within the transaction to ensure
            proper resource management.
        """
        result: neo4j.Result = tx.run(self.query, self.parameters)

        # Ensure we consume the result inside the transaction
        summary: neo4j.ResultSummary = result.consume()

        # Handle stats
        stat_handler.incr("constraints_added", summary.counters.constraints_added)
        stat_handler.incr("constraints_removed", summary.counters.constraints_removed)
        stat_handler.incr("indexes_added", summary.counters.indexes_added)
        stat_handler.incr("indexes_removed", summary.counters.indexes_removed)
        stat_handler.incr("labels_added", summary.counters.labels_added)
        stat_handler.incr("labels_removed", summary.counters.labels_removed)
        stat_handler.incr("nodes_created", summary.counters.nodes_created)
        stat_handler.incr("nodes_deleted", summary.counters.nodes_deleted)
        stat_handler.incr("properties_set", summary.counters.properties_set)
        stat_handler.incr(
            "relationships_created", summary.counters.relationships_created
        )
        stat_handler.incr(
            "relationships_deleted", summary.counters.relationships_deleted
        )

        return summary

    def _run_iterative(self, session: neo4j.Session) -> None:
        """
        Execute an iterative statement in chunks until no more updates are made.

        This method runs the statement repeatedly in chunks of the specified iteration size
        until the query returns no updates. It's useful for processing large datasets
        without overwhelming the database or running into memory constraints.

        Args:
            session (neo4j.Session): The Neo4j session to use for executing the query.

        Note:
            The method continues execution until summary.counters.contains_updates
            returns False, indicating no more records were modified. The LIMIT_SIZE
            parameter is automatically set to the iterationsize value.
        """
        self.parameters["LIMIT_SIZE"] = self.iterationsize

        while True:
            summary: neo4j.ResultSummary = session.write_transaction(
                self._run_noniterative
            )

            if not summary.counters.contains_updates:
                break

    @classmethod
    def create_from_json(
        cls,
        json_obj: Dict[str, Any],
        short_job_name: Optional[str] = None,
        job_sequence_num: Optional[int] = None,
    ):
        """
        Create a GraphStatement instance from a JSON object.

        This class method constructs a GraphStatement from a dictionary representation,
        typically loaded from a JSON file. It provides a convenient way to deserialize
        stored statement configurations.

        Args:
            json_obj (Dict[str, Any]): The JSON object containing statement configuration.
                Expected keys: "query", "parameters", "iterative", "iterationsize".
            short_job_name (Optional[str], optional): The short name of the job this statement
                belongs to, used for logging and naming. Defaults to None.
            job_sequence_num (Optional[int], optional): The sequence number of this statement
                within the job, used for logging and tracking. Defaults to None.

        Returns:
            GraphStatement: A new GraphStatement instance created from the JSON object.

        Note:
            Missing keys in the JSON object will use default values:
            - query: "" (empty string)
            - parameters: {} (empty dict)
            - iterative: False
            - iterationsize: 0
        """
        return cls(
            json_obj.get("query", ""),
            json_obj.get("parameters", {}),
            json_obj.get("iterative", False),
            json_obj.get("iterationsize", 0),
            short_job_name,
            job_sequence_num,
        )

    @classmethod
    def create_from_json_file(cls, file_path: Path):
        """
        Create a GraphStatement instance from a JSON file.

        This class method reads a JSON file and creates a GraphStatement instance
        from its contents. It's a convenient way to load statement configurations
        from external files.

        Args:
            file_path (Path): The path to the JSON file to read.

        Returns:
            GraphStatement: A new GraphStatement instance created from the JSON file.

        Raises:
            FileNotFoundError: If the specified file does not exist.
            json.JSONDecodeError: If the file contains invalid JSON.
            PermissionError: If the file cannot be read due to permissions.

        Note:
            The job short name is automatically extracted from the filename (without extension)
            using the get_job_shortname() utility function. The sequence number defaults to None.
        """
        with open(file_path) as json_file:
            data = json.load(json_file)

        return cls.create_from_json(data, get_job_shortname(file_path))
