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
    """

    def default(self, obj):
        if isinstance(obj, GraphStatement):
            return obj.as_dict()
        else:
            # Let the default encoder roll up the exception.
            return json.JSONEncoder.default(self, obj)


# TODO move this cartography.util after we move util.run_*_job to cartography.graph.job.
def get_job_shortname(file_path: Union[Path, str]) -> str:
    # Return filename without path and extension
    return os.path.splitext(file_path)[0]


class GraphStatement:
    """
    A statement that will run against the cartography graph. Statements can query or update the graph.
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
        """
        tmp = self.parameters.copy()
        tmp.update(parameters)
        self.parameters = tmp

    def run(self, session: neo4j.Session) -> None:
        """
        Run the statement. This will execute the query against the graph.
        """
        if self.iterative:
            self._run_iterative(session)
        else:
            session.write_transaction(self._run_noniterative)

        logger.info(
            f"Completed {self.parent_job_name} statement #{self.parent_job_sequence_num}"
        )

    def as_dict(self) -> Dict[str, Any]:
        """
        Convert statement to a dictionary.
        """
        return {
            "query": self.query,
            "parameters": self.parameters,
            "iterative": self.iterative,
            "iterationsize": self.iterationsize,
        }

    def _run_noniterative(self, tx: neo4j.Transaction) -> neo4j.ResultSummary:
        """
        Non-iterative statement execution.
        Returns a ResultSummary instead of Result to avoid ResultConsumedError.
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
        Iterative statement execution.

        Expects the query to return the total number of records updated.
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
        Create a statement from a JSON blob.
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
        Create a statement from a JSON file.
        """
        with open(file_path) as json_file:
            data = json.load(json_file)

        return cls.create_from_json(data, get_job_shortname(file_path))
