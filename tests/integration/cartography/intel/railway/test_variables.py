import cartography.intel.railway.variables
from cartography.models.railway.variable import RailwayVariableNodeProperties
from tests.integration.cartography.intel.railway.test_projects import (
    _common_job_parameters,
)
from tests.integration.cartography.intel.railway.test_projects import TEST_PROJECT_ID
from tests.integration.cartography.intel.railway.test_projects import TEST_UPDATE_TAG
from tests.integration.cartography.intel.railway.test_serviceinstances import (
    _sync_compute_tier,
)
from tests.integration.cartography.intel.railway.test_serviceinstances import BUNDLES
from tests.integration.cartography.intel.railway.test_serviceinstances import (
    POSTGRES_INSTANCE_ID,
)
from tests.integration.cartography.intel.railway.test_serviceinstances import (
    PRODUCTION_ENV_ID,
)
from tests.integration.cartography.intel.railway.test_serviceinstances import (
    WEB_INSTANCE_ID,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

FEATURE_FLAG_ID = "eb81ef18-1120-4a00-be88-91a478317532"
POSTGRES_PASSWORD_ID = "67ce0a54-a56c-4dff-a534-62c0b06ef375"


def _sync_variables(neo4j_session):
    _sync_compute_tier(neo4j_session)
    cartography.intel.railway.variables.sync(
        neo4j_session,
        _common_job_parameters(),
        BUNDLES,
        TEST_UPDATE_TAG,
    )


def test_railway_variable_schema_has_no_value_property():
    # Guard: Railway can return variable values. Cartography must never store them, so a
    # `value` property must never appear on this schema.
    property_names = {
        field.name
        for field in RailwayVariableNodeProperties.__dataclass_fields__.values()
    }
    assert "value" not in property_names


def test_load_railway_variables(neo4j_session):
    # Act
    _sync_variables(neo4j_session)

    # Assert names and the sealed flag are ingested
    loaded = check_nodes(neo4j_session, "RailwayVariable", ["id", "name", "is_sealed"])
    assert (FEATURE_FLAG_ID, "FEATURE_FLAG", False) in loaded
    assert (POSTGRES_PASSWORD_ID, "POSTGRES_PASSWORD", False) in loaded
    # The captured project had 14 variables in production and none in staging.
    assert len(loaded) == 14

    # Assert no value ever reaches the graph
    values = neo4j_session.run(
        "MATCH (v:RailwayVariable) WHERE v.value IS NOT NULL RETURN count(v) AS c",
    ).single()["c"]
    assert values == 0

    # Assert the project tenant edge
    assert check_rels(
        neo4j_session,
        "RailwayProject",
        "id",
        "RailwayVariable",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) >= {
        (TEST_PROJECT_ID, FEATURE_FLAG_ID),
    }

    # Every variable belongs to an environment
    environment_rels = check_rels(
        neo4j_session,
        "RailwayEnvironment",
        "id",
        "RailwayVariable",
        "id",
        "HAS",
        rel_direction_right=True,
    )
    assert len(environment_rels) == 14
    assert all(env_id == PRODUCTION_ENV_ID for env_id, _ in environment_rels)

    # Service-scoped variables also attach to the workload that consumes them
    usage = check_rels(
        neo4j_session,
        "RailwayServiceInstance",
        "id",
        "RailwayVariable",
        "id",
        "USES_SECRET",
        rel_direction_right=True,
    )
    assert (WEB_INSTANCE_ID, FEATURE_FLAG_ID) in usage
    assert (POSTGRES_INSTANCE_ID, POSTGRES_PASSWORD_ID) in usage

    # The Secret ontology label
    assert (FEATURE_FLAG_ID,) in check_nodes(neo4j_session, "Secret", ["id"])
