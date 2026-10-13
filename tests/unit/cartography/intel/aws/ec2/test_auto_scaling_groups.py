from cartography.intel.aws.ec2 import auto_scaling_groups


def test_transform_auto_scaling_group_uses_aws_launch_template_fields():
    transformed = auto_scaling_groups.transform_auto_scaling_groups(
        [
            {
                "AutoScalingGroupARN": "arn:aws:autoscaling:us-east-1:123:group/test",
                "LaunchTemplate": {
                    "LaunchTemplateName": "template-name",
                    "LaunchTemplateId": "lt-123",
                    "Version": "7",
                },
            }
        ]
    )

    assert transformed.group_list[0]["LaunchTemplateName"] == "template-name"
    assert transformed.group_list[0]["LaunchTemplateId"] == "lt-123"
    assert transformed.group_list[0]["LaunchTemplateVersion"] == "7"
