import json
import logging
import string
from pathlib import Path
from string import Template
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Set
from typing import Union

import neo4j

from cartography.graph.cleanupbuilder import build_cleanup_queries
from cartography.graph.cleanupbuilder import build_cleanup_query_for_matchlink
from cartography.graph.statement import get_job_shortname
from cartography.graph.statement import GraphStatement
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelSchema

logger = logging.getLogger(__name__)


def _get_identifiers(template: string.Template) -> List[str]:
    """
    Extract variable names from a Template object.

    This function extracts all variable identifiers (parameters) from a string Template
    that start with '$'. It's used to analyze query parameters before Python 3.11's
    built-in ``get_identifiers()`` method.

    Args:
        template (string.Template): A string Template object containing variable placeholders.

    Returns:
        List[str]: A list of variable names that start with '$' in the given Template.

    Examples:
        >>> from string import Template
        >>> template = Template("MATCH (n:Node {id: $node_id}) SET n.tag = $update_tag")
        >>> identifiers = _get_identifiers(template)
        >>> sorted(identifiers)
        ['node_id', 'update_tag']

    Note:
        This is a temporary implementation borrowed from the CPython GitHub issue.
        Once migrated to Python 3.11+, this can be replaced with the built-in
        ``template.get_identifiers()`` method.

    See Also:
        CPython issue: https://github.com/python/cpython/issues/90465#issuecomment-1093941790
    """
    return list(
        set(
            filter(
                lambda v: v is not None,
                (
                    mo.group("named") or mo.group("braced")
                    for mo in template.pattern.finditer(template.template)
                ),
            ),
        ),
    )


def get_parameters(queries: List[str]) -> Set[str]:
    """
    Extract all parameters from a list of Neo4j queries.

    This function analyzes all given Neo4j queries and extracts all parameter identifiers
    that start with '$'. It's useful for validating that all required parameters are
    provided before executing a job.

    Args:
        queries (List[str]): A list of Neo4j queries with parameters indicated by
            leading '$' (e.g., ``$node_id``, ``$update_tag``).

    Returns:
        Set[str]: The set of all unique parameters across all given Neo4j queries.

    Note:
        This function is commonly used in ``GraphJob.from_node_schema()`` to validate
        that all required parameters are provided for cleanup queries.
    """
    parameter_set = set()
    for query in queries:
        as_template = Template(query)
        params = _get_identifiers(as_template)
        parameter_set.update(params)
    return parameter_set


class GraphJobJSONEncoder(json.JSONEncoder):
    """
    JSON encoder with support for GraphJob instances.

    This custom JSON encoder extends the default JSONEncoder to handle serialization
    of GraphJob objects. It automatically converts GraphJob instances to their
    dictionary representation using the ``as_dict()`` method.

    Note:
        This encoder only handles GraphJob instances. For other custom objects,
        it falls back to the default JSONEncoder behavior, which may raise
        a TypeError for non-serializable objects.
    """

    def default(self, obj: Any) -> Any:
        """
        Handle serialization of custom objects.

        This method is called by the JSON encoder for objects that are not
        natively serializable. It converts GraphJob instances to dictionaries
        and delegates other objects to the default encoder.

        Args:
            obj (Any): The object to be serialized.

        Returns:
            Any: The serializable representation of the object.

        Raises:
            TypeError: If the object is not a GraphJob and cannot be serialized
                by the default encoder.
        """
        if isinstance(obj, GraphJob):
            return obj.as_dict()
        else:
            # Let the default encoder roll up the exception.
            return json.JSONEncoder.default(self, obj)


