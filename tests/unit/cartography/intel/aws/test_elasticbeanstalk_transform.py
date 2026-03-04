from cartography.intel.aws.elasticbeanstalk import (
    transform_elasticbeanstalk_environments,
)


def test_transform_elasticbeanstalk_environments():
    """Test that the transform collects the IDs of child resources"""
    environments = [
        {
            "AbortableOperationInProgress": False,
            "ApplicationName": "test",
            "CNAME": "test.elasticbeanstalk.com",
            "EndpointURL": "test.elb.amazonaws.com",
            "EnvironmentArn": "arn:aws:elasticbeanstalk:test",
            "EnvironmentId": "e-test",
            "EnvironmentLinks": [],
            "EnvironmentName": "test",
            "Health": "Green",
            "HealthStatus": "Ok",
            "PlatformArn": "arn:aws:elasticbeanstalk:test",
            "Resources": {
                "AutoScalingGroups": [{"Name": "asg1"}, {"Name": "asg2"}],
                "EnvironmentName": "test",
                "Instances": [
                    {"Id": "i-instance1"},
                    {"Id": "i-instance2"},
                    {"Id": "i-instance3"},
                    {"Id": "i-instance4"},
                ],
                "LaunchConfigurations": [{"Name": "lc1"}, {"Name": "lc2"}],
                "LaunchTemplates": [
                    {"Id": "lt1"},
                    {"Id": "lt2"},
                    {"Id": "lt3"},
                ],
                "LoadBalancers": [{"Name": "alb1"}, {"Name": "alb2"}],
                "Queues": [
                    {"Name": "q1", "URL": "https://q1"},
                    {"Name": "q2", "URL": "https://q2"},
                ],
                "Triggers": [{"Name": "t1"}, {"Name": "t2"}],
            },
            "SolutionStackName": "test",
            "Status": "Ready",
            "Tier": {"Name": "test", "Type": "Standard", "Version": "1.0"},
            "VersionLabel": "test",
        }
    ]

    transformed_environments = transform_elasticbeanstalk_environments(
        environments=environments, region="test"
    )

    assert len(transformed_environments) == 1

    assert transformed_environments[0]["ASG_NAMES"] == ["asg1", "asg2"]
    assert transformed_environments[0]["INSTANCE_IDS"] == [
        "i-instance1",
        "i-instance2",
        "i-instance3",
        "i-instance4",
    ]
    assert transformed_environments[0]["LAUNCHCONFIG_NAMES"] == ["lc1", "lc2"]
    assert transformed_environments[0]["LAUNCHTEMPLATE_IDS"] == ["lt1", "lt2", "lt3"]
    assert transformed_environments[0]["LOADBALANCER_NAMES"] == ["alb1", "alb2"]
    assert transformed_environments[0]["QUEUE_URLS"] == ["https://q1", "https://q2"]
    assert transformed_environments[0]["TRIGGER_NAMES"] == ["t1", "t2"]
