clusterId1 = "j-awesome"
clusterId2 = "j-meh"

DESCRIBE_CLUSTERS = [
    {
        "Status": {
            "Timeline": {
                "ReadyDateTime": 1436475075.199,
                "CreationDateTime": 1436474656.563,
            },
            "State": "WAITING",
            "StateChangeReason": {
                "Message": "Waiting for steps to run",
            },
        },
        "Ec2InstanceAttributes": {
            "ServiceAccessSecurityGroup": "sg-xxxxxxxx",
            "EmrManagedMasterSecurityGroup": "sg-xxxxxxxx",
            "IamInstanceProfile": "EMR_EC2_DefaultRole",
            "Ec2KeyName": "myKey",
            "Ec2AvailabilityZone": "us-east-1c",
            "EmrManagedSlaveSecurityGroup": "sg-yyyyyyyyy",
        },
        "Name": "I am the walrus",
        "Id": clusterId1,
        "ClusterArn": "arn:aws:elasticmapreduce:us-east-1:190000000000:cluster/"
        + clusterId1,
        "ServiceRole": "EMR_DefaultRole",
        "Tags": [],
        "TerminationProtected": True,
        "ReleaseLabel": "emr-4.0.0",
        "NormalizedInstanceHours": 96,
        "InstanceGroups": [
            {
                "RequestedInstanceCount": 2,
                "Status": {
                    "Timeline": {
                        "ReadyDateTime": 1436475074.245,
                        "CreationDateTime": 1436474656.564,
                        "EndDateTime": 1436638158.387,
                    },
                    "State": "RUNNING",
                    "StateChangeReason": {
                        "Message": "",
                    },
                },
                "Name": "CORE",
                "InstanceGroupType": "CORE",
                "Id": "ig-YYYYYYY",
                "Configurations": [],
                "InstanceType": "m3.large",
                "Market": "ON_DEMAND",
                "RunningInstanceCount": 2,
            },
            {
                "RequestedInstanceCount": 1,
                "Status": {
                    "Timeline": {
                        "ReadyDateTime": 1436475074.245,
                        "CreationDateTime": 1436474656.564,
                        "EndDateTime": 1436638158.387,
                    },
                    "State": "RUNNING",
                    "StateChangeReason": {
                        "Message": "",
                    },
                },
                "Name": "MASTER",
                "InstanceGroupType": "MASTER",
                "Id": "ig-XXXXXXXXX",
                "Configurations": [],
                "InstanceType": "m3.large",
                "Market": "ON_DEMAND",
                "RunningInstanceCount": 1,
            },
        ],
        "Applications": [
            {
                "Name": "Hadoop",
            },
        ],
        "VisibleToAllUsers": True,
        "BootstrapActions": [],
        "MasterPublicDnsName": "ec2-54-147-144-78.compute-1.amazonaws.com",
        "AutoTerminate": False,
        "Configurations": [
            {
                "Properties": {
                    "fs.s3.consistent.retryPeriodSeconds": "20",
                    "fs.s3.enableServerSideEncryption": "true",
                    "fs.s3.consistent": "false",
                    "fs.s3.consistent.retryCount": "2",
                },
                "Classification": "emrfs-site",
            },
        ],
    },
    {
        "Status": {
            "Timeline": {
                "ReadyDateTime": 1436475075.199,
                "CreationDateTime": 1436474656.563,
            },
            "State": "WAITING",
            "StateChangeReason": {
                "Message": "Waiting for steps to run",
            },
        },
        "Ec2InstanceAttributes": {
            "ServiceAccessSecurityGroup": "sg-zzzzzzzz",
            "EmrManagedMasterSecurityGroup": "sg-zzzzzzzz",
            "IamInstanceProfile": "EMR_EC2_DefaultRole",
            "Ec2KeyName": "myKey",
            "Ec2AvailabilityZone": "us-east-1c",
            "EmrManagedSlaveSecurityGroup": "sg-yyyyyyyyy",
        },
        "Name": "You're out of your element!",
        "Id": clusterId2,
        "ClusterArn": "arn:aws:elasticmapreduce:us-east-1:190000000000:cluster/"
        + clusterId2,
        "ServiceRole": "EMR_DefaultRole",
        "Tags": [],
        "TerminationProtected": True,
        "ReleaseLabel": "emr-3.0.0",
        "NormalizedInstanceHours": 12,
        "InstanceGroups": [
            {
                "RequestedInstanceCount": 1,
                "Status": {
                    "Timeline": {
                        "ReadyDateTime": 1436475074.245,
                        "CreationDateTime": 1436474656.564,
                        "EndDateTime": 1436638158.387,
                    },
                    "State": "RUNNING",
                    "StateChangeReason": {
                        "Message": "",
                    },
                },
                "Name": "CORE",
                "InstanceGroupType": "CORE",
                "Id": "ig-AAAAAAA",
                "Configurations": [],
                "InstanceType": "m3.xlarge",
                "Market": "ON_DEMAND",
                "RunningInstanceCount": 1,
            },
            {
                "RequestedInstanceCount": 1,
                "Status": {
                    "Timeline": {
                        "ReadyDateTime": 1436475074.245,
                        "CreationDateTime": 1436474656.564,
                        "EndDateTime": 1436638158.387,
                    },
                    "State": "RUNNING",
                    "StateChangeReason": {
                        "Message": "",
                    },
                },
                "Name": "MASTER",
                "InstanceGroupType": "MASTER",
                "Id": "ig-ZZZZZZZZZ",
                "Configurations": [],
                "InstanceType": "m3.xlarge",
                "Market": "ON_DEMAND",
                "RunningInstanceCount": 1,
            },
        ],
        "Applications": [
            {
                "Name": "Hadoop",
            },
        ],
        "VisibleToAllUsers": True,
        "BootstrapActions": [],
        "MasterPublicDnsName": "ec2-54-147-144-79.compute-1.amazonaws.com",
        "AutoTerminate": False,
        "Configurations": [
            {
                "Properties": {
                    "fs.s3.consistent.retryPeriodSeconds": "20",
                    "fs.s3.enableServerSideEncryption": "true",
                    "fs.s3.consistent": "false",
                    "fs.s3.consistent.retryCount": "2",
                },
                "Classification": "emrfs-site",
            },
        ],
    },
]
