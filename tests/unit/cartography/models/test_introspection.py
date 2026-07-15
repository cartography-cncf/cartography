from dataclasses import dataclass
from typing import ClassVar

import cartography.analysis.gsuite as gsuite_analysis
import cartography.analysis.ontology as ontology_analysis
import cartography.models.gcp as gcp_models
import cartography.models.github as github_models
import cartography.models.lastpass as lastpass_models
from cartography.analysis.ontology.analysis import DNS_RECORD_LINKING_JOBS
from cartography.graph.analysis import AddRelationship
from cartography.graph.analysis import AnalysisJob
from cartography.graph.analysis import AnalysisStatement
from cartography.graph.analysis import SetProperty
from cartography.graph.analysis import SetRelationshipPropertyIfMissing
from cartography.models.aws.ec2.instances import EC2InstanceSchema
from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ConditionalNodeLabel
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_source_node_matcher
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import SourceNodeMatcher
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.gcp.artifact_registry.image import (
    GCPArtifactRegistryImageSchema,
)
from cartography.models.gcp.artifact_registry.image_layer import (
    GCPArtifactRegistryImageLayerSchema,
)
from cartography.models.gcp.artifact_registry.repository_image import (
    GCPArtifactRegistryRepositoryImageSchema,
)
from cartography.models.introspection import AnalysisJobDefinition
from cartography.models.introspection import build_data_model
from cartography.models.introspection import inspect_data_model
from cartography.models.introspection import iter_analysis_jobs
from cartography.models.introspection import iter_model_classes
from cartography.models.introspection import iter_permission_relationships
from cartography.models.introspection import PermissionRelationshipDefinition
from cartography.models.jamf.computer import JamfComputerSchema
from cartography.models.semgrep.dependencies import SemgrepGoLibrarySchema
from cartography.models.semgrep.dependencies import SemgrepNpmLibrarySchema


@dataclass(frozen=True)
class SampleNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("Id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    email: PropertyRef = PropertyRef(
        "Email",
        extra_index=True,
        description="Primary email address.",
    )


@dataclass(frozen=True)
class SampleRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SampleNodeToTenantRel(CartographyRelSchema):
    """The tenant contains the sample node."""

    target_node_label: str = "SampleTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENANT_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SampleRelProperties = SampleRelProperties()


@dataclass(frozen=True)
class SampleNodeToTargetRel(CartographyRelSchema):
    """The sample node points to its target."""

    target_node_label: str = "SampleTarget"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TargetId")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "POINTS_TO"
    properties: SampleRelProperties = SampleRelProperties()


@dataclass(frozen=True)
class SampleNodeSchema(CartographyNodeSchema):
    """A node used to verify runtime model introspection."""

    label: str = "SampleNode"
    properties: SampleNodeProperties = SampleNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [
            "Sample",
            ConditionalNodeLabel("ActiveSample", {"active": "true"}),
        ]
    )
    sub_resource_relationship: SampleNodeToTenantRel = SampleNodeToTenantRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [SampleNodeToTargetRel()]
    )


@dataclass(frozen=True)
class IntrospectionExcludedSampleSchema(CartographyNodeSchema):
    """A runtime-only schema template."""

    __cartography_introspection_exclude__: ClassVar[bool] = True
    label: str = "ExcludedSample"
    properties: SampleNodeProperties = SampleNodeProperties()


@dataclass(frozen=True)
class SampleMatchLink(CartographyRelSchema):
    """Links an existing sample node to an existing peer."""

    source_node_label: str = "SampleNode"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("SourceId")}
    )
    target_node_label: str = "SamplePeer"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PeerId")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "PEERS_WITH"
    properties: SampleRelProperties = SampleRelProperties()


SAMPLE_ANALYSIS_JOB = AnalysisJob(
    name="Sample model analysis",
    short_name="sample_model_analysis",
    statements=(
        AnalysisStatement(
            match="MATCH (sample:SampleNode)-[peer:PEERS_WITH]->(:SamplePeer)",
            effects=(
                SetProperty(
                    "sample",
                    "analyzed",
                    True,
                    label="SampleNode",
                ),
                SetRelationshipPropertyIfMissing(
                    "peer",
                    "confidence",
                    1,
                    source_label="SampleNode",
                    rel_label="PEERS_WITH",
                    target_label="SamplePeer",
                ),
                AddRelationship(
                    "sample",
                    "ANALYZED_AS",
                    "peer",
                    source_label="SampleNode",
                    target_label="SamplePeer",
                    properties={"method": "sample"},
                ),
                AddRelationship(
                    "sample",
                    "MATCHES",
                    "peer",
                    source_label="SampleNode",
                    target_label="SamplePeer",
                    undirected=True,
                ),
            ),
        ),
    ),
)
SAMPLE_ANALYSIS_DEFINITION = AnalysisJobDefinition(
    job=SAMPLE_ANALYSIS_JOB,
    module="sample",
    qualified_name="sample.analysis.SAMPLE_ANALYSIS_JOB",
)


