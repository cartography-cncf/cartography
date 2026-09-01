from cartography.analysis.ontology.analysis import RAILWAY_CONTAINER_CONFIGURED_IMAGE
from cartography.util import run_typed_analysis_job

TEST_UPDATE_TAG = 123456789


def test_railway_current_deployment_links_only_to_configured_image_tag(neo4j_session):
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    neo4j_session.run(
        """
        CREATE (instance:RailwayServiceInstance {
            id: 'instance', source_image: 'registry.example.com/team/app:stable'
        })
        CREATE (current:RailwayDeployment:Container {id: 'current'})
        CREATE (historical:RailwayDeployment {id: 'historical'})
        CREATE (tag:ImageTag {
            id: 'tag', uri: 'registry.example.com/team/app:stable'
        })
        CREATE (image:Image {id: 'sha256:current-tag-target'})
        CREATE (current)-[:WORKLOAD_PARENT]->(instance)
        CREATE (historical)-[:WORKLOAD_PARENT]->(instance)
        CREATE (tag)-[:IMAGE]->(image)
        """
    )

    run_typed_analysis_job(
        RAILWAY_CONTAINER_CONFIGURED_IMAGE,
        neo4j_session,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    configured = neo4j_session.run(
        """
        MATCH (deployment:RailwayDeployment)-[:CONFIGURED_IMAGE]->(tag:ImageTag)
        RETURN deployment.id AS deployment_id, tag.id AS tag_id
        """
    ).values()
    assert configured == [["current", "tag"]]

    runtime_edges = neo4j_session.run(
        """
        MATCH (:RailwayDeployment {id: 'current'})-[r:HAS_IMAGE|RESOLVED_IMAGE]->(:Image)
        RETURN count(r) AS count
        """
    ).single()["count"]
    assert runtime_edges == 0


def test_railway_configured_image_cleanup_removes_stale_relationships(neo4j_session):
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    neo4j_session.run(
        """
        CREATE (instance:RailwayServiceInstance {
            id: 'instance', source_image: 'registry.example.com/team/app:new'
        })
        CREATE (deployment:RailwayDeployment:Container {id: 'current'})
        CREATE (old_tag:ImageTag {id: 'old', uri: 'registry.example.com/team/app:old'})
        CREATE (new_tag:ImageTag {id: 'new', uri: 'registry.example.com/team/app:new'})
        CREATE (deployment)-[:WORKLOAD_PARENT]->(instance)
        CREATE (deployment)-[:CONFIGURED_IMAGE {lastupdated: $stale_tag}]->(old_tag)
        """,
        stale_tag=TEST_UPDATE_TAG - 1,
    )

    run_typed_analysis_job(
        RAILWAY_CONTAINER_CONFIGURED_IMAGE,
        neo4j_session,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    configured = neo4j_session.run(
        """
        MATCH (:RailwayDeployment {id: 'current'})-[:CONFIGURED_IMAGE]->(tag:ImageTag)
        RETURN tag.id AS tag_id
        """
    ).values()
    assert configured == [["new"]]
