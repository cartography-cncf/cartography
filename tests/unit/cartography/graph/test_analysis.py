import json
from pathlib import Path

import pytest

from cartography.graph.analysis import AnalysisJob
from cartography.graph.analysis import AnalysisScope
from cartography.graph.analysis import AnalysisStatement
from cartography.graph.analysis import PropertyEffect
from cartography.graph.analysis import RelationshipPropertyEffect
from cartography.graph.analysis import RelationshipEffect
from cartography.graph.job import GraphJob


def test_relationship_job_appends_cleanup_statement():
    # Arrange
    job = AnalysisJob(
        name="Lambda functions with ECR images",
        short_name="aws_lambda_ecr",
        effect=RelationshipEffect("AWSLambda", "HAS", "ECRImage"),
        statements=(
            AnalysisStatement(
                "MATCH (l:AWSLambda), (e:ECRImage) "
                "WHERE e.digest = 'sha256:' + l.codesha256 "
                "MERGE (l)-[r:HAS]->(e) "
                "SET r.lastupdated = $UPDATE_TAG",
            ),
        ),
    )

    # Act
    graph_job = job.to_graph_job()

    # Assert
    assert job.relationships_added() == (job.effect,)
    assert job.properties_set() == ()
    assert len(graph_job.statements) == 2
    assert graph_job.statements[1].query == (
        "MATCH (source:AWSLambda)-[r:HAS]->(target:ECRImage)\n"
        "WHERE r.lastupdated <> $UPDATE_TAG\n"
        "DELETE r"
    )
    assert graph_job.statements[1].iterative is True


def test_scoped_relationship_cleanup_targets_source_by_default():
    # Arrange
    job = AnalysisJob(
        name="GCP LB exposure",
        short_name="gcp_lb_exposure",
        scope=AnalysisScope("GCPProject", "PROJECT_ID"),
        effect=RelationshipEffect("GCPBackendService", "EXPOSE", "GCPInstance"),
        statements=(
            AnalysisStatement(
                "MATCH (p:GCPProject{id: $PROJECT_ID})-[:RESOURCE]->"
                "(bs:GCPBackendService)-[:ROUTES_TO]->(:GCPInstanceGroup)"
                "-[:HAS_MEMBER]->(i:GCPInstance) "
                "MERGE (bs)-[r:EXPOSE]->(i) "
                "SET r.lastupdated = $UPDATE_TAG",
            ),
        ),
    )

    # Act
    graph_job = job.to_graph_job()

    # Assert
    assert graph_job.statements[1].query == (
        "MATCH (scope:GCPProject {id: $PROJECT_ID})-[:RESOURCE]->(source)\n"
        "MATCH (source:GCPBackendService)-[r:EXPOSE]->(target:GCPInstance)\n"
        "WHERE r.lastupdated <> $UPDATE_TAG\n"
        "DELETE r"
    )


def test_relationship_job_allows_multiple_statements_for_one_effect():
    # Arrange
    job = AnalysisJob(
        name="Resolved image analysis",
        short_name="resolved_image_analysis",
        effect=RelationshipEffect("Container", "RESOLVED_IMAGE", "Image"),
        statements=(
            AnalysisStatement(
                "MATCH (c:Container)-[:HAS_IMAGE]->(i:Image) "
                "MERGE (c)-[r:RESOLVED_IMAGE]->(i) "
                "SET r.lastupdated = $UPDATE_TAG",
            ),
            AnalysisStatement(
                "MATCH (c:Container)-[:HAS_IMAGE]->(:ImageManifestList)"
                "-[:CONTAINS_IMAGE]->(i:Image) "
                "MERGE (c)-[r:RESOLVED_IMAGE]->(i) "
                "SET r.lastupdated = $UPDATE_TAG",
            ),
        ),
    )

    # Act
    graph_job = job.to_graph_job()

    # Assert
    assert len(graph_job.statements) == 3
    assert graph_job.statements[2].query.startswith(
        "MATCH (source:Container)-[r:RESOLVED_IMAGE]->(target:Image)",
    )


def test_property_job_prepends_cleanup_statement():
    # Arrange
    job = AnalysisJob(
        name="Semgrep SAST risk analysis",
        short_name="semgrep_sast_risk_analysis",
        scope=AnalysisScope("SemgrepDeployment", "DEPLOYMENT_ID"),
        effect=PropertyEffect("SemgrepSASTFinding", ("risk_severity",)),
        statements=(
            AnalysisStatement(
                "MATCH (g:GitHubRepository{archived:true})"
                "<-[:FOUND_IN]-(s:SemgrepSASTFinding)"
                "<-[:RESOURCE]-(:SemgrepDeployment{id:$DEPLOYMENT_ID}) "
                "SET s.risk_severity = 'INFO'",
            ),
        ),
    )

    # Act
    graph_job = job.to_graph_job()

    # Assert
    assert job.relationships_added() == ()
    assert job.properties_set() == (job.effect,)
    assert graph_job.statements[0].query == (
        "MATCH (scope:SemgrepDeployment {id: $DEPLOYMENT_ID})"
        "-[:RESOURCE]->(node:SemgrepSASTFinding)\n"
        "REMOVE node.risk_severity"
    )
    assert graph_job.statements[1].query.startswith("MATCH (g:GitHubRepository")


def test_property_effect_requires_properties():
    # Act and assert
    with pytest.raises(ValueError, match="at least one property"):
        PropertyEffect("EC2KeyPair", ())


def test_relationship_property_job_prepends_cleanup_statement():
    # Arrange
    job = AnalysisJob(
        name="Supply chain source file",
        short_name="supply_chain_source_file",
        effect=RelationshipPropertyEffect(
            "Image",
            "PACKAGED_FROM",
            ("dockerfile_path",),
        ),
        statements=(
            AnalysisStatement(
                "MATCH (i:Image)-[r:PACKAGED_FROM]->(:GitHubRepository) "
                "WHERE r.dockerfile_path IS NULL "
                "SET r.dockerfile_path = i.source_file",
            ),
        ),
    )

    # Act
    graph_job = job.to_graph_job()

    # Assert
    assert job.properties_set() == (job.effect,)
    assert graph_job.statements[0].query == (
        "MATCH (source:Image)-[r:PACKAGED_FROM]->(target)\n" "REMOVE r.dockerfile_path"
    )


def test_relationship_property_effect_requires_properties():
    # Act and assert
    with pytest.raises(ValueError, match="at least one property"):
        RelationshipPropertyEffect("Image", "PACKAGED_FROM", ())


def test_analysis_job_requires_statements():
    # Act and assert
    with pytest.raises(ValueError, match="at least one statement"):
        AnalysisJob(
            name="empty",
            effect=PropertyEffect("EC2KeyPair", ("user_uploaded",)),
            statements=(),
        )


@pytest.mark.parametrize(
    "job_file",
    sorted(Path("cartography/data/jobs/analysis").glob("*.json"))
    + sorted(Path("cartography/data/jobs/scoped_analysis").glob("*.json")),
    ids=lambda path: path.name,
)
def test_existing_analysis_json_jobs_still_deserialize(job_file):
    # Arrange
    data = json.loads(job_file.read_text())

    # Act
    job = GraphJob.from_json(data, job_file.stem)

    # Assert
    assert job.name == data["name"]
    assert len(job.statements) == len(data["statements"])
