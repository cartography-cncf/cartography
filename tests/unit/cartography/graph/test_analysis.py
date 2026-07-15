import json
import pkgutil
import re
from pathlib import Path
from types import ModuleType
from typing import Iterator

import pytest

import cartography.analysis
from cartography.graph.analysis import AddRelationship
from cartography.graph.analysis import AddToSet
from cartography.graph.analysis import AddValuesToSet
from cartography.graph.analysis import AnalysisJob
from cartography.graph.analysis import AnalysisStatement
from cartography.graph.analysis import Case
from cartography.graph.analysis import IncrementalMatch
from cartography.graph.analysis import PropertyEffect
from cartography.graph.analysis import RawCypher
from cartography.graph.analysis import RelationshipEffect
from cartography.graph.analysis import RelationshipPropertyEffect
from cartography.graph.analysis import ScopeById
from cartography.graph.analysis import SetProperty
from cartography.graph.analysis import SetRelationshipProperty
from cartography.graph.analysis import SetRelationshipPropertyIfMissing
from cartography.graph.analysisbuilder import compile_query
from cartography.graph.analysisbuilder import properties_set
from cartography.graph.analysisbuilder import relationships_added
from cartography.graph.analysisbuilder import to_graph_job
from cartography.graph.job import GraphJob
from tests.unit.cartography.graph.helpers import clean_query_list

MUTATING_CYPHER_RE = re.compile(
    r"\b(CREATE|DELETE|DETACH|MERGE|REMOVE|SET)\b",
    re.IGNORECASE,
)


def _analysis_modules() -> Iterator[ModuleType]:
    for module_info in pkgutil.walk_packages(
        cartography.analysis.__path__,
        prefix=f"{cartography.analysis.__name__}.",
    ):
        if module_info.ispkg:
            continue
        module = __import__(module_info.name, fromlist=["_"])
        yield module


def _analysis_jobs() -> Iterator[AnalysisJob]:
    seen: set[int] = set()
    for module in _analysis_modules():
        for value in vars(module).values():
            jobs: tuple[AnalysisJob, ...]
            if isinstance(value, AnalysisJob):
                jobs = (value,)
            elif isinstance(value, tuple) and all(
                isinstance(item, AnalysisJob) for item in value
            ):
                jobs = value
            else:
                continue

            for job in jobs:
                if id(job) in seen:
                    continue
                seen.add(id(job))
                yield job


def test_typed_analysis_jobs_declare_effects_and_keep_match_queries_read_only():
    for job in _analysis_jobs():
        for index, statement in enumerate(job.statements):
            assert statement.query is None, (
                f"{job.short_name or job.name} statement {index} uses raw query; "
                "write/cleanup-only analysis must stay as JSON."
            )
            assert (
                statement.effects
            ), f"{job.short_name or job.name} statement {index} has no effects."
            assert statement.match is not None
            assert not MUTATING_CYPHER_RE.search(statement.match), (
                f"{job.short_name or job.name} statement {index} has a mutating "
                "match query; mutations must be declared as effects."
            )
            assert "$UPDATE_TAG" not in statement.match, (
                f"{job.short_name or job.name} statement {index} inlines its "
                "freshness filter; use incremental_on."
            )
            if job.scope:
                assert job.scope.scope_on
                assert f"${job.scope.id_param}" not in statement.match, (
                    f"{job.short_name or job.name} statement {index} inlines "
                    "its declared scope."
                )


def test_relationship_job_appends_cleanup_statement():
    # Arrange
    job = AnalysisJob(
        name="Lambda functions with ECR images",
        short_name="aws_lambda_ecr",
        statements=(
            AnalysisStatement(
                match=(
                    "MATCH (l:AWSLambda), (e:ECRImage) "
                    "WHERE e.digest = 'sha256:' + l.codesha256"
                ),
                effects=(
                    AddRelationship(
                        "l",
                        "HAS",
                        "e",
                        source_label="AWSLambda",
                        target_label="ECRImage",
                    ),
                ),
            ),
        ),
    )

    # Act
    graph_job = to_graph_job(job)

    # Assert
    assert relationships_added(job) == (
        RelationshipEffect("AWSLambda", "HAS", "ECRImage"),
    )
    assert properties_set(job) == ()
    assert len(graph_job.statements) == 2
    assert graph_job.statements[1].query == (
        "MATCH (source:AWSLambda)-[r:HAS]->(target:ECRImage)\n"
        "WHERE r.lastupdated <> $UPDATE_TAG\n"
        "WITH r LIMIT $LIMIT_SIZE\n"
        "DELETE r"
    )
    assert graph_job.statements[1].iterative is True
    assert graph_job.statements[1].parameters["LIMIT_SIZE"] == 10000


