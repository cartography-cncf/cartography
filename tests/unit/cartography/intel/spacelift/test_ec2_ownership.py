from cartography.intel.spacelift.ec2_ownership import transform_ec2_ownership
from cartography.models.spacelift.cloudtrailevent import (
    CloudTrailSpaceliftEventNodeProperties,
)

SPACELIFT_USER_IDENTITY = (
    "arn=arn:aws:sts::000000000000:assumed-role/"
    "SpaceLift-Administrator-Access/run-1@spacelift.io"
)


def _start_instances_record(**overrides):
    record = {
        "eventid": "45f1164a-cba5-4169-8b09-8066a2634d9b",
        "useridentity": SPACELIFT_USER_IDENTITY,
        "eventtime": "2024-01-01T10:00:00Z",
        "eventname": "StartInstances",
        "account": "000000000000",
        "awsregion": "us-east-1",
        "requestparameters": '{"instancesSet":{"items":[{"instanceId":"i-01234567"}]}}',
    }
    record.update(overrides)
    return record


def test_transform_leaves_error_code_null_for_successful_calls():
    # Arrange
    cloudtrail_data = [_start_instances_record()]

    # Act
    events = transform_ec2_ownership(cloudtrail_data)

    # Assert
    assert len(events) == 1
    assert events[0]["event_name"] == "StartInstances"
    assert events[0]["instance_ids"] == ["i-01234567"]
    assert events[0]["error_code"] is None
    assert events[0]["error_message"] is None


def test_transform_keeps_failed_calls_and_records_the_error():
    # Arrange
    cloudtrail_data = [
        _start_instances_record(
            errorcode="AccessDenied",
            errormessage="User is not authorized to perform ec2:StartInstances",
        )
    ]

    # Act
    events = transform_ec2_ownership(cloudtrail_data)

    # Assert
    # The failed call is still a CloudTrail fact, so the event is kept with the same
    # event name and instance ids; only error_code tells it apart from a real mutation.
    assert len(events) == 1
    assert events[0]["event_name"] == "StartInstances"
    assert events[0]["instance_ids"] == ["i-01234567"]
    assert events[0]["error_code"] == "AccessDenied"
    assert (
        events[0]["error_message"]
        == "User is not authorized to perform ec2:StartInstances"
    )


def test_schema_exposes_cloudtrail_error_status():
    # Arrange
    properties = CloudTrailSpaceliftEventNodeProperties()

    # Act
    # (nothing to do: we are asserting on the declared schema documentation)

    # Assert
    # The writer emits both fields, so the generated schema docs must declare them.
    assert properties.error_code.name == "error_code"
    assert properties.error_message.name == "error_message"
