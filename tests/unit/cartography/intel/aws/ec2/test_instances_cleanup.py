from unittest.mock import MagicMock
from unittest.mock import patch

from cartography.intel.aws.ec2.instances import cleanup
from cartography.intel.aws.ec2.instances import EC2_INSTANCE_CLEANUP_ITERATIONSIZE
from cartography.models.aws.ec2.instances import EC2InstanceSchema

FAKE_COMMON_JOB_PARAMETERS = {
    "UPDATE_TAG": 123456789,
    "AWS_ID": "123456789012",
}


def test_ec2_instance_cleanup_uses_reduced_iterationsize():
    """
    EC2Instance cleanup uses DETACH DELETE, which deletes every relationship on each
    matched node, not just the ones EC2InstanceSchema declares. Measured against a large
    production account, this made a default-sized (10000) batch touch over 700K
    relationships. cleanup() must ask for a much smaller iterationsize specifically for
    EC2InstanceSchema so a single DETACH DELETE batch's relationship-delete volume stays
    in the same order of magnitude that default assumes.
    """
    with patch(
        "cartography.intel.aws.ec2.instances.GraphJob.from_node_schema",
    ) as mock_from_node_schema:
        mock_from_node_schema.return_value = MagicMock()

        cleanup(MagicMock(), FAKE_COMMON_JOB_PARAMETERS)

        ec2_instance_calls = [
            call
            for call in mock_from_node_schema.call_args_list
            if isinstance(call.args[0] if call.args else None, EC2InstanceSchema)
        ]
        assert len(ec2_instance_calls) == 1, (
            "cleanup() must call GraphJob.from_node_schema(EC2InstanceSchema(), ...) "
            "exactly once"
        )

        _args, kwargs = ec2_instance_calls[0]
        assert kwargs.get("iterationsize") == EC2_INSTANCE_CLEANUP_ITERATIONSIZE
        assert EC2_INSTANCE_CLEANUP_ITERATIONSIZE < 10000, (
            "the whole point of this override is to be smaller than the "
            "GraphJob.from_node_schema default of 10000"
        )


def test_ec2_instance_cleanup_does_not_override_iterationsize_for_other_schemas():
    """
    The reduced iterationsize is specific to EC2InstanceSchema's DETACH DELETE fan-out
    problem. Other schemas cleaned up in the same function (EC2Reservation,
    EC2InstanceAutoScalingGroup, EC2Ipv6Address) have no measured fan-out issue and
    should keep using GraphJob.from_node_schema's own default.
    """
    with patch(
        "cartography.intel.aws.ec2.instances.GraphJob.from_node_schema",
    ) as mock_from_node_schema:
        mock_from_node_schema.return_value = MagicMock()

        cleanup(MagicMock(), FAKE_COMMON_JOB_PARAMETERS)

        non_ec2_instance_calls = [
            call
            for call in mock_from_node_schema.call_args_list
            if not isinstance(call.args[0] if call.args else None, EC2InstanceSchema)
        ]
        assert len(non_ec2_instance_calls) == 3

        for _args, kwargs in non_ec2_instance_calls:
            assert "iterationsize" not in kwargs
