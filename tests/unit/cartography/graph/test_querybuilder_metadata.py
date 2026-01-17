from cartography.graph.querybuilder import _get_module_from_schema
from cartography.models.aws.cloudtrail.trail import CloudTrailTrailSchema
from cartography.models.aws.identitycenter.awspermissionset import (
    AWSRoleToSSOUserMatchLink,
)
from cartography.models.tailscale.user import TailscaleUserToTailnetRel
from tests.data.graph.querybuilder.sample_models.simple_node import SimpleNodeSchema


def test_querybuilder_metadata_module_name():
    # Regular Node Schema
    assert _get_module_from_schema(CloudTrailTrailSchema()) == "cartography:aws"
    # Regular Relationship Schema
    assert _get_module_from_schema(TailscaleUserToTailnetRel) == "cartography:tailscale"
    # Regular MatchLink Schema
    assert _get_module_from_schema(AWSRoleToSSOUserMatchLink) == "cartography:aws"


def test_querybuilder_metadata_external_module_name():
    # Test for Schema defined outside of cartography.models
    assert (
        _get_module_from_schema(SimpleNodeSchema)
        == "unknown:tests.data.graph.querybuilder.sample_models.simple_node"
    )
