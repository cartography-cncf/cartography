from dataclasses import fields

from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.ontology.mapping.data.cves import CVES_ONTOLOGY_MAPPING
from cartography.models.ontology.mapping.data.security_issues import (
    SECURITY_ISSUES_ONTOLOGY_MAPPING,
)
from cartography.models.ontology.mapping.data.tenants import TENANTS_ONTOLOGY_MAPPING
from cartography.models.ontology.mapping.specs import OntologyFieldMapping
from cartography.models.ontology.mapping.specs import OntologyMapping
from cartography.models.orca import OrcaAlertSchema
from cartography.models.orca import OrcaOrganizationSchema
from cartography.models.orca import OrcaVulnerabilityFindingSchema

TARGET_CONTEXT_PROPERTIES = {
    "target_orca_inventory_id",
    "target_orca_asset_unique_id",
    "target_provider_id",
    "target_arn",
    "target_cloud_provider",
    "target_cloud_account_id",
    "target_region",
    "target_name",
    "target_type",
}


def _extra_labels(schema: CartographyNodeSchema) -> set[str]:
    assert schema.extra_node_labels is not None
    return {label.label for label in schema.extra_node_labels.labels}


def _mapping_fields(
    mapping: OntologyMapping,
    node_label: str,
) -> dict[str, OntologyFieldMapping]:
    node = next(node for node in mapping.nodes if node.node_label == node_label)
    return {field.ontology_field: field for field in node.fields}


def test_orca_schemas_use_supported_ontology_labels() -> None:
    # Arrange
    organization = OrcaOrganizationSchema()
    alert = OrcaAlertSchema()
    vulnerability = OrcaVulnerabilityFindingSchema()

    # Assert
    assert _extra_labels(organization) == {"Tenant"}
    assert _extra_labels(alert) == {"SecurityIssue"}
    assert _extra_labels(vulnerability) == {"CVE"}
    assert "Risk" not in {
        *_extra_labels(organization),
        *_extra_labels(alert),
        *_extra_labels(vulnerability),
    }
    assert organization.scoped_cleanup is False
    assert organization.sub_resource_relationship is None


def test_orca_child_schemas_use_flat_organization_ownership() -> None:
    # Act and assert
    for schema in (
        OrcaAlertSchema(),
        OrcaVulnerabilityFindingSchema(),
    ):
        relationship = schema.sub_resource_relationship
        assert relationship is not None
        organization_id = getattr(relationship.target_node_matcher, "id")
        organization_property = getattr(schema.properties, "organization_id")

        assert relationship.target_node_label == "OrcaOrganization"
        assert relationship.rel_label == "RESOURCE"
        assert relationship.direction is LinkDirection.INWARD
        assert organization_id.name == "ORCA_ORGANIZATION_ID"
        assert organization_id.set_in_kwargs is True
        assert organization_property.name == "ORCA_ORGANIZATION_ID"
        assert organization_property.set_in_kwargs is True


def test_orca_findings_do_not_create_asset_relationships() -> None:
    # Act and assert
    for schema in (OrcaAlertSchema(), OrcaVulnerabilityFindingSchema()):
        assert schema.other_relationships is None


def test_orca_findings_retain_consistent_target_context() -> None:
    # Act and assert
    for schema in (OrcaAlertSchema(), OrcaVulnerabilityFindingSchema()):
        properties = {
            model_field.name: getattr(schema.properties, model_field.name)
            for model_field in fields(schema.properties)
        }

        assert TARGET_CONTEXT_PROPERTIES <= properties.keys()
        for property_name in TARGET_CONTEXT_PROPERTIES:
            assert properties[property_name].name == property_name

        for property_name in {
            "target_orca_inventory_id",
            "target_orca_asset_unique_id",
            "target_provider_id",
            "target_arn",
            "target_cloud_account_id",
        }:
            assert properties[property_name].extra_index is True

        for property_name in {"target_name", "target_region", "target_type"}:
            assert properties[property_name].extra_index is False


def test_orca_node_properties_are_documented() -> None:
    # Act and assert
    for schema in (
        OrcaOrganizationSchema(),
        OrcaAlertSchema(),
        OrcaVulnerabilityFindingSchema(),
    ):
        undocumented = [
            model_field.name
            for model_field in fields(schema.properties)
            if not getattr(schema.properties, model_field.name).description
        ]

        assert undocumented == []


def test_orca_ontology_mappings_use_provider_semantics() -> None:
    # Arrange
    tenant_fields = _mapping_fields(
        TENANTS_ONTOLOGY_MAPPING["orca"],
        "OrcaOrganization",
    )
    alert_fields = _mapping_fields(
        SECURITY_ISSUES_ONTOLOGY_MAPPING["orca"],
        "OrcaAlert",
    )
    vulnerability_fields = _mapping_fields(
        CVES_ONTOLOGY_MAPPING["orca"],
        "OrcaVulnerabilityFinding",
    )

    # Assert
    assert tenant_fields["name"].node_field == "name"
    assert tenant_fields["name"].required is True

    assert alert_fields["title"].node_field == "title"
    assert alert_fields["title"].required is True
    assert alert_fields["type"].node_field == "alert_type"
    assert alert_fields["first_seen"].node_field == "created_at"
    assert alert_fields["severity"].extra["map"]["critical"] == "critical"
    assert "unknown" not in alert_fields["severity"].extra["map"]
    assert alert_fields["status"].extra["map"] == {
        "open": "open",
        "in_progress": "open",
        "close": "fixed",
        "dismiss": "ignored",
        "OPEN": "open",
        "IN_PROGRESS": "open",
        "CLOSE": "fixed",
        "DISMISS": "ignored",
    }

    assert set(vulnerability_fields) == {
        "cve_id",
        "description",
        "references",
        "vector_string",
        "base_score",
        "base_severity",
    }
    assert vulnerability_fields["cve_id"].node_field == "cve_id"
    assert vulnerability_fields["description"].indexed is False
    assert vulnerability_fields["references"].indexed is False
    assert vulnerability_fields["base_severity"].extra["map"]["LOW"] == "low"