def test_relationship_cleanup_can_keep_provider_owned_edges():
    job = AnalysisJob(
        name="DNS records to EC2 instances",
        statements=(
            AnalysisStatement(
                match="MATCH (dns:DNSRecord), (i:EC2Instance)",
                effects=(
                    AddRelationship(
                        "dns",
                        "DNS_POINTS_TO",
                        "i",
                        source_label="DNSRecord",
                        target_label="EC2Instance",
                        cleanup_where="NOT source:AWSDNSRecord",
                    ),
                ),
            ),
        ),
    )

    graph_job = to_graph_job(job)

    assert graph_job.statements[1].query == (
        "MATCH (source:DNSRecord)-[r:DNS_POINTS_TO]->(target:EC2Instance)\n"
        "WHERE r.lastupdated <> $UPDATE_TAG AND (NOT source:AWSDNSRecord)\n"
        "WITH r LIMIT $LIMIT_SIZE\n"
        "DELETE r"
    )


def test_statement_compiles_add_relationship_effect():
    # Arrange
    statement = AnalysisStatement(
        match=(
            "MATCH (l:AWSLambda)\n"
            "MATCH (e:ECRImage)\n"
            "WHERE e.digest = 'sha256:' + l.codesha256"
        ),
        effects=(
            AddRelationship(
                "l",
                "HAS",
                "e",
                source_label="AWSLambda",
                target_label="ECRImage",
            ),
        ),
    )

    # Act and assert
    assert clean_query_list([compile_query(statement)]) == clean_query_list(
        [
            """
            MATCH (l:AWSLambda)
            MATCH (e:ECRImage)
            WHERE e.digest = 'sha256:' + l.codesha256
            MERGE (l)-[r:HAS]->(e)
            ON CREATE SET r.firstseen = timestamp()
            SET r.lastupdated = $UPDATE_TAG
            """
        ]
    )


def test_statement_compiles_incremental_node_and_relationship_matches():
    # Arrange
    statement = AnalysisStatement(
        match="MATCH (d:Device)-[obs:OBSERVED_AS]->(:Agent)",
        effects=(SetProperty("d", "linked", True, label="Device"),),
        incremental_on=("d", IncrementalMatch("obs", relationship=True)),
    )

    # Act
    query = compile_query(statement)

    # Assert
    assert query.startswith(
        "MATCH (d:Device {lastupdated: $UPDATE_TAG})\n"
        "MATCH ()-[obs:OBSERVED_AS {lastupdated: $UPDATE_TAG}]->()\n"
        "MATCH (d:Device)-[obs:OBSERVED_AS]->(:Agent)"
    )


def test_matching_fingerprint_uses_update_tag_firstseen():
    # Arrange
    from cartography.analysis.aws.analysis import AWS_EC2_KEYPAIR_MATCHING_FINGERPRINT

    statement = AWS_EC2_KEYPAIR_MATCHING_FINGERPRINT.statements[0]

    # Act and assert
    assert "ON CREATE SET r.firstseen = $UPDATE_TAG" in compile_query(statement)


def test_statement_compiles_property_effects():
    # Arrange
    statement = AnalysisStatement(
        match="MATCH (instance:EC2Instance) WHERE instance.publicipaddress IS NOT NULL",
        effects=(
            AddToSet(
                "instance",
                "exposed_internet_type",
                "direct",
                label="EC2Instance",
            ),
            SetProperty("instance", "exposed_internet", True, label="EC2Instance"),
        ),
    )

    # Act and assert
    assert compile_query(statement) == (
        "MATCH (instance:EC2Instance) WHERE instance.publicipaddress IS NOT NULL\n"
        "SET instance.exposed_internet_type = "
        "CASE WHEN instance.exposed_internet_type IS NULL THEN ['direct'] "
        "WHEN NOT 'direct' IN instance.exposed_internet_type "
        "THEN instance.exposed_internet_type + ['direct'] "
        "ELSE instance.exposed_internet_type END\n"
        "SET instance.exposed_internet = true"
    )


