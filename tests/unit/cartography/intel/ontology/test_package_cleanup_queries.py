from cartography.graph.cleanupbuilder import build_cleanup_queries
from cartography.models.ontology.package import PackageSchema


def test_package_cleanup_queries_cover_derived_relationships():
    queries = build_cleanup_queries(PackageSchema())

    expected_rel_clauses = [
        "MATCH (n)-[r:DETECTED_AS]->(:TrivyPackage)",
        "MATCH (n)-[r:DETECTED_AS]->(:SyftPackage)",
        "MATCH (n)-[r:DEPLOYED]->(:Image)",
        "MATCH (n)-[r:SHOULD_UPDATE_TO]->(:TrivyFix)",
        "MATCH (n)-[r:DEPENDS_ON]->(:Package)",
        "MATCH (n)<-[r:AFFECTS]-(:TrivyImageFinding)",
    ]

    for clause in expected_rel_clauses:
        assert any(
            clause in query for query in queries
        ), f"Missing cleanup query for package relationship clause: {clause}"
