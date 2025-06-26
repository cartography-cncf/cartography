import datetime
from datetime import timezone as tz

GET_ECS_CLUSTERS = [
    {
        "clusterArn": "arn:aws:ecs:us-east-1:000000000000:cluster/test_cluster",
        "clusterName": "test_cluster",
        "status": "ACTIVE",
        "registeredContainerInstancesCount": 0,
        "runningTasksCount": 1,
        "pendingTasksCount": 0,
        "activeServicesCount": 1,
        "statistics": [],
        "tags": [],
        "settings": [
            {
                "name": "containerInsights",
                "value": "disabled",
            },
        ],
        "capacityProviders": [
            "FARGATE_SPOT",
            "FARGATE",
        ],
        "defaultCapacityProviderStrategy": [
            {
                "capacityProvider": "FARGATE",
                "weight": 0,
                "base": 0,
            },
        ],
    },
]

GET_ECS_CONTAINER_INSTANCES = [
    {
        "containerInstanceArn": "arn:aws:ecs:us-east-1:000000000000:container-instance/test_instance/a0000000000000000000000000000000",  # noqa:E501
        "ec2InstanceId": "i-00000000000000000",
        "version": 100000,
        "versionInfo": {
            "agentVersion": "1.47.0",
            "agentHash": "0000aaaa",
            "dockerVersion": "DockerVersion: 19.03.6-ce",
        },
        "remainingResources": [
            {
                "name": "CPU",
                "type": "INTEGER",
                "doubleValue": 0.0,
                "longValue": 0,
                "integerValue": 4096,
            },
            {
                "name": "MEMORY",
                "type": "INTEGER",
                "doubleValue": 0.0,
                "longValue": 0,
                "integerValue": 1683,
            },
            {
                "name": "PORTS",
                "type": "STRINGSET",
                "doubleValue": 0.0,
                "longValue": 0,
                "integerValue": 0,
                "stringSetValue": ["22", "2376", "2375", "51678", "51679"],
            },  # noqa:E501
            {
                "name": "PORTS_UDP",
                "type": "STRINGSET",
                "doubleValue": 0.0,
                "longValue": 0,
                "integerValue": 0,
                "stringSetValue": [],
            },  # noqa:E501
        ],
        "registeredResources": [
            {
                "name": "CPU",
                "type": "INTEGER",
                "doubleValue": 0.0,
                "longValue": 0,
                "integerValue": 4096,
            },
            {
                "name": "MEMORY",
                "type": "INTEGER",
                "doubleValue": 0.0,
                "longValue": 0,
                "integerValue": 7827,
            },
            {
                "name": "PORTS",
                "type": "STRINGSET",
                "doubleValue": 0.0,
                "longValue": 0,
                "integerValue": 0,
                "stringSetValue": ["22", "2376", "2375", "51678", "51679"],
            },  # noqa:E501
            {
                "name": "PORTS_UDP",
                "type": "STRINGSET",
                "doubleValue": 0.0,
                "longValue": 0,
                "integerValue": 0,
                "stringSetValue": [],
            },  # noqa:E501
        ],
        "status": "ACTIVE",
        "agentConnected": True,
        "runningTasksCount": 2,
        "pendingTasksCount": 0,
        "attributes": [
            {"name": "ecs.capability.branch-cni-plugin-version", "value": "a0000000-"},
            {"name": "ecs.ami-id", "value": "ami-00000000000000000"},
        ],
        "registeredAt": datetime.datetime(
            2021,
            10,
            12,
            12,
            19,
            6,
            294000,
            tzinfo=tz.utc,
        ),
        "attachments": [],
        "tags": [],
    },
]

