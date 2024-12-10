from dataclasses import fields

from cartography.client.core.tx import load_graph_data
from cartography.graph.cleanupbuilder import build_cleanup_queries
from cartography.graph.job import GraphJob
from cartography.graph.querybuilder import build_ingestion_query
from tests.data.graph.querybuilder.sample_models.node_without_sub_resource import NodeA, NodeAProperties
from tests.data.graph.querybuilder.sample_models.simple_node import SimpleNodeSchema, SimpleNodeProperties
from tests.data.util.fake_data import generate_fake_data


def test_build_cleanup_queries_no_sub_resource(neo4j_session):
    # Arrange
    data = generate_fake_data(10, SimpleNodeProperties)
    query = build_ingestion_query(SimpleNodeSchema())
    load_graph_data(
        neo4j_session,
        query,
        data,
        lastupdated=1,
    )

    data = generate_fake_data(10, NodeAProperties)
    query = build_ingestion_query(NodeA())
    load_graph_data(
        neo4j_session,
        query,
        data,
        lastupdated=1,
        sub_resource_id=3,
    )

    # Act
    common_job_parameters = {'UPDATE_TAG' : 1}
    cleanup_job = GraphJob.from_node_schema(NodeA(), common_job_parameters)
    cleanup_job.run(neo4j_session)


    expected_queries = [
        """
        MATCH (n:NodeA)
        MATCH (n)<-[r:POINTS_TO]-(:NodeB)
        WHERE r.lastupdated <> $UPDATE_TAG
        WITH r LIMIT $LIMIT_SIZE
        DELETE r;
        """
    ]

    assert clean_query_list(actual_queries) == clean_query_list(expected_queries)
