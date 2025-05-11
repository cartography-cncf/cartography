from cartography.graph.querybuilder import build_create_index_queries
from cartography.models.aws.emr import EMRClusterSchema
from tests.data.graph.querybuilder.sample_models.interesting_asset import (
    InterestingAssetSchema,
)


def test_build_create_index_queries():
    result = build_create_index_queries(InterestingAssetSchema())
    assert set(result) == {
        "CREATE INDEX IF NOT EXISTS FOR (n:InterestingAsset) ON (n.id);",
        "CREATE INDEX IF NOT EXISTS FOR (n:InterestingAsset) ON (n.lastupdated);",
        "CREATE INDEX IF NOT EXISTS FOR (n:AnotherNodeLabel) ON (n.id);",
        "CREATE INDEX IF NOT EXISTS FOR (n:YetAnotherNodeLabel) ON (n.id);",
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
    assert set(result) == {
        "CREATE INDEX IF NOT EXISTS FOR (n:EMRCluster) ON (n.id);",
        "CREATE INDEX IF NOT EXISTS FOR (n:EMRCluster) ON (n.lastupdated);",
        "CREATE INDEX IF NOT EXISTS FOR (n:AWSAccount) ON (n.id);",
        "CREATE INDEX IF NOT EXISTS FOR (n:EMRCluster) ON (n.arn);",
    }
