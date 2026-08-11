import cartography.models.bbot as bbot_models
from cartography.models.bbot.events import BBOT_RELATIONSHIP_CATALOG
from cartography.models.bbot.events import BBOT_SCHEMAS
from cartography.models.introspection import inspect_data_model
from cartography.models.schema_docs import GENERATED_NOTICE
from cartography.models.schema_docs import render_module_schema


def test_bbot_schema_docs_describe_runtime_relationships():
    # Arrange
    model = inspect_data_model(bbot_models)
    catalog = {
        (source_label, relationship_name, target_label)
        for source_label, relationship_name, target_label, _ in BBOT_RELATIONSHIP_CATALOG
    }
    expected_discovery_relationships = {
        (source_schema.label, "DISCOVERED_FROM", target_schema.label)
        for event_type, source_schema in BBOT_SCHEMAS.items()
        if event_type != "SCAN"
        for target_schema in BBOT_SCHEMAS.values()
    }

    # Act
    page = render_module_schema(model, "bbot")

    # Assert
    assert page.startswith(GENERATED_NOTICE)
    assert "No description provided." not in page
    assert expected_discovery_relationships <= catalog
    assert "(:BbotEmailAddress)-[:DISCOVERED_FROM]->(:BbotASN)" in page
    assert "(:BbotDNSName)-[:RESOLVES_TO]->(:BbotIPAddress)" in page
    assert "(:BbotFinding)-[:AFFECTS]->(:BbotStorageBucket)" in page
    assert "(:BbotIPAddress)-[:ANNOUNCED_BY]->(:BbotASN)" in page