def test_build_data_model_introspects_nodes_properties_and_relationships():
    # Arrange
    model_classes = [
        SampleNodeSchema,
        SampleNodeToTenantRel,
        SampleNodeToTargetRel,
        SampleMatchLink,
    ]

    # Act
    model = build_data_model(model_classes)

    # Assert
    node = model.get_node("SampleNode")
    assert node is not None
    assert node.descriptions == ("A node used to verify runtime model introspection.",)
    assert node.extra_labels == ("Sample",)
    assert tuple(label.label for label in node.conditional_labels) == ("ActiveSample",)

    email = node.get_property("email")
    assert email is not None
    assert email.source_names == ("Email",)
    assert email.descriptions == ("Primary email address.",)
    assert email.indexed
    assert not email.ontology

    firstseen = node.get_property("firstseen")
    assert firstseen is not None
    assert not firstseen.ontology
    assert firstseen.generated_by == ("querybuilder",)

    relationships = {
        (
            relationship.source_label,
            relationship.label,
            relationship.target_label,
        ): relationship
        for relationship in model.relationships
    }
    assert ("SampleTenant", "RESOURCE", "SampleNode") in relationships
    assert ("SampleNode", "POINTS_TO", "SampleTarget") in relationships
    assert ("SampleNode", "PEERS_WITH", "SamplePeer") in relationships
    assert relationships[("SampleNode", "PEERS_WITH", "SamplePeer")].origins == (
        "matchlink",
    )


def test_build_data_model_skips_runtime_only_schema_templates():
    model = build_data_model([SampleNodeSchema, IntrospectionExcludedSampleSchema])

    assert model.get_node("SampleNode") is not None
    assert model.get_node("ExcludedSample") is None


def test_build_data_model_classifies_semantic_labels_without_normalized_fields():
    model = build_data_model(
        [
            GCPArtifactRegistryImageSchema,
            GCPArtifactRegistryImageLayerSchema,
            GCPArtifactRegistryRepositoryImageSchema,
        ]
    )

    image = model.get_node("GCPArtifactRegistryImage")
    layer = model.get_node("GCPArtifactRegistryImageLayer")
    tag = model.get_node("GCPArtifactRegistryRepositoryImage")
    assert image is not None
    assert layer is not None
    assert tag is not None
    assert {"ImageAttestation", "ImageManifestList"} <= set(image.ontology_labels)
    assert "ImageLayer" in layer.ontology_labels
    assert "ImageTag" in tag.ontology_labels


def test_gcp_composite_nodes_preserve_partial_label_provenance():
    model = inspect_data_model(gcp_models)

    label = model.get_node("GCPLabel")
    subnet = model.get_node("GCPSubnet")
    assert label is not None
    assert subnet is not None
    assert label.extra_labels == ("GCPBucketLabel", "Label", "Tag")
    assert label.partial_extra_labels == ("GCPBucketLabel", "Tag")
    assert subnet.extra_labels == ("Subnet",)
    assert subnet.partial_extra_labels == ("Subnet",)


def test_build_data_model_introspects_typed_analysis_effects():
    # Act
    model = build_data_model(
        [SampleNodeSchema, SampleMatchLink],
        [SAMPLE_ANALYSIS_DEFINITION],
    )

    # Assert
    node = model.get_node("SampleNode")
    assert node is not None
    analyzed = node.get_property("analyzed")
    assert analyzed is not None
    assert analyzed.generated_by == ("analysis:sample_model_analysis",)
    assert analyzed.analysis_jobs == (SAMPLE_ANALYSIS_DEFINITION,)

    relationships = {
        (
            relationship.source_label,
            relationship.label,
            relationship.target_label,
        ): relationship
        for relationship in model.relationships
    }
    analyzed_as = relationships[("SampleNode", "ANALYZED_AS", "SamplePeer")]
    assert analyzed_as.origins == ("analysis",)
    assert analyzed_as.direction == LinkDirection.OUTWARD
    assert analyzed_as.analysis_jobs == (SAMPLE_ANALYSIS_DEFINITION,)
    assert {prop.name for prop in analyzed_as.properties} == {
        "firstseen",
        "lastupdated",
        "method",
    }

    peers_with = relationships[("SampleNode", "PEERS_WITH", "SamplePeer")]
    assert peers_with.origins == ("analysis", "matchlink")
    assert {prop.name for prop in peers_with.properties} == {
        "confidence",
        "firstseen",
        "lastupdated",
    }
    assert relationships[("SampleNode", "MATCHES", "SamplePeer")].direction is None


def test_build_data_model_adds_generated_ontology_properties():
    # Act
    model = build_data_model([EC2InstanceSchema])

    # Assert
    node = model.get_node("AWSEC2Instance")
    assert node is not None
    ontology_name = node.get_property("_ont_name")
    assert ontology_name is not None
    assert ontology_name.ontology
    assert ontology_name.generated_by == ("ontology",)
    assert ontology_name.indexed
    assert ontology_name.source_names == ("instanceid",)
    ontology_source = node.get_property("_ont_source")
    assert ontology_source is not None
    assert ontology_source.ontology
    assert ontology_source.generated_by == ("ontology",)
    assert node.ontology_labels == ("ComputeInstance",)


