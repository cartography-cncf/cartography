from dataclasses import dataclass

from cartography.models.aws.extra_labels import LEGACY_GLUE_JOB
from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class GlueJobNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "Name", description="The name you assign to this job definition"
    )
    arn: PropertyRef = PropertyRef(
        "Name",
        extra_index=True,
        description="The name you assign to this job definition",
    )
    profile_name: PropertyRef = PropertyRef(
        "ProfileName",
        description="The name of an AWS Glue usage profile associated with the job",
    )
    job_mode: PropertyRef = PropertyRef(
        "JobMode", description="A mode that describes how a job was created"
    )
    connections: PropertyRef = PropertyRef(
        "Connections", description="The connections used for this job"
    )
    region: PropertyRef = PropertyRef(
        "Region", set_in_kwargs=True, description="The region of the Glue job"
    )
    description: PropertyRef = PropertyRef(
        "Description", description="The description of the job"
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GlueJobToAwsAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GlueJobToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GlueJobToAwsAccountRelProperties = GlueJobToAwsAccountRelProperties()


@dataclass(frozen=True)
class GlueJobToGlueConnectionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GlueJobToGlueConnectionRel(CartographyRelSchema):
    target_node_label: str = "AWSGlueConnection"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("Connections", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES"
    properties: GlueJobToGlueConnectionRelProperties = (
        GlueJobToGlueConnectionRelProperties()
    )


@dataclass(frozen=True)
class GlueJobSchema(CartographyNodeSchema):
    """Representation of an AWS [Glue Job](https://docs.aws.amazon.com/glue/latest/webapi/API_GetJobs.html)"""

    label: str = "AWSGlueJob"
    # DEPRECATED: legacy GlueJob node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([LEGACY_GLUE_JOB])
    properties: GlueJobNodeProperties = GlueJobNodeProperties()
    sub_resource_relationship: GlueJobToAWSAccountRel = GlueJobToAWSAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GlueJobToGlueConnectionRel(),
        ]
    )
