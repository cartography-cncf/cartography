import datetime

DESCRIBE_VOLUMES = [
    {
        'Attachments': [{
            'InstanceId': 'i-01',
            'State': 'attached',
        }],
        'AvailabilityZone': 'US West 1',
        'CreateTime': datetime.datetime(2018, 10, 14, 16, 30, 26),
        'Encrypted': True,
        'KmsKeyId': 'k-1',
        'OutpostArn': 'arn1',
        'Size': 123,
        'SnapshotId': 'sn-01',
        'State': 'available',
        'VolumeId': 'vol-0df',
        'Iops': 123,
        'VolumeType': 'standard',
        'FastRestored': True,
        'MultiAttachEnabled': True,
        'Throughput': 123,
    },
    {
        'Attachments': [{
            'InstanceId': 'i-02',
            'State': 'attached',
        }],
        'AvailabilityZone': 'US West 1',
        'CreateTime': datetime.datetime(2018, 10, 14, 16, 30, 26),
        'Encrypted': True,
        'KmsKeyId': 'k-1',
        'OutpostArn': 'arn1',
        'Size': 123,
        'State': 'available',
        'VolumeId': 'vol-03',
        'Iops': 123,
        'SnapshotId': 'sn-02',
        'VolumeType': 'standard',
        'FastRestored': True,
        'MultiAttachEnabled': True,
        'Throughput': 123,
    },
]
