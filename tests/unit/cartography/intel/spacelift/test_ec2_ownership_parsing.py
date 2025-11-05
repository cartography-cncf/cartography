"""
Unit tests for EC2 ownership parsing functions with real CloudTrail data formats.
"""

from cartography.intel.spacelift.ec2_ownership import extract_instance_ids
from cartography.intel.spacelift.ec2_ownership import extract_spacelift_run_id


def test_extract_spacelift_run_id_hive_struct_format():
    """Test extraction from real Athena Hive struct format."""
    # Real format from Athena storage
    useridentity_str = (
        "{type=AssumedRole, principalid=AROAZT5MTNTJ2MJ4K6W7D:01K6DZ7S8Q1CN6YW2VW82JCYYX@workload-prod-ai_us-west-2_infrastruc, "
        "arn=arn:aws:sts::661250075859:assumed-role/SpaceLift-Administrator-Access/01K6DZ7S8Q1CN6YW2VW82JCYYX@workload-prod-ai_us-west-2_infrastruc, "
        "accountid=661250075859, invokedby=null, accesskeyid=ASIAZT5MTNTJ5AOX5BLO, username=null, "
        "sessioncontext={attributes={mfaauthenticated=false, creationdate=2025-09-30T19:15:32Z}, "
        "sessionissuer={type=Role, principalid=AROAZT5MTNTJ2MJ4K6W7D, "
        "arn=arn:aws:iam::661250075859:role/SpaceLift-Administrator-Access, accountid=661250075859, "
        "username=SpaceLift-Administrator-Access}}}"
    )

    result = extract_spacelift_run_id(useridentity_str)

    assert result == "01K6DZ7S8Q1CN6YW2VW82JCYYX"


def test_extract_spacelift_run_id_no_spacelift():
    """Test that non-Spacelift identities return None."""
    useridentity_str = (
        "{type=AssumedRole, principalid=AROAEXAMPLE:regular-session, "
        "arn=arn:aws:sts::123456789012:assumed-role/RegularRole/session}"
    )

    result = extract_spacelift_run_id(useridentity_str)

    assert result is None


def test_extract_instance_ids_from_responseelements_string():
    """Test extraction from responseelements as JSON string (Athena format)."""
    record = {
        "responseelements": '{"requestId":"07ebc6b2-7750-4382-ac33-04b9d862113c","reservationId":"r-0f73264af854c0d64","ownerId":"661250075859","groupSet":{},"instancesSet":{"items":[{"instanceId":"i-0f5139368648f4f62","imageId":"ami-05f991c49d264708f"}]}}'
    }

    result = extract_instance_ids(record)

    assert "i-0f5139368648f4f62" in result
    assert len(result) == 1


def test_extract_instance_ids_from_resources_hive_struct():
    """Test extraction from resources field in Hive struct format (Athena format)."""
    record = {
        "resources": "[{arn=arn:aws:ec2:us-west-2:661250075859:instance/i-0f5139368648f4f62, accountid=661250075859, type=AWS::EC2::Instance}]"
    }

    result = extract_instance_ids(record)

    assert "i-0f5139368648f4f62" in result
    assert len(result) == 1


def test_extract_instance_ids_from_requestparameters_string():
    """Test extraction from requestparameters as JSON string (Athena format)."""
    record = {
        "requestparameters": '{"instancesSet":{"items":[{"instanceId":"i-047edc554f1c2a7e8"}]},"filterSet":{}}'
    }

    result = extract_instance_ids(record)

    assert "i-047edc554f1c2a7e8" in result
    assert len(result) == 1


def test_extract_instance_ids_from_dict_format():
    """Test extraction also works when fields are already parsed as dicts (for backward compatibility)."""
    record = {
        "resources": [
            {
                "ARN": "arn:aws:ec2:us-east-1:123456789012:instance/i-01234567",
                "accountId": "123456789012",
            }
        ],
        "responseelements": {"instancesSet": {"items": [{"instanceId": "i-89abcdef"}]}},
    }

    result = extract_instance_ids(record)

    assert "i-01234567" in result
    assert "i-89abcdef" in result
    assert len(result) == 2


def test_extract_instance_ids_multiple_sources():
    """Test extraction from multiple fields in the same record."""
    record = {
        "resources": "[{arn=arn:aws:ec2:us-west-2:661250075859:instance/i-0f5139368648f4f62, accountid=661250075859}]",
        "requestparameters": '{"instancesSet":{"items":[{"instanceId":"i-0f5139368648f4f62"}]}}',
        "responseelements": '{"instancesSet":{"items":[{"instanceId":"i-0f5139368648f4f62"}]}}',
    }

    result = extract_instance_ids(record)

    # Should deduplicate - same instance ID appears in all 3 fields
    assert result == ["i-0f5139368648f4f62"]


def test_extract_instance_ids_dry_run_has_no_responseelements():
    """Test that DryRun operations (errorcode set, responseelements null) still work."""
    record = {
        "errorcode": "Client.DryRunOperation",
        "errormessage": "Request would have succeeded, but DryRun flag is set.",
        "requestparameters": '{"instancesSet":{"items":[{"imageId":"ami-02fea268d7a3212fd","minCount":1,"maxCount":1}]}}',
        "responseelements": None,
        "resources": None,
    }

    result = extract_instance_ids(record)

    # DryRun doesn't create instances, so no instance IDs in request
    assert result == []