GET_ECS_SERVICES = [
    {
        "serviceArn": "arn:aws:ecs:us-east-1:000000000000:service/test_instance/test_service",
        "serviceName": "test_service",
        "clusterArn": "arn:aws:ecs:us-east-1:000000000000:cluster/test_cluster",
        "loadBalancers": [
            {
                "targetGroupArn": "arn:aws:elasticloadbalancing:us-east-1:000000000000:targetgroup/test_group/0000000000090000",  # noqa:E501
                "containerName": "test_container",
                "containerPort": 8080,
            },
        ],
        "serviceRegistries": [],
        "status": "ACTIVE",
        "desiredCount": 1,
        "runningCount": 1,
        "pendingCount": 0,
        "launchType": "FARGATE",
        "platformVersion": "LATEST",
        "taskDefinition": "arn:aws:ecs:us-east-1:000000000000:task-definition/test_definition:0",
        "deploymentConfiguration": {
            "deploymentCircuitBreaker": {
                "enable": False,
                "rollback": False,
            },
            "maximumPercent": 200,
            "minimumHealthyPercent": 50,
        },
        "deployments": [
            {
                "id": "ecs-svc/0000000000000000000",
                "status": "PRIMARY",
                "taskDefinition": "arn:aws:ecs:us-east-1:000000000000:task-definition/test_definition:0",
                "desiredCount": 1,
                "pendingCount": 0,
                "runningCount": 1,
                "failedTasks": 0,
                "createdAt": datetime.datetime(
                    2021,
                    12,
                    28,
                    6,
                    42,
                    3,
                    786000,
                    tzinfo=tz.utc,
                ),
                "updatedAt": datetime.datetime(
                    2021,
                    12,
                    28,
                    6,
                    45,
                    4,
                    665000,
                    tzinfo=tz.utc,
                ),
                "launchType": "FARGATE",
                "platformVersion": "1.4.0",
                "networkConfiguration": {
                    "awsvpcConfiguration": {
                        "subnets": [
                            "subnet-00000000000000000",
                            "subnet-00000000000000001",
                        ],
                        "securityGroups": ["sg-00000000000000000"],
                        "assignPublicIp": "DISABLED",
                    },
                },
                "rolloutState": "COMPLETED",
                "rolloutStateReason": "ECS deployment ecs-svc/0000000000000000000 completed.",
            },
        ],
        "roleArn": "arn:aws:iam::000000000000:role/aws-service-role/ecs.amazonaws.com/AWSServiceRoleForECS",
        "events": [],
        "createdAt": datetime.datetime(2021, 9, 8, 10, 15, 57, 44000, tzinfo=tz.utc),
        "placementConstraints": [],
        "placementStrategy": [],
        "networkConfiguration": {
            "awsvpcConfiguration": {
                "subnets": ["subnet-00000000000000000", "subnet-00000000000000001"],
                "securityGroups": ["sg-00000000000000000"],
                "assignPublicIp": "DISABLED",
            },
        },
        "healthCheckGracePeriodSeconds": 0,
        "schedulingStrategy": "REPLICA",
        "createdBy": "arn:aws:iam::000000000000:role/aws-reserved/sso.amazonaws.com/us-east-1/AWSReservedSSO_role-test",
        "enableECSManagedTags": False,
        "propagateTags": "NONE",
        "enableExecuteCommand": True,
    },
]

GET_ECS_TASK_DEFINITIONS = [
    {
        "taskDefinitionArn": "arn:aws:ecs:us-east-1:000000000000:task-definition/test_definition:0",
        "containerDefinitions": [
            {
                "name": "test",
                "image": "test/test:latest",
                "cpu": 256,
                "memory": 512,
                "memoryReservation": 128,
                "portMappings": [
                    {
                        "containerPort": 4141,
                        "hostPort": 4141,
                        "protocol": "tcp",
                    },
                ],
                "essential": True,
                "environment": [
                    {
                        "name": "TEST_ENV",
                        "value": "false",
                    },
                ],
                "mountPoints": [],
                "volumesFrom": [],
                "secrets": [
                    {
                        "name": "TEST_SECRET",
                        "valueFrom": "/test/secret",
                    },
                ],
                "startTimeout": 30,
                "stopTimeout": 30,
                "readonlyRootFilesystem": False,
                "logConfiguration": {
                    "logDriver": "awslogs",
                    "options": {
                        "awslogs-group": "test",
                        "awslogs-region": "us-east-1",
                        "awslogs-stream-prefix": "ecs",
                    },
                },
            },
        ],
        "family": "test_family",
        "taskRoleArn": "arn:aws:iam::000000000000:role/test-ecs_task_execution",
        "executionRoleArn": "arn:aws:iam::000000000000:role/test-ecs_task_execution",
        "networkMode": "awsvpc",
        "revision": 4,
        "volumes": [],
        "status": "ACTIVE",
        "requiresAttributes": [
            {"name": "com.amazonaws.ecs.capability.logging-driver.awslogs"},
            {"name": "ecs.capability.execution-role-awslogs"},
            {"name": "com.amazonaws.ecs.capability.docker-remote-api.1.19"},
            {"name": "com.amazonaws.ecs.capability.docker-remote-api.1.21"},
            {"name": "com.amazonaws.ecs.capability.task-iam-role"},
            {"name": "ecs.capability.container-ordering"},
            {"name": "ecs.capability.secrets.ssm.environment-variables"},
            {"name": "com.amazonaws.ecs.capability.docker-remote-api.1.18"},
            {"name": "ecs.capability.task-eni"},
        ],
        "placementConstraints": [],
        "compatibilities": [
            "EC2",
            "FARGATE",
        ],
        "requiresCompatibilities": ["FARGATE"],
        "cpu": "256",
        "memory": "512",
        "registeredAt": datetime.datetime(
            2021,
            7,
            20,
            2,
            11,
            30,
            570000,
            tzinfo=tz.utc,
        ),
        "registeredBy": "arn:aws:sts::000000000000:assumed-role/AWSReservedSSO_role-test/test_user@example.com",
    },
]

