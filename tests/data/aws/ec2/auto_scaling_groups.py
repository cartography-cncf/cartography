import datetime
from datetime import timezone as tz

GET_LAUNCH_CONFIGURATIONS = [
    {
        'LaunchConfigurationName': 'example-lc-1',
        'LaunchConfigurationARN': 'arn:aws:autoscaling:us-east-1:000000000000:launchConfiguration:00000000-0000-0000-0000-000000000000:launchConfigurationName/example-lc-1',  # noqa:E501
        'ImageId': 'ami-00000000000000000',
        'KeyName': 'example-key',
        'SecurityGroups': [
            'sg-00000000000000000',
        ],
        'ClassicLinkVPCSecurityGroups': [],
        'UserData': '...',
        'InstanceType': 'r5.4xlarge',
        'KernelId': '',
        'RamdiskId': '',
        'BlockDeviceMappings': [
            {
                'DeviceName': '/dev/xvda',
                'Ebs': {
                    'VolumeSize': 200,
                    'VolumeType': 'gp2',
                    'DeleteOnTermination': True,
                },
            },
        ],
        'InstanceMonitoring': {
            'Enabled': False,
        },
        'IamInstanceProfile': 'example-lc-1',
        'CreatedTime': datetime.datetime(2021, 9, 21, 10, 55, 34, 222000, tzinfo=tz.utc),
        'EbsOptimized': True,
        'AssociatePublicIpAddress': True,
    },
    {
        'LaunchConfigurationName': 'example-lc-2',
        'LaunchConfigurationARN': 'arn:aws:autoscaling:us-east-1:000000000000:launchConfiguration:00000000-0000-0000-0000-000000000000:launchConfigurationName/example-lc-2',  # noqa:E501
        'ImageId': 'ami-00000000000000000',
        'KeyName': 'example-key',
        'SecurityGroups': [
            'sg-00000000000000000',
        ],
        'ClassicLinkVPCSecurityGroups': [],
        'UserData': '...',
        'InstanceType': 'r5.4xlarge',
        'KernelId': '',
        'RamdiskId': '',
        'BlockDeviceMappings': [
            {
                'DeviceName': '/dev/xvda',
                'Ebs': {
                    'VolumeSize': 200,
                    'VolumeType': 'gp2',
                    'DeleteOnTermination': True,
                },
            },
        ],
        'InstanceMonitoring': {
            'Enabled': False,
        },
        'IamInstanceProfile': 'example-lc-2',
        'CreatedTime': datetime.datetime(2021, 9, 21, 10, 55, 34, 222000, tzinfo=tz.utc),
        'EbsOptimized': True,
        'AssociatePublicIpAddress': True,
    },
    {
        'LaunchConfigurationName': 'example-lc-3',
        'LaunchConfigurationARN': 'arn:aws:autoscaling:us-east-1:000000000000:launchConfiguration:00000000-0000-0000-0000-000000000000:launchConfigurationName/example-lc-3',  # noqa:E501
        'ImageId': 'ami-00000000000000000',
        'KeyName': 'example-key',
        'SecurityGroups': [
            'sg-00000000000000000',
        ],
        'ClassicLinkVPCSecurityGroups': [],
        'UserData': '...',
        'InstanceType': 'r5.4xlarge',
        'KernelId': '',
        'RamdiskId': '',
        'BlockDeviceMappings': [
            {
                'DeviceName': '/dev/xvda',
                'Ebs': {
                    'VolumeSize': 200,
                    'VolumeType': 'gp2',
                    'DeleteOnTermination': True,
                },
            },
        ],
        'InstanceMonitoring': {
            'Enabled': False,
        },
        'IamInstanceProfile': 'example-lc-3',
        'CreatedTime': datetime.datetime(2021, 9, 21, 10, 55, 34, 222000, tzinfo=tz.utc),
        'EbsOptimized': True,
        'AssociatePublicIpAddress': True,
    },
]

GET_AUTO_SCALING_GROUPS = [
    {
        'AutoScalingGroupName': 'example-asg-1',
        'AutoScalingGroupARN': 'arn:aws:autoscaling:us-east-1:000000000000:autoScalingGroup:00000000-0000-0000-0000-000000000000:autoScalingGroupName/example-asg-1',  # noqa:E501
        'LaunchConfigurationName': 'example-lc-1',
        'MinSize': 1,
        'MaxSize': 1,
        'DesiredCapacity': 1,
        'DefaultCooldown': 300,
        'AvailabilityZones': [
            'us-east-1a',
            'us-east-1b',
        ],
        'LoadBalancerNames': [],
        'TargetGroupARNs': [],
        'HealthCheckType': 'EC2',
        'HealthCheckGracePeriod': 300,
        'Instances': [],
        'CreatedTime': datetime.datetime(2021, 9, 21, 10, 55, 34, 222000, tzinfo=tz.utc),
        'SuspendedProcesses': [],
        'VPCZoneIdentifier': 'subnet-00000000000000000,subnet-11111111111111111',
        'NewInstancesProtectedFromScaleIn': False,
        'ServiceLinkedRoleARN': 'arn:aws:iam::000000000000:role/aws-service-role/autoscaling.amazonaws.com/AWSServiceRoleForAutoScaling',  # noqa:E501
        'MaxInstanceLifetime': 2592000,
        'CapacityRebalance': False,
    },
    {
        'AutoScalingGroupName': 'example-asg-2',
        'AutoScalingGroupARN': 'arn:aws:autoscaling:us-east-1:000000000000:autoScalingGroup:00000000-0000-0000-0000-000000000000:autoScalingGroupName/example-asg-2',  # noqa:E501
        'MinSize': 1,
        'MaxSize': 1,
        'DesiredCapacity': 1,
        'DefaultCooldown': 300,
        'AvailabilityZones': [
            'us-east-1a',
            'us-east-1b',
        ],
        'LoadBalancerNames': [],
        'TargetGroupARNs': [],
        'HealthCheckType': 'EC2',
        'HealthCheckGracePeriod': 300,
        # Should match instance IDs from cartography.tests.data.aws.ec2.instances.py
        'Instances': [
            {
                "InstanceId": "i-01",
            },
            {
                "InstanceId": "i-02",
            },
            {
                "InstanceId": "i-03",
            },
            {
                "InstanceId": "i-04",
            },
        ],
        'CreatedTime': datetime.datetime(2021, 9, 21, 10, 55, 34, 222000, tzinfo=tz.utc),
        'SuspendedProcesses': [],
        'VPCZoneIdentifier': 'subnet-00000000000000000,subnet-11111111111111111',
        'NewInstancesProtectedFromScaleIn': False,
        'ServiceLinkedRoleARN': 'arn:aws:iam::000000000000:role/aws-service-role/autoscaling.amazonaws.com/AWSServiceRoleForAutoScaling',  # noqa:E501
        'MaxInstanceLifetime': 2592000,
        'CapacityRebalance': False,
    },
]
