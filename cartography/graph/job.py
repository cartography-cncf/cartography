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
from cartography.graph.statement import get_job_shortname
from cartography.graph.statement import GraphStatement
from cartography.models.core.nodes import CartographyNodeSchema

logger = logging.getLogger(__name__)


def _get_identifiers(template: string.Template) -> List[str]:
    """
    :param template: A string Template
    :return: the variable names that start with a '$' like $this in the given Template.
    Stolen from https://github.com/python/cpython/issues/90465#issuecomment-1093941790.
    TODO we can get rid of this and use template.get_identifiers() once we are on python 3.11
    """
    return list(
        set(
            filter(
                lambda v: v is not None,
                (
                    mo.group('named') or mo.group('braced')
                    for mo in template.pattern.finditer(template.template)
                ),
            ),
        ),
    )


def get_parameters(queries: List[str]) -> Set[str]:
    """
    :param queries: A list of Neo4j queries with parameters indicated by leading '$' like $this.
    :return: The set of all parameters across all given Neo4j queries.
    """
    parameter_set = set()
    for query in queries:
        as_template = Template(query)
        params = _get_identifiers(as_template)
        parameter_set.update(params)
    return parameter_set


class GraphJobJSONEncoder(json.JSONEncoder):
    """
    Support JSON serialization for GraphJob instances.
    """

    def default(self, obj: Any) -> Any:
        if isinstance(obj, GraphJob):
            return obj.as_dict()
        else:
            # Let the default encoder roll up the exception.
            return json.JSONEncoder.default(self, obj)


class GraphJob:
    """
    A job that will run against the cartography graph. A job is a sequence of statements which execute sequentially.
    """

    def __init__(self, name: str, statements: List[GraphStatement], short_name: Optional[str] = None):
        # E.g. "Okta intel module cleanup"
        self.name = name
        self.statements: List[GraphStatement] = statements
        # E.g. "okta_import_cleanup"
        self.short_name = short_name

    def merge_parameters(self, parameters: Dict) -> None:
        """
        Merge parameters for all job statements.
        """
        for s in self.statements:
            s.merge_parameters(parameters)

    def run(self, neo4j_session: neo4j.Session) -> None:
        """
        Run the job. This will execute all statements sequentially.
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
        log_msg = f"Finished job {self.short_name}" if self.short_name else f"Finished job {self.name}"
        logger.info(log_msg)

    def as_dict(self) -> Dict:
        """
        Convert job to a dictionary.
        """
        return {
            "name": self.name,
            "statements": [s.as_dict() for s in self.statements],
            "short_name": self.short_name,
        }

    @classmethod
    def from_json(cls, blob: str, short_name: Optional[str] = None) -> 'GraphJob':
        """
        Create a job from a JSON blob.
        """
        data: Dict = json.loads(blob)
        statements = _get_statements_from_json(data, short_name)
        name = data["name"]
        return cls(name, statements, short_name)

    @classmethod
    def from_node_schema(
            cls,
            node_schema: CartographyNodeSchema,
            parameters: Dict[str, Any],
    ) -> 'GraphJob':
        """
        Create a cleanup job from a CartographyNodeSchema object.
        For a given node, the fields used in the node_schema.sub_resource_relationship.target_node_node_matcher.keys()
        must be provided as keys and values in the params dict.
        """
        queries: List[str] = build_cleanup_queries(node_schema)

        expected_param_keys: Set[str] = get_parameters(queries)
        actual_param_keys: Set[str] = set(parameters.keys())
        # Hacky, but LIMIT_SIZE is specified by default in cartography.graph.statement, so we exclude it from validation
        actual_param_keys.add('LIMIT_SIZE')

        missing_params: Set[str] = expected_param_keys - actual_param_keys

        if missing_params:
            raise ValueError(
                f'GraphJob is missing the following expected query parameters: "{missing_params}". Please check the '
                f'value passed to `parameters`.',
            )

        statements: List[GraphStatement] = [
            GraphStatement(
                query,
                parameters=parameters,
                iterative=True,
                iterationsize=100,
                parent_job_name=node_schema.label,
                parent_job_sequence_num=idx,
            ) for idx, query in enumerate(queries, start=1)
        ]

        return cls(
            f"Cleanup {node_schema.label}",
            statements,
            node_schema.label,
        )

    @classmethod
    def from_json_file(cls, file_path: Union[str, Path]) -> 'GraphJob':
        """
        Create a job from a JSON file.
        """
        with open(file_path) as j_file:
            data: Dict = json.load(j_file)

        job_shortname: str = get_job_shortname(file_path)
        statements: List[GraphStatement] = _get_statements_from_json(data, job_shortname)
        name: str = data["name"]
        return cls(name, statements, job_shortname)

    @classmethod
    def run_from_json(
        cls, neo4j_session: neo4j.Session, blob: str, parameters: Dict, short_name: Optional[str] = None,
    ) -> None:
        """
        Run a job from a JSON blob. This will deserialize the job and execute all statements sequentially.
        """
        if not parameters:
            parameters = {}

        job: GraphJob = cls.from_json(blob, short_name)
        job.merge_parameters(parameters)
        job.run(neo4j_session)

    @classmethod
    def run_from_json_file(cls, file_path: Union[str, Path], neo4j_session: neo4j.Session, parameters: Dict) -> None:
        """
        Run a job from a JSON file. This will deserialize the job and execute all statements sequentially.
        """
        if not parameters:
            parameters = {}

        job: GraphJob = cls.from_json_file(file_path)

        job.merge_parameters(parameters)
        job.run(neo4j_session)


def _get_statements_from_json(blob: Dict, short_job_name: Optional[str] = None) -> List[GraphStatement]:
    """
    Deserialize all statements from the JSON blob.
    """
    statements: List[GraphStatement] = []
    for i, statement_data in enumerate(blob["statements"]):
        # i+1 to make it 1-based and not 0-based to help with log readability
        statement: GraphStatement = GraphStatement.create_from_json(statement_data, short_job_name, i + 1)
        statements.append(statement)

    return statements