class GraphJob:
    """
    A job that executes a sequence of Neo4j statements against the cartography graph.

    A GraphJob represents a complete unit of work that consists of one or more
    GraphStatements executed sequentially. Jobs are commonly used for data loading,
    cleanup operations, and complex graph transformations.

    Args:
        name (str): Human-readable name for the job (e.g., "AWS EC2 instance cleanup").
        statements (List[GraphStatement]): List of GraphStatement objects to execute
            in sequence.
        short_name (Optional[str]): Short identifier/slug for the job (e.g., "ec2_cleanup").
            If not provided, logging will use the full name.

    Attributes:
        name (str): The human-readable job name.
        statements (List[GraphStatement]): The list of statements to execute.
        short_name (Optional[str]): The job's short identifier for logging.

    Examples:
        Creating a simple job:

        >>> from cartography.graph.statement import GraphStatement
        >>> stmt1 = GraphStatement("MATCH (n:TestNode) SET n.processed = true")
        >>> stmt2 = GraphStatement("MATCH (n:TestNode) WHERE n.stale = true DELETE n")
        >>> job = GraphJob("Test cleanup job", [stmt1, stmt2], "test_cleanup")
        >>> job.name
        'Test cleanup job'
        >>> len(job.statements)
        2

        Creating a job from a node schema:

        >>> parameters = {"UPDATE_TAG": 1642784400, "account_id": "123456789012"}
        >>> job = GraphJob.from_node_schema(aws_ec2_schema, parameters)
        >>> job.name
        'Cleanup AWSEC2Instance'

    Note:
        - Statements are executed in the order they appear in the list.
        - If any statement fails, the entire job fails and subsequent statements are not executed.
        - Jobs automatically handle parameter merging and provide structured logging.
    """

    def __init__(
        self,
        name: str,
        statements: List[GraphStatement],
        short_name: Optional[str] = None,
    ):
        """
        Initialize a new GraphJob instance.

        Args:
            name (str): Human-readable name for the job.
            statements (List[GraphStatement]): List of statements to execute sequentially.
            short_name (Optional[str]): Short identifier for logging purposes.
        """
        # E.g. "Okta intel module cleanup"
        self.name = name
        self.statements: List[GraphStatement] = statements
        # E.g. "okta_import_cleanup"
        self.short_name = short_name

    def merge_parameters(self, parameters: Dict) -> None:
        """
        Merge parameters into all job statements.

        This method distributes the provided parameters to all statements in the job,
        allowing for centralized parameter management at the job level.

        Args:
            parameters (Dict): Dictionary of parameters to merge into all statements.
                Keys should match the parameter names used in the Neo4j queries.

        Examples:
            >>> job = GraphJob("Test job", [statement1, statement2])
            >>> job.merge_parameters({"UPDATE_TAG": 1642784400, "account_id": "123456789012"})
            >>> # All statements in the job now have access to these parameters
        """
        for s in self.statements:
            s.merge_parameters(parameters)

    def run(self, neo4j_session: neo4j.Session) -> None:
        """
        Execute the job by running all statements sequentially.

        This method executes each statement in the job in order. If any statement
        fails, the entire job fails and subsequent statements are not executed.
        Progress is logged at debug and info levels.

        Args:
            neo4j_session (neo4j.Session): The Neo4j session to use for execution.

        Raises:
            Exception: Any exception raised by a statement execution is re-raised
                after logging the error.

        Examples:
            >>> job = GraphJob("Cleanup job", [cleanup_statement])
            >>> job.run(neo4j_session)
            # Logs: "Starting job 'Cleanup job'."
            # Logs: "Finished job cleanup_job" (if short_name is set)
        """
        logger.debug("Starting job '%s'.", self.name)
        for stm in self.statements:
            try:
                stm.run(neo4j_session)
            except Exception as e:
                logger.error(
                    "Unhandled error while executing statement in job '%s': %s",
                    self.name,
                    e,
                )
                raise
        log_msg = (
            f"Finished job {self.short_name}"
            if self.short_name
            else f"Finished job {self.name}"
        )
        logger.info(log_msg)

    def as_dict(self) -> Dict:
        """
        Convert the job to a dictionary representation.

        This method serializes the job to a dictionary format suitable for JSON
        serialization or other forms of persistence.

        Returns:
            Dict: A dictionary containing the job's name, statements, and short_name.
                The statements are also converted to their dictionary representations.

        Examples:
            >>> job = GraphJob("Test job", [statement], "test_job")
            >>> job_dict = job.as_dict()
            >>> job_dict.keys()
            dict_keys(['name', 'statements', 'short_name'])
            >>> job_dict['name']
            'Test job'
        """
        return {
            "name": self.name,
            "statements": [s.as_dict() for s in self.statements],
            "short_name": self.short_name,
        }

    @classmethod
    def from_json(
        cls, blob: Union[str, dict], short_name: Optional[str] = None
    ) -> "GraphJob":
        """
        Create a GraphJob instance from a JSON string.

        This class method deserializes a JSON string into a GraphJob object,
        reconstructing all statements and their parameters.

        Args:
            blob (Union[str, dict]): The JSON string or dictionary to deserialize. Must contain a 'name' field
                and a 'statements' field with a list of statement definitions. If a string is provided,
                it will be parsed as JSON. If a dictionary is provided, it will be used directly.
            short_name (Optional[str]): Override the short name for the job.
                If not provided, uses the short_name from JSON if available.

        Returns:
            GraphJob: A new GraphJob instance created from the JSON data.

        Raises:
            json.JSONDecodeError: If the blob is not valid JSON.
            KeyError: If the JSON doesn't contain required fields ('name', 'statements').

        Examples:
            >>> json_str = '''
            ... {
            ...     "name": "Test Job",
            ...     "statements": [
            ...         {
            ...             "query": "MATCH (n:TestNode) RETURN count(n)",
            ...             "parameters": {}
            ...         }
            ...     ]
            ... }
            ... '''
            >>> job = GraphJob.from_json(json_str, "test_job")
            >>> job.name
            'Test Job'
            >>> job.short_name
            'test_job'
        """
        data = json.loads(blob) if isinstance(blob, str) else blob
        statements = _get_statements_from_json(data, short_name)
        name = data["name"]
        return cls(name, statements, short_name)

    @classmethod
    def from_node_schema(
        cls,
        node_schema: CartographyNodeSchema,
        parameters: Dict[str, Any],
        iterationsize: int = 100,
        cascade_delete: bool = False,
    ) -> "GraphJob":
        """
        Create a cleanup job from a CartographyNodeSchema.

        This class method generates a cleanup job that removes stale nodes and
        relationships based on the provided node schema configuration. It automatically
        creates the necessary cleanup queries and validates that all required
        parameters are provided.

        For a given node, the fields used in the
        node_schema.sub_resource_relationship.target_node_matcher.keys()
        must be provided as keys and values in the parameters dict.

        Args:
            node_schema (CartographyNodeSchema): The node schema object defining
                the structure and relationships of nodes to clean up.
            parameters (Dict[str, Any]): Parameters for the cleanup queries.
                Must include all parameters required by the generated queries.
                Common parameters include UPDATE_TAG and sub-resource identifiers.
            iterationsize (int, optional): The number of items to process in each iteration.
                Defaults to 100.
            cascade_delete (bool): If True, also delete all child nodes that have a
                relationship to stale nodes matching node_schema.sub_resource_relationship.rel_label.
                Defaults to False to preserve existing behavior.

        Returns:
            GraphJob: A new GraphJob instance configured for cleanup operations.

        Raises:
            ValueError: If the provided parameters don't match the expected
                parameters for the cleanup queries.
        """
        queries: List[str] = build_cleanup_queries(node_schema, cascade_delete)

        expected_param_keys: Set[str] = get_parameters(queries)
        actual_param_keys: Set[str] = set(parameters.keys())
        # Hacky, but LIMIT_SIZE is specified by default in cartography.graph.statement, so we exclude it from validation
        actual_param_keys.add("LIMIT_SIZE")

        missing_params: Set[str] = expected_param_keys - actual_param_keys

        if missing_params:
            raise ValueError(
                f'GraphJob is missing the following expected query parameters: "{missing_params}". Please check the '
                f"value passed to `parameters`.",
            )

        statements: List[GraphStatement] = [
            GraphStatement(
                query,
                parameters=parameters,
                iterative=True,
                iterationsize=iterationsize,
                parent_job_name=node_schema.label,
                parent_job_sequence_num=idx,
            )
            for idx, query in enumerate(queries, start=1)
        ]

        return cls(
            f"Cleanup {node_schema.label}",
            statements,
            node_schema.label,
        )

    @classmethod
    def from_matchlink(
        cls,
        rel_schema: CartographyRelSchema,
        sub_resource_label: str,
        sub_resource_id: str,
        update_tag: int,
        iterationsize: int = 100,
    ) -> "GraphJob":
        """
        Create a cleanup job for matchlink relationships.

        This class method generates a cleanup job specifically for cleaning up stale
        relationships created by ``load_matchlinks()`` operations. It should only be used
        for matchlink cleanup and not for general relationship cleanup.

        Args:
            rel_schema (CartographyRelSchema): The relationship schema object defining
                the structure of relationships to clean up. Must have source_node_matcher
                and target_node_matcher defined.
            sub_resource_label (str): The label of the sub-resource to scope cleanup to.
            sub_resource_id (str): The ID of the sub-resource to scope cleanup to.
            update_tag (int): The update tag to identify stale relationships.
            iterationsize (int, optional): The number of items to process in each iteration.
                Defaults to 100.

        Returns:
            GraphJob: A new GraphJob instance configured for matchlink cleanup.

        Note:
            - This method is specifically designed for matchlink cleanup operations.
            - Required relationship properties ``_sub_resource_label`` and ``_sub_resource_id``
              must be defined in the rel_schema.
            - For a given rel_schema, the fields used in the rel_schema.properties._sub_resource_label.name and
            rel_schema.properties._sub_resource_id.name must be provided as keys and values in the params dict.
            - The rel_schema must have a source_node_matcher and target_node_matcher.
            - The number of items to process in each iteration. Defaults to 100.
        """
        cleanup_link_query = build_cleanup_query_for_matchlink(rel_schema)
        logger.debug("Cleanup query: %s", cleanup_link_query)

        parameters = {
            "UPDATE_TAG": update_tag,
            "_sub_resource_label": sub_resource_label,
            "_sub_resource_id": sub_resource_id,
        }

        statement = GraphStatement(
            cleanup_link_query,
            parameters=parameters,
            iterative=True,
            iterationsize=iterationsize,
            parent_job_name=rel_schema.rel_label,
        )

        return cls(
            f"Cleanup {rel_schema.rel_label} between {rel_schema.source_node_label} and {rel_schema.target_node_label}",
            [statement],
            rel_schema.rel_label,
        )

    @classmethod
    def from_json_file(cls, file_path: Union[str, Path]) -> "GraphJob":
        """
        Create a GraphJob instance from a JSON file.

        This class method reads a JSON file and deserializes it into a GraphJob object.
        The job's short name is automatically derived from the file path.

        Args:
            file_path (Union[str, Path]): The path to the JSON file to read and parse.

        Returns:
            GraphJob: A new GraphJob instance created from the JSON file.

        Raises:
            FileNotFoundError: If the specified file does not exist.
            json.JSONDecodeError: If the file contains invalid JSON.
            KeyError: If the JSON file doesn't contain required fields ('name', 'statements').
        """
        with open(file_path, encoding="utf-8") as j_file:
            data: Dict = json.load(j_file)

        job_shortname: str = get_job_shortname(file_path)
        statements: List[GraphStatement] = _get_statements_from_json(
            data,
            job_shortname,
        )
        name: str = data["name"]
        return cls(name, statements, job_shortname)

    @classmethod
    def run_from_json(
        cls,
        neo4j_session: neo4j.Session,
        blob: Union[str, dict],
        parameters: Dict,
        short_name: Optional[str] = None,
    ) -> None:
        """
        Create and execute a job from a JSON string.

        This convenience method combines job creation and execution in a single call.
        It deserializes the JSON, merges parameters, and executes all statements.

        Args:
            neo4j_session (neo4j.Session): The Neo4j session to use for execution.
            blob (Union[str, dict]): The JSON string or dictionary containing the job definition.
                If a string is provided, it will be parsed as JSON. If a dictionary is provided,
                it will be used directly.
            parameters (Dict): Parameters to merge into all job statements.
            short_name (Optional[str]): Override the short name for the job.
        """
        if not parameters:
            parameters = {}

        job: GraphJob = cls.from_json(blob, short_name)
        job.merge_parameters(parameters)
        job.run(neo4j_session)

    @classmethod
    def run_from_json_file(
        cls,
        file_path: Union[str, Path],
        neo4j_session: neo4j.Session,
        parameters: Dict,
    ) -> None:
        """
        Create and execute a job from a JSON file.

        This convenience method combines job creation from file and execution in a single call.
        It reads the JSON file, merges parameters, and executes all statements.

        Args:
            file_path (Union[str, Path]): The path to the JSON file containing the job definition.
            neo4j_session (neo4j.Session): The Neo4j session to use for execution.
            parameters (Dict): Parameters to merge into all job statements.

        Raises:
            FileNotFoundError: If the specified file does not exist.
            json.JSONDecodeError: If the file contains invalid JSON.
        """
        if not parameters:
            parameters = {}

        job: GraphJob = cls.from_json_file(file_path)

        job.merge_parameters(parameters)
        job.run(neo4j_session)


def _get_statements_from_json(
    blob: Dict,
    short_job_name: Optional[str] = None,
) -> List[GraphStatement]:
    """
    Deserialize GraphStatement objects from a JSON dictionary.

    This function creates a list of GraphStatement objects from the 'statements'
    field in a JSON blob. Each statement is assigned a sequence number for
    logging and debugging purposes.

    Args:
        blob (Dict): The JSON dictionary containing a 'statements' field with
            a list of statement definitions.
        short_job_name (Optional[str]): Short name for the job, used for logging
            and statement naming purposes.

    Returns:
        List[GraphStatement]: A list of GraphStatement instances created from
            the JSON blob.

    Raises:
        KeyError: If the JSON blob doesn't contain the 'statements' field.
    """
    statements: List[GraphStatement] = []
    for i, statement_data in enumerate(blob["statements"]):
        # i+1 to make it 1-based and not 0-based to help with log readability
        statement: GraphStatement = GraphStatement.create_from_json(
            statement_data,
            short_job_name,
            i + 1,
        )
        statements.append(statement)

    return statements
