import datetime
from datetime import timezone as tz


GET_LAUNCH_TEMPLATES = [
    {
        'LaunchTemplateId': 'lt-00000000000000000',
        'LaunchTemplateName': 'eks-00000000-0000-0000-0000-000000000000',
        'CreateTime': datetime.datetime(2021, 10, 12, 6, 27, 52, tzinfo=tz.utc),
        'CreatedBy': 'arn:aws:sts::000000000000:assumed-role/AWSServiceRoleForAmazonEKSNodegroup/EKS',
        'DefaultVersionNumber': 1,
        'LatestVersionNumber': 1,
        'Tags': [
            {
                'Key': 'eks:cluster-name',
                'Value': 'eks-cluster-example',
            },
            {
                'Key': 'eks:nodegroup-name',
                'Value': 'private-node-group-example',
            },
        ],
    },
]

GET_LAUNCH_TEMPLATE_VERSIONS = [
    {
        'LaunchTemplateId': 'lt-00000000000000000',
        'LaunchTemplateName': 'eks-00000000-0000-0000-0000-000000000000',
        'VersionNumber': 1,
        'CreateTime': datetime.datetime(2021, 10, 12, 6, 27, 52, tzinfo=tz.utc),
        'CreatedBy': 'arn:aws:sts::000000000000:assumed-role/AWSServiceRoleForAmazonEKSNodegroup/EKS',
        'DefaultVersion': True,
        'LaunchTemplateData': {
            'IamInstanceProfile': {
                'Name': 'eks-00000000-0000-0000-0000-000000000000',
            },
            'BlockDeviceMappings': [
                {
                    'DeviceName': '/dev/xvda',
                    'Ebs': {
                        'DeleteOnTermination': True,
                        'VolumeSize': 20,
                        'VolumeType': 'gp2',
                    },
                },
            ],
            'NetworkInterfaces': [
                {
                    'DeviceIndex': 0,
                    'Groups': ['sg-00000000000000000'],
                },
            ],
            'ImageId': 'ami-00000000000000000',
            'InstanceType': 'm5.large',
            'UserData': '...',
            'MetadataOptions': {
                'HttpPutResponseHopLimit': 2,
            },
        },
    },
]