def test_statement_compiles_multiple_values_to_set():
    statement = AnalysisStatement(
        match="MATCH (bucket:S3Bucket)",
        effects=(
            AddValuesToSet(
                "bucket",
                "anonymous_actions",
                ("s3:ListBucket", "s3:GetBucketAcl"),
                label="S3Bucket",
            ),
        ),
    )

    assert compile_query(statement) == (
        "MATCH (bucket:S3Bucket)\n"
        "SET bucket.anonymous_actions = "
        "CASE WHEN bucket.anonymous_actions IS NULL THEN ['s3:ListBucket'] "
        "WHEN NOT 's3:ListBucket' IN bucket.anonymous_actions "
        "THEN bucket.anonymous_actions + ['s3:ListBucket'] "
        "ELSE bucket.anonymous_actions END\n"
        "SET bucket.anonymous_actions = "
        "CASE WHEN bucket.anonymous_actions IS NULL THEN ['s3:GetBucketAcl'] "
        "WHEN NOT 's3:GetBucketAcl' IN bucket.anonymous_actions "
        "THEN bucket.anonymous_actions + ['s3:GetBucketAcl'] "
        "ELSE bucket.anonymous_actions END"
    )


def test_statement_compiles_case_expression():
    statement = AnalysisStatement(
        match="MATCH (bucket:GCPBucket)",
        effects=(
            SetProperty(
                "bucket",
                "_ont_public",
                Case(
                    when=(("bucket.disabled = true", False),),
                    else_=RawCypher("coalesce(bucket.public, false)"),
                ),
                label="GCPBucket",
            ),
        ),
    )

    assert compile_query(statement) == (
        "MATCH (bucket:GCPBucket)\n"
        "SET bucket._ont_public = CASE WHEN bucket.disabled = true THEN false "
        "ELSE coalesce(bucket.public, false) END"
    )


def test_statement_rejects_property_effect_without_label():
    # Arrange
    statement = AnalysisStatement(
        match="MATCH (n:Node)",
        effects=(SetProperty("n", "flag", True),),
    )

    # Act and assert
    with pytest.raises(ValueError, match="Property effects require label"):
        compile_query(statement)


def test_statement_rejects_mixed_raw_and_compiled_query():
    # Act and assert
    with pytest.raises(ValueError, match="query or match/effects"):
        AnalysisStatement(
            "MATCH (n) RETURN n",
            match="MATCH (n)",
            effects=(SetProperty("n", "flag", True),),
        )


def test_scoped_relationship_cleanup_targets_source_by_default():
    # Arrange
    job = AnalysisJob(
        name="GCP LB exposure",
        short_name="gcp_lb_exposure",
        scope=ScopeById("GCPProject", "PROJECT_ID", scope_on="bs"),
        statements=(
            AnalysisStatement(
                match="MATCH (bs:GCPBackendService)-[:ROUTES_TO]->(:GCPInstanceGroup)"
                "-[:HAS_MEMBER]->(i:GCPInstance)",
                effects=(
                    AddRelationship(
                        "bs",
                        "EXPOSE",
                        "i",
                        source_label="GCPBackendService",
                        target_label="GCPInstance",
                    ),
                ),
            ),
        ),
    )

    # Act
    graph_job = to_graph_job(job)

    # Assert
    assert graph_job.statements[1].query == (
        "MATCH (scope:GCPProject {id: $PROJECT_ID})-[:RESOURCE]->(source)\n"
        "MATCH (source:GCPBackendService)-[r:EXPOSE]->(target:GCPInstance)\n"
        "WHERE r.lastupdated <> $UPDATE_TAG\n"
        "WITH r LIMIT $LIMIT_SIZE\n"
        "DELETE r"
    )
    assert graph_job.statements[0].query.startswith(
        "MATCH (scope:GCPProject {id: $PROJECT_ID})-[:RESOURCE]->(bs)\n"
        "MATCH (bs:GCPBackendService)"
    )


def test_relationship_job_allows_multiple_statements_for_one_effect():
    # Arrange
    job = AnalysisJob(
        name="Resolved image analysis",
        short_name="resolved_image_analysis",
        statements=(
            AnalysisStatement(
                match="MATCH (c:Container)-[:HAS_IMAGE]->(i:Image)",
                effects=(
                    AddRelationship(
                        "c",
                        "RESOLVED_IMAGE",
                        "i",
                        source_label="Container",
                        target_label="Image",
                    ),
                ),
            ),
            AnalysisStatement(
                match="MATCH (c:Container)-[:HAS_IMAGE]->(:ImageManifestList)"
                "-[:CONTAINS_IMAGE]->(i:Image)",
                effects=(
                    AddRelationship(
                        "c",
                        "RESOLVED_IMAGE",
                        "i",
                        source_label="Container",
                        target_label="Image",
                    ),
                ),
            ),
        ),
    )

    # Act
    graph_job = to_graph_job(job)

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
        scope=ScopeById("SemgrepDeployment", "DEPLOYMENT_ID", scope_on="s"),
        statements=(
            AnalysisStatement(
                match="MATCH (g:GitHubRepository{archived:true})"
                "<-[:FOUND_IN]-(s:SemgrepSASTFinding)",
                effects=(
                    SetProperty(
                        "s",
                        "risk_severity",
                        "INFO",
                        label="SemgrepSASTFinding",
                    ),
                ),
            ),
        ),
    )

    # Act
    graph_job = to_graph_job(job)

    # Assert
    assert relationships_added(job) == ()
    assert properties_set(job) == (
        PropertyEffect("SemgrepSASTFinding", ("risk_severity",)),
    )
    assert graph_job.statements[0].query == (
        "MATCH (scope:SemgrepDeployment {id: $DEPLOYMENT_ID})"
        "-[:RESOURCE]->(node:SemgrepSASTFinding)\n"
        "WHERE node.risk_severity IS NOT NULL\n"
        "WITH node LIMIT $LIMIT_SIZE\n"
        "REMOVE node.risk_severity"
    )
    assert graph_job.statements[1].query.startswith(
        "MATCH (scope:SemgrepDeployment {id: $DEPLOYMENT_ID})"
        "-[:RESOURCE]->(s)\n"
        "MATCH (g:GitHubRepository"
    )