GET_ECS_TASKS = [
    {
        "attachments": [
            {
                "id": "00000000-0000-0000-0000-000000000000",
                "type": "ElasticNetworkInterface",
                "status": "ATTACHED",
                "details": [
                    {
                        "name": "subnetId",
                        "value": "subnet-00000000000000000",
                    },
                    {
                        "name": "networkInterfaceId",
                        "value": "eni-00000000000000000",
                    },
                    {
                        "name": "macAddress",
                        "value": "00:00:00:00:00:00",
                    },
                    {
                        "name": "privateDnsName",
                        "value": "ip-00-00-0-000.us-east-1.compute.internal",
                    },
                    {
                        "name": "privateIPv4Address",
                        "value": "00.00.0.000",
                    },
                ],
            },
        ],
        "attributes": [
            {
                "name": "ecs.cpu-architecture",
                "value": "x86_64",
            },
        ],
        "availabilityZone": "us-east-1a",
        "clusterArn": "arn:aws:ecs:us-east-1:000000000000:cluster/test_cluster",
        "connectivity": "CONNECTED",
        "connectivityAt": datetime.datetime(
            2021,
            12,
            28,
            6,
            42,
            27,
            78000,
            tzinfo=tz.utc,
        ),
        "containerInstanceArn": "arn:aws:ecs:us-east-1:000000000000:container-instance/test_instance/a0000000000000000000000000000000",
        "containers": [
            {
                "containerArn": "arn:aws:ecs:us-east-1:000000000000:container/test_instance/00000000000000000000000000000000/00000000-0000-0000-0000-000000000000",  # noqa:E501
                "taskArn": "arn:aws:ecs:us-east-1:000000000000:task/test_task/00000000000000000000000000000000",
                "name": "test-task_container",
                "image": "000000000000.dkr.ecr.us-east-1.amazonaws.com/test-image:latest",
                "imageDigest": "sha256:0000000000000000000000000000000000000000000000000000000000000000",
                "runtimeId": "0000000000000000000000000000000000000000000",
                "lastStatus": "RUNNING",
                "networkBindings": [],
                "networkInterfaces": [
                    {
                        "attachmentId": "00000000-0000-0000-0000-000000000000",
                        "privateIpv4Address": "00.00.0.000",
                    },
                ],
                "healthStatus": "UNKNOWN",
                "managedAgents": [
                    {
                        "lastStartedAt": datetime.datetime(
                            2021,
                            12,
                            28,
                            6,
                            43,
                            16,
                            321000,
                            tzinfo=tz.utc,
                        ),
                        "name": "ExecuteCommandAgent",
                        "lastStatus": "RUNNING",
                    },
                ],
                "cpu": "1024",
                "memory": "2048",
                "memoryReservation": "128",
            },
        ],
        "cpu": "1024",
        "createdAt": datetime.datetime(2021, 12, 28, 6, 42, 23, 184000, tzinfo=tz.utc),
        "desiredStatus": "RUNNING",
        "enableExecuteCommand": True,
        "group": "service:test_service",
        "healthStatus": "UNKNOWN",
        "lastStatus": "RUNNING",
        "launchType": "FARGATE",
        "memory": "2048",
        "overrides": {
            "containerOverrides": [
                {
                    "name": "test-task_container",
                },
            ],
            "inferenceAcceleratorOverrides": [],
        },
        "platformVersion": "1.4.0",
        "pullStartedAt": datetime.datetime(
            2021,
            12,
            28,
            6,
            42,
            36,
            31000,
            tzinfo=tz.utc,
        ),
        "pullStoppedAt": datetime.datetime(
            2021,
            12,
            28,
            6,
            43,
            8,
            114000,
            tzinfo=tz.utc,
        ),
        "startedAt": datetime.datetime(2021, 12, 28, 6, 43, 14, 190000, tzinfo=tz.utc),
        "startedBy": "ecs-svc/0000000000000000000",
        "tags": [],
        "taskArn": "arn:aws:ecs:us-east-1:000000000000:task/test_task/00000000000000000000000000000000",
        "taskDefinitionArn": "arn:aws:ecs:us-east-1:000000000000:task-definition/test_definition:0",
        "version": 3,
        "ephemeralStorage": {
            "sizeInGiB": 20,
        },
    },
]
