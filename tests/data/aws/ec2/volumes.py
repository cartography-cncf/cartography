import datetime

DESCRIBE_VOLUMES = {
    {
        'AvailabilityZone': 'US West 1',
        'CreateTime': datetime.datetime(2018, 10, 14, 16, 30, 26),
        'Encrypted': True,
        'KmsKeyId': 'k-1',
        'OutpostArn': 'arn1',
        'Size': 123,
        'SnapshotId': 'sn-01',
        'State': 'available',
        'VolumeId': 'v-01',
        'Iops': 123,
        'VolumeType': 'standard',
        'FastRestored': True,
        'MultiAttachEnabled': True,
        'Throughput': 123
    },
    {
        'AvailabilityZone': 'US West 1',
        'CreateTime': datetime.datetime(2018, 10, 14, 16, 30, 26),
        'Encrypted': True,
        'KmsKeyId': 'k-1',
        'OutpostArn': 'arn1',
        'Size': 123,
        'State': 'available',
        'VolumeId': 'v-02',
        'Iops': 123,
        'VolumeType': 'standard',
        'FastRestored': True,
        'MultiAttachEnabled': True,
        'Throughput': 123
    },
}
