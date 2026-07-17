from unittest.mock import MagicMock
from unittest.mock import patch

from cartography.intel.github.repos import _GITHUB_DEPENDENCY_CLEANUP_QUERIES
from cartography.intel.github.repos import cleanup_github_dependencies


def test_dependency_cleanup_queries_are_scoped_to_github_owned_nodes():
    """
    Regression test for issue #3035: `Dependency` is a shared canonical label
    (Semgrep and Socket dependency nodes carry it as an extra label), so the
    GitHub dependency cleanup must be scoped to nodes that also carry the
    GitHubDependency label. An unscoped `MATCH (n:Dependency)` would delete
    other modules' stale nodes and their relationships.
    """
    assert len(_GITHUB_DEPENDENCY_CLEANUP_QUERIES) == 3
    for query in _GITHUB_DEPENDENCY_CLEANUP_QUERIES:
        assert "(n:Dependency:GitHubDependency)" in query
        assert "(n:Dependency)" not in query


def test_cleanup_github_dependencies_runs_the_scoped_queries():
    """
    cleanup_github_dependencies() must execute exactly the scoped queries with
    the caller's job parameters, not a query set generated from the schema's
    primary label alone.
    """
    neo4j_session = MagicMock()
    common_job_parameters = {"UPDATE_TAG": 12345}

    with patch("cartography.intel.github.repos.GraphStatement") as statement_cls:
        with patch("cartography.intel.github.repos.GraphJob") as job_cls:
            cleanup_github_dependencies(neo4j_session, common_job_parameters)

    ran_queries = [call.args[0] for call in statement_cls.call_args_list]
    assert ran_queries == _GITHUB_DEPENDENCY_CLEANUP_QUERIES
    for call in statement_cls.call_args_list:
        assert call.kwargs["parameters"] == common_job_parameters
        assert call.kwargs["iterative"] is True
    job_cls.return_value.run.assert_called_once_with(neo4j_session)
