from cartography.graph.querybuilder import build_create_index_queries
from cartography.models.aws.dynamodb.tables import DynamoDBTableSchema
from cartography.models.aws.emr import EMRClusterSchema
from cartography.models.trivy.findings import TrivyImageFindingSchema
from tests.data.graph.querybuilder.sample_models.interesting_asset import (
    InterestingAssetSchema,
)


def test_build_create_index_queries():
    result = build_create_index_queries(InterestingAssetSchema())
    assert set(result) == {
        "CREATE INDEX IF NOT EXISTS FOR (n:InterestingAsset) ON (n.id);",
        "CREATE INDEX IF NOT EXISTS FOR (n:InterestingAsset) ON (n.lastupdated);",
        "CREATE INDEX IF NOT EXISTS FOR (n:AnotherNodeLabel) ON (n.id);",
        "CREATE INDEX IF NOT EXISTS FOR (n:AnotherNodeLabel) ON (n.lastupdated);",
        "CREATE INDEX IF NOT EXISTS FOR (n:YetAnotherNodeLabel) ON (n.id);",
        "CREATE INDEX IF NOT EXISTS FOR (n:YetAnotherNodeLabel) ON (n.lastupdated);",
        "CREATE INDEX IF NOT EXISTS FOR (n:SubResource) ON (n.id);",
        "CREATE INDEX IF NOT EXISTS FOR (n:HelloAsset) ON (n.id);",
        "CREATE INDEX IF NOT EXISTS FOR (n:WorldAsset) ON (n.id);",
    }


def test_build_create_index_queries_for_emr():
    """
    The EMR sync is our poster child for testing out the Cartography data model. This is a realistic scenario of index
    creation.
    """
    result = build_create_index_queries(EMRClusterSchema())
    assert {
        "CREATE INDEX IF NOT EXISTS FOR (n:EMRCluster) ON (n.id);",
        "CREATE INDEX IF NOT EXISTS FOR (n:EMRCluster) ON (n.lastupdated);",
        "CREATE INDEX IF NOT EXISTS FOR (n:AWSAccount) ON (n.id);",
        "CREATE INDEX IF NOT EXISTS FOR (n:EMRCluster) ON (n.arn);",
        "CREATE INDEX IF NOT EXISTS FOR (n:ComputeCluster) ON (n.id);",
    }.issubset(set(result))

    assert {
        "CREATE INDEX IF NOT EXISTS FOR (n:ComputeCluster) ON (n._ont_source);",
        "CREATE INDEX IF NOT EXISTS FOR (n:ComputeCluster) ON (n._ont_name);",
        "CREATE INDEX IF NOT EXISTS FOR (n:ComputeCluster) ON (n._ont_region);",
        "CREATE INDEX IF NOT EXISTS FOR (n:ComputeCluster) ON (n._ont_version);",
    }.issubset(set(result))


def test_build_create_index_queries_skips_unindexed_ontology_fields():
    """
    Unbounded ontology fields (references, description, problem_types) declare indexed=False
    so they do not get a RANGE index on the semantic labels. Their `_ont_<field>` values can
    exceed Neo4j's index value limit (~8 KB) and crash the sync. Bounded fields and _ont_source
    must still be indexed. TrivyImageFinding carries the "Risk" and "CVE" semantic labels.
    """
    result = set(build_create_index_queries(TrivyImageFindingSchema()))

    for label in ("Risk", "CVE"):
        for field in ("references", "description", "problem_types"):
            assert (
                f"CREATE INDEX IF NOT EXISTS FOR (n:{label}) ON (n._ont_{field});"
                not in result
            )

    # Bounded ontology fields and _ont_source are still indexed on the semantic labels.
    assert {
        "CREATE INDEX IF NOT EXISTS FOR (n:Risk) ON (n._ont_source);",
        "CREATE INDEX IF NOT EXISTS FOR (n:Risk) ON (n._ont_cve_id);",
        "CREATE INDEX IF NOT EXISTS FOR (n:CVE) ON (n._ont_source);",
        "CREATE INDEX IF NOT EXISTS FOR (n:CVE) ON (n._ont_cve_id);",
    }.issubset(result)


def test_build_create_index_queries_for_dynamodb_table_arn():
    result = build_create_index_queries(DynamoDBTableSchema())

    assert "CREATE INDEX IF NOT EXISTS FOR (n:DynamoDBTable) ON (n.arn);" in result
