from dataclasses import dataclass

import cartography.analysis.gsuite as gsuite_analysis
import cartography.analysis.ontology as ontology_analysis
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
from cartography.models.introspection import AnalysisJobDefinition
from cartography.models.introspection import build_data_model
from cartography.models.introspection import iter_analysis_jobs
from cartography.models.introspection import iter_model_classes


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
    node = model.get_node("EC2Instance")
    assert node is not None
    ontology_name = node.get_property("_ont_name")
    assert ontology_name is not None
    assert ontology_name.ontology
    assert ontology_name.generated_by == ("ontology",)
    assert ontology_name.indexed
    assert ontology_name.source_names == ("instanceid",)
    assert node.ontology_labels == ("ComputeInstance",)


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
