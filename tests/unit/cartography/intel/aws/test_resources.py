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
