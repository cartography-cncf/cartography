from cartography.intel.aws import AWS_EC2_ASSET_EXPOSURE_AUTO_SCALING_GROUP_DEPS
from cartography.intel.aws import AWS_EC2_IAM_INSTANCE_PROFILE_DEPS
from cartography.intel.aws import AWS_LAMBDA_ECR_DEPS
from cartography.intel.aws import AWS_LB_NACL_DIRECT_DEPS
from cartography.intel.aws.resources import RESOURCE_FUNCTIONS


def test_ecs_syncs_last_to_minimize_stale_analysis_relationships():
    # Arrange
    resource_order = list(RESOURCE_FUNCTIONS)

    # Act
    last_resource = resource_order[-1]

    # Assert
    assert last_resource == "ecs"
    assert resource_order.index("ec2:instance") < resource_order.index("ecs")
    assert resource_order.index("ec2:load_balancer_v2") < resource_order.index("ecs")


def test_analysis_producers_sync_close_to_their_analysis_jobs():
    # Arrange
    resource_order = list(RESOURCE_FUNCTIONS)

    # Act
    analysis_tail = resource_order[-3:]

    # Assert
    assert analysis_tail == ["ec2:autoscalinggroup", "ec2:keypair", "ecs"]
    assert resource_order.index("eks") + 1 == resource_order.index("guardduty")


def test_analysis_dependency_sets_include_all_required_producers():
    # Arrange
    expected_dependencies = {
        "instance_profile": {"iam", "iaminstanceprofiles", "ec2:instance"},
        "lambda_ecr": {"ecr", "lambda_function"},
        "lb_nacl": {
            "ec2:network_acls",
            "ec2:load_balancer_v2",
            "ec2:subnet",
        },
    }

    # Act
    actual_dependencies = {
        "instance_profile": AWS_EC2_IAM_INSTANCE_PROFILE_DEPS,
        "lambda_ecr": AWS_LAMBDA_ECR_DEPS,
        "lb_nacl": AWS_LB_NACL_DIRECT_DEPS,
    }

    # Assert
    assert actual_dependencies == expected_dependencies
    assert "ec2:autoscalinggroup" in AWS_EC2_ASSET_EXPOSURE_AUTO_SCALING_GROUP_DEPS
