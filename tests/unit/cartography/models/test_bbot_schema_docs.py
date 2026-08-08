import cartography.models.bbot as bbot_models
from cartography.models.introspection import inspect_data_model
from cartography.models.schema_docs import GENERATED_NOTICE
from cartography.models.schema_docs import render_module_schema


def test_bbot_schema_docs_describe_runtime_relationships():
    # Arrange
    model = inspect_data_model(bbot_models)

    # Act
    page = render_module_schema(model, "bbot")

    # Assert
    assert page.startswith(GENERATED_NOTICE)
    assert "No description provided." not in page
    assert "(:BbotDNSName)-[:RESOLVES_TO]->(:BbotIPAddress)" in page
    assert "(:BbotFinding)-[:AFFECTS]->(:BbotStorageBucket)" in page
    assert "(:BbotIPAddress)-[:ANNOUNCED_BY]->(:BbotASN)" in page