def test_build_data_model_exposes_ontology_catalog_metadata():
    # Act
    model = build_data_model([EC2InstanceSchema])

    # Assert
    semantic_labels = {
        semantic_label.label: semantic_label
        for semantic_label in model.ontology_semantic_labels
    }
    compute_instance = semantic_labels["ComputeInstance"]
    assert "AWSEC2Instance" in compute_instance.concrete_node_labels
    assert {prop.name for prop in compute_instance.properties} >= {
        "_ont_name",
        "_ont_public_ip_address",
        "_ont_source",
    }
    assert semantic_labels["ImageTag"].mapping_group is None

    constraints = {
        (
            constraint.source_label,
            constraint.label,
            constraint.target_label,
        )
        for constraint in model.ontology_relationship_constraints
    }
    assert len(constraints) == 36
    assert ("ComputePod", "USES_SECRET", "Secret") in constraints
    assert ("Container", "RESOLVED_IMAGE", "Image") in constraints


def test_build_data_model_distinguishes_canonical_ontology_projections():
    # Act
    model = build_data_model([JamfComputerSchema])

    # Assert
    node = model.get_node("JamfComputer")
    assert node is not None
    assert node.ontology_projections == ("Device",)
    assert not any(prop.name.startswith("_ont_") for prop in node.properties)


def test_build_data_model_projects_nodes_through_additional_labels():
    # Act
    model = build_data_model([SemgrepGoLibrarySchema, SemgrepNpmLibrarySchema])

    # Assert
    for node_label in ("SemgrepGoLibrary", "SemgrepNpmLibrary"):
        node = model.get_node(node_label)
        assert node is not None
        assert node.ontology_projections == ("Package",)


def test_iter_model_classes_discovers_each_defined_model_once():
    # Act
    model_classes = list(iter_model_classes(lastpass_models))

    # Assert
    qualified_names = [
        f"{model_class.__module__}.{model_class.__qualname__}"
        for model_class in model_classes
    ]
    assert qualified_names == sorted(set(qualified_names))
    assert any(
        model_class.__name__ == "LastpassUserSchema" for model_class in model_classes
    )


def test_iter_model_classes_skips_private_bases_and_discovers_public_subclasses():
    # Act
    model_class_names = {
        model_class.__name__ for model_class in iter_model_classes(github_models)
    }

    # Assert
    assert "_GitHubCollaboratorSchema" not in model_class_names
    assert "GitHubDirectCollaboratorAdminSchema" in model_class_names
    assert "GitHubOutsideCollaboratorWriteSchema" in model_class_names


def test_iter_analysis_jobs_discovers_each_defined_job_once():
    # Act
    definitions = list(iter_analysis_jobs(gsuite_analysis))

    # Assert
    assert [definition.qualified_name for definition in definitions] == [
        "cartography.analysis.gsuite.analysis.GSUITE_HUMAN_LINK"
    ]
    assert definitions[0].module == "gsuite"


def test_iter_analysis_jobs_discovers_jobs_stored_in_tuples():
    # Act
    definitions = list(iter_analysis_jobs(ontology_analysis))

    # Assert
    discovered_job_ids = {id(definition.job) for definition in definitions}
    assert {id(job) for job in DNS_RECORD_LINKING_JOBS} <= discovered_job_ids
    assert len(discovered_job_ids) == len(definitions)


def test_iter_permission_relationships_discovers_provider_yaml_definitions():
    # Act
    definitions = list(iter_permission_relationships())

    # Assert
    assert (
        PermissionRelationshipDefinition(
            provider="aws",
            source_label="AWSPrincipal",
            target_label="AWSS3Bucket",
            relationship_name="CAN_READ",
            permissions=("S3:GetObject",),
            config_path="cartography/data/permission_relationships.yaml",
        )
        in definitions
    )
    azure_sql_sources = {
        definition.source_label
        for definition in definitions
        if definition.provider == "azure"
        and definition.target_label == "AzureSQLServer"
        and definition.relationship_name == "CAN_READ"
    }
    assert azure_sql_sources == {
        "EntraUser",
        "EntraGroup",
        "EntraServicePrincipal",
    }


def test_build_data_model_adds_permission_evaluation_relationships():
    # Arrange
    definition = PermissionRelationshipDefinition(
        provider="gcp",
        source_label="GCPPrincipal",
        target_label="GCPBucket",
        relationship_name="CAN_READ",
        permissions=("storage.objects.get",),
        config_path="cartography/data/gcp_permission_relationships.yaml",
    )

    # Act
    model = build_data_model([], permission_relationships=(definition,))

    # Assert
    relationship = model.relationships[0]
    assert relationship.source_label == "GCPPrincipal"
    assert relationship.target_label == "GCPBucket"
    assert relationship.label == "CAN_READ"
    assert relationship.direction is LinkDirection.OUTWARD
    assert relationship.modules == ("gcp",)
    assert relationship.origins == ("permission_evaluation",)
    assert relationship.permission_relationships == (definition,)
    assert {prop.name for prop in relationship.properties} == {
        "firstseen",
        "lastupdated",
        "has_condition",
        "condition_title",
        "condition_expression",
    }
    assert model.permission_relationships == (definition,)
