from dataclasses import fields

from cartography.models.core.common import PropertyRef
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
from cartography.models.orca import OrcaAssetSchema
from cartography.models.orca import OrcaOrganizationSchema
from cartography.models.orca import OrcaVulnerabilitySchema


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
    vulnerability = OrcaVulnerabilitySchema()

    # Act and assert
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
    for schema in (
        OrcaAssetSchema(),
        OrcaAlertSchema(),
        OrcaVulnerabilitySchema(),
    ):
        # Act
        relationship = schema.sub_resource_relationship
        assert relationship is not None
        organization_id = getattr(relationship.target_node_matcher, "id")
        organization_property = getattr(schema.properties, "organization_id")

        # Assert
        assert relationship.target_node_label == "OrcaOrganization"
        assert relationship.rel_label == "RESOURCE"
        assert relationship.direction is LinkDirection.INWARD
        assert organization_id.name == "ORCA_ORGANIZATION_ID"
        assert organization_id.set_in_kwargs is True
        assert organization_property.name == "ORCA_ORGANIZATION_ID"
        assert organization_property.set_in_kwargs is True


def test_orca_findings_affect_orca_assets() -> None:
    for schema in (OrcaAlertSchema(), OrcaVulnerabilitySchema()):
        # Act
        assert schema.other_relationships is not None
        relationships = [
            relationship
            for relationship in schema.other_relationships.rels
            if relationship.rel_label == "AFFECTS"
        ]

        # Assert
        assert len(relationships) == 1
        relationship = relationships[0]
        assert relationship.target_node_label == "OrcaAsset"
        assert relationship.direction is LinkDirection.OUTWARD
        current_asset = getattr(relationship.target_node_matcher, "lastupdated")
        assert current_asset.name == "lastupdated"
        assert current_asset.set_in_kwargs is True
        if schema.label == "OrcaAlert":
            assert getattr(relationship.target_node_matcher, "id").name == "asset_id"
        else:
            organization_id = getattr(
                relationship.target_node_matcher,
                "organization_id",
            )
            asset_unique_id = getattr(
                relationship.target_node_matcher,
                "asset_unique_id",
            )
            assert organization_id.name == "ORCA_ORGANIZATION_ID"
            assert organization_id.set_in_kwargs is True
            assert asset_unique_id.name == "asset_unique_id"


def test_orca_node_properties_are_documented() -> None:
    for schema in (
        OrcaOrganizationSchema(),
        OrcaAssetSchema(),
        OrcaAlertSchema(),
        OrcaVulnerabilitySchema(),
    ):
        # Act
        undocumented = [
            model_field.name
            for model_field in fields(schema.properties)
            if isinstance(
                property_ref := getattr(schema.properties, model_field.name),
                PropertyRef,
            )
            and not property_ref.description
        ]

        # Assert
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
        "OrcaVulnerability",
    )

    # Act and assert
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