def test_property_effect_requires_properties():
    # Act and assert
    with pytest.raises(ValueError, match="at least one property"):
        PropertyEffect("EC2KeyPair", ())


def test_relationship_property_job_prepends_cleanup_statement():
    # Arrange
    job = AnalysisJob(
        name="Supply chain source file",
        short_name="supply_chain_source_file",
        statements=(
            AnalysisStatement(
                match="MATCH (i:Image)-[r:PACKAGED_FROM]->(:GitHubRepository) "
                "WHERE r.dockerfile_path IS NULL",
                effects=(
                    SetRelationshipProperty(
                        "r",
                        "dockerfile_path",
                        "i.source_file",
                        source_label="Image",
                        rel_label="PACKAGED_FROM",
                    ),
                ),
            ),
        ),
    )

    # Act
    graph_job = to_graph_job(job)

    # Assert
    assert properties_set(job) == (
        RelationshipPropertyEffect("Image", "PACKAGED_FROM", ("dockerfile_path",)),
    )
    assert graph_job.statements[0].query == (
        "MATCH (source:Image)-[r:PACKAGED_FROM]->(target)\n"
        "WHERE r.dockerfile_path IS NOT NULL\n"
        "WITH r LIMIT $LIMIT_SIZE\n"
        "REMOVE r.dockerfile_path"
    )


def test_relationship_property_effect_requires_properties():
    # Act and assert
    with pytest.raises(ValueError, match="at least one property"):
        RelationshipPropertyEffect("Image", "PACKAGED_FROM", ())


def test_relationship_property_if_missing_does_not_claim_cleanup_ownership():
    # Arrange
    from cartography.analysis.ontology.analysis import SUPPLY_CHAIN_SOURCE_FILE

    # Act
    graph_job = to_graph_job(SUPPLY_CHAIN_SOURCE_FILE)

    # Assert
    assert properties_set(SUPPLY_CHAIN_SOURCE_FILE) == ()
    assert len(graph_job.statements) == 1
    assert graph_job.statements[0].query == (
        "MATCH (i:Image)-[r:PACKAGED_FROM]->() "
        "WHERE r.dockerfile_path IS NULL AND i.source_file IS NOT NULL\n"
        "SET r.dockerfile_path = i.source_file"
    )
    assert "REMOVE r.dockerfile_path" not in graph_job.statements[0].query


def test_statement_compiles_relationship_property_if_missing_effect():
    statement = AnalysisStatement(
        match="MATCH (i:Image)-[r:PACKAGED_FROM]->() WHERE r.dockerfile_path IS NULL",
        effects=(
            SetRelationshipPropertyIfMissing(
                "r",
                "dockerfile_path",
                RawCypher("i.source_file"),
            ),
        ),
    )

    assert compile_query(statement) == (
        "MATCH (i:Image)-[r:PACKAGED_FROM]->() WHERE r.dockerfile_path IS NULL\n"
        "SET r.dockerfile_path = i.source_file"
    )


def test_analysis_job_requires_statements():
    # Act and assert
    with pytest.raises(ValueError, match="at least one statement"):
        AnalysisJob(
            name="empty",
            statements=(),
        )


def test_scope_by_id_requires_one_anchor_per_statement():
    statement = AnalysisStatement(
        match="MATCH (n:Node)",
        effects=(SetProperty("n", "flag", True, label="Node"),),
    )

    with pytest.raises(ValueError, match="one variable per statement"):
        AnalysisJob(
            name="invalid scope",
            statements=(statement, statement),
            scope=ScopeById("Tenant", "TENANT_ID", scope_on=("n",)),
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
