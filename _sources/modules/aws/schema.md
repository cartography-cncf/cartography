<!-- Generated from the data model. Do not edit manually. -->

## AWS Schema

```mermaid
graph LR
    AWSACMCertificate -- USED_BY --> AWSELBV2Listener
    AWSAPIGatewayResource -- HAS_INTEGRATION --> AWSAPIGatewayIntegration
    AWSAPIGatewayResource -- HAS_METHOD --> AWSAPIGatewayMethod
    AWSAPIGatewayRestAPI -- ASSOCIATED_WITH --> AWSAPIGatewayStage
    AWSAPIGatewayRestAPI -- HAS_DEPLOYMENT --> AWSAPIGatewayDeployment
    AWSAPIGatewayRestAPI -- RESOURCE --> AWSAPIGatewayResource
    AWSAPIGatewayStage -- HAS_CERTIFICATE --> AWSAPIGatewayClientCertificate
    AWSAccount -- MEMBER --> AWSInspectorFinding
    AWSAccount -- PARENT --> AWSOrganizationRoot
    AWSAccount -- PARENT --> AWSOrganizationalUnit
    AWSAccount -- RESOURCE --> AWSACMCertificate
    AWSAccount -- RESOURCE --> AWSAPIGatewayClientCertificate
    AWSAccount -- RESOURCE --> AWSAPIGatewayDeployment
    AWSAccount -- RESOURCE --> AWSAPIGatewayIntegration
    AWSAccount -- RESOURCE --> AWSAPIGatewayMethod
    AWSAccount -- RESOURCE --> AWSAPIGatewayResource
    AWSAccount -- RESOURCE --> AWSAPIGatewayRestAPI
    AWSAccount -- RESOURCE --> AWSAPIGatewayStage
    AWSAccount -- RESOURCE --> AWSAPIGatewayV2API
    AWSAccount -- RESOURCE --> AWSAccountAccessKey
    AWSAccount -- RESOURCE --> AWSAutoScalingGroup
    AWSAccount -- RESOURCE --> AWSBedrockAgent
    AWSAccount -- RESOURCE --> AWSBedrockCustomModel
    AWSAccount -- RESOURCE --> AWSBedrockFoundationModel
    AWSAccount -- RESOURCE --> AWSBedrockGuardrail
    AWSAccount -- RESOURCE --> AWSBedrockKnowledgeBase
    AWSAccount -- RESOURCE --> AWSBedrockProvisionedModelThroughput
    AWSAccount -- RESOURCE --> AWSCloudFormationStack
    AWSAccount -- RESOURCE --> AWSCloudFrontDistribution
    AWSAccount -- RESOURCE --> AWSCloudTrailTrail
    AWSAccount -- RESOURCE --> AWSCloudWatchLogGroup
    AWSAccount -- RESOURCE --> AWSCloudWatchLogMetricFilter
    AWSAccount -- RESOURCE --> AWSCloudWatchMetricAlarm
    AWSAccount -- RESOURCE --> AWSCodeBuildProject
    AWSAccount -- RESOURCE --> AWSCognitoIdentityPool
    AWSAccount -- RESOURCE --> AWSCognitoUserPool
    AWSAccount -- RESOURCE --> AWSConfigDeliveryChannel
    AWSAccount -- RESOURCE --> AWSConfigRule
    AWSAccount -- RESOURCE --> AWSConfigurationRecorder
    AWSAccount -- RESOURCE --> AWSDBSubnetGroup
    AWSAccount -- RESOURCE --> AWSDNSRecord
    AWSAccount -- RESOURCE --> AWSDNSZone
    AWSAccount -- RESOURCE --> AWSDynamoDBArchivalSummary
    AWSAccount -- RESOURCE --> AWSDynamoDBBackup
    AWSAccount -- RESOURCE --> AWSDynamoDBBillingModeSummary
    AWSAccount -- RESOURCE --> AWSDynamoDBGlobalSecondaryIndex
    AWSAccount -- RESOURCE --> AWSDynamoDBRestoreSummary
    AWSAccount -- RESOURCE --> AWSDynamoDBSSEDescription
    AWSAccount -- RESOURCE --> AWSDynamoDBStream
    AWSAccount -- RESOURCE --> AWSDynamoDBTable
    AWSAccount -- RESOURCE --> AWSEBSSnapshot
    AWSAccount -- RESOURCE --> AWSEBSVolume
    AWSAccount -- RESOURCE --> AWSEC2Image
    AWSAccount -- RESOURCE --> AWSEC2Instance
    AWSAccount -- RESOURCE --> AWSEC2Ipv6Address
    AWSAccount -- RESOURCE --> AWSEC2KeyPair
    AWSAccount -- RESOURCE --> AWSEC2NetworkAcl
    AWSAccount -- RESOURCE --> AWSEC2NetworkAclRule
    AWSAccount -- RESOURCE --> AWSEC2PrivateIp
    AWSAccount -- RESOURCE --> AWSEC2Reservation
    AWSAccount -- RESOURCE --> AWSEC2ReservedInstance
    AWSAccount -- RESOURCE --> AWSEC2Route
    AWSAccount -- RESOURCE --> AWSEC2RouteTable
    AWSAccount -- RESOURCE --> AWSEC2RouteTableAssociation
    AWSAccount -- RESOURCE --> AWSEC2SecurityGroup
    AWSAccount -- RESOURCE --> AWSEC2Subnet
    AWSAccount -- RESOURCE --> AWSECRImage
    AWSAccount -- RESOURCE --> AWSECRImageLayer
    AWSAccount -- RESOURCE --> AWSECRPullThroughCacheRule
    AWSAccount -- RESOURCE --> AWSECRRepository
    AWSAccount -- RESOURCE --> AWSECRRepositoryImage
    AWSAccount -- RESOURCE --> AWSECSCluster
    AWSAccount -- RESOURCE --> AWSECSContainer
    AWSAccount -- RESOURCE --> AWSECSContainerDefinition
    AWSAccount -- RESOURCE --> AWSECSContainerInstance
    AWSAccount -- RESOURCE --> AWSECSService
    AWSAccount -- RESOURCE --> AWSECSTask
    AWSAccount -- RESOURCE --> AWSECSTaskDefinition
    AWSAccount -- RESOURCE --> AWSEKSAccessEntry
    AWSAccount -- RESOURCE --> AWSEKSCluster
    AWSAccount -- RESOURCE --> AWSELBListener
    AWSAccount -- RESOURCE --> AWSELBV2Listener
    AWSAccount -- RESOURCE --> AWSELBV2TargetGroup
    AWSAccount -- RESOURCE --> AWSEMRCluster
    AWSAccount -- RESOURCE --> AWSESDomain
    AWSAccount -- RESOURCE --> AWSEfsAccessPoint
    AWSAccount -- RESOURCE --> AWSEfsFileSystem
    AWSAccount -- RESOURCE --> AWSEfsMountTarget
    AWSAccount -- RESOURCE --> AWSElasticIPAddress
    AWSAccount -- RESOURCE --> AWSElasticacheCluster
    AWSAccount -- RESOURCE --> AWSElasticacheTopic
    AWSAccount -- RESOURCE --> AWSEventBridgeRule
    AWSAccount -- RESOURCE --> AWSEventBridgeTarget
    AWSAccount -- RESOURCE --> AWSFederatedPrincipal
    AWSAccount -- RESOURCE --> AWSGlueConnection
    AWSAccount -- RESOURCE --> AWSGlueJob
    AWSAccount -- RESOURCE --> AWSGroup
    AWSAccount -- RESOURCE --> AWSGuardDutyDetector
    AWSAccount -- RESOURCE --> AWSGuardDutyFinding
    AWSAccount -- RESOURCE --> AWSIdentityCenter
    AWSAccount -- RESOURCE --> AWSInlinePolicy
    AWSAccount -- RESOURCE --> AWSInspectorFinding
    AWSAccount -- RESOURCE --> AWSInspectorPackage
    AWSAccount -- RESOURCE --> AWSInstanceProfile
    AWSAccount -- RESOURCE --> AWSInternetGateway
    AWSAccount -- RESOURCE --> AWSIpPermissionInbound
    AWSAccount -- RESOURCE --> AWSIpRange
    AWSAccount -- RESOURCE --> AWSIpRule
    AWSAccount -- RESOURCE --> AWSKMSAlias
    AWSAccount -- RESOURCE --> AWSKMSGrant
    AWSAccount -- RESOURCE --> AWSKMSKey
    AWSAccount -- RESOURCE --> AWSLambda
    AWSAccount -- RESOURCE --> AWSLambdaEventSourceMapping
    AWSAccount -- RESOURCE --> AWSLambdaFunctionAlias
    AWSAccount -- RESOURCE --> AWSLambdaLayer
    AWSAccount -- RESOURCE --> AWSLaunchConfiguration
    AWSAccount -- RESOURCE --> AWSLaunchTemplate
    AWSAccount -- RESOURCE --> AWSLaunchTemplateVersion
    AWSAccount -- RESOURCE --> AWSLoadBalancer
    AWSAccount -- RESOURCE --> AWSLoadBalancerV2
    AWSAccount -- RESOURCE --> AWSMfaDevice
    AWSAccount -- RESOURCE --> AWSNameServer
    AWSAccount -- RESOURCE --> AWSNetworkInterface
    AWSAccount -- RESOURCE --> AWSPeeringConnection
    AWSAccount -- RESOURCE --> AWSPermissionSet
    AWSAccount -- RESOURCE --> AWSPrincipal
    AWSAccount -- RESOURCE --> AWSRDSCluster
    AWSAccount -- RESOURCE --> AWSRDSEventSubscription
    AWSAccount -- RESOURCE --> AWSRDSInstance
    AWSAccount -- RESOURCE --> AWSRDSSnapshot
    AWSAccount -- RESOURCE --> AWSRedshiftCluster
    AWSAccount -- RESOURCE --> AWSRole
    AWSAccount -- RESOURCE --> AWSRootPrincipal
    AWSAccount -- RESOURCE --> AWSRouteTable
    AWSAccount -- RESOURCE --> AWSS3AccountPublicAccessBlock
    AWSAccount -- RESOURCE --> AWSS3Acl
    AWSAccount -- RESOURCE --> AWSS3Bucket
    AWSAccount -- RESOURCE --> AWSS3PolicyStatement
    AWSAccount -- RESOURCE --> AWSSAMLProvider
    AWSAccount -- RESOURCE --> AWSSESEmailIdentity
    AWSAccount -- RESOURCE --> AWSSNSTopic
    AWSAccount -- RESOURCE --> AWSSNSTopicSubscription
    AWSAccount -- RESOURCE --> AWSSQSQueue
    AWSAccount -- RESOURCE --> AWSSSMInstanceInformation
    AWSAccount -- RESOURCE --> AWSSSMInstancePatch
    AWSAccount -- RESOURCE --> AWSSSMParameter
    AWSAccount -- RESOURCE --> AWSSSOGroup
    AWSAccount -- RESOURCE --> AWSSSOUser
    AWSAccount -- RESOURCE --> AWSSageMakerDomain
    AWSAccount -- RESOURCE --> AWSSageMakerEndpoint
    AWSAccount -- RESOURCE --> AWSSageMakerEndpointConfig
    AWSAccount -- RESOURCE --> AWSSageMakerModel
    AWSAccount -- RESOURCE --> AWSSageMakerModelPackage
    AWSAccount -- RESOURCE --> AWSSageMakerModelPackageGroup
    AWSAccount -- RESOURCE --> AWSSageMakerNotebookInstance
    AWSAccount -- RESOURCE --> AWSSageMakerTrainingJob
    AWSAccount -- RESOURCE --> AWSSageMakerTransformJob
    AWSAccount -- RESOURCE --> AWSSageMakerUserProfile
    AWSAccount -- RESOURCE --> AWSSecretsManagerSecret
    AWSAccount -- RESOURCE --> AWSSecretsManagerSecretVersion
    AWSAccount -- RESOURCE --> AWSSecurityHub
    AWSAccount -- RESOURCE --> AWSServerCertificate
    AWSAccount -- RESOURCE --> AWSTransitGateway
    AWSAccount -- RESOURCE --> AWSTransitGatewayAttachment
    AWSAccount -- RESOURCE --> AWSUser
    AWSAccount -- RESOURCE --> AWSVpc
    AWSAccount -- RESOURCE --> AWSVpcEndpoint
    AWSAccountAccessKey -- OWNED_BY --> AWSUser
    AWSAutoScalingGroup -- HAS_LAUNCH_CONFIG --> AWSLaunchConfiguration
    AWSAutoScalingGroup -- HAS_LAUNCH_TEMPLATE --> AWSLaunchTemplate
    AWSAutoScalingGroup -- TAGGED --> AWSTag
    AWSAutoScalingGroup -- VPC_IDENTIFIER --> AWSEC2Subnet
    AWSBedrockAgent -- HAS_ROLE --> AWSRole
    AWSBedrockAgent -- INVOKES --> AWSLambda
    AWSBedrockAgent -- USES_KNOWLEDGE_BASE --> AWSBedrockKnowledgeBase
    AWSBedrockAgent -- USES_MODEL --> AWSBedrockCustomModel
    AWSBedrockAgent -- USES_MODEL --> AWSBedrockFoundationModel
    AWSBedrockAgent -- USES_MODEL --> AWSBedrockProvisionedModelThroughput
    AWSBedrockCustomModel -- BASED_ON --> AWSBedrockFoundationModel
    AWSBedrockCustomModel -- TRAINED_FROM --> AWSS3Bucket
    AWSBedrockGuardrail -- APPLIED_TO --> AWSBedrockAgent
    AWSBedrockKnowledgeBase -- SOURCES_DATA_FROM --> AWSS3Bucket
    AWSBedrockKnowledgeBase -- USES_EMBEDDING_MODEL --> AWSBedrockFoundationModel
    AWSBedrockProvisionedModelThroughput -- PROVIDES_CAPACITY_FOR --> AWSBedrockCustomModel
    AWSBedrockProvisionedModelThroughput -- PROVIDES_CAPACITY_FOR --> AWSBedrockFoundationModel
    AWSCloudFormationStack -- HAS_EXECUTION_ROLE --> AWSRole
    AWSCloudFrontDistribution -- SERVES_FROM --> AWSS3Bucket
    AWSCloudFrontDistribution -- USES_CERTIFICATE --> AWSACMCertificate
    AWSCloudFrontDistribution -- USES_LAMBDA_EDGE --> AWSLambda
    AWSCloudTrailTrail -- LOGS_TO --> AWSS3Bucket
    AWSCloudTrailTrail -- SENDS_LOGS_TO_CLOUDWATCH --> AWSCloudWatchLogGroup
    AWSCloudWatchLogMetricFilter -- METRIC_FILTER_OF --> AWSCloudWatchLogGroup
    AWSCognitoIdentityPool -- ASSOCIATED_WITH --> AWSRole
    AWSDBSubnetGroup -- RESOURCE --> AWSEC2Subnet
    AWSDBSubnetGroup -- TAGGED --> AWSTag
    AWSDNSRecord -- DNS_POINTS_TO --> AWSDNSRecord
    AWSDNSRecord -- DNS_POINTS_TO --> AWSEC2Instance
    AWSDNSRecord -- DNS_POINTS_TO --> AWSESDomain
    AWSDNSRecord -- DNS_POINTS_TO --> AWSElasticIPAddress
    AWSDNSRecord -- DNS_POINTS_TO --> AWSLoadBalancer
    AWSDNSRecord -- DNS_POINTS_TO --> AWSLoadBalancerV2
    AWSDNSRecord -- DNS_POINTS_TO --> AWSNameServer
    AWSDNSRecord -- MEMBER_OF_DNS_ZONE --> AWSDNSZone
    AWSDNSZone -- NAMESERVER --> AWSNameServer
    AWSDNSZone -- SUBZONE --> AWSDNSZone
    AWSDynamoDBArchivalSummary -- ARCHIVED_TO_BACKUP --> AWSDynamoDBBackup
    AWSDynamoDBRestoreSummary -- RESTORED_FROM_BACKUP --> AWSDynamoDBBackup
    AWSDynamoDBRestoreSummary -- RESTORED_FROM_TABLE --> AWSDynamoDBTable
    AWSDynamoDBSSEDescription -- USES_KMS_KEY --> AWSKMSKey
    AWSDynamoDBTable -- GLOBAL_SECONDARY_INDEX --> AWSDynamoDBGlobalSecondaryIndex
    AWSDynamoDBTable -- HAS_ARCHIVAL --> AWSDynamoDBArchivalSummary
    AWSDynamoDBTable -- HAS_BILLING --> AWSDynamoDBBillingModeSummary
    AWSDynamoDBTable -- HAS_RESTORE --> AWSDynamoDBRestoreSummary
    AWSDynamoDBTable -- HAS_SSE --> AWSDynamoDBSSEDescription
    AWSDynamoDBTable -- LATEST_STREAM --> AWSDynamoDBStream
    AWSDynamoDBTable -- TAGGED --> AWSTag
    AWSEBSSnapshot -- CREATED_FROM --> AWSEBSVolume
    AWSEBSVolume -- ATTACHED_TO --> AWSEC2Instance
    AWSEBSVolume -- TAGGED --> AWSTag
    AWSEC2Instance -- ASSUMES --> AWSRole
    AWSEC2Instance -- ELASTIC_IP_ADDRESS --> AWSElasticIPAddress
    AWSEC2Instance -- HAS_INFORMATION --> AWSSSMInstanceInformation
    AWSEC2Instance -- HAS_PATCH --> AWSSSMInstancePatch
    AWSEC2Instance -- INSTANCE_PROFILE --> AWSInstanceProfile
    AWSEC2Instance -- MEMBER_AUTO_SCALE_GROUP --> AWSAutoScalingGroup
    AWSEC2Instance -- MEMBER_OF_EC2_RESERVATION --> AWSEC2Reservation
    AWSEC2Instance -- MEMBER_OF_EC2_SECURITY_GROUP --> AWSEC2SecurityGroup
    AWSEC2Instance -- MEMBER_OF_EKS_CLUSTER --> AWSEKSCluster
    AWSEC2Instance -- NETWORK_INTERFACE --> AWSNetworkInterface
    AWSEC2Instance -- PART_OF_SUBNET --> AWSEC2Subnet
    AWSEC2Instance -- STS_ASSUMEROLE_ALLOW --> AWSRole
    AWSEC2Instance -- TAGGED --> AWSTag
    AWSEC2KeyPair ---|MATCHING_FINGERPRINT| AWSEC2KeyPair
    AWSEC2KeyPair -- SSH_LOGIN_TO --> AWSEC2Instance
    AWSEC2KeyPair -- TAGGED --> AWSTag
    AWSEC2NetworkAcl -- MEMBER_OF_AWS_VPC --> AWSVpc
    AWSEC2NetworkAcl -- PART_OF_SUBNET --> AWSEC2Subnet
    AWSEC2NetworkAcl -- PROTECTS --> AWSLoadBalancerV2
    AWSEC2NetworkAclRule -- MEMBER_OF_NACL --> AWSEC2NetworkAcl
    AWSEC2Route -- ROUTES_TO_GATEWAY --> AWSInternetGateway
    AWSEC2Route -- ROUTES_TO_VPC_ENDPOINT --> AWSVpcEndpoint
    AWSEC2RouteTable -- ASSOCIATION --> AWSEC2RouteTableAssociation
    AWSEC2RouteTable -- MEMBER_OF_AWS_VPC --> AWSVpc
    AWSEC2RouteTable -- ROUTE --> AWSEC2Route
    AWSEC2RouteTableAssociation -- ASSOCIATED_IGW_FOR_INGRESS --> AWSInternetGateway
    AWSEC2RouteTableAssociation -- ASSOCIATED_SUBNET --> AWSEC2Subnet
    AWSEC2SecurityGroup -- ALLOWS_TRAFFIC_FROM --> AWSEC2SecurityGroup
    AWSEC2SecurityGroup -- TAGGED --> AWSTag
    AWSEC2Subnet -- MEMBER_OF_AWS_VPC --> AWSVpc
    AWSEC2Subnet -- TAGGED --> AWSTag
    AWSECRImage -- ATTESTS --> AWSECRImage
    AWSECRImage -- BUILT_FROM --> AWSECRImage
    AWSECRImage -- CONTAINS_IMAGE --> AWSECRImage
    AWSECRImage -- HAS_LAYER --> AWSECRImageLayer
    AWSECRImage -- HEAD --> AWSECRImageLayer
    AWSECRImage -- TAIL --> AWSECRImageLayer
    AWSECRImageLayer -- NEXT --> AWSECRImageLayer
    AWSECRPullThroughCacheRule -- ASSOCIATED_WITH --> AWSRole
    AWSECRPullThroughCacheRule -- USES_SECRET --> AWSSecretsManagerSecret
    AWSECRRepository -- REPO_IMAGE --> AWSECRRepositoryImage
    AWSECRRepository -- TAGGED --> AWSTag
    AWSECRRepositoryImage -- IMAGE --> AWSECRImage
    AWSECSCluster -- HAS_CONTAINER_INSTANCE --> AWSECSContainerInstance
    AWSECSCluster -- HAS_SERVICE --> AWSECSService
    AWSECSCluster -- HAS_TASK --> AWSECSTask
    AWSECSCluster -- TAGGED --> AWSTag
    AWSECSContainer -- HAS_IMAGE --> AWSECRImage
    AWSECSContainer -- TAGGED --> AWSTag
    AWSECSContainer -- WORKLOAD_PARENT --> AWSECSTask
    AWSECSContainerInstance -- HAS_TASK --> AWSECSTask
    AWSECSContainerInstance -- IS_INSTANCE --> AWSEC2Instance
    AWSECSContainerInstance -- TAGGED --> AWSTag
    AWSECSService -- HAS_TASK --> AWSECSTask
    AWSECSService -- HAS_TASK_DEFINITION --> AWSECSTaskDefinition
    AWSECSService -- WORKLOAD_PARENT --> AWSECSCluster
    AWSECSTask -- HAS_CONTAINER --> AWSECSContainer
    AWSECSTask -- HAS_TASK_DEFINITION --> AWSECSTaskDefinition
    AWSECSTask -- NETWORK_INTERFACE --> AWSNetworkInterface
    AWSECSTask -- TAGGED --> AWSTag
    AWSECSTask -- WORKLOAD_PARENT --> AWSECSCluster
    AWSECSTask -- WORKLOAD_PARENT --> AWSECSService
    AWSECSTaskDefinition -- HAS_CONTAINER_DEFINITION --> AWSECSContainerDefinition
    AWSECSTaskDefinition -- HAS_EXECUTION_ROLE --> AWSRole
    AWSECSTaskDefinition -- HAS_TASK_ROLE --> AWSRole
    AWSECSTaskDefinition -- TAGGED --> AWSTag
    AWSEKSCluster -- HAS_ACCESS_ENTRY --> AWSEKSAccessEntry
    AWSEKSCluster -- TAGGED --> AWSTag
    AWSELBV2TargetGroup -- TARGETS --> AWSECSService
    AWSEMRCluster -- TAGGED --> AWSTag
    AWSESDomain -- MEMBER_OF_EC2_SECURITY_GROUP --> AWSEC2SecurityGroup
    AWSESDomain -- PART_OF_SUBNET --> AWSEC2Subnet
    AWSESDomain -- TAGGED --> AWSTag
    AWSEfsAccessPoint -- ACCESS_POINT_OF --> AWSEfsFileSystem
    AWSEfsFileSystem -- ENCRYPTED_BY --> AWSKMSKey
    AWSEfsMountTarget -- ATTACHED_TO --> AWSEfsFileSystem
    AWSElasticIPAddress -- TAGGED --> AWSTag
    AWSElasticacheCluster -- TAGGED --> AWSTag
    AWSElasticacheTopic -- CACHE_CLUSTER --> AWSElasticacheCluster
    AWSEventBridgeRule -- ASSOCIATED_WITH --> AWSRole
    AWSEventBridgeTarget -- LINKED_TO_RULE --> AWSEventBridgeRule
    AWSGlueJob -- USES --> AWSGlueConnection
    AWSGuardDutyFinding -- AFFECTS --> AWSAccountAccessKey
    AWSGuardDutyFinding -- AFFECTS --> AWSEC2Instance
    AWSGuardDutyFinding -- AFFECTS --> AWSEKSCluster
    AWSGuardDutyFinding -- AFFECTS --> AWSRole
    AWSGuardDutyFinding -- AFFECTS --> AWSS3Bucket
    AWSGuardDutyFinding -- AFFECTS --> AWSUser
    AWSGuardDutyFinding -- DETECTED_BY --> AWSGuardDutyDetector
    AWSGuardDutyFinding -- REMOTE_ACCOUNT --> AWSAccount
    AWSIdentityCenter -- HAS_PERMISSION_SET --> AWSPermissionSet
    AWSInspectorFinding -- AFFECTS --> AWSEC2Instance
    AWSInspectorFinding -- AFFECTS --> AWSECRImage
    AWSInspectorFinding -- AFFECTS --> AWSECRRepository
    AWSInspectorFinding -- HAS --> AWSInspectorPackage
    AWSInstanceProfile -- ASSOCIATED_WITH --> AWSRole
    AWSInternetGateway -- ATTACHED_TO --> AWSVpc
    AWSInternetGateway -- TAGGED --> AWSTag
    AWSIpPermissionInbound -- MEMBER_OF_EC2_SECURITY_GROUP --> AWSEC2SecurityGroup
    AWSIpRange -- MEMBER_OF_IP_RULE --> AWSIpRule
    AWSIpRule -- MEMBER_OF_EC2_SECURITY_GROUP --> AWSEC2SecurityGroup
    AWSKMSAlias -- KNOWN_AS --> AWSKMSKey
    AWSKMSGrant -- APPLIED_ON --> AWSKMSKey
    AWSKMSKey -- TAGGED --> AWSTag
    AWSLambda -- ASSUMES --> AWSRole
    AWSLambda -- HAS --> AWSECRImage
    AWSLambda -- HAS --> AWSLambdaLayer
    AWSLambda -- HAS_IMAGE --> AWSECRImage
    AWSLambda -- KNOWN_AS --> AWSLambdaFunctionAlias
    AWSLambda -- RESOURCE --> AWSLambdaEventSourceMapping
    AWSLambda -- STS_ASSUMEROLE_ALLOW --> AWSPrincipal
    AWSLambda -- TAGGED --> AWSTag
    AWSLaunchTemplate -- VERSION --> AWSLaunchTemplateVersion
    AWSLoadBalancer -- ELB_LISTENER --> AWSELBListener
    AWSLoadBalancer -- EXPOSE --> AWSEC2Instance
    AWSLoadBalancer -- MEMBER_OF_EC2_SECURITY_GROUP --> AWSEC2SecurityGroup
    AWSLoadBalancer -- NETWORK_INTERFACE --> AWSNetworkInterface
    AWSLoadBalancer -- PART_OF_SUBNET --> AWSEC2Subnet
    AWSLoadBalancer -- SOURCE_SECURITY_GROUP --> AWSEC2SecurityGroup
    AWSLoadBalancer -- TAGGED --> AWSTag
    AWSLoadBalancerV2 -- ELBV2_LISTENER --> AWSELBV2Listener
    AWSLoadBalancerV2 -- ELBV2_TARGET_GROUP --> AWSELBV2TargetGroup
    AWSLoadBalancerV2 -- EXPOSE --> AWSEC2Instance
    AWSLoadBalancerV2 -- EXPOSE --> AWSEC2PrivateIp
    AWSLoadBalancerV2 -- EXPOSE --> AWSECSContainer
    AWSLoadBalancerV2 -- EXPOSE --> AWSLambda
    AWSLoadBalancerV2 -- EXPOSE --> AWSLoadBalancerV2
    AWSLoadBalancerV2 -- MEMBER_OF_EC2_SECURITY_GROUP --> AWSEC2SecurityGroup
    AWSLoadBalancerV2 -- NETWORK_INTERFACE --> AWSNetworkInterface
    AWSLoadBalancerV2 -- PART_OF_SUBNET --> AWSEC2Subnet
    AWSLoadBalancerV2 -- SUBNET --> AWSEC2Subnet
    AWSLoadBalancerV2 -- TAGGED --> AWSTag
    AWSNetworkInterface -- ELASTIC_IP_ADDRESS --> AWSElasticIPAddress
    AWSNetworkInterface -- IPV6_ADDRESS --> AWSEC2Ipv6Address
    AWSNetworkInterface -- MEMBER_OF_EC2_SECURITY_GROUP --> AWSEC2SecurityGroup
    AWSNetworkInterface -- PART_OF_SUBNET --> AWSEC2Subnet
    AWSNetworkInterface -- PRIVATE_IP_ADDRESS --> AWSEC2PrivateIp
    AWSNetworkInterface -- TAGGED --> AWSTag
    AWSOrganization -- RESOURCE --> AWSOrganizationRoot
    AWSOrganizationRoot -- PARENT --> AWSOrganization
    AWSOrganizationRoot -- RESOURCE --> AWSAccount
    AWSOrganizationRoot -- RESOURCE --> AWSOrganizationalUnit
    AWSOrganizationalUnit -- PARENT --> AWSOrganizationRoot
    AWSOrganizationalUnit -- PARENT --> AWSOrganizationalUnit
    AWSOrganizationalUnit -- RESOURCE --> AWSAccount
    AWSOrganizationalUnit -- RESOURCE --> AWSOrganizationalUnit
    AWSPeeringConnection -- ACCEPTER_CIDR --> AWSCidrBlock
    AWSPeeringConnection -- ACCEPTER_VPC --> AWSVpc
    AWSPeeringConnection -- REQUESTER_CIDR --> AWSCidrBlock
    AWSPeeringConnection -- REQUESTER_VPC --> AWSVpc
    AWSPermissionSet -- ASSIGNED_TO_ROLE --> AWSRole
    AWSPrincipal -- ASSUMED_ROLE --> AWSRole
    AWSPrincipal -- CAN_ADMINISTER --> AWSRDSInstance
    AWSPrincipal -- CAN_ADMINISTER --> AWSRedshiftCluster
    AWSPrincipal -- CAN_EXEC --> AWSCloudFormationStack
    AWSPrincipal -- CAN_EXECUTE_COMMAND --> AWSECSTask
    AWSPrincipal -- CAN_PASS_ROLE --> AWSRole
    AWSPrincipal -- CAN_QUERY --> AWSDynamoDBTable
    AWSPrincipal -- CAN_QUERY --> AWSRDSInstance
    AWSPrincipal -- CAN_READ --> AWSS3Bucket
    AWSPrincipal -- CAN_START_SESSION --> AWSEC2Instance
    AWSPrincipal -- CAN_WRITE --> AWSDynamoDBTable
    AWSPrincipal -- CAN_WRITE --> AWSS3Bucket
    AWSPrincipal -- GET_SECRET --> AWSSecretsManagerSecret
    AWSPrincipal -- GRANTED_ACCESS_TO --> AWSEKSAccessEntry
    AWSPrincipal -- POLICY --> AWSInlinePolicy
    AWSPrincipal -- POLICY --> AWSManagedPolicy
    AWSPrincipal -- STS_ASSUMEROLE_ALLOW --> AWSRole
    AWSRDSCluster -- TAGGED --> AWSTag
    AWSRDSEventSubscription -- MONITORS --> AWSRDSCluster
    AWSRDSEventSubscription -- MONITORS --> AWSRDSInstance
    AWSRDSEventSubscription -- MONITORS --> AWSRDSSnapshot
    AWSRDSEventSubscription -- NOTIFIES --> AWSSNSTopic
    AWSRDSInstance -- ENCRYPTED_BY --> AWSKMSKey
    AWSRDSInstance -- IS_CLUSTER_MEMBER_OF --> AWSRDSCluster
    AWSRDSInstance -- IS_READ_REPLICA_OF --> AWSRDSInstance
    AWSRDSInstance -- MEMBER_OF_DB_SUBNET_GROUP --> AWSDBSubnetGroup
    AWSRDSInstance -- MEMBER_OF_EC2_SECURITY_GROUP --> AWSEC2SecurityGroup
    AWSRDSInstance -- TAGGED --> AWSTag
    AWSRDSSnapshot -- IS_SNAPSHOT_SOURCE --> AWSRDSInstance
    AWSRDSSnapshot -- TAGGED --> AWSTag
    AWSRedshiftCluster -- MEMBER_OF_AWS_VPC --> AWSVpc
    AWSRedshiftCluster -- MEMBER_OF_EC2_SECURITY_GROUP --> AWSEC2SecurityGroup
    AWSRedshiftCluster -- STS_ASSUMEROLE_ALLOW --> AWSPrincipal
    AWSRedshiftCluster -- TAGGED --> AWSTag
    AWSRole -- ALLOWED_BY --> AWSSSOGroup
    AWSRole -- ALLOWED_BY --> AWSSSOUser
    AWSRole -- TAGGED --> AWSTag
    AWSRole -- TRUSTS_AWS_PRINCIPAL --> AWSPrincipal
    AWSS3Acl -- APPLIES_TO --> AWSS3Bucket
    AWSS3Bucket -- ENCRYPTED_BY --> AWSKMSKey
    AWSS3Bucket -- NOTIFIES --> AWSSNSTopic
    AWSS3Bucket -- POLICY_STATEMENT --> AWSS3PolicyStatement
    AWSS3Bucket -- TAGGED --> AWSTag
    AWSSNSTopicSubscription -- HAS_SUBSCRIPTION --> AWSSNSTopic
    AWSSQSQueue -- HAS_DEADLETTER_QUEUE --> AWSSQSQueue
    AWSSQSQueue -- TAGGED --> AWSTag
    AWSSSMParameter -- ENCRYPTED_BY --> AWSKMSKey
    AWSSSOGroup -- HAS_PERMISSION_SET --> AWSPermissionSet
    AWSSSOGroup -- HAS_ROLE --> AWSPermissionSet
    AWSSSOUser -- ASSUMED_ROLE_WITH_SAML --> AWSRole
    AWSSSOUser -- HAS_PERMISSION_SET --> AWSPermissionSet
    AWSSSOUser -- HAS_ROLE --> AWSPermissionSet
    AWSSSOUser -- MEMBER_OF --> AWSSSOGroup
    AWSSSOUser -- MEMBER_OF_SSO_GROUP --> AWSSSOGroup
    AWSSageMakerDomain -- CONTAINS --> AWSSageMakerUserProfile
    AWSSageMakerEndpoint -- USES --> AWSSageMakerEndpointConfig
    AWSSageMakerEndpointConfig -- USES --> AWSSageMakerModel
    AWSSageMakerModel -- DERIVES_FROM --> AWSSageMakerModelPackage
    AWSSageMakerModel -- HAS_EXECUTION_ROLE --> AWSRole
    AWSSageMakerModel -- REFERENCES_ARTIFACTS_IN --> AWSS3Bucket
    AWSSageMakerModelPackage -- MEMBER_OF --> AWSSageMakerModelPackageGroup
    AWSSageMakerModelPackage -- REFERENCES_ARTIFACTS_IN --> AWSS3Bucket
    AWSSageMakerNotebookInstance -- CAN_INVOKE --> AWSSageMakerTrainingJob
    AWSSageMakerNotebookInstance -- HAS_EXECUTION_ROLE --> AWSRole
    AWSSageMakerTrainingJob -- HAS_EXECUTION_ROLE --> AWSRole
    AWSSageMakerTrainingJob -- PRODUCES_MODEL_ARTIFACT --> AWSS3Bucket
    AWSSageMakerTrainingJob -- READS_FROM --> AWSS3Bucket
    AWSSageMakerTransformJob -- USES --> AWSSageMakerModel
    AWSSageMakerTransformJob -- WRITES_TO --> AWSS3Bucket
    AWSSageMakerUserProfile -- HAS_EXECUTION_ROLE --> AWSRole
    AWSSecretsManagerSecret -- ENCRYPTED_BY --> AWSKMSKey
    AWSSecretsManagerSecret -- TAGGED --> AWSTag
    AWSSecretsManagerSecretVersion -- ENCRYPTED_BY --> AWSKMSKey
    AWSSecretsManagerSecretVersion -- VERSION_OF --> AWSSecretsManagerSecret
    AWSTransitGateway -- SHARED_WITH --> AWSAccount
    AWSTransitGateway -- TAGGED --> AWSTag
    AWSTransitGatewayAttachment -- ATTACHED_TO --> AWSTransitGateway
    AWSTransitGatewayAttachment -- PART_OF_SUBNET --> AWSEC2Subnet
    AWSTransitGatewayAttachment -- TAGGED --> AWSTag
    AWSUser -- AWS_ACCESS_KEY --> AWSAccountAccessKey
    AWSUser -- MEMBER_AWS_GROUP --> AWSGroup
    AWSUser -- MEMBER_OF --> AWSGroup
    AWSUser -- MFA_DEVICE --> AWSMfaDevice
    AWSUser -- TAGGED --> AWSTag
    AWSVpc -- BLOCK_ASSOCIATION --> AWSCidrBlock
    AWSVpc -- MEMBER_OF_EC2_SECURITY_GROUP --> AWSEC2SecurityGroup
    AWSVpc -- RESOURCE --> AWSTransitGatewayAttachment
    AWSVpc -- TAGGED --> AWSTag
    AWSVpcEndpoint -- MEMBER_OF_AWS_VPC --> AWSVpc
    AWSVpcEndpoint -- MEMBER_OF_SECURITY_GROUP --> AWSEC2SecurityGroup
    AWSVpcEndpoint -- ROUTES_THROUGH --> AWSRouteTable
    AWSVpcEndpoint -- USES_SUBNET --> AWSEC2Subnet
```

### AWSAccount

Represents an AWS account.

> **Ontology Mapping**: Some schema variants may also use the ontology label [`Tenant`](#ontology-tenant).

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The AWS Account ID number |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| account_access_keys_present |  | 1 if root account access keys exist, 0 otherwise. From IAM GetAccountSummary. |
| account_mfa_enabled |  | 1 if the root account has MFA enabled, 0 otherwise. From IAM GetAccountSummary. |
| account_signing_certificates_present |  | 1 if root account signing certificates exist, 0 otherwise. From IAM GetAccountSummary. |
| arn | Yes | The AWS Organizations ARN for this account, when discovered from AWS Organizations. |
| email |  | The email address associated with the account, when discovered from AWS Organizations. |
| foreign |  | Whether this account was discovered outside the configured AWS sync scope. |
| groups |  | Number of IAM groups in the account. From IAM GetAccountSummary. |
| inscope |  | Indicates that the account is part of the sync scope (true or false). |
| instance_profiles |  | Number of instance profiles in the account. From IAM GetAccountSummary. |
| joined_method |  | The method by which the account joined the organization. |
| joined_timestamp |  | The date the account joined the organization. |
| mfa_devices |  | Number of MFA devices registered in the account. From IAM GetAccountSummary. |
| mfa_devices_in_use |  | Number of MFA devices currently in use. From IAM GetAccountSummary. |
| name |  | The name of the account |
| org_id | Yes | The AWS Organization ID that contains this account, when available. |
| policies |  | Number of IAM policies in the account. From IAM GetAccountSummary. |
| policy_versions_in_use |  | Number of policy versions in use. From IAM GetAccountSummary. |
| providers |  | Number of identity providers in the account. From IAM GetAccountSummary. |
| roles |  | Number of IAM roles in the account. From IAM GetAccountSummary. |
| server_certificates |  | Number of server certificates in the account. From IAM GetAccountSummary. |
| state |  | The AWS Organizations account lifecycle state. |
| status |  | The legacy AWS Organizations account status. AWS recommends using `state` instead. |
| users |  | Number of IAM users in the account. From IAM GetAccountSummary. |
| *_ont_name* | Yes | Normalized field sourced from `name`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |
| *_ont_status* | Yes | Normalized field sourced from `state`. |

#### Relationships

- `(:AWSAccount)-[:MEMBER]->(:AWSInspectorFinding)`

- `(:AWSAccount)-[:PARENT]->(:AWSOrganizationRoot)`

- `(:AWSAccount)-[:PARENT]->(:AWSOrganizationalUnit)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSACMCertificate)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSAPIGatewayClientCertificate)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSAPIGatewayDeployment)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSAPIGatewayIntegration)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSAPIGatewayMethod)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSAPIGatewayResource)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSAPIGatewayRestAPI)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSAPIGatewayStage)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSAPIGatewayV2API)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSAccountAccessKey)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSAutoScalingGroup)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSBedrockAgent)`: Defines the relationship from AWSBedrockAgent to AWSAccount.)

- `(:AWSAccount)-[:RESOURCE]->(:AWSBedrockCustomModel)`: Defines the relationship from AWSBedrockCustomModel to AWSAccount.

- `(:AWSAccount)-[:RESOURCE]->(:AWSBedrockFoundationModel)`: Defines the relationship from AWSBedrockFoundationModel to AWSAccount.

- `(:AWSAccount)-[:RESOURCE]->(:AWSBedrockGuardrail)`: Indicates that an AWS account contains the Bedrock guardrail.

- `(:AWSAccount)-[:RESOURCE]->(:AWSBedrockKnowledgeBase)`: Defines the relationship from AWSBedrockKnowledgeBase to AWSAccount.

- `(:AWSAccount)-[:RESOURCE]->(:AWSBedrockProvisionedModelThroughput)`: Defines the relationship from AWSBedrockProvisionedModelThroughput to AWSAccount.

- `(:AWSAccount)-[:RESOURCE]->(:AWSCloudFormationStack)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSCloudFrontDistribution)`: Indicates that an AWS account contains the CloudFront distribution.

- `(:AWSAccount)-[:RESOURCE]->(:AWSCloudTrailTrail)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSCloudWatchLogGroup)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSCloudWatchLogMetricFilter)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSCloudWatchMetricAlarm)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSCodeBuildProject)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSCognitoIdentityPool)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSCognitoUserPool)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSConfigDeliveryChannel)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSConfigRule)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSConfigurationRecorder)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSDBSubnetGroup)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSDNSRecord)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSDNSZone)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSDynamoDBArchivalSummary)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSDynamoDBBackup)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSDynamoDBBillingModeSummary)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSDynamoDBGlobalSecondaryIndex)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSDynamoDBRestoreSummary)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSDynamoDBSSEDescription)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSDynamoDBStream)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSDynamoDBTable)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSEBSSnapshot)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSEBSVolume)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSEC2Image)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSEC2Instance)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSEC2Ipv6Address)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSEC2KeyPair)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSEC2NetworkAcl)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSEC2NetworkAclRule)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSEC2PrivateIp)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSEC2Reservation)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSEC2ReservedInstance)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSEC2Route)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSEC2RouteTable)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSEC2RouteTableAssociation)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSEC2SecurityGroup)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSEC2Subnet)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSECRImage)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSECRImageLayer)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSECRPullThroughCacheRule)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSECRRepository)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSECRRepositoryImage)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSECSCluster)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSECSContainer)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSECSContainerDefinition)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSECSContainerInstance)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSECSService)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSECSTask)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSECSTaskDefinition)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSEKSAccessEntry)`: An EKS access entry is a resource within an AWS account.

- `(:AWSAccount)-[:RESOURCE]->(:AWSEKSCluster)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSELBListener)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSELBV2Listener)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSELBV2TargetGroup)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSEMRCluster)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSESDomain)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSEfsAccessPoint)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSEfsFileSystem)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSEfsMountTarget)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSElasticIPAddress)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSElasticacheCluster)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSElasticacheTopic)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSEventBridgeRule)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSEventBridgeTarget)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSFederatedPrincipal)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSGlueConnection)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSGlueJob)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSGroup)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSGuardDutyDetector)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSGuardDutyFinding)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSIdentityCenter)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSInlinePolicy)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSInspectorFinding)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSInspectorPackage)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSInstanceProfile)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSInternetGateway)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSIpPermissionInbound)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSIpRange)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSIpRule)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSKMSAlias)`: Relationship between KMS Alias and AWS Account

- `(:AWSAccount)-[:RESOURCE]->(:AWSKMSGrant)`: Relationship between AWSKMSGrant and AWS Account

- `(:AWSAccount)-[:RESOURCE]->(:AWSKMSKey)`: Relationship between AWSKMSKey and AWS Account

- `(:AWSAccount)-[:RESOURCE]->(:AWSLambda)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSLambdaEventSourceMapping)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSLambdaFunctionAlias)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSLambdaLayer)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSLaunchConfiguration)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSLaunchTemplate)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSLaunchTemplateVersion)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSLoadBalancer)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSLoadBalancerV2)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSMfaDevice)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSNameServer)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSNetworkInterface)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSPeeringConnection)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSPermissionSet)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSPrincipal)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSRDSCluster)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSRDSEventSubscription)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSRDSInstance)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSRDSSnapshot)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSRedshiftCluster)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSRole)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSRootPrincipal)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSRouteTable)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSS3AccountPublicAccessBlock)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSS3Acl)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSS3Bucket)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSS3PolicyStatement)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSSAMLProvider)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSSESEmailIdentity)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSSNSTopic)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSSNSTopicSubscription)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSSQSQueue)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSSSMInstanceInformation)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSSSMInstancePatch)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSSSMParameter)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSSSOGroup)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSSSOUser)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSSageMakerDomain)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSSageMakerEndpoint)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSSageMakerEndpointConfig)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSSageMakerModel)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSSageMakerModelPackage)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSSageMakerModelPackageGroup)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSSageMakerNotebookInstance)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSSageMakerTrainingJob)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSSageMakerTransformJob)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSSageMakerUserProfile)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSSecretsManagerSecret)`: Relationship between Secret and AWS Account

- `(:AWSAccount)-[:RESOURCE]->(:AWSSecretsManagerSecretVersion)`: Relationship between Secret Version and AWS Account

- `(:AWSAccount)-[:RESOURCE]->(:AWSSecurityHub)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSServerCertificate)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSTransitGateway)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSTransitGatewayAttachment)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSUser)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSVpc)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSVpcEndpoint)`

- `(:AWSGuardDutyFinding)-[:REMOTE_ACCOUNT]->(:AWSAccount)`

- `(:AWSOrganizationRoot)-[:RESOURCE]->(:AWSAccount)`

- `(:AWSOrganizationalUnit)-[:RESOURCE]->(:AWSAccount)`

- `(:AWSTransitGateway)-[:SHARED_WITH]->(:AWSAccount)`

- `(:DatabricksCredentialConfig)-[:IN_ACCOUNT]->(:AWSAccount)`: A Databricks credential configuration uses a role in an AWS account.

### AWSAccountAccessKey

Representation of an AWS [Access Key](https://docs.aws.amazon.com/IAM/latest/APIReference/API_AccessKey.html).

> **Ontology Mapping**: This node uses the ontology label [`APIKey`](#ontology-apikey).

> **Additional Labels**: This node also uses `AccountAccessKey`.

> **Additional Label Definitions**:
>
> - `AccountAccessKey`: Compatibility label for the deprecated `AccountAccessKey` aws node label. Use `AWSAccountAccessKey` instead. Scheduled for removal in v1.0.0.

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The access key ID (same as accesskeyid) |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| accesskeyid | Yes | The ID for this access key |
| createdate |  | Date when access key was created |
| createdate_dt |  | Access-key creation timestamp normalized as a Neo4j datetime. |
| lastuseddate |  | Date when the key was last used |
| lastuseddate_dt |  | Most recent access-key use timestamp normalized as a Neo4j datetime. |
| lastusedregion |  | The region where the access key was last used |
| lastusedservice |  | The service that was last used with the access key |
| status |  | Active: valid for API calls.  Inactive: not valid for API calls |
| *_ont_created_at* | Yes | Normalized field sourced from `createdate`. |
| *_ont_last_used_at* | Yes | Normalized field sourced from `lastuseddate`. |
| *_ont_name* | Yes | Normalized field sourced from `accesskeyid`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSAccountAccessKey)`

- `(:AWSAccountAccessKey)-[:OWNED_BY]->(:AWSUser)`

- `(:AWSGuardDutyFinding)-[:AFFECTS]->(:AWSAccountAccessKey)`

- `(:AWSUser)-[:AWS_ACCESS_KEY]->(:AWSAccountAccessKey)`

- `(:User)-[:OWNS]->(:APIKey)`: generated by analysis job `Ontology - User OWNS APIKey linking`.

### AWSACMCertificate

Representation of an AWS [ACM Certificate](https://docs.aws.amazon.com/acm/latest/APIReference/API_CertificateDetail.html).

> **Ontology Mapping**: This node uses the ontology label [`Certificate`](#ontology-certificate).

> **Additional Labels**: This node also uses `ACMCertificate`.

> **Additional Label Definitions**:
>
> - `ACMCertificate`: Compatibility label for the deprecated `ACMCertificate` aws node label. Use `AWSACMCertificate` instead. Scheduled for removal in v1.0.0.

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The ARN of the certificate |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| arn | Yes | The Amazon Resource Name (ARN) of the certificate |
| domainname |  | The primary domain name of the certificate |
| in_use_by |  | List of ARNs of resources that use this certificate |
| key_algorithm |  | The key algorithm used |
| not_after |  | The time after which the certificate expires |
| not_before |  | The time before which the certificate is invalid |
| region |  | The AWS region where the certificate is located |
| signature_algorithm |  | The signature algorithm |
| status |  | The status of the certificate |
| type |  | The source of the certificate |
| *_ont_domain* | Yes | Normalized field sourced from `domainname`. |
| *_ont_expiry* | Yes | Normalized field sourced from `not_after`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |

#### Relationships

- `(:AWSACMCertificate)-[:USED_BY]->(:AWSELBV2Listener)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSACMCertificate)`

- `(:AWSCloudFrontDistribution)-[:USES_CERTIFICATE]->(:AWSACMCertificate)`: Indicates that the CloudFront distribution uses an ACM certificate for HTTPS.

### AWSAPIGatewayClientCertificate

Representation of an AWS [API Gateway Client Certificate](https://docs.aws.amazon.com/apigateway/api-reference/resource/client-certificate/).

> **Additional Labels**: This node also uses `APIGatewayClientCertificate`.

> **Additional Label Definitions**:
>
> - `APIGatewayClientCertificate`: Compatibility label for the deprecated `APIGatewayClientCertificate` aws node label. Use `AWSAPIGatewayClientCertificate` instead. Scheduled for removal in v1.0.0.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The identifier of the client certificate |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| createddate |  | The timestamp when the client certificate was created |
| expirationdate |  | The timestamp when the client certificate will expire |

#### Relationships

- `(:AWSAPIGatewayStage)-[:HAS_CERTIFICATE]->(:AWSAPIGatewayClientCertificate)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSAPIGatewayClientCertificate)`

### AWSAPIGatewayDeployment

Representation of an AWS [API Gateway Deployment](https://docs.aws.amazon.com/apigateway/latest/api/API_GetDeployments.html).

> **Additional Labels**: This node also uses `APIGatewayDeployment`.

> **Additional Label Definitions**:
>
> - `APIGatewayDeployment`: Compatibility label for the deprecated `APIGatewayDeployment` aws node label. Use `AWSAPIGatewayDeployment` instead. Scheduled for removal in v1.0.0.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The identifier for the deployment resource as string of api id and deployment id |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| arn | Yes | The identifier for the deployment resource. |
| description |  | The description for the deployment resource. |
| region |  | The region for the deployment resource. |

#### Relationships

- `(:AWSAPIGatewayRestAPI)-[:HAS_DEPLOYMENT]->(:AWSAPIGatewayDeployment)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSAPIGatewayDeployment)`

### AWSAPIGatewayIntegration

Representation of an AWS [API Gateway Integration](https://docs.aws.amazon.com/apigateway/latest/api/API_GetIntegration.html).

> **Additional Labels**: This node also uses `APIGatewayIntegration`.

> **Additional Label Definitions**:
>
> - `APIGatewayIntegration`: Compatibility label for the deprecated `APIGatewayIntegration` aws node label. Use `AWSAPIGatewayIntegration` instead. Scheduled for removal in v1.0.0.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The id represented as ApiId/ResourceId/HttpMethod |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| api_id |  | The  identifier for the API |
| connection_id |  | The ID of the VpcLink used for the integration when connectionType=VPC_LINK and undefined, otherwise |
| connection_type |  | The type of the network connection to the integration endpoint |
| credentials |  | Specifies the credentials required for the integration, if any |
| httpmethod |  | Specifies a get integration request's HTTP method |
| integration_http_method |  | Specifies the integration's HTTP method type |
| resource_id |  | Identifier for respective resource |
| type |  | Specifies an API method integration type |
| uri |  | Specifies Uniform Resource Identifier (URI) of the integration endpoint |

#### Relationships

- `(:AWSAPIGatewayResource)-[:HAS_INTEGRATION]->(:AWSAPIGatewayIntegration)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSAPIGatewayIntegration)`

### AWSAPIGatewayMethod

Representation of an AWS [API Gateway Method](https://docs.aws.amazon.com/apigateway/latest/api/API_GetMethod.html).

> **Additional Labels**: This node also uses `APIGatewayMethod`.

> **Additional Label Definitions**:
>
> - `APIGatewayMethod`: Compatibility label for the deprecated `APIGatewayMethod` aws node label. Use `AWSAPIGatewayMethod` instead. Scheduled for removal in v1.0.0.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The id represented as ApiId/ResourceId/HttpMethod |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| api_id |  | The  identifier for the API |
| api_key_required |  | A boolean flag specifying whether a valid ApiKey is required to invoke this method |
| authorization_type |  | The method's authorization type |
| authorizer_id |  | The identifier of an authorizer to use on this method |
| httpmethod |  | The method's HTTP verb |
| operation_name |  | A human-friendly operation identifier for the method |
| request_validator_id |  | The identifier of a RequestValidator for request validation |
| resource_id |  | Identifier for respective resource |

#### Relationships

- `(:AWSAPIGatewayResource)-[:HAS_METHOD]->(:AWSAPIGatewayMethod)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSAPIGatewayMethod)`

### AWSAPIGatewayResource

Representation of an AWS [API Gateway Resource](https://docs.aws.amazon.com/apigateway/api-reference/resource/resource/).

> **Additional Labels**: This node also uses `APIGatewayResource`.

> **Additional Label Definitions**:
>
> - `APIGatewayResource`: Compatibility label for the deprecated `APIGatewayResource` aws node label. Use `AWSAPIGatewayResource` instead. Scheduled for removal in v1.0.0.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The id of the resource |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| parentid |  | The id of the parent resource |
| path |  | The full path of the resource |
| pathpart |  | The last path segment of the resource |

#### Relationships

- `(:AWSAPIGatewayResource)-[:HAS_INTEGRATION]->(:AWSAPIGatewayIntegration)`

- `(:AWSAPIGatewayResource)-[:HAS_METHOD]->(:AWSAPIGatewayMethod)`

- `(:AWSAPIGatewayRestAPI)-[:RESOURCE]->(:AWSAPIGatewayResource)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSAPIGatewayResource)`

### AWSAPIGatewayRestAPI

Representation of an AWS [API Gateway REST API](https://docs.aws.amazon.com/apigateway/latest/api/API_GetRestApis.html).

> **Additional Labels**: This node also uses `APIGatewayRestAPI`.

> **Additional Label Definitions**:
>
> - `APIGatewayRestAPI`: Compatibility label for the deprecated `APIGatewayRestAPI` aws node label. Use `AWSAPIGatewayRestAPI` instead. Scheduled for removal in v1.0.0.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The id of the REST API |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| anonymous_access |  | True if this API has a resource policy that allows anonymous/public access (policy-level analysis via PolicyUniverse). |
| anonymous_actions |  | List of anonymous internet accessible actions that may be run on the API (policy-level). |
| createddate |  | The timestamp when the REST API was created |
| disableexecuteapiendpoint |  | Specifies whether clients can invoke your API by using the default `execute-api` endpoint |
| endpoint_type | Yes | The endpoint configuration type: `EDGE` (CloudFront), `REGIONAL` (direct), or `PRIVATE` (VPC-only). |
| exposed_internet | Yes | True if the API is network-reachable from the internet (`EDGE` or `REGIONAL`), false for `PRIVATE` endpoints. |
| minimumcompressionsize |  | A nullable integer that is used to enable or disable the compression of the REST API |
| region |  | The region where the REST API is created |
| version |  | The version identifier for the API |

#### Relationships

- `(:AWSAPIGatewayRestAPI)-[:ASSOCIATED_WITH]->(:AWSAPIGatewayStage)`

- `(:AWSAPIGatewayRestAPI)-[:HAS_DEPLOYMENT]->(:AWSAPIGatewayDeployment)`

- `(:AWSAPIGatewayRestAPI)-[:RESOURCE]->(:AWSAPIGatewayResource)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSAPIGatewayRestAPI)`

### AWSAPIGatewayStage

Representation of an AWS [API Gateway Stage](https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-stages.html).

> **Additional Labels**: This node also uses `APIGatewayStage`.

> **Additional Label Definitions**:
>
> - `APIGatewayStage`: Compatibility label for the deprecated `APIGatewayStage` aws node label. Use `AWSAPIGatewayStage` instead. Scheduled for removal in v1.0.0.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The ARN of the API Gateway Stage |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| cacheclusterenabled |  | Specifies whether a cache cluster is enabled for the stage. |
| cacheclusterstatus |  | The status of the cache cluster for the stage, if enabled. |
| clientcertificateid |  | The identifier of a client certificate for an API stage. |
| createddate |  | The timestamp when the stage was created |
| deploymentid |  | The identifier of the Deployment that the stage points to. |
| stagename |  | The name of the API Gateway Stage |
| tracingenabled |  | Specifies whether active tracing with X-ray is enabled for the Stage |
| webaclarn |  | The ARN of the WebAcl associated with the Stage |

#### Relationships

- `(:AWSAPIGatewayRestAPI)-[:ASSOCIATED_WITH]->(:AWSAPIGatewayStage)`

- `(:AWSAPIGatewayStage)-[:HAS_CERTIFICATE]->(:AWSAPIGatewayClientCertificate)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSAPIGatewayStage)`

### AWSAPIGatewayV2API

Representation of an AWS [API Gateway v2 API](https://docs.aws.amazon.com/apigatewayv2/latest/api-reference/apis.html#apisget).

> **Additional Labels**: This node also uses `APIGatewayV2API`.

> **Additional Label Definitions**:
>
> - `APIGatewayV2API`: Compatibility label for the deprecated `APIGatewayV2API` aws node label. Use `AWSAPIGatewayV2API` instead. Scheduled for removal in v1.0.0.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The id of the API |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| apiendpoint |  | The endpoint URL of the API |
| apikeyselectionexpression |  | Expression for selecting API keys |
| createddate |  | The timestamp when the API was created |
| description |  | The description of the API |
| name |  | The name of the API |
| protocoltype |  | The protocol type (HTTP or WEBSOCKET) |
| region |  | The region where the API is created |
| routeselectionexpression |  | Expression for selecting routes |
| version |  | The version identifier for the API |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSAPIGatewayV2API)`

### AWSAutoScalingGroup

Representation of an AWS [Auto Scaling Group Resource](https://docs.aws.amazon.com/autoscaling/ec2/userguide/AWSAutoScalingGroup.html).

> **Additional Labels**: This node also uses `AutoScalingGroup`.

> **Additional Label Definitions**:
>
> - `AutoScalingGroup`: Compatibility label for the deprecated `AutoScalingGroup` aws node label. Use `AWSAutoScalingGroup` instead. Scheduled for removal in v1.0.0.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The ARN of the Auto Scaling Group (same as arn) |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| arn |  | The ARN of the Auto Scaling Group |
| capacityrebalance |  | Indicates whether Capacity Rebalancing is enabled. |
| createdtime |  | The date and time the group was created. |
| defaultcooldown |  | The duration of the default cooldown period, in seconds. |
| desiredcapacity |  | The desired size of the group. |
| exposed_internet |  | Property generated by analysis job: `AWS Auto Scaling group internet exposure`. |
| exposed_internet_type |  | Property generated by analysis job: `AWS Auto Scaling group internet exposure`. |
| healthcheckgraceperiod |  | The amount of time, in seconds, that Amazon EC2 Auto Scaling waits before checking the health status of an EC2 instance that has come into service. |
| healthchecktype |  | The service to use for the health checks. |
| launchconfigurationname |  | The name of the associated launch configuration. |
| launchtemplateid |  | The ID of the launch template. |
| launchtemplatename |  | The name of the launch template. |
| launchtemplateversion |  | The version number of the launch template. |
| maxinstancelifetime |  | The maximum amount of time, in seconds, that an instance can be in service. |
| maxsize |  | The maximum size of the group. |
| minsize |  | The minimum size of the group. |
| name |  | The name of the Auto Scaling group |
| newinstancesprotectedfromscalein |  | Indicates whether newly launched instances are protected from termination by Amazon EC2 Auto Scaling when scaling in. |
| region |  | The region of the auto scaling group. |
| status |  | The current state of the group when the DeleteAutoScalingGroup operation is in progress. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSAutoScalingGroup)`

- `(:AWSAutoScalingGroup)-[:HAS_LAUNCH_CONFIG]->(:AWSLaunchConfiguration)`

- `(:AWSAutoScalingGroup)-[:HAS_LAUNCH_TEMPLATE]->(:AWSLaunchTemplate)`

- `(:AWSAutoScalingGroup)-[:TAGGED]->(:AWSTag)`: `AWSAutoScalingGroup` is tagged with an `AWSTag` discovered by the AWS Resource Groups Tagging API.

- `(:AWSAutoScalingGroup)-[:VPC_IDENTIFIER]->(:AWSEC2Subnet)`

- `(:AWSEC2Instance)-[:MEMBER_AUTO_SCALE_GROUP]->(:AWSAutoScalingGroup)`

### AWSBedrockAgent

Representation of an AWS [Bedrock Agent](https://docs.aws.amazon.com/bedrock/latest/userguide/agents.html). Agents are autonomous AI assistants that can break down tasks, use tools (Lambda functions), and search knowledge bases to accomplish complex goals.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The ARN of the agent |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| agent_id | Yes | The unique identifier of the agent |
| agent_name |  | The name of the agent |
| agent_resource_role_arn |  | The ARN of the IAM role that the agent assumes |
| agent_status |  | The status of the agent (e.g., "CREATING", "PREPARED", "FAILED") |
| arn | Yes | The ARN of the agent |
| created_at |  | The timestamp when the agent was created |
| description |  | The description of the agent |
| foundation_model |  | The ARN of the foundation or custom model the agent uses |
| idle_session_ttl_in_seconds |  | The time in seconds before idle sessions expire |
| instruction |  | The instructions that guide the agent's behavior |
| prepared_at |  | The timestamp when the agent was last prepared |
| region |  | The AWS region where the agent exists |
| updated_at |  | The timestamp when the agent was last updated |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSBedrockAgent)`: Defines the relationship from AWSBedrockAgent to AWSAccount.)

- `(:AWSBedrockAgent)-[:HAS_ROLE]->(:AWSRole)`: Defines the relationship from AWSBedrockAgent to AWSRole (existing IAM role nodes).

- `(:AWSBedrockAgent)-[:INVOKES]->(:AWSLambda)`: Defines the relationship from AWSBedrockAgent to AWSLambda (existing Lambda function nodes).

- `(:AWSBedrockAgent)-[:USES_KNOWLEDGE_BASE]->(:AWSBedrockKnowledgeBase)`: Defines the relationship from AWSBedrockAgent to AWSBedrockKnowledgeBase.

- `(:AWSBedrockAgent)-[:USES_MODEL]->(:AWSBedrockCustomModel)`: Defines the relationship from AWSBedrockAgent to AWSBedrockCustomModel.
Only created when the agent uses a custom model directly.

- `(:AWSBedrockAgent)-[:USES_MODEL]->(:AWSBedrockFoundationModel)`: Defines the relationship from AWSBedrockAgent to AWSBedrockFoundationModel.
Only created when the agent uses a foundation model directly (not via provisioned throughput).

- `(:AWSBedrockAgent)-[:USES_MODEL]->(:AWSBedrockProvisionedModelThroughput)`: Defines the relationship from AWSBedrockAgent to AWSBedrockProvisionedModelThroughput.
Created when the agent uses a provisioned throughput for model inference.

- `(:AWSBedrockGuardrail)-[:APPLIED_TO]->(:AWSBedrockAgent)`: Defines the relationship from AWSBedrockGuardrail to AWSBedrockAgent.

### AWSBedrockCustomModel

Representation of an AWS [Bedrock Custom Model](https://docs.aws.amazon.com/bedrock/latest/userguide/custom-models.html). Custom models are created through fine-tuning or continued pre-training of foundation models using customer-provided training data.

> **Ontology Mapping**: This node uses the ontology label [`AIModel`](#ontology-aimodel).

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The ARN of the custom model |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| arn | Yes | The ARN of the custom model |
| base_model_arn |  | The ARN of the foundation model this custom model is based on |
| base_model_name |  | Name of the foundation model customized to produce this model. |
| creation_time |  | The timestamp when the custom model was created |
| customization_type |  | The type of customization (e.g., "FINE_TUNING", "CONTINUED_PRE_TRAINING") |
| job_arn |  | The ARN of the training job |
| job_name |  | The name of the training job that created this model |
| model_name |  | The name of the custom model |
| output_data_s3_uri |  | The S3 URI where training output is stored |
| region |  | The AWS region where the custom model exists |
| status |  | Current status of this `AWSBedrockCustomModel` node. |
| training_data_s3_uri |  | The S3 URI of the training data |
| *_ont_name* | Yes | Normalized field sourced from `model_name`. |
| *_ont_provider* | Yes | Property generated by the ontology mapping. |
| *_ont_source* |  | Module that populated this node's ontology fields. |
| *_ont_status* | Yes | Normalized field sourced from `status`. |
| *_ont_type* | Yes | Normalized field sourced from `customization_type`. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSBedrockCustomModel)`: Defines the relationship from AWSBedrockCustomModel to AWSAccount.

- `(:AWSBedrockAgent)-[:USES_MODEL]->(:AWSBedrockCustomModel)`: Defines the relationship from AWSBedrockAgent to AWSBedrockCustomModel.
Only created when the agent uses a custom model directly.

- `(:AWSBedrockCustomModel)-[:BASED_ON]->(:AWSBedrockFoundationModel)`: Defines the relationship from AWSBedrockCustomModel to AWSBedrockFoundationModel.

- `(:AWSBedrockCustomModel)-[:TRAINED_FROM]->(:AWSS3Bucket)`: Defines the relationship from AWSBedrockCustomModel to AWSS3Bucket (training data source).

- `(:AWSBedrockProvisionedModelThroughput)-[:PROVIDES_CAPACITY_FOR]->(:AWSBedrockCustomModel)`: Defines the relationship from AWSBedrockProvisionedModelThroughput to AWSBedrockCustomModel.
This relationship is created when the provisioned throughput is for a custom model.

### AWSBedrockFoundationModel

Representation of an AWS [Bedrock Foundation Model](https://docs.aws.amazon.com/bedrock/latest/userguide/models-supported.html). Foundation models are pre-trained large language models and multimodal models provided by AI companies like Anthropic, Amazon, Meta, and others.

> **Ontology Mapping**: This node uses the ontology label [`AIModel`](#ontology-aimodel).

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The ARN of the foundation model |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| arn | Yes | The ARN of the foundation model |
| customizations_supported |  | List of customization types supported (e.g., ["FINE_TUNING"]) |
| inference_types_supported |  | List of inference types supported (e.g., ["ON_DEMAND", "PROVISIONED"]) |
| input_modalities |  | List of input modalities the model supports (e.g., ["TEXT", "IMAGE"]) |
| model_id | Yes | The model identifier (e.g., "anthropic.claude-3-5-sonnet-20240620-v1:0") |
| model_lifecycle_status |  | The lifecycle status of the model (e.g., "ACTIVE", "LEGACY") |
| model_name |  | The human-readable name of the model |
| output_modalities |  | List of output modalities the model supports (e.g., ["TEXT"]) |
| provider_name |  | The provider of the model (e.g., "Anthropic", "Amazon", "Meta") |
| region |  | The AWS region where the model is available |
| response_streaming_supported |  | Whether the model supports streaming responses |
| *_ont_name* | Yes | Normalized field sourced from `model_name`. |
| *_ont_provider* | Yes | Normalized field sourced from `provider_name`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |
| *_ont_status* | Yes | Normalized field sourced from `model_lifecycle_status`. |
| *_ont_type* | Yes | Property generated by the ontology mapping. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSBedrockFoundationModel)`: Defines the relationship from AWSBedrockFoundationModel to AWSAccount.

- `(:AWSBedrockAgent)-[:USES_MODEL]->(:AWSBedrockFoundationModel)`: Defines the relationship from AWSBedrockAgent to AWSBedrockFoundationModel.
Only created when the agent uses a foundation model directly (not via provisioned throughput).

- `(:AWSBedrockCustomModel)-[:BASED_ON]->(:AWSBedrockFoundationModel)`: Defines the relationship from AWSBedrockCustomModel to AWSBedrockFoundationModel.

- `(:AWSBedrockKnowledgeBase)-[:USES_EMBEDDING_MODEL]->(:AWSBedrockFoundationModel)`: Defines the relationship from AWSBedrockKnowledgeBase to AWSBedrockFoundationModel.

- `(:AWSBedrockProvisionedModelThroughput)-[:PROVIDES_CAPACITY_FOR]->(:AWSBedrockFoundationModel)`: Defines the relationship from AWSBedrockProvisionedModelThroughput to AWSBedrockFoundationModel.
This relationship is created when the provisioned throughput is for a foundation model.

### AWSBedrockGuardrail

Representation of an AWS [Bedrock Guardrail](https://docs.aws.amazon.com/bedrock/latest/userguide/guardrails.html). Guardrails provide content filtering, safety controls, and policy enforcement for models and agents by blocking harmful content and enforcing responsible AI usage.

The [:APPLIED_TO] relationship from Guardrail→Agent is created from the Agent side
using AWSBedrockGuardrailToAgentRel (defined in agent.py).

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The ARN of the guardrail |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| arn | Yes | The ARN of the guardrail |
| blocked_input_messaging |  | The message returned when input is blocked |
| blocked_outputs_messaging |  | The message returned when output is blocked |
| created_at |  | The timestamp when the guardrail was created |
| description |  | The description of the guardrail |
| guardrail_id | Yes | The unique identifier of the guardrail |
| name |  | The name of the guardrail |
| region |  | The AWS region where the guardrail exists |
| status |  | The status of the guardrail (e.g., "CREATING", "READY", "FAILED") |
| updated_at |  | The timestamp when the guardrail was last updated |
| version |  | The version of the guardrail |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSBedrockGuardrail)`: Indicates that an AWS account contains the Bedrock guardrail.

- `(:AWSBedrockGuardrail)-[:APPLIED_TO]->(:AWSBedrockAgent)`: Defines the relationship from AWSBedrockGuardrail to AWSBedrockAgent.

### AWSBedrockKnowledgeBase

Representation of an AWS [Bedrock Knowledge Base](https://docs.aws.amazon.com/bedrock/latest/userguide/knowledge-base.html). Knowledge bases enable RAG (Retrieval Augmented Generation) by converting documents from S3 into vector embeddings for semantic search.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The ARN of the knowledge base |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| arn | Yes | The ARN of the knowledge base |
| created_at |  | The timestamp when the knowledge base was created |
| description |  | The description of the knowledge base |
| knowledge_base_configuration_type |  | Type of retrieval configuration used by the knowledge base. |
| knowledge_base_id | Yes | The unique identifier of the knowledge base |
| name |  | The name of the knowledge base |
| region |  | The AWS region where the knowledge base exists |
| role_arn |  | The ARN of the IAM role that the knowledge base uses |
| status |  | The status of the knowledge base (e.g., "CREATING", "ACTIVE", "DELETING") |
| storage_configuration_type |  | Type of vector storage used by the knowledge base. |
| updated_at |  | The timestamp when the knowledge base was last updated |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSBedrockKnowledgeBase)`: Defines the relationship from AWSBedrockKnowledgeBase to AWSAccount.

- `(:AWSBedrockAgent)-[:USES_KNOWLEDGE_BASE]->(:AWSBedrockKnowledgeBase)`: Defines the relationship from AWSBedrockAgent to AWSBedrockKnowledgeBase.

- `(:AWSBedrockKnowledgeBase)-[:SOURCES_DATA_FROM]->(:AWSS3Bucket)`: Defines the relationship from AWSBedrockKnowledgeBase to AWSS3Bucket.

- `(:AWSBedrockKnowledgeBase)-[:USES_EMBEDDING_MODEL]->(:AWSBedrockFoundationModel)`: Defines the relationship from AWSBedrockKnowledgeBase to AWSBedrockFoundationModel.

### AWSBedrockProvisionedModelThroughput

Representation of AWS [Bedrock Provisioned Throughput](https://docs.aws.amazon.com/bedrock/latest/userguide/prov-throughput.html). Provisioned throughput provides reserved capacity for foundation models and custom models, ensuring consistent performance and availability for production workloads.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The ARN of the provisioned throughput |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| arn | Yes | The ARN of the provisioned throughput |
| commitment_duration |  | The commitment duration for the purchase (e.g., "OneMonth", "SixMonths") |
| commitment_expiration_time |  | The timestamp when the commitment expires |
| creation_time |  | The timestamp when the provisioned throughput was created |
| desired_model_arn |  | The desired model ARN (used during updates) |
| desired_model_units |  | The desired number of model units (used during updates) |
| foundation_model_arn |  | The ARN of the foundation model |
| last_modified_time |  | The timestamp when the provisioned throughput was last modified |
| model_arn |  | The ARN of the model (foundation or custom) |
| model_units |  | The number of model units allocated |
| provisioned_model_name |  | The name of the provisioned model throughput |
| region |  | The AWS region where the provisioned throughput exists |
| status |  | The status of the provisioned throughput (e.g., "Creating", "InService", "Updating") |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSBedrockProvisionedModelThroughput)`: Defines the relationship from AWSBedrockProvisionedModelThroughput to AWSAccount.

- `(:AWSBedrockAgent)-[:USES_MODEL]->(:AWSBedrockProvisionedModelThroughput)`: Defines the relationship from AWSBedrockAgent to AWSBedrockProvisionedModelThroughput.
Created when the agent uses a provisioned throughput for model inference.

- `(:AWSBedrockProvisionedModelThroughput)-[:PROVIDES_CAPACITY_FOR]->(:AWSBedrockCustomModel)`: Defines the relationship from AWSBedrockProvisionedModelThroughput to AWSBedrockCustomModel.
This relationship is created when the provisioned throughput is for a custom model.

- `(:AWSBedrockProvisionedModelThroughput)-[:PROVIDES_CAPACITY_FOR]->(:AWSBedrockFoundationModel)`: Defines the relationship from AWSBedrockProvisionedModelThroughput to AWSBedrockFoundationModel.
This relationship is created when the provisioned throughput is for a foundation model.

### AWSCidrBlock

This node label is loaded by more than one sync path:

- An IPv4 [CIDR block used in VPC configuration](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_VpcCidrBlockAssociation.html), associated with a VPC and also labeled `AWSIpv4CidrBlock`.
- An IPv6 [CIDR block used in VPC configuration](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_VpcCidrBlockAssociation.html), associated with a VPC and also labeled `AWSIpv6CidrBlock`.

> **Additional Labels**: Some schema variants may also use `AWSIpv4CidrBlock`, `AWSIpv6CidrBlock`.

> **Additional Label Definitions**:
>
> - `AWSIpv4CidrBlock`: A aws node participating in the shared AWSIpv4CidrBlock graph interface.
> - `AWSIpv6CidrBlock`: A aws node participating in the shared AWSIpv6CidrBlock graph interface.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Unique identifier for this `AWSCidrBlock` node. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| association_id |  | Identifier of the association linked to this `AWSCidrBlock` node. |
| block_state |  | State of the CIDR block association, for example ``associating \| associated \| failing \| failed``. |
| block_state_message |  | Message giving more information about the CIDR block association state. |
| cidr_block |  | IPv4 or IPv6 CIDR range associated with the VPC. |
| vpcid |  | Identifier of the VPC linked to this `AWSCidrBlock` node. |

#### Relationships

- `(:AWSPeeringConnection)-[:ACCEPTER_CIDR]->(:AWSCidrBlock)`

- `(:AWSPeeringConnection)-[:REQUESTER_CIDR]->(:AWSCidrBlock)`

- `(:AWSVpc)-[:BLOCK_ASSOCIATION]->(:AWSCidrBlock)`

### AWSCloudFormationStack

Representation of an AWS [CloudFormation Stack](https://docs.aws.amazon.com/AWSCloudFormation/latest/APIReference/API_Stack.html).

> **Additional Labels**: This node also uses `CloudFormationStack`.

> **Additional Label Definitions**:
>
> - `CloudFormationStack`: Compatibility label for the deprecated `CloudFormationStack` aws node label. Use `AWSCloudFormationStack` instead. Scheduled for removal in v1.0.0.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The unique identifier (ARN) of the CloudFormation Stack |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| arn | Yes | The Amazon Resource Name (ARN) of the CloudFormation Stack |
| creation_time |  | The time at which the stack was created |
| description |  | A user-defined description associated with the stack |
| disable_rollback |  | Whether rollback is disabled |
| last_updated_time |  | The time the stack was last updated |
| parent_id |  | For nested stacks, the stack ID of the parent |
| region |  | The AWS region where the stack exists |
| role_arn |  | The ARN of the IAM role used by CloudFormation |
| root_id |  | For nested stacks, the stack ID of the root stack |
| stack_name |  | The name of the stack |
| stack_status |  | Current status of the stack (e.g., CREATE_COMPLETE) |
| stack_status_reason |  | Success/failure message associated with the stack status |
| tags |  | A JSON string of tags associated with the stack |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSCloudFormationStack)`

- `(:AWSCloudFormationStack)-[:HAS_EXECUTION_ROLE]->(:AWSRole)`

- `(:AWSPrincipal)-[:CAN_EXEC]->(:AWSCloudFormationStack)`: `AWSPrincipal` receives evaluated `CAN_EXEC` access to `AWSCloudFormationStack` from AWS IAM policies.
  - Evaluated permissions: `cloudformation:UpdateStack`
  - Properties:

    | Field | Description |
    |-------|-------------|
    | condition_keys | IAM condition context keys used by the permission. |
    | conditions | IAM conditions that restrict this permission. |
    | has_condition | Whether an IAM condition restricts this permission. |

### AWSCloudFrontDistribution

Representation of an AWS [CloudFront Distribution](https://docs.aws.amazon.com/cloudfront/latest/APIReference/API_DistributionSummary.html).

CloudFront is AWS's global content delivery network (CDN) service. CloudFront distributions are the primary resource that defines how content is cached and delivered to end users.

> **Additional Labels**: This node also uses `CloudFrontDistribution`.

> **Additional Label Definitions**:
>
> - `CloudFrontDistribution`: Compatibility label for the deprecated `CloudFrontDistribution` aws node label. Use `AWSCloudFrontDistribution` instead. Scheduled for removal in v1.0.0.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The ARN of the CloudFront distribution |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| acm_certificate_arn |  | The ARN of the ACM certificate for HTTPS |
| aliases |  | List of CNAMEs (alternate domain names) for the distribution |
| arn | Yes | The ARN of the CloudFront distribution |
| cloudfront_default_certificate |  | Whether the default CloudFront certificate is used |
| comment |  | Optional comment describing the distribution |
| distribution_id | Yes | The unique identifier for the distribution (e.g., E1A2B3C4D5E6F7) |
| domain_name |  | The CloudFront domain name (e.g., d1234567890abc.cloudfront.net) |
| enabled |  | Whether the distribution is enabled |
| etag |  | The entity tag for the distribution configuration |
| geo_restriction_locations |  | List of country codes for geo restrictions |
| geo_restriction_type |  | The type of geo restriction (none, whitelist, blacklist) |
| http_version |  | The HTTP version supported (e.g., http2, http2and3) |
| iam_certificate_id |  | The IAM certificate ID if using IAM certificates |
| is_ipv6_enabled |  | Whether IPv6 is enabled for the distribution |
| last_modified_time |  | Timestamp when the CloudFront distribution configuration was last modified. |
| minimum_protocol_version |  | The minimum TLS protocol version (e.g., TLSv1.2_2021) |
| price_class |  | The price class for the distribution (e.g., PriceClass_100, PriceClass_All) |
| ssl_support_method |  | The SSL/TLS support method (e.g., sni-only) |
| staging |  | Whether this is a staging distribution |
| status |  | The current status of the distribution (e.g., Deployed, InProgress) |
| viewer_protocol_policy |  | The viewer protocol policy from the default cache behavior |
| web_acl_id |  | The AWS WAF Web ACL ID associated with the distribution |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSCloudFrontDistribution)`: Indicates that an AWS account contains the CloudFront distribution.

- `(:AWSCloudFrontDistribution)-[:SERVES_FROM]->(:AWSS3Bucket)`: Indicates that the CloudFront distribution serves content from an S3 bucket origin.

- `(:AWSCloudFrontDistribution)-[:USES_CERTIFICATE]->(:AWSACMCertificate)`: Indicates that the CloudFront distribution uses an ACM certificate for HTTPS.

- `(:AWSCloudFrontDistribution)-[:USES_LAMBDA_EDGE]->(:AWSLambda)`: Indicates that the CloudFront distribution uses a Lambda function for Lambda@Edge processing.

- `(:DNSRecord)-[:DNS_POINTS_TO]->(:AWSCloudFrontDistribution)`: generated by analysis job `Ontology - DNSRecord to AWSCloudFrontDistribution linking`.

### AWSCloudTrailTrail

Representation of an AWS [CloudTrail Trail](https://docs.aws.amazon.com/awscloudtrail/latest/APIReference/API_Trail.html).

> **Additional Labels**: This node also uses `CloudTrailTrail`.

> **Additional Label Definitions**:
>
> - `CloudTrailTrail`: Compatibility label for the deprecated `CloudTrailTrail` aws node label. Use `AWSCloudTrailTrail` instead. Scheduled for removal in v1.0.0.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The ARN of the trail (same as arn) |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| advanced_event_selectors |  | JSON array of advanced event selectors configured for the AWSCloudTrailTrail. |
| arn |  | The ARN of the trail |
| cloudwatch_logs_log_group_arn |  | The ARN identifier representing the log group where the AWSCloudTrailTrail delivers logs. |
| cloudwatch_logs_role_arn |  | The role ARN that the AWSCloudTrailTrail's CloudWatch Logs endpoint assumes. |
| event_selectors |  | JSON array of event selectors configured for the AWSCloudTrailTrail. |
| has_custom_event_selectors |  | Indicates if the AWSCloudTrailTrail has custom event selectors. |
| has_insight_selectors |  | Indicates if the AWSCloudTrailTrail has insight types specified. |
| home_region |  | The Region where the AWSCloudTrailTrail was created. |
| include_global_service_events |  | Indicates if the AWSCloudTrailTrail includes AWS API calls from global services. |
| is_multi_region_trail |  | Indicates if the AWSCloudTrailTrail exists in one or all Regions. |
| is_organization_trail |  | Indicates if the AWSCloudTrailTrail is an organization trail. |
| kms_key_id |  | The AWS KMS key ID that encrypts the AWSCloudTrailTrail's delivered logs. |
| log_file_validation_enabled |  | Indicates if log file validation is enabled for the AWSCloudTrailTrail. |
| name |  | The name of the AWSCloudTrailTrail. |
| region |  | The AWS region |
| s3_bucket_name |  | The Amazon S3 bucket name where the AWSCloudTrailTrail delivers files. |
| s3_key_prefix |  | The S3 key prefix used after the bucket name for the AWSCloudTrailTrail's log files. |
| sns_topic_arn |  | The ARN of the SNS topic used by the AWSCloudTrailTrail for delivery notifications. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSCloudTrailTrail)`

- `(:AWSCloudTrailTrail)-[:LOGS_TO]->(:AWSS3Bucket)`

- `(:AWSCloudTrailTrail)-[:SENDS_LOGS_TO_CLOUDWATCH]->(:AWSCloudWatchLogGroup)`

### AWSCloudWatchLogGroup

Representation of an AWS [CloudWatch Log Group](https://docs.aws.amazon.com/AmazonCloudWatchLogs/latest/APIReference/API_LogGroup.html)

> **Additional Labels**: This node also uses `CloudWatchLogGroup`.

> **Additional Label Definitions**:
>
> - `CloudWatchLogGroup`: Compatibility label for the deprecated `CloudWatchLogGroup` aws node label. Use `AWSCloudWatchLogGroup` instead. Scheduled for removal in v1.0.0.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The ARN of the log group |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| arn | Yes | The Amazon Resource Name (ARN) of the log group |
| creation_time |  | The creation time of the log group, expressed as the number of milliseconds after Jan 1, 1970 00:00:00 UTC |
| data_protection_status |  | Displays whether this log group has a protection policy, or whether it had one in the past |
| inherited_properties |  | Displays all the properties that this log group has inherited from account-level settings |
| kms_key_id |  | The Amazon Resource Name (ARN) of the AWS KMS key to use when encrypting log data |
| log_group_arn |  | The Amazon Resource Name (ARN) of the log group |
| log_group_class |  | This specifies the log group class for this log group |
| log_group_name |  | The name of the log group |
| metric_filter_count |  | The number of metric filters |
| retention_in_days |  | The number of days to retain the log events in the specified log group |
| stored_bytes |  | The number of bytes stored |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSCloudWatchLogGroup)`

- `(:AWSCloudTrailTrail)-[:SENDS_LOGS_TO_CLOUDWATCH]->(:AWSCloudWatchLogGroup)`

- `(:AWSCloudWatchLogMetricFilter)-[:METRIC_FILTER_OF]->(:AWSCloudWatchLogGroup)`

### AWSCloudWatchLogMetricFilter

Representation of an AWS [CloudWatch Log Metric Filter](https://docs.aws.amazon.com/AmazonCloudWatchLogs/latest/APIReference/API_DescribeMetricFilters.html)

> **Additional Labels**: This node also uses `CloudWatchLogMetricFilter`.

> **Additional Label Definitions**:
>
> - `CloudWatchLogMetricFilter`: Compatibility label for the deprecated `CloudWatchLogMetricFilter` aws node label. Use `AWSCloudWatchLogMetricFilter` instead. Scheduled for removal in v1.0.0.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Ensures that the id field is a unique combination of logGroupName and filterName |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| arn | Yes | The name of the metric filter. CloudWatch exposes no ARN for metric filters, so the filter name is stored here for query convenience |
| filter_name |  | The name of the filter pattern used to extract metric data from log events |
| filter_pattern |  | The pattern used to extract metric data from CloudWatch log events |
| log_group_name |  | The name of the log group to which this metric filter is applied |
| metric_name |  | The name of the metric emitted by this filter |
| metric_namespace |  | The namespace of the metric emitted by this filter |
| metric_value |  | The value to publish to the CloudWatch metric when a log event matches the filter pattern |
| region |  | The region of the CloudWatch Log Metric Filter |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSCloudWatchLogMetricFilter)`

- `(:AWSCloudWatchLogMetricFilter)-[:METRIC_FILTER_OF]->(:AWSCloudWatchLogGroup)`

### AWSCloudWatchMetricAlarm

Representation of an AWS [CloudWatch Metric Alarm](https://docs.aws.amazon.com/AmazonCloudWatch/latest/APIReference/API_DescribeAlarms.html)

> **Additional Labels**: This node also uses `CloudWatchMetricAlarm`.

> **Additional Label Definitions**:
>
> - `CloudWatchMetricAlarm`: Compatibility label for the deprecated `CloudWatchMetricAlarm` aws node label. Use `AWSCloudWatchMetricAlarm` instead. Scheduled for removal in v1.0.0.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The ARN of the CloudWatch Metric Alarm |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| actions_enabled |  | Indicates whether actions should be executed during any changes to the alarm state |
| alarm_description |  | The description of the alarm |
| alarm_name |  | The name of the alarm |
| arn | Yes | The ARN of the CloudWatch Metric Alarm |
| comparison_operator |  | The arithmetic operation to use when comparing the specified statistic and threshold. The specified statistic value is used as the first operand |
| region |  | The region of the CloudWatch Metric Alarm |
| state_reason |  | An explanation for the alarm state, in text format |
| state_value |  | The state value for the alarm |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSCloudWatchMetricAlarm)`

### AWSCodeBuildProject

Representation of an AWS [CodeBuild Project](https://docs.aws.amazon.com/codebuild/latest/APIReference/API_Project.html)

> **Ontology Mapping**: This node uses the ontology label [`CICDPipeline`](#ontology-cicdpipeline).

> **Additional Labels**: This node also uses `CodeBuildProject`.

> **Additional Label Definitions**:
>
> - `CodeBuildProject`: Compatibility label for the deprecated `CodeBuildProject` aws node label. Use `AWSCodeBuildProject` instead. Scheduled for removal in v1.0.0.

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The ARN of the CodeBuild Project |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| arn | Yes | The Amazon Resource Name (ARN) of the CodeBuild Project |
| created |  | The creation time of the CodeBuild Project |
| environment_variables |  | A list of environment variables used in the build environment. Each variable is represented as a string in the format `<NAME>=<VALUE>`. Variables of type `PLAINTEXT` retain their values (e.g., `ENV=prod`), while variables of type `PARAMETER_STORE`, `SECRETS_MANAGER`, etc., have values redacted as `<REDACTED>` (e.g., `SECRET_TOKEN=<REDACTED>`) |
| name | Yes | The CodeBuild Project name |
| region |  | The region of the codebuild project |
| source_location |  | Information about the location of the source code to be built |
| source_type |  | The type of repository that contains the source code to be built |
| *_ont_name* | Yes | Normalized field sourced from `name`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |
| *_ont_type* | Yes | Property generated by the ontology mapping. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSCodeBuildProject)`

### AWSCognitoIdentityPool

Representation of an AWS [Cognito Identity Pool](https://docs.aws.amazon.com/cognitoidentity/latest/APIReference/API_ListIdentityPools.html)

> **Additional Labels**: This node also uses `CognitoIdentityPool`.

> **Additional Label Definitions**:
>
> - `CognitoIdentityPool`: Compatibility label for the deprecated `CognitoIdentityPool` aws node label. Use `AWSCognitoIdentityPool` instead. Scheduled for removal in v1.0.0.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The id of Cognito Identity Pool |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| arn | Yes | The id of the Cognito Identity Pool. The API returns no ARN for identity pools, so the id is stored here for query convenience |
| region |  | The region of the Cognito Identity Pool |
| roles |  | list of aws roles associated with Cognito Identity Pool |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSCognitoIdentityPool)`

- `(:AWSCognitoIdentityPool)-[:ASSOCIATED_WITH]->(:AWSRole)`

### AWSCognitoUserPool

Representation of an AWS [Cognito User Pool](https://docs.aws.amazon.com/cognito-user-identity-pools/latest/APIReference/API_ListUserPools.html)

> **Additional Labels**: This node also uses `CognitoUserPool`.

> **Additional Label Definitions**:
>
> - `CognitoUserPool`: Compatibility label for the deprecated `CognitoUserPool` aws node label. Use `AWSCognitoUserPool` instead. Scheduled for removal in v1.0.0.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The id of Cognito User Pool |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| arn | Yes | The id of the Cognito User Pool. ListUserPools returns no ARN, so the id is stored here for query convenience |
| name |  | Name of Cognito User Pool |
| region |  | The region of the Cognito User Pool |
| status |  | Status of User Pool |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSCognitoUserPool)`

### AWSConfigDeliveryChannel

Representation of an AWS [Config Delivery Channel](https://docs.aws.amazon.com/config/latest/APIReference/API_DeliveryChannel.html)

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | A combination of name:account\_id:region |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| config_snapshot_delivery_properties_delivery_frequency |  | The frequency with which AWS Config delivers configuration snapshots. |
| name |  | The name of the delivery channel. |
| region |  | The region of the delivery channel. |
| s3_bucket_name |  | The name of the Amazon S3 bucket to which AWS Config delivers configuration snapshots and configuration history files. |
| s3_key_prefix |  | The prefix for the specified Amazon S3 bucket. |
| s3_kms_key_arn |  | The Amazon Resource Name (ARN) of the AWS Key Management Service (KMS) customer managed key (CMK) used to encrypt objects delivered by AWS Config. Must belong to the same Region as the destination S3 bucket. |
| sns_topic_arn |  | The Amazon Resource Name (ARN) of the Amazon SNS topic to which AWS Config sends notifications about configuration changes. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSConfigDeliveryChannel)`

### AWSConfigRule

Representation of an AWS [Config Rule](https://docs.aws.amazon.com/config/latest/APIReference/API_DeliveryChannel.html)

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The ARN of the config rule. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| arn |  | The ARN of the config rule. |
| created_by |  | Service principal name of the service that created the rule. |
| description |  | The description that you provide for the AWS Config rule. |
| input_parameters |  | A string, in JSON format, that is passed to the AWS Config rule Lambda function. |
| maximum_execution_frequency |  | The maximum frequency with which AWS Config runs evaluations for a rule. |
| name |  | The name of the delivery channel. |
| region |  | The region of the delivery channel. |
| rule_id |  | The ID of the AWS Config rule. |
| scope_compliance_resource_types |  | The resource types of only those AWS resources that you want to trigger an evaluation for the rule. You can only specify one type if you also specify a resource ID for ComplianceResourceId. |
| scope_tag_compliance_resource_id |  | The resource types of only those AWS resources that you want to trigger an evaluation for the rule. You can only specify one type if you also specify a resource ID for ComplianceResourceId. |
| scope_tag_key |  | The tag key that is applied to only those AWS resources that you want to trigger an evaluation for the rule. |
| scope_tag_value |  | The tag value applied to only those AWS resources that you want to trigger an evaluation for the rule. If you specify a value for TagValue, you must also specify a value for TagKey. |
| source_details |  | Provides the source and type of the event that causes AWS Config to evaluate your AWS resources. |
| source_identifier |  | For AWS Config managed rules, a predefined identifier from a list. For example, IAM\_PASSWORD\_POLICY is a managed rule. |
| source_owner |  | Indicates whether AWS or the customer owns and manages the AWS Config rule. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSConfigRule)`

### AWSConfigurationRecorder

Representation of an AWS [Config Configuration Recorder](https://docs.aws.amazon.com/config/latest/APIReference/API_ConfigurationRecorder.html)

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | A combination of name:account\_id:region |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| name |  | The name of the recorder. |
| recording_group_all_supported |  | Specifies whether AWS Config records configuration changes for every supported type of regional resource. |
| recording_group_include_global_resource_types |  | Specifies whether AWS Config includes all supported types of global resources (for example, IAM resources) with the resources that it records. |
| recording_group_resource_types |  | A comma-separated list that specifies the types of AWS resources for which AWS Config records configuration changes (for example, AWS::EC2::Instance or AWS::CloudTrail::Trail). |
| region |  | The region of the configuration recorder. |
| role_arn |  | Amazon Resource Name (ARN) of the IAM role used to describe the AWS resources associated with the account. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSConfigurationRecorder)`

### AWSDBSubnetGroup

Representation of an RDS [DB Subnet Group](https://docs.aws.amazon.com/AmazonRDS/latest/APIReference/API_DBSubnetGroup.html).  For more information on how RDS instances interact with these, please see [this article](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_VPC.WorkingWithRDSInstanceinaVPC.html).

> **Additional Labels**: This node also uses `DBSubnetGroup`.

> **Additional Label Definitions**:
>
> - `DBSubnetGroup`: Compatibility label for the deprecated `DBSubnetGroup` aws node label. Use `AWSDBSubnetGroup` instead. Scheduled for removal in v1.0.0.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The ARN of the AWSDBSubnetGroup |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| description |  | Description of the DB Subnet Group |
| name |  | The name of AWSDBSubnetGroup |
| region |  | The AWS region where the DB Subnet Group is located. |
| status |  | The status of the group |
| vpc_id |  | The ID of the VPC (Virtual Private Cloud) that this DB Subnet Group is associated with. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSDBSubnetGroup)`

- `(:AWSDBSubnetGroup)-[:RESOURCE]->(:AWSEC2Subnet)`

- `(:AWSDBSubnetGroup)-[:TAGGED]->(:AWSTag)`: `AWSDBSubnetGroup` is tagged with an `AWSTag` discovered by the AWS Resource Groups Tagging API.

- `(:AWSRDSInstance)-[:MEMBER_OF_DB_SUBNET_GROUP]->(:AWSDBSubnetGroup)`

### AWSDNSRecord

Representation of an AWS DNS [ResourceRecordSet](https://docs.aws.amazon.com/Route53/latest/APIReference/API_ResourceRecordSet.html).

> **Ontology Mapping**: This node uses the ontology label [`DNSRecord`](#ontology-dnsrecord).

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The zone id, the record `name` and the record `type` concatenated together. Not affected by the `value` normalization described below. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| name | Yes | Name of this `AWSDNSRecord` node. |
| type |  | Type of this `AWSDNSRecord` node. |
| value |  | If it is an A or AAAA record, this is the IP address the DNSRecord resolves to. For CNAME or ALIAS records, this is the target hostname or AWS resource name, lowercased and with the trailing root dot removed. Alias targets pointing at a load balancer additionally have Route53's `dualstack.` prefix removed, since the ELB APIs report the same load balancer without it. Everywhere else a leading `dualstack.` is kept, because on an ordinary CNAME or an alias to another record in the same hosted zone it is part of a genuinely different hostname. If it is an NS record, the `name` is used here. |
| *_ont_name* | Yes | Normalized field sourced from `name`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |
| *_ont_type* | Yes | Normalized field sourced from `type`. |
| *_ont_value* | Yes | Normalized field sourced from `value`. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSDNSRecord)`

- `(:AWSDNSRecord)-[:DNS_POINTS_TO]->(:AWSDNSRecord)`

- `(:AWSDNSRecord)-[:DNS_POINTS_TO]->(:AWSEC2Instance)`

- `(:AWSDNSRecord)-[:DNS_POINTS_TO]->(:AWSESDomain)`

- `(:AWSDNSRecord)-[:DNS_POINTS_TO]->(:AWSElasticIPAddress)`

- `(:AWSDNSRecord)-[:DNS_POINTS_TO]->(:AWSLoadBalancer)`

- `(:AWSDNSRecord)-[:DNS_POINTS_TO]->(:AWSLoadBalancerV2)`

- `(:AWSDNSRecord)-[:DNS_POINTS_TO]->(:AWSNameServer)`

- `(:AWSDNSRecord)-[:DNS_POINTS_TO]->(:Ip)`

- `(:AWSDNSRecord)-[:MEMBER_OF_DNS_ZONE]->(:AWSDNSZone)`

### AWSDNSZone

Representation of an AWS DNS [HostedZone](https://docs.aws.amazon.com/Route53/latest/APIReference/API_HostedZone.html).

> **Ontology Mapping**: This node uses the ontology label [`DNSZone`](#ontology-dnszone).

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Unique identifier for this `AWSDNSZone` node. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| comment |  | Comment attached to the Route 53 hosted zone. |
| name | Yes | Name of this `AWSDNSZone` node. |
| privatezone |  | Whether the hosted zone is private and associated with one or more VPCs. |
| zoneid |  | Identifier of the zoneid linked to this `AWSDNSZone` node. |
| *_ont_name* | Yes | Normalized field sourced from `name`. |
| *_ont_public* | Yes | Normalized field sourced from `privatezone`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSDNSZone)`

- `(:AWSDNSRecord)-[:MEMBER_OF_DNS_ZONE]->(:AWSDNSZone)`

- `(:AWSDNSZone)-[:NAMESERVER]->(:AWSNameServer)`

- `(:AWSDNSZone)-[:SUBZONE]->(:AWSDNSZone)`

### AWSDynamoDBArchivalSummary

Representation of DynamoDB [Archival Summary](https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_ArchivalSummary.html) for archived tables.

> **Additional Labels**: This node also uses `DynamoDBArchivalSummary`.

> **Additional Label Definitions**:
>
> - `DynamoDBArchivalSummary`: Compatibility label for the deprecated `DynamoDBArchivalSummary` aws node label. Use `AWSDynamoDBArchivalSummary` instead. Scheduled for removal in v1.0.0.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Unique identifier (table ARN + "/archival") |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| archival_backup_arn |  | The ARN of the backup created when the table was archived |
| archival_date_time |  | The date and time when table archival was initiated |
| archival_reason |  | The reason for archiving the table |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSDynamoDBArchivalSummary)`

- `(:AWSDynamoDBArchivalSummary)-[:ARCHIVED_TO_BACKUP]->(:AWSDynamoDBBackup)`

- `(:AWSDynamoDBTable)-[:HAS_ARCHIVAL]->(:AWSDynamoDBArchivalSummary)`

### AWSDynamoDBBackup

Representation of a DynamoDB [Backup](https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_BackupDetails.html). Currently a stub entity referenced by archival and restore summaries.

> **Additional Labels**: This node also uses `DynamoDBBackup`.

> **Additional Label Definitions**:
>
> - `DynamoDBBackup`: Compatibility label for the deprecated `DynamoDBBackup` aws node label. Use `AWSDynamoDBBackup` instead. Scheduled for removal in v1.0.0.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The ARN of the backup |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| arn |  | The ARN of the backup |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSDynamoDBBackup)`

- `(:AWSDynamoDBArchivalSummary)-[:ARCHIVED_TO_BACKUP]->(:AWSDynamoDBBackup)`

- `(:AWSDynamoDBRestoreSummary)-[:RESTORED_FROM_BACKUP]->(:AWSDynamoDBBackup)`

### AWSDynamoDBBillingModeSummary

Representation of DynamoDB [Billing Mode Summary](https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_BillingModeSummary.html).

> **Additional Labels**: This node also uses `DynamoDBBillingModeSummary`.

> **Additional Label Definitions**:
>
> - `DynamoDBBillingModeSummary`: Compatibility label for the deprecated `DynamoDBBillingModeSummary` aws node label. Use `AWSDynamoDBBillingModeSummary` instead. Scheduled for removal in v1.0.0.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Unique identifier (table ARN + "/billing") |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| billing_mode |  | The billing mode (PROVISIONED or PAY_PER_REQUEST) |
| last_update_to_pay_per_request_date_time |  | When the table was last switched to PAY_PER_REQUEST mode |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSDynamoDBBillingModeSummary)`

- `(:AWSDynamoDBTable)-[:HAS_BILLING]->(:AWSDynamoDBBillingModeSummary)`

### AWSDynamoDBGlobalSecondaryIndex

Representation of a DynamoDB [Global Secondary Index](https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_GlobalSecondaryIndexDescription.html).

> **Additional Labels**: This node also uses `DynamoDBGlobalSecondaryIndex`.

> **Additional Label Definitions**:
>
> - `DynamoDBGlobalSecondaryIndex`: Compatibility label for the deprecated `DynamoDBGlobalSecondaryIndex` aws node label. Use `AWSDynamoDBGlobalSecondaryIndex` instead. Scheduled for removal in v1.0.0.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The ARN of the global secondary index |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| arn |  | The Amazon Resource Name (ARN) of the global secondary index |
| name |  | The name of the global secondary index |
| provisioned_throughput_read_capacity_units |  | The maximum number of read capacity units for the global secondary index |
| provisioned_throughput_write_capacity_units |  | The maximum number of write capacity units for the global secondary index |
| region |  | The AWS region |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSDynamoDBGlobalSecondaryIndex)`

- `(:AWSDynamoDBTable)-[:GLOBAL_SECONDARY_INDEX]->(:AWSDynamoDBGlobalSecondaryIndex)`

### AWSDynamoDBRestoreSummary

Representation of DynamoDB [Restore Summary](https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_RestoreSummary.html) for restored tables.

> **Additional Labels**: This node also uses `DynamoDBRestoreSummary`.

> **Additional Label Definitions**:
>
> - `DynamoDBRestoreSummary`: Compatibility label for the deprecated `DynamoDBRestoreSummary` aws node label. Use `AWSDynamoDBRestoreSummary` instead. Scheduled for removal in v1.0.0.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Unique identifier (table ARN + "/restore") |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| restore_date_time |  | Point in time or source backup time for the restore |
| restore_in_progress |  | Indicates whether a restore is currently in progress |
| source_backup_arn |  | The ARN of the backup from which the table was restored |
| source_table_arn |  | The ARN of the source table from which the table was restored |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSDynamoDBRestoreSummary)`

- `(:AWSDynamoDBRestoreSummary)-[:RESTORED_FROM_BACKUP]->(:AWSDynamoDBBackup)`

- `(:AWSDynamoDBRestoreSummary)-[:RESTORED_FROM_TABLE]->(:AWSDynamoDBTable)`

- `(:AWSDynamoDBTable)-[:HAS_RESTORE]->(:AWSDynamoDBRestoreSummary)`

### AWSDynamoDBSSEDescription

Representation of DynamoDB [Server-Side Encryption description](https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_SSEDescription.html).

> **Additional Labels**: This node also uses `DynamoDBSSEDescription`.

> **Additional Label Definitions**:
>
> - `DynamoDBSSEDescription`: Compatibility label for the deprecated `DynamoDBSSEDescription` aws node label. Use `AWSDynamoDBSSEDescription` instead. Scheduled for removal in v1.0.0.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Unique identifier (table ARN + "/sse") |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| kms_master_key_arn |  | The ARN of the KMS key used for encryption (if SSE type is KMS) |
| sse_status | Yes | The current state of SSE (e.g., ENABLED, DISABLED) |
| sse_type |  | The server-side encryption type (AES256 or KMS) |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSDynamoDBSSEDescription)`

- `(:AWSDynamoDBSSEDescription)-[:USES_KMS_KEY]->(:AWSKMSKey)`: Relationship to AWSKMSKey. Only created when SSEType is "KMS" and KMSMasterKeyArn exists.

- `(:AWSDynamoDBTable)-[:HAS_SSE]->(:AWSDynamoDBSSEDescription)`

### AWSDynamoDBStream

Representation of a DynamoDB [Stream](https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_StreamSpecification.html).

> **Additional Labels**: This node also uses `DynamoDBStream`.

> **Additional Label Definitions**:
>
> - `DynamoDBStream`: Compatibility label for the deprecated `DynamoDBStream` aws node label. Use `AWSDynamoDBStream` instead. Scheduled for removal in v1.0.0.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The ARN of the stream |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| arn |  | The ARN of the stream |
| stream_enabled |  | Whether the stream is enabled |
| stream_label |  | A timestamp used as the stream label |
| stream_view_type |  | What information is written to the stream (KEYS_ONLY, NEW_IMAGE, OLD_IMAGE, NEW_AND_OLD_IMAGES) |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSDynamoDBStream)`

- `(:AWSDynamoDBTable)-[:LATEST_STREAM]->(:AWSDynamoDBStream)`

### AWSDynamoDBTable

Representation of an AWS [AWSDynamoDBTable](https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_TableDescription.html).

> **Ontology Mapping**: This node uses the ontology label [`Database`](#ontology-database).

> **Additional Labels**: This node also uses `DynamoDBTable`.

> **Additional Label Definitions**:
>
> - `DynamoDBTable`: Compatibility label for the deprecated `DynamoDBTable` aws node label. Use `AWSDynamoDBTable` instead. Scheduled for removal in v1.0.0.

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Unique identifier for this `AWSDynamoDBTable` node. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| arn | Yes | Amazon Resource Name (ARN) of this `AWSDynamoDBTable` node. |
| creation_date_time |  | Timestamp when the table was created. |
| name |  | Name of this `AWSDynamoDBTable` node. |
| provisioned_throughput_read_capacity_units |  | Provisioned read capacity units for the table. |
| provisioned_throughput_write_capacity_units |  | Provisioned write capacity units for the table. |
| region |  | AWS Region containing this `AWSDynamoDBTable` node. |
| rows |  | Approximate number of items stored in the table. |
| size |  | Total table size in bytes. |
| table_status |  | Current operational status of the table. |
| *_ont_location* | Yes | Normalized field sourced from `region`. |
| *_ont_name* | Yes | Normalized field sourced from `name`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |
| *_ont_type* | Yes | Property generated by the ontology mapping. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSDynamoDBTable)`

- `(:AWSDynamoDBRestoreSummary)-[:RESTORED_FROM_TABLE]->(:AWSDynamoDBTable)`

- `(:AWSDynamoDBTable)-[:GLOBAL_SECONDARY_INDEX]->(:AWSDynamoDBGlobalSecondaryIndex)`

- `(:AWSDynamoDBTable)-[:HAS_ARCHIVAL]->(:AWSDynamoDBArchivalSummary)`

- `(:AWSDynamoDBTable)-[:HAS_BILLING]->(:AWSDynamoDBBillingModeSummary)`

- `(:AWSDynamoDBTable)-[:HAS_RESTORE]->(:AWSDynamoDBRestoreSummary)`

- `(:AWSDynamoDBTable)-[:HAS_SSE]->(:AWSDynamoDBSSEDescription)`

- `(:AWSDynamoDBTable)-[:LATEST_STREAM]->(:AWSDynamoDBStream)`

- `(:AWSDynamoDBTable)-[:TAGGED]->(:AWSTag)`: `AWSDynamoDBTable` is tagged with an `AWSTag` discovered by the AWS Resource Groups Tagging API.

- `(:AWSPrincipal)-[:CAN_QUERY]->(:AWSDynamoDBTable)`: `AWSPrincipal` receives evaluated `CAN_QUERY` access to `AWSDynamoDBTable` from AWS IAM policies.
  - Evaluated permissions: `dynamodb:BatchGetItem`, `dynamodb:GetItem`, `dynamodb:GetRecords`, `dynamodb:Query`, `dynamodb:Scan`
  - Properties:

    | Field | Description |
    |-------|-------------|
    | condition_keys | IAM condition context keys used by the permission. |
    | conditions | IAM conditions that restrict this permission. |
    | has_condition | Whether an IAM condition restricts this permission. |

- `(:AWSPrincipal)-[:CAN_WRITE]->(:AWSDynamoDBTable)`: `AWSPrincipal` receives evaluated `CAN_WRITE` access to `AWSDynamoDBTable` from AWS IAM policies.
  - Evaluated permissions: `dynamodb:BatchWriteItem`, `dynamodb:DeleteItem`, `dynamodb:PutItem`, `dynamodb:UpdateItem`
  - Properties:

    | Field | Description |
    |-------|-------------|
    | condition_keys | IAM condition context keys used by the permission. |
    | conditions | IAM conditions that restrict this permission. |
    | has_condition | Whether an IAM condition restricts this permission. |

### AWSEBSSnapshot

Representation of an AWS [EBS Snapshot](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/EBSSnapshots.html).

> **Ontology Mapping**: This node uses the ontology label [`Snapshot`](#ontology-snapshot).

> **Additional Labels**: This node also uses `EBSSnapshot`.

> **Additional Label Definitions**:
>
> - `EBSSnapshot`: Compatibility label for the deprecated `EBSSnapshot` aws node label. Use `AWSEBSSnapshot` instead. Scheduled for removal in v1.0.0.

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The ID of the EBS Snapshot. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| dataencryptionkeyid |  | The data encryption key identifier for the snapshot. |
| description |  | The description of the snapshot. |
| encrypted |  | Indicates whether the snapshot is encrypted. |
| ispublic |  | Whether this `AWSEBSSnapshot` node is publicly accessible. |
| kmskeyid |  | The Amazon Resource Name (ARN) of the AWS Key Management Service (AWS KMS) customer master key (CMK) that was used to protect the volume encryption key for the parent volume. |
| outpostarn |  | The ARN of the AWS Outpost on which the snapshot is stored. |
| ownerid |  | Identifier of the owner linked to this `AWSEBSSnapshot` node. |
| progress |  | The progress of the snapshot, as a percentage. |
| region |  | The region of the snapshot. |
| snapshotid | Yes | The snapshot ID. |
| starttime |  | The time stamp when the snapshot was initiated. |
| state |  | The snapshot state. |
| statemessage |  | Encrypted Amazon EBS snapshots are copied asynchronously. If a snapshot copy operation fails (for example, if the proper AWS Key Management Service (AWS KMS) permissions are not obtained) this field displays error state details to help you diagnose why the error occurred. This parameter is only returned by DescribeSnapshots . |
| volumeid |  | The volume ID. |
| volumesize |  | The size of the volume, in GiB. |
| *_ont_created_at* | Yes | Normalized field sourced from `starttime`. |
| *_ont_encrypted* | Yes | Normalized field sourced from `encrypted`. |
| *_ont_name* | Yes | Normalized field sourced from `id`. |
| *_ont_public* | Yes | Normalized field sourced from `ispublic`. |
| *_ont_region* | Yes | Normalized field sourced from `region`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |
| *_ont_source_id* | Yes | Normalized field sourced from `volumeid`. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSEBSSnapshot)`

- `(:AWSEBSSnapshot)-[:CREATED_FROM]->(:AWSEBSVolume)`

### AWSEBSVolume

Representation of an AWS [EBS Volume](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ebs-volumes.html).

> **Ontology Mapping**: This node uses the ontology label [`BlockStorage`](#ontology-blockstorage).

> **Additional Labels**: This node also uses `EBSVolume`.

> **Additional Label Definitions**:
>
> - `EBSVolume`: Compatibility label for the deprecated `EBSVolume` aws node label. Use `AWSEBSVolume` instead. Scheduled for removal in v1.0.0.

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The ID of the EBS Volume (same as volumeid) |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| arn | Yes | The Amazon Resource Name (ARN) of the volume |
| availabilityzone |  | The Availability Zone for the volume. |
| createtime |  | The time stamp when volume creation was initiated. |
| deleteontermination |  | Indicates whether the volume is deleted on instance termination. |
| encrypted |  | Indicates whether the volume is encrypted. |
| fastrestored |  | Indicates whether the volume was created using fast snapshot restore. |
| iops |  | The number of I/O operations per second (IOPS). |
| kmskeyid |  | The Amazon Resource Name (ARN) of the AWS Key Management Service (AWS KMS) customer master key (CMK) that was used to protect the volume encryption key for the volume. |
| multiattachenabled |  | Indicates whether Amazon EBS Multi-Attach is enabled. |
| outpostarn |  | The Amazon Resource Name (ARN) of the Outpost. |
| region |  | The region of the volume. |
| size |  | The size of the volume, in GiBs. |
| snapshotid |  | The snapshot ID. |
| state |  | The volume state. |
| type |  | The volume type. |
| volumeid | Yes | The ID of the EBS Volume |
| *_ont_encrypted* | Yes | Normalized field sourced from `encrypted`. |
| *_ont_name* | Yes | Normalized field sourced from `id`. |
| *_ont_region* | Yes | Normalized field sourced from `region`. |
| *_ont_size_gb* | Yes | Normalized field sourced from `size`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |
| *_ont_state* | Yes | Normalized field sourced from `state`. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSEBSVolume)`

- `(:AWSEBSSnapshot)-[:CREATED_FROM]->(:AWSEBSVolume)`

- `(:AWSEBSVolume)-[:ATTACHED_TO]->(:AWSEC2Instance)`

- `(:AWSEBSVolume)-[:TAGGED]->(:AWSTag)`: `AWSEBSVolume` is tagged with an `AWSTag` discovered by the AWS Resource Groups Tagging API.

### AWSEC2Image

Representation of an AWS [EC2 Images (AMIs)](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/AMIs.html).

> **Additional Labels**: This node also uses `EC2Image`.

> **Additional Label Definitions**:
>
> - `EC2Image`: Compatibility label for the deprecated `EC2Image` aws node label. Use `AWSEC2Image` instead. Scheduled for removal in v1.0.0.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The ID of the AMI. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| architecture |  | The architecture of the image. |
| bootmode |  | The boot mode of the image. |
| creationdate |  | The date and time the image was created. |
| description |  | The description of the AMI that was provided during image creation. |
| enasupport |  | Specifies whether enhanced networking with ENA is enabled. |
| hypervisor |  | The hypervisor type of the image. |
| image_owner_alias |  | AWS-provided alias for the machine image owner. |
| imageid | Yes | Identifier of the imageid linked to this `AWSEC2Image` node. |
| ispublic |  | Indicates whether the image has public launch permissions. |
| kernel_id |  | Identifier of the kernel linked to this `AWSEC2Image` node. |
| location |  | The location of the AMI. |
| name | Yes | The name of the AMI that was provided during image creation. |
| owner |  | AWS account ID of the machine image owner. |
| platform |  | This value is set to `windows` for Windows AMIs; otherwise, it is blank. |
| platform_details |  | Operating-system platform details for the machine image. |
| ramdisk_id |  | Identifier of the ramdisk linked to this `AWSEC2Image` node. |
| region |  | The region of the image. |
| rootdevicename |  | The device name of the root device volume (for example, `/dev/sda1` ). |
| rootdevicetype |  | The type of root device used by the AMI. |
| sriov_net_support |  | SR-IOV networking capability advertised by the machine image. |
| state |  | The current state of the AMI. |
| type |  | The type of image. |
| usageoperation |  | The operation of the Amazon EC2 instance and the billing code that is associated with the AMI. |
| virtualizationtype |  | The type of virtualization of the AMI. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSEC2Image)`

### AWSEC2Instance

Our representation of an AWS [EC2 Instance](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_Instance.html).

> **Ontology Mapping**: Some schema variants may also use the ontology label [`ComputeInstance`](#ontology-computeinstance).

> **Additional Labels**: This node also uses `EC2Instance`.

> **Additional Label Definitions**:
>
> - `EC2Instance`: Compatibility label for the deprecated `EC2Instance` aws node label. Use `AWSEC2Instance` instead. Scheduled for removal in v1.0.0.

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Same as `instanceid` below. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| architecture |  | The architecture of the image. |
| arn | Yes | The Amazon Resource Name of the instance, e.g. `arn:aws:ec2:{region}:{account}:instance/{instanceid}`. Synthesized by cartography for IAM permission matching. |
| availabilityzone |  | The Availability Zone of the instance. |
| bootmode |  | The boot mode of the instance. |
| ebsoptimized |  | Indicates whether the instance is optimized for Amazon EBS I/O. |
| eks_cluster_name |  | The name of the EKS cluster this instance belongs to, if applicable. Extracted from instance tags. |
| exposed_internet | Yes | The `exposed_internet` flag on an EC2 instance is set to `True` when (1) the instance is part of an EC2 security group or is connected to a network interface connected to an EC2 security group that allows connectivity from the 0.0.0.0/0 subnet or (2) the instance is connected to an Elastic Load Balancer that has its own `exposed_internet` flag set to `True`. |
| exposed_internet_type |  | Property generated by analysis job: `AWS EC2 instance internet exposure`. |
| hibernationoptions |  | Indicates whether the instance is enabled for hibernation. |
| hostresourcegrouparn |  | The ARN of the host resource group in which to launch the instances. |
| iaminstanceprofile |  | The IAM instance profile associated with the instance, if applicable. |
| imageid |  | The ID of the [Amazon Machine Image](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/AMIs.html) used to launch the instance |
| imdsaccessmode |  | A derived helper field that normalizes the `metadatahttptokens` setting to `v2_only` or `v1_or_v2` for easier security queries. |
| imdsv1enabled |  | A derived boolean that is `true` when IMDSv1 remains allowed on the instance. |
| imdsv2required |  | A derived boolean that is `true` when the instance requires IMDSv2 and disables IMDSv1. |
| instanceid | Yes | The instance id provided by AWS.  This is [globally unique](https://forums.aws.amazon.com/thread.jspa?threadID=137203) |
| instancelifecycle |  | Indicates whether this is a Spot Instance or a Scheduled Instance. |
| instancetype |  | The instance type.  See API docs linked above for specifics. |
| ipv6address |  | The primary IPv6 address assigned to the instance's primary network interface (DeviceIndex=0), if any. |
| launchtime |  | The time the instance was launched |
| launchtimeunix |  | EC2 instance launch time expressed as a Unix timestamp. |
| metadatahttpendpoint |  | Indicates whether the instance metadata HTTP endpoint is enabled. |
| metadatahttpprotocolipv6 |  | Indicates whether the IPv6 endpoint for the instance metadata service is enabled. |
| metadatahttpputresponsehoplimit |  | The maximum number of network hops that an IMDSv2 session token response can travel. |
| metadatahttptokens | Yes | The EC2 metadata service token setting. `required` means IMDSv2 is required and IMDSv1 is disabled; `optional` means either IMDSv1 or IMDSv2 may be used. |
| metadatainstancetags |  | Indicates whether instance tags are exposed through the instance metadata service. |
| monitoringstate |  | Whether monitoring is enabled.  Valid Values: disabled, disabling, enabled,  pending. |
| platform |  | The value is `Windows` for Windows instances; otherwise blank. |
| privateipaddress |  | The private IPv4 address assigned to the instance |
| publicdnsname | Yes | The public DNS name assigned to the instance |
| publicipaddress |  | The public IPv4 address assigned to the instance if applicable |
| region |  | The AWS region this Instance is running in |
| state |  | The [current state](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_InstanceState.html) of the instance. |
| tenancy |  | The tenancy of the instance. |
| *_ont_created_at* | Yes | Normalized field sourced from `launchtime`. |
| *_ont_name* | Yes | Normalized field sourced from `instanceid`. |
| *_ont_private_ip_address* | Yes | Normalized field sourced from `privateipaddress`. |
| *_ont_public_ip_address* | Yes | Normalized field sourced from `publicipaddress`. |
| *_ont_region* | Yes | Normalized field sourced from `region`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |
| *_ont_state* | Yes | Normalized field sourced from `state`. |
| *_ont_type* | Yes | Normalized field sourced from `instancetype`. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSEC2Instance)`

- `(:AWSDNSRecord)-[:DNS_POINTS_TO]->(:AWSEC2Instance)`

- `(:AWSEBSVolume)-[:ATTACHED_TO]->(:AWSEC2Instance)`

- `(:AWSEC2Instance)-[:ASSUMES]->(:AWSRole)`

- `(:AWSEC2Instance)-[:ELASTIC_IP_ADDRESS]->(:AWSElasticIPAddress)`

- `(:AWSEC2Instance)-[:HAS_INFORMATION]->(:AWSSSMInstanceInformation)`

- `(:AWSEC2Instance)-[:HAS_PATCH]->(:AWSSSMInstancePatch)`

- `(:AWSEC2Instance)-[:INSTANCE_PROFILE]->(:AWSInstanceProfile)`

- `(:AWSEC2Instance)-[:MEMBER_AUTO_SCALE_GROUP]->(:AWSAutoScalingGroup)`

- `(:AWSEC2Instance)-[:MEMBER_OF_EC2_RESERVATION]->(:AWSEC2Reservation)`

- `(:AWSEC2Instance)-[:MEMBER_OF_EC2_SECURITY_GROUP]->(:AWSEC2SecurityGroup)`

- `(:AWSEC2Instance)-[:MEMBER_OF_EKS_CLUSTER]->(:AWSEKSCluster)`

- `(:AWSEC2Instance)-[:NETWORK_INTERFACE]->(:AWSNetworkInterface)`

- `(:AWSEC2Instance)-[:PART_OF_SUBNET]->(:AWSEC2Subnet)`

- `(:AWSEC2Instance)-[:STS_ASSUMEROLE_ALLOW]->(:AWSRole)`: generated by analysis job `EC2 Instances assume IAM roles`.

- `(:AWSEC2Instance)-[:TAGGED]->(:AWSTag)`: `AWSEC2Instance` is tagged with an `AWSTag` discovered by the AWS Resource Groups Tagging API.

- `(:AWSEC2KeyPair)-[:SSH_LOGIN_TO]->(:AWSEC2Instance)`

- `(:AWSECSContainerInstance)-[:IS_INSTANCE]->(:AWSEC2Instance)`

- `(:AWSGuardDutyFinding)-[:AFFECTS]->(:AWSEC2Instance)`

- `(:AWSInspectorFinding)-[:AFFECTS]->(:AWSEC2Instance)`

- `(:AWSLoadBalancer)-[:EXPOSE]->(:AWSEC2Instance)`

- `(:AWSLoadBalancerV2)-[:EXPOSE]->(:AWSEC2Instance)`: Indicates that the load balancer exposes an EC2 instance as a traffic target.
  - Properties:

    | Field | Description |
    |-------|-------------|
    | port | Port on which the listener or target group receives traffic. |
    | protocol | Protocol used by the listener or target group. |
    | target_group_arn | ARN of the Elastic Load Balancing target group represented by this relationship. |

- `(:AWSPrincipal)-[:CAN_START_SESSION]->(:AWSEC2Instance)`: `AWSPrincipal` receives evaluated `CAN_START_SESSION` access to `AWSEC2Instance` from AWS IAM policies.
  - Evaluated permissions: `ssm:StartSession`
  - Target precondition: `(:AWSEC2Instance)-[:HAS_INFORMATION]->(:AWSSSMInstanceInformation)` must exist
  - Properties:

    | Field | Description |
    |-------|-------------|
    | condition_keys | IAM condition context keys used by the permission. |
    | conditions | IAM conditions that restrict this permission. |
    | has_condition | Whether an IAM condition restricts this permission. |

- `(:DNSRecord)-[:DNS_POINTS_TO]->(:AWSEC2Instance)`: generated by analysis job `Ontology - DNSRecord to AWSEC2Instance linking`.

- `(:KubernetesNode)-[:IS_INSTANCE]->(:AWSEC2Instance)`: Links a node to the EC2 instance backing it.

- `(:PublicIP)-[:POINTS_TO]->(:ComputeInstance)`

- `(:SpaceliftCloudTrailEvent)-[:AFFECTED]->(:AWSEC2Instance)`: Links a CloudTrail event to the EC2 instances it affected.

- `(:SpaceliftRun)-[:AFFECTED]->(:AWSEC2Instance)`: Links a Spacelift run to the EC2 instances it affected.

### AWSEC2Ipv6Address

Representation of an IPv6 address assigned to an EC2 network interface. Each `AWSEC2Ipv6Address` node corresponds to one entry in `NetworkInterfaces[].Ipv6Addresses[]` from the AWS [DescribeInstances](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeInstances.html) API.

> **Additional Labels**: This node also uses `EC2Ipv6Address`, `Ip`.

> **Additional Label Definitions**:
>
> - `EC2Ipv6Address`: Compatibility label for the deprecated `EC2Ipv6Address` aws node label. Use `AWSEC2Ipv6Address` instead. Scheduled for removal in v1.0.0.
> - `Ip`: A aws node participating in the shared Ip graph interface.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Same as `ipv6_address` — the IPv6 address string |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| ipv6_address | Yes | The IPv6 address (e.g. `2001:db8::1`) |
| network_interface_id |  | The ID of the network interface this address is assigned to |
| primary |  | `true` if this is the primary IPv6 address on the interface (`IsPrimaryIpv6`), `false` otherwise |
| region |  | The AWS region |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSEC2Ipv6Address)`

- `(:AWSNetworkInterface)-[:IPV6_ADDRESS]->(:AWSEC2Ipv6Address)`

### AWSEC2KeyPair

Representation of an AWS [EC2 Key Pair](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_KeyPairInfo.html)

> **Additional Labels**: This node also uses `EC2KeyPair`, `KeyPair`.

> **Additional Label Definitions**:
>
> - `EC2KeyPair`: Compatibility label for the deprecated `EC2KeyPair` aws node label. Use `AWSEC2KeyPair` instead. Scheduled for removal in v1.0.0.
> - `KeyPair`: A aws node participating in the shared KeyPair graph interface.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | same as `arn` |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| arn | Yes | AWS-unique identifier for this object |
| duplicate_keyfingerprint |  | Property generated by analysis job: `Analysis jobs for EC2 Key Pairs properties`. |
| keyfingerprint | Yes | The fingerprint of the public key |
| keyname |  | The name of the key pair |
| region |  | The AWS region |
| user_uploaded |  | Property generated by analysis job: `Analysis jobs for EC2 Key Pairs properties`. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSEC2KeyPair)`

- `(:AWSEC2KeyPair)-[:MATCHING_FINGERPRINT]-(:AWSEC2KeyPair)`: generated by analysis job `Analysis jobs for EC2 Key Pairs matching fingerprints`.

- `(:AWSEC2KeyPair)-[:SSH_LOGIN_TO]->(:AWSEC2Instance)`

- `(:AWSEC2KeyPair)-[:TAGGED]->(:AWSTag)`: `AWSEC2KeyPair` is tagged with an `AWSTag` discovered by the AWS Resource Groups Tagging API.

### AWSEC2NetworkAcl

Representation of an AWS [EC2 Network ACL](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_NetworkAcl.html)

> **Additional Labels**: This node also uses `EC2NetworkAcl`.

> **Additional Label Definitions**:
>
> - `EC2NetworkAcl`: Compatibility label for the deprecated `EC2NetworkAcl` aws node label. Use `AWSEC2NetworkAcl` instead. Scheduled for removal in v1.0.0.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Unique identifier for this `AWSEC2NetworkAcl` node. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| arn |  | Amazon Resource Name (ARN) of this `AWSEC2NetworkAcl` node. |
| is_default |  | Whether this `AWSEC2NetworkAcl` node default. |
| network_acl_id |  | Identifier of the network ACL linked to this `AWSEC2NetworkAcl` node. |
| region |  | AWS Region containing this `AWSEC2NetworkAcl` node. |
| vpc_id |  | Identifier of the VPC linked to this `AWSEC2NetworkAcl` node. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSEC2NetworkAcl)`

- `(:AWSEC2NetworkAcl)-[:MEMBER_OF_AWS_VPC]->(:AWSVpc)`

- `(:AWSEC2NetworkAcl)-[:PART_OF_SUBNET]->(:AWSEC2Subnet)`

- `(:AWSEC2NetworkAcl)-[:PROTECTS]->(:AWSLoadBalancerV2)`: generated by analysis job `AWS LoadBalancer to NACL direct relationship`.

- `(:AWSEC2NetworkAclRule)-[:MEMBER_OF_NACL]->(:AWSEC2NetworkAcl)`

### AWSEC2NetworkAclRule

This node label is loaded by more than one sync path:

- An egress entry of an AWS [EC2 Network ACL Rule Entry](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_NetworkAclEntry.html). For additional explanation see the [network ACL rules guide](https://docs.aws.amazon.com/vpc/latest/userguide/nacl-rules.html).
- An inbound entry of an AWS [EC2 Network ACL Rule Entry](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_NetworkAclEntry.html). For additional explanation see the [network ACL rules guide](https://docs.aws.amazon.com/vpc/latest/userguide/nacl-rules.html).

> **Additional Labels**: This node also uses `EC2NetworkAclRule`.

> **Additional Labels**: Some schema variants may also use `IpPermissionEgress`, `IpPermissionInbound`.

> **Additional Label Definitions**:
>
> - `EC2NetworkAclRule`: Compatibility label for the deprecated `EC2NetworkAclRule` aws node label. Use `AWSEC2NetworkAclRule` instead. Scheduled for removal in v1.0.0.
> - `IpPermissionEgress`: A node participating in the shared IpPermissionEgress graph interface.
> - `IpPermissionInbound`: A node participating in the shared IpPermissionInbound graph interface.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Unique identifier for this `AWSEC2NetworkAclRule` node. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| cidrblock |  | IPv4 CIDR range matched by the network ACL rule. |
| egress |  | Whether this `AWSEC2NetworkAclRule` node applies to outbound traffic. |
| fromport |  | Lowest transport-layer port matched by the network ACL rule. |
| ipv6cidrblock |  | IPv6 CIDR range matched by the network ACL rule. |
| network_acl_id |  | Identifier of the network ACL linked to this `AWSEC2NetworkAclRule` node. |
| protocol |  | IP protocol number matched by the network ACL rule. |
| region |  | AWS Region containing this `AWSEC2NetworkAclRule` node. |
| ruleaction |  | Whether matching traffic is allowed or denied. |
| rulenumber |  | Evaluation order of the network ACL rule. |
| toport |  | Highest transport-layer port matched by the network ACL rule. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSEC2NetworkAclRule)`

- `(:AWSEC2NetworkAclRule)-[:MEMBER_OF_NACL]->(:AWSEC2NetworkAcl)`

### AWSEC2PrivateIp

Representation of an AWS EC2 [InstancePrivateIpAddress](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_InstancePrivateIpAddress.html)

> **Additional Labels**: This node also uses `EC2PrivateIp`.

> **Additional Label Definitions**:
>
> - `EC2PrivateIp`: Compatibility label for the deprecated `EC2PrivateIp` aws node label. Use `AWSEC2PrivateIp` instead. Scheduled for removal in v1.0.0.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Unique identifier for the private IP |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| ip_owner_id |  | Id of the owner, e.g. `amazon-elb` for ELBs |
| network_interface_id |  | id of the network interface with which the IP is associated with |
| primary |  | Indicates whether this IPv4 address is the primary private IP address of the network interface. |
| private_ip_address |  | The private IPv4 address of the network interface. |
| public_ip |  | The public IP address or Elastic IP address bound to the network interface. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSEC2PrivateIp)`

- `(:AWSLoadBalancerV2)-[:EXPOSE]->(:AWSEC2PrivateIp)`: Indicates that the load balancer exposes a private IP address as a traffic target.
  - Properties:

    | Field | Description |
    |-------|-------------|
    | port | Port on which the listener or target group receives traffic. |
    | protocol | Protocol used by the listener or target group. |
    | target_group_arn | ARN of the Elastic Load Balancing target group represented by this relationship. |

- `(:AWSNetworkInterface)-[:PRIVATE_IP_ADDRESS]->(:AWSEC2PrivateIp)`

### AWSEC2Reservation

Representation of an AWS EC2 [Reservation](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_Reservation.html).

> **Additional Labels**: This node also uses `EC2Reservation`.

> **Additional Label Definitions**:
>
> - `EC2Reservation`: Compatibility label for the deprecated `EC2Reservation` aws node label. Use `AWSEC2Reservation` instead. Scheduled for removal in v1.0.0.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The ID of the reservation (same as reservationid) |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| ownerid |  | The ID of the AWS account that owns the reservation. |
| region |  | The AWS region |
| requesterid |  | The ID of the requester that launched the instances on your behalf |
| reservationid |  | The ID of the reservation. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSEC2Reservation)`

- `(:AWSEC2Instance)-[:MEMBER_OF_EC2_RESERVATION]->(:AWSEC2Reservation)`

### AWSEC2ReservedInstance

Representation of an AWS [EC2 Reserved Instance](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-reserved-instances.html).

> **Additional Labels**: This node also uses `EC2ReservedInstance`.

> **Additional Label Definitions**:
>
> - `EC2ReservedInstance`: Compatibility label for the deprecated `EC2ReservedInstance` aws node label. Use `AWSEC2ReservedInstance` instead. Scheduled for removal in v1.0.0.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The ID of the Reserved Instance. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| availabilityzone |  | The Availability Zone in which the Reserved Instance can be used. |
| count |  | The number of reservations purchased. |
| currencycode |  | The currency of the Reserved Instance. It's specified using ISO 4217 standard currency codes. |
| duration |  | The duration of the Reserved Instance, in seconds. |
| end |  | The time when the Reserved Instance expires. |
| fixedprice |  | The purchase price of the Reserved Instance. |
| instancetenancy |  | The tenancy of the instance. |
| offeringclass |  | The offering class of the Reserved Instance. |
| offeringtype |  | The Reserved Instance offering type. |
| productdescription |  | The Reserved Instance product platform description. |
| region |  | The region of the reserved instance. |
| scope |  | The scope of the Reserved Instance. |
| start |  | The date and time the Reserved Instance started. |
| state |  | The state of the Reserved Instance purchase. |
| type |  | The instance type on which the Reserved Instance can be used. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSEC2ReservedInstance)`

### AWSEC2Route

Representation of an AWS [EC2 Route](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_Route.html).

> **Additional Labels**: This node also uses `EC2Route`.

> **Additional Label Definitions**:
>
> - `EC2Route`: Compatibility label for the deprecated `EC2Route` aws node label. Use `AWSEC2Route` instead. Scheduled for removal in v1.0.0.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The ID of the route, formatted as `route_table_id\|destination_cidr\|target_components` where target components are prefixed with their type (e.g., gw-, nat-, pcx-) and joined with underscores. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| carrier_gateway_id |  | The ID of the carrier gateway |
| core_network_arn |  | The Amazon Resource Name (ARN) of the core network |
| destination_cidr_block |  | The IPv4 CIDR block used for the destination match |
| destination_ipv6_cidr_block |  | The IPv6 CIDR block used for the destination match |
| destination_prefix_list_id |  | The ID of the prefix list used for the destination match |
| egress_only_internet_gateway_id |  | The ID of the egress-only internet gateway |
| gateway_id |  | The ID of the gateway |
| instance_id |  | The ID of the instance |
| instance_owner_id |  | The owner ID of the instance |
| local_gateway_id |  | The ID of the local gateway |
| nat_gateway_id |  | The ID of the NAT gateway |
| network_interface_id |  | The ID of the network interface |
| origin |  | How the route was created |
| region |  | The AWS region the route is in |
| state |  | The state of the route |
| target |  | The ID of the route association's target -- either 'Main', or a subnet ID or a gateway ID. This is an invented field that we created to have an ID because the underlying EC2 route association is a "union" data structure of many different possible targets. |
| transit_gateway_id |  | The ID of the transit gateway |
| vpc_endpoint_id |  | Identifier of the VPC endpoint linked to this `AWSEC2Route` node. |
| vpc_peering_connection_id |  | The ID of the VPC peering connection |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSEC2Route)`

- `(:AWSEC2Route)-[:ROUTES_TO_GATEWAY]->(:AWSInternetGateway)`

- `(:AWSEC2Route)-[:ROUTES_TO_VPC_ENDPOINT]->(:AWSVpcEndpoint)`

- `(:AWSEC2RouteTable)-[:ROUTE]->(:AWSEC2Route)`

### AWSEC2RouteTable

Representation of an AWS [EC2 Route Table](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_RouteTable.html).

> **Additional Labels**: This node also uses `EC2RouteTable`.

> **Additional Label Definitions**:
>
> - `EC2RouteTable`: Compatibility label for the deprecated `EC2RouteTable` aws node label. Use `AWSEC2RouteTable` instead. Scheduled for removal in v1.0.0.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The ID of the route table |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| main |  | If True, this route table is the main route table for VPC, meaning that any subnets in this VPC not explicitly associated with another route table will use this route table. |
| owner_id |  | The AWS account ID of the route table owner |
| region |  | The AWS region the route table is in |
| route_table_id | Yes | The ID of the route table (same as id) |
| vpc_id |  | The ID of the VPC the route table is associated with |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSEC2RouteTable)`

- `(:AWSEC2RouteTable)-[:ASSOCIATION]->(:AWSEC2RouteTableAssociation)`

- `(:AWSEC2RouteTable)-[:MEMBER_OF_AWS_VPC]->(:AWSVpc)`

- `(:AWSEC2RouteTable)-[:ROUTE]->(:AWSEC2Route)`

### AWSEC2RouteTableAssociation

Representation of an AWS [EC2 Route Table Association](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_RouteTableAssociation.html).

> **Additional Labels**: This node also uses `EC2RouteTableAssociation`.

> **Additional Label Definitions**:
>
> - `EC2RouteTableAssociation`: Compatibility label for the deprecated `EC2RouteTableAssociation` aws node label. Use `AWSEC2RouteTableAssociation` instead. Scheduled for removal in v1.0.0.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The ID of the route table association |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| association_state |  | The state of the association |
| association_state_message |  | The message describing the state of the association |
| gateway_id |  | The ID of the gateway (if associated with a gateway) |
| main |  | Whether this is the main route table association |
| region |  | The AWS region the association is in |
| route_table_association_id | Yes | The ID of the route table association (same as id) |
| route_table_id |  | The ID of the route table |
| subnet_id |  | The ID of the subnet (if associated with a subnet) |
| target |  | Subnet or gateway identifier associated with the route table. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSEC2RouteTableAssociation)`

- `(:AWSEC2RouteTable)-[:ASSOCIATION]->(:AWSEC2RouteTableAssociation)`

- `(:AWSEC2RouteTableAssociation)-[:ASSOCIATED_IGW_FOR_INGRESS]->(:AWSInternetGateway)`

- `(:AWSEC2RouteTableAssociation)-[:ASSOCIATED_SUBNET]->(:AWSEC2Subnet)`

### AWSEC2SecurityGroup

Representation of an AWS EC2 [Security Group](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_SecurityGroup.html).

> **Ontology Mapping**: Some schema variants may also use the ontology label [`NetworkAccessControl`](#ontology-networkaccesscontrol).

> **Additional Labels**: This node also uses `EC2SecurityGroup`.

> **Additional Label Definitions**:
>
> - `EC2SecurityGroup`: Compatibility label for the deprecated `EC2SecurityGroup` aws node label. Use `AWSEC2SecurityGroup` instead. Scheduled for removal in v1.0.0.

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Same as `groupid` |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| description |  | A description of the security group |
| groupid | Yes | The ID of the security group. Note that these are globally unique in AWS. |
| name |  | The name of the security group |
| region |  | The AWS region this security group is installed in |
| *_ont_name* | Yes | Normalized field sourced from `name`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSEC2SecurityGroup)`

- `(:AWSEC2Instance)-[:MEMBER_OF_EC2_SECURITY_GROUP]->(:AWSEC2SecurityGroup)`

- `(:AWSEC2SecurityGroup)-[:ALLOWS_TRAFFIC_FROM]->(:AWSEC2SecurityGroup)`

- `(:AWSEC2SecurityGroup)-[:TAGGED]->(:AWSTag)`: `AWSEC2SecurityGroup` is tagged with an `AWSTag` discovered by the AWS Resource Groups Tagging API.

- `(:AWSESDomain)-[:MEMBER_OF_EC2_SECURITY_GROUP]->(:AWSEC2SecurityGroup)`

- `(:AWSIpPermissionInbound)-[:MEMBER_OF_EC2_SECURITY_GROUP]->(:AWSEC2SecurityGroup)`

- `(:AWSIpRule)-[:MEMBER_OF_EC2_SECURITY_GROUP]->(:AWSEC2SecurityGroup)`

- `(:AWSLoadBalancer)-[:MEMBER_OF_EC2_SECURITY_GROUP]->(:AWSEC2SecurityGroup)`

- `(:AWSLoadBalancer)-[:SOURCE_SECURITY_GROUP]->(:AWSEC2SecurityGroup)`

- `(:AWSLoadBalancerV2)-[:MEMBER_OF_EC2_SECURITY_GROUP]->(:AWSEC2SecurityGroup)`

- `(:AWSNetworkInterface)-[:MEMBER_OF_EC2_SECURITY_GROUP]->(:AWSEC2SecurityGroup)`

- `(:AWSRDSInstance)-[:MEMBER_OF_EC2_SECURITY_GROUP]->(:AWSEC2SecurityGroup)`

- `(:AWSRedshiftCluster)-[:MEMBER_OF_EC2_SECURITY_GROUP]->(:AWSEC2SecurityGroup)`

- `(:AWSVpc)-[:MEMBER_OF_EC2_SECURITY_GROUP]->(:AWSEC2SecurityGroup)`

- `(:AWSVpcEndpoint)-[:MEMBER_OF_SECURITY_GROUP]->(:AWSEC2SecurityGroup)`

- `(:DatabricksNetworkConfig)-[:USES_SECURITY_GROUP]->(:AWSEC2SecurityGroup)`: A Databricks network configuration uses an AWS security group.

### AWSEC2Subnet

Representation of an AWS EC2 [Subnet](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_Subnet.html).

> **Ontology Mapping**: This node uses the ontology label [`Subnet`](#ontology-subnet).

> **Additional Labels**: This node also uses `EC2Subnet`.

> **Additional Label Definitions**:
>
> - `EC2Subnet`: Compatibility label for the deprecated `EC2Subnet` aws node label. Use `AWSEC2Subnet` instead. Scheduled for removal in v1.0.0.

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | same as subnetid |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| assignipv6addressoncreation |  | Indicates whether a network interface created in this subnet (including a network interface created by RunInstances ) receives an IPv6 address. |
| availability_zone |  | The Availability Zone of the subnet |
| availability_zone_id |  | The AZ ID of the subnet |
| available_ip_address_count |  | The number of unused private IPv4 addresses in the subnet. The IPv4 addresses for any stopped instances are considered unavailable |
| cidr_block |  | The IPv4 CIDR block assigned to the subnet |
| default_for_az |  | Indicates whether this is the default subnet for the Availability Zone. |
| map_customer_owned_ip_on_launch |  | Indicates whether a network interface created in this subnet (including a network interface created by RunInstances ) receives a customer-owned IPv4 address |
| map_public_ip_on_launch |  | Indicates whether instances launched in this subnet receive a public IPv4 address |
| name |  | The IPv4 CIDR block assigned to the subnet |
| region |  | The AWS region the subnet is installed on |
| state |  | The current state of the subnet. |
| subnet_arn |  | The Amazon Resource Name (ARN) of the subnet |
| subnet_id | Yes | The ID of the subnet |
| subnetid | Yes | The ID of the subnet |
| vpc_id |  | The ID of the VPC this subnet belongs to |
| *_ont_availability_zone* | Yes | Normalized field sourced from `availability_zone`. |
| *_ont_cidr_block* | Yes | Normalized field sourced from `cidr_block`. |
| *_ont_name* | Yes | Normalized field sourced from `id`. |
| *_ont_region* | Yes | Normalized field sourced from `region`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSEC2Subnet)`

- `(:AWSAutoScalingGroup)-[:VPC_IDENTIFIER]->(:AWSEC2Subnet)`

- `(:AWSDBSubnetGroup)-[:RESOURCE]->(:AWSEC2Subnet)`

- `(:AWSEC2Instance)-[:PART_OF_SUBNET]->(:AWSEC2Subnet)`

- `(:AWSEC2NetworkAcl)-[:PART_OF_SUBNET]->(:AWSEC2Subnet)`

- `(:AWSEC2RouteTableAssociation)-[:ASSOCIATED_SUBNET]->(:AWSEC2Subnet)`

- `(:AWSEC2Subnet)-[:MEMBER_OF_AWS_VPC]->(:AWSVpc)`

- `(:AWSEC2Subnet)-[:TAGGED]->(:AWSTag)`: `AWSEC2Subnet` is tagged with an `AWSTag` discovered by the AWS Resource Groups Tagging API.

- `(:AWSESDomain)-[:PART_OF_SUBNET]->(:AWSEC2Subnet)`

- `(:AWSLoadBalancer)-[:PART_OF_SUBNET]->(:AWSEC2Subnet)`

- `(:AWSLoadBalancerV2)-[:PART_OF_SUBNET]->(:AWSEC2Subnet)`

- `(:AWSLoadBalancerV2)-[:SUBNET]->(:AWSEC2Subnet)`

- `(:AWSNetworkInterface)-[:PART_OF_SUBNET]->(:AWSEC2Subnet)`

- `(:AWSTransitGatewayAttachment)-[:PART_OF_SUBNET]->(:AWSEC2Subnet)`

- `(:AWSVpcEndpoint)-[:USES_SUBNET]->(:AWSEC2Subnet)`

- `(:DatabricksNetworkConfig)-[:USES_SUBNET]->(:AWSEC2Subnet)`: A Databricks network configuration uses an AWS subnet.

### AWSECRImage

This node label is loaded by more than one sync path:

- Representation of an ECR image identified by its digest (e.g. a SHA hash). Specifically, this is the "digest part" of [`ecr.list_images()`](https://docs.aws.amazon.com/AmazonECR/latest/APIReference/API_ImageIdentifier.html). Also see AWSECRRepositoryImage.

For multi-architecture images, Cartography creates AWSECRImage nodes for the manifest list, each platform-specific image, and any attestations.
- Representation of an ECR image identified by its digest (e.g. a SHA hash). Specifically, this is the "digest part" of [`ecr.list_images()`](https://docs.aws.amazon.com/AmazonECR/latest/APIReference/API_ImageIdentifier.html). Also see AWSECRRepositoryImage.

For multi-architecture images, Cartography creates AWSECRImage nodes for the manifest list, each platform-specific image, and any attestations.

Cleanup runs after layer enrichment so unchanged closures can refresh their
relationship timestamps before stale HAS_LAYER and BUILT_FROM edges are removed.

> **Additional Labels**: This node also uses `ECRImage`.

> **Additional Label Definitions**:
>
> - `ECRImage`: Compatibility label for the deprecated `ECRImage` aws node label. Use `AWSECRImage` instead. Scheduled for removal in v1.0.0.

> **Conditional Labels**:
>
> - [`Image`](#ontology-image) (ontology label) when `type` equals `image`. A concrete single-platform container image.
> - [`ImageAttestation`](#ontology-imageattestation) (ontology label) when `type` equals `attestation`. A cross-provider ImageAttestation resource in Cartography's ontology.
> - [`ImageManifestList`](#ontology-imagemanifestlist) (ontology label) when `type` equals `manifest_list`. A cross-provider ImageManifestList resource in Cartography's ontology.

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Same as digest |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| architecture |  | CPU architecture (e.g., `"amd64"`, `"arm64"`). Set to `"unknown"` for attestations, `null` for manifest lists. |
| artifact_media_type |  | The artifact media type if this is an OCI artifact. Optional field. |
| attestation_type |  | For attestations only: the type of attestation (e.g., `"attestation-manifest"`). `null` for regular images. |
| attests_digest |  | For attestations only: the digest of the image this attestation is for. `null` for regular images. |
| child_image_digests |  | For manifest lists only: list of platform-specific image digests contained in this manifest list. Excludes attestations. `null` for regular images and attestations. |
| digest | Yes | The hash of this ECR image |
| invocation_run_number |  | CI/CD run number from SLSA provenance (e.g., the GitHub Actions run number). |
| invocation_uri | Yes | CI/CD invocation URI from SLSA provenance (e.g., GitHub repository URL). Indexed for cross-module matching. |
| invocation_workflow | Yes | CI/CD workflow path from SLSA provenance (e.g., `.github/workflows/build.yml`). Indexed for cross-module matching. |
| layer_diff_ids |  | Ordered list of image layer digests for this image. Only set for `type="image"` nodes. `null` for manifest lists and attestations. |
| media_type |  | The OCI/Docker media type of this manifest (e.g., `"application/vnd.oci.image.manifest.v1+json"`) |
| os |  | Operating system (e.g., `"linux"`, `"windows"`). Set to `"unknown"` for attestations, `null` for manifest lists. |
| region |  | The AWS region |
| source_file |  | Dockerfile path from SLSA provenance (`configSource.entryPoint` prefixed with `vcs localdir:dockerfile` if present). |
| source_revision |  | Source commit revision from SLSA provenance attestations. |
| source_uri | Yes | Source repository URI extracted from SLSA provenance attestations (e.g., a GitLab project URL or GitHub repo URL). Indexed for cross-module matching. |
| type | Yes | Type of image: `"image"` (platform-specific or single-arch image), `"manifest_list"` (multi-arch index), or `"attestation"` (attestation manifest) |
| variant |  | Architecture variant (e.g., `"v8"` for ARM). Optional field. |
| *_ont_architecture* | Yes | Normalized field sourced from `architecture`. |
| *_ont_digest* | Yes | Normalized field sourced from `digest`. |
| *_ont_os* | Yes | Normalized field sourced from `os`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSECRImage)`

- `(:AWSECRImage)-[:ATTESTS]->(:AWSECRImage)`: Relationship from an attestation AWSECRImage to the AWSECRImage it attests/validates.
Only applies to AWSECRImage nodes with type="attestation".

- `(:AWSECRImage)-[:BUILT_FROM]->(:AWSECRImage)`: Relationship from an AWSECRImage to its parent AWSECRImage (BUILT_FROM).
This relationship is created when provenance attestations explicitly specify the parent image.
  - Properties:

    | Field | Description |
    |-------|-------------|
    | confidence | Confidence level assigned to the inferred relationship. |
    | from_attestation | Whether the parent image relationship was derived from a provenance attestation. |
    | parent_image_uri | Container image URI identifying the parent image in this relationship. |

- `(:AWSECRImage)-[:CONTAINS_IMAGE]->(:AWSECRImage)`: Relationship from a manifest list AWSECRImage to platform-specific ECRImages it contains.
Only applies to AWSECRImage nodes with type="manifest_list".

- `(:AWSECRImage)-[:HAS_LAYER]->(:AWSECRImageLayer)`

- `(:AWSECRImage)-[:HEAD]->(:AWSECRImageLayer)`

- `(:AWSECRImage)-[:TAIL]->(:AWSECRImageLayer)`

- `(:AWSECRRepositoryImage)-[:IMAGE]->(:AWSECRImage)`

- `(:AWSECSContainer)-[:HAS_IMAGE]->(:AWSECRImage)`

- `(:AWSInspectorFinding)-[:AFFECTS]->(:AWSECRImage)`

- `(:AWSLambda)-[:HAS]->(:AWSECRImage)`: generated by analysis job `Lambda functions with ECR images`.

- `(:AWSLambda)-[:HAS_IMAGE]->(:AWSECRImage)`

- `(:AzureContainerInstance)-[:HAS_IMAGE]->(:AWSECRImage)`: An Azure container uses an Amazon ECR image with the same digest.

- `(:AzureFunctionApp)-[:HAS_IMAGE]->(:AWSECRImage)`: An Azure Function App uses an Amazon ECR image with the same digest.

- `(:ComputeService)-[:HAS_RUNTIME_IMAGE]->(:Image)`: generated by analysis job `Workload HAS_RUNTIME_IMAGE inventory analysis`.
  - Properties:

    | Field | Description |
    |-------|-------------|
    | exposed_internet | Property generated by analysis job: `Workload HAS_RUNTIME_IMAGE inventory analysis`. |

- `(:Container)-[:RESOLVED_IMAGE]->(:Image)`: generated by analysis job `Container RESOLVED_IMAGE analysis`.

- `(:Function)-[:RESOLVED_IMAGE]->(:Image)`: generated by analysis job `Function RESOLVED_IMAGE analysis`.

- `(:GCPCloudRunJobContainer)-[:HAS_IMAGE]->(:AWSECRImage)`

- `(:GCPCloudRunServiceContainer)-[:HAS_IMAGE]->(:AWSECRImage)`

- `(:KubernetesContainer)-[:HAS_IMAGE]->(:AWSECRImage)`: Links a container to the image it runs, hosted in Amazon ECR.

- `(:PackageVersion)-[:DEPLOYED]->(:Image)`: A canonical package version is deployed on a container image.

### AWSECRImageLayer

Representation of an individual Docker image layer discovered while processing ECR manifests. Layers are de-duplicated by `diff_id`, so multiple images (or multiple points within the same image) may reference the same `AWSECRImageLayer` node. Note that `diff_id` is the **uncompressed** (DiffID) SHA-256 of the layer tar stream. Docker's canonical empty layer therefore always appears as `sha256:5f70bf18a086007016e948b04aed3b82103a36bea41755b6cddfaf10ace3c6ef` and is marked with `is_empty = true`. (If you inspect registry manifests you may see the compressed blob digest `sha256:a3ed95ca...`, both refer to the same empty layer.)

> **Ontology Mapping**: Some schema variants may also use the ontology label [`ImageLayer`](#ontology-imagelayer).

> **Additional Labels**: This node also uses `ECRImageLayer`.

> **Additional Label Definitions**:
>
> - `ECRImageLayer`: Compatibility label for the deprecated `ECRImageLayer` aws node label. Use `AWSECRImageLayer` instead. Scheduled for removal in v1.0.0.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Same as `diff_id` |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| diff_id |  | Digest of the layer |
| history |  | The `created_by` command from the image config that created this layer (e.g., `/bin/sh -c pip install flask`). Used for Dockerfile matching. |
| is_empty |  | Boolean flag identifying Docker's empty layer (true when the **DiffID** is `sha256:5f70bf18...`). |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSECRImageLayer)`

- `(:AWSECRImage)-[:HAS_LAYER]->(:AWSECRImageLayer)`

- `(:AWSECRImage)-[:HEAD]->(:AWSECRImageLayer)`

- `(:AWSECRImage)-[:TAIL]->(:AWSECRImageLayer)`

- `(:AWSECRImageLayer)-[:NEXT]->(:AWSECRImageLayer)`

### AWSECRPullThroughCacheRule

Representation of an AWS Elastic Container Registry [pull through cache rule](https://docs.aws.amazon.com/AmazonECR/latest/APIReference/API_PullThroughCacheRule.html).

> **Additional Labels**: This node also uses `ECRPullThroughCacheRule`.

> **Additional Label Definitions**:
>
> - `ECRPullThroughCacheRule`: Compatibility label for the deprecated `ECRPullThroughCacheRule` aws node label. Use `AWSECRPullThroughCacheRule` instead. Scheduled for removal in v1.0.0.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Synthetic ID in the format `registry_id:region:ecr_repository_prefix` |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| created_at |  | Date and time when the rule was created |
| credential_arn | Yes | The Secrets Manager secret ARN used for upstream registry credentials, when configured |
| custom_role_arn | Yes | The IAM role ARN used for pull through cache operations, when configured |
| ecr_repository_prefix | Yes | The ECR repository prefix used when caching images from the upstream registry |
| region |  | The region of the rule |
| registry_id | Yes | The AWS registry ID associated with the rule |
| updated_at |  | Date and time when the rule was last updated |
| upstream_registry | Yes | The upstream source registry name associated with the rule |
| upstream_registry_url |  | The upstream registry URL associated with the rule |
| upstream_repository_prefix |  | The upstream repository prefix associated with the rule |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSECRPullThroughCacheRule)`

- `(:AWSECRPullThroughCacheRule)-[:ASSOCIATED_WITH]->(:AWSRole)`

- `(:AWSECRPullThroughCacheRule)-[:USES_SECRET]->(:AWSSecretsManagerSecret)`

### AWSECRRepository

Representation of an AWS Elastic Container Registry [Repository](https://docs.aws.amazon.com/AmazonECR/latest/APIReference/API_Repository.html).

> **Ontology Mapping**: This node uses the ontology label [`ContainerRegistry`](#ontology-containerregistry).

> **Additional Labels**: This node also uses `ECRRepository`.

> **Additional Label Definitions**:
>
> - `ECRRepository`: Compatibility label for the deprecated `ECRRepository` aws node label. Use `AWSECRRepository` instead. Scheduled for removal in v1.0.0.

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Same as ARN |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| arn | Yes | The ARN of the repository |
| created_at |  | Date and time when the repository was created |
| name | Yes | The name of the repository |
| region |  | The region of the repository |
| uri | Yes | The URI of the repository |
| *_ont_created_at* | Yes | Normalized field sourced from `created_at`. |
| *_ont_location* | Yes | Normalized field sourced from `region`. |
| *_ont_name* | Yes | Normalized field sourced from `name`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |
| *_ont_uri* | Yes | Normalized field sourced from `uri`. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSECRRepository)`

- `(:AWSECRRepository)-[:REPO_IMAGE]->(:AWSECRRepositoryImage)`

- `(:AWSECRRepository)-[:TAGGED]->(:AWSTag)`: `AWSECRRepository` is tagged with an `AWSTag` discovered by the AWS Resource Groups Tagging API.

- `(:AWSInspectorFinding)-[:AFFECTS]->(:AWSECRRepository)`

### AWSECRRepositoryImage

An ECR image may be referenced and tagged by more than one ECR Repository. To best represent this, we've created an `AWSECRRepositoryImage` node as a layer of indirection between the repo and the image.

More concretely explained, we run [`ecr.list_images()`](https://docs.aws.amazon.com/AmazonECR/latest/APIReference/API_ImageIdentifier.html), and then store the image tag on an `AWSECRRepositoryImage` node and the image digest hash on a separate `AWSECRImage` node.

This way, more than one `AWSECRRepositoryImage` can reference/be connected to the same `AWSECRImage`.

> **Ontology Mapping**: This node uses the ontology label [`ImageTag`](#ontology-imagetag).

> **Additional Labels**: This node also uses `ECRRepositoryImage`.

> **Additional Label Definitions**:
>
> - `ECRRepositoryImage`: Compatibility label for the deprecated `ECRRepositoryImage` aws node label. Use `AWSECRRepositoryImage` instead. Scheduled for removal in v1.0.0.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | same as uri |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| artifact_media_type |  | The media type of the image artifact |
| image_manifest_media_type |  | The media type of the image manifest, see [opencontainers image spec](https://github.com/opencontainers/image-spec/blob/main/media-types.md) |
| image_pushed_at |  | The date and time the image was pushed to the repository |
| image_size_bytes |  | The size of the image in bytes |
| last_recorded_pull_time |  | The date and time the image was last pulled |
| region |  | AWS Region containing this `AWSECRRepositoryImage` node. |
| repo_uri |  | URI of the ECR repository containing the image. |
| tag |  | The tag applied to the repository image, e.g. "latest" |
| uri |  | The URI where the repository image is stored |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSECRRepositoryImage)`

- `(:AWSECRRepository)-[:REPO_IMAGE]->(:AWSECRRepositoryImage)`

- `(:AWSECRRepositoryImage)-[:IMAGE]->(:AWSECRImage)`

### AWSECSCluster

Representation of an AWS ECS [Cluster](https://docs.aws.amazon.com/AmazonECS/latest/APIReference/API_Cluster.html)

> **Ontology Mapping**: This node uses the ontology label [`ComputeCluster`](#ontology-computecluster).

> **Additional Labels**: This node also uses `ECSCluster`.

> **Additional Label Definitions**:
>
> - `ECSCluster`: Compatibility label for the deprecated `ECSCluster` aws node label. Use `AWSECSCluster` instead. Scheduled for removal in v1.0.0.

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The ARN of the cluster |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| arn | Yes | The ARN of the cluster |
| attachments_status |  | The status of the capacity providers associated with the cluster. |
| capacity_providers |  | The capacity providers associated with the cluster. |
| ecc_kms_key_id |  | An AWS Key Management Service key ID to encrypt the data between the local client and the container. |
| ecc_log_configuration_cloud_watch_encryption_enabled |  | Determines whether to enable encryption on the CloudWatch logs. |
| ecc_log_configuration_cloud_watch_log_group_name |  | The name of the CloudWatch log group to send logs to. |
| ecc_log_configuration_s3_bucket_name |  | The name of the S3 bucket to send logs to. |
| ecc_log_configuration_s3_encryption_enabled |  | Determines whether to use encryption on the S3 logs. |
| ecc_log_configuration_s3_key_prefix |  | An optional folder in the S3 bucket to place logs in. |
| ecc_logging |  | The log setting to use for redirecting logs for your execute command results. |
| name |  | A user-generated string that you use to identify your cluster. |
| region |  | The region of the cluster. |
| status |  | The status of the cluster |
| *_ont_name* | Yes | Normalized field sourced from `name`. |
| *_ont_region* | Yes | Normalized field sourced from `region`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |
| *_ont_status* | Yes | Normalized field sourced from `status`. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSECSCluster)`

- `(:AWSECSCluster)-[:HAS_CONTAINER_INSTANCE]->(:AWSECSContainerInstance)`

- `(:AWSECSCluster)-[:HAS_SERVICE]->(:AWSECSService)`

- `(:AWSECSCluster)-[:HAS_TASK]->(:AWSECSTask)`

- `(:AWSECSCluster)-[:TAGGED]->(:AWSTag)`: `AWSECSCluster` is tagged with an `AWSTag` discovered by the AWS Resource Groups Tagging API.

- `(:AWSECSService)-[:WORKLOAD_PARENT]->(:AWSECSCluster)`

- `(:AWSECSTask)-[:WORKLOAD_PARENT]->(:AWSECSCluster)`

### AWSECSContainer

Representation of an AWS ECS [Container](https://docs.aws.amazon.com/AmazonECS/latest/APIReference/API_Container.html)

> **Ontology Mapping**: This node uses the ontology label [`Container`](#ontology-container).

> **Additional Labels**: This node also uses `ECSContainer`.

> **Additional Label Definitions**:
>
> - `ECSContainer`: Compatibility label for the deprecated `ECSContainer` aws node label. Use `AWSECSContainer` instead. Scheduled for removal in v1.0.0.

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The ARN of the container |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| architecture |  | Raw container architecture value captured from ECS runtime/task definition (for example, `x86_64`, `ARM64`). |
| architecture_normalized |  | Canonicalized architecture value (for example, `amd64`, `arm64`, `arm`, `386`, `unknown`). |
| architecture_source |  | Source for architecture inference (`runtime_api_exact` or `task_definition_hint`). |
| arn | Yes | The arn of the container. |
| cpu |  | The number of CPU units set for the container. |
| exit_code |  | The exit code returned from the container. |
| exposed_internet |  | Property generated by analysis job: `AWS ECS internet exposure`. |
| exposed_internet_type |  | Property generated by analysis job: `AWS ECS internet exposure`. |
| gpu_ids |  | The IDs of each GPU assigned to the container. |
| health_status |  | The health status of the container. |
| image |  | The image used for the container. |
| image_digest |  | The container image manifest digest. |
| last_status | Yes | The last known status of the container. |
| memory |  | The hard limit (in MiB) of memory set for the container. |
| memory_reservation |  | The soft limit (in MiB) of memory set for the container. |
| name |  | The name of the container. |
| reason |  | A short (255 max characters) human-readable string to provide additional details about a running or stopped container. |
| region |  | The region of the container. |
| runtime_id |  | The ID of the Docker container. |
| task_arn |  | The ARN of the task. |
| *_ont_cpu* | Yes | Normalized field sourced from `cpu`. |
| *_ont_health_status* | Yes | Normalized field sourced from `health_status`. |
| *_ont_image* | Yes | Normalized field sourced from `image`. |
| *_ont_image_digest* | Yes | Normalized field sourced from `image_digest`. |
| *_ont_memory* | Yes | Normalized field sourced from `memory`. |
| *_ont_name* | Yes | Normalized field sourced from `name`. |
| *_ont_region* | Yes | Normalized field sourced from `region`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |
| *_ont_state* | Yes | Normalized field sourced from `last_status`. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSECSContainer)`

- `(:AWSECSContainer)-[:HAS_IMAGE]->(:AWSECRImage)`

- `(:AWSECSContainer)-[:HAS_IMAGE]->(:GCPArtifactRegistryImage)`: Matches containers to GAR image artifacts by runtime digest (imageDigest).

- `(:AWSECSContainer)-[:HAS_IMAGE]->(:GitHubContainerImage)`: Matches containers to GitHub Container Registry images by runtime digest (imageDigest).

- `(:AWSECSContainer)-[:HAS_IMAGE]->(:GitLabContainerImage)`: Relationship from AWSECSContainer to GitLabContainerImage.
Matches containers to GitLab registry images by runtime digest (imageDigest).

- `(:AWSECSContainer)-[:TAGGED]->(:AWSTag)`: `AWSECSContainer` is tagged with an `AWSTag` discovered by the AWS Resource Groups Tagging API.

- `(:AWSECSContainer)-[:WORKLOAD_PARENT]->(:AWSECSTask)`

- `(:AWSECSTask)-[:HAS_CONTAINER]->(:AWSECSContainer)`

- `(:AWSLoadBalancerV2)-[:EXPOSE]->(:AWSECSContainer)`: generated by analysis job `AWS LoadBalancer to ECS Container direct relationship`.
  - Properties:

    | Field | Description |
    |-------|-------------|
    | exposure_type | Property generated by analysis job: `AWS LoadBalancer to ECS Container direct relationship`. |

- `(:Container)-[:RESOLVED_IMAGE]->(:Image)`: generated by analysis job `Container RESOLVED_IMAGE analysis`.

### AWSECSContainerDefinition

Representation of an AWS ECS [Container Definition](https://docs.aws.amazon.com/AmazonECS/latest/APIReference/API_ContainerDefinition.html)

> **Additional Labels**: This node also uses `ECSContainerDefinition`.

> **Additional Label Definitions**:
>
> - `ECSContainerDefinition`: Compatibility label for the deprecated `ECSContainerDefinition` aws node label. Use `AWSECSContainerDefinition` instead. Scheduled for removal in v1.0.0.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The ARN of the task definition, plus the container definition name |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| command |  | The command that's passed to the container. |
| cpu |  | The number of cpu units reserved for the container. |
| disable_networking |  | When this parameter is true, networking is disabled within the container. |
| dns_search_domains |  | A list of DNS search domains that are presented to the container. |
| dns_servers |  | A list of DNS servers that are presented to the container. |
| docker_security_options |  | A list of strings to provide custom labels for SELinux and AppArmor multi-level security systems. This field isn't valid for containers in tasks using the Fargate launch type. |
| entry_point |  | The entry point that's passed to the container. |
| essential |  | If the essential parameter of a container is marked as true, and that container fails or stops for any reason, all other containers that are part of the task are stopped. |
| hostname |  | The hostname to use for your container. |
| image |  | The image used to start a container. This string is passed directly to the Docker daemon. |
| interactive |  | When this parameter is true, you can deploy containerized applications that require stdin or a tty to be allocated. |
| links |  | The links parameter allows containers to communicate with each other without the need for port mappings. |
| memory |  | The amount (in MiB) of memory to present to the container. |
| memory_reservation |  | The soft limit (in MiB) of memory to reserve for the container. |
| name |  | The name of a container. |
| privileged |  | When this parameter is true, the container is given elevated privileges on the host container instance (similar to the root user). |
| pseudo_terminal |  | When this parameter is true, a TTY is allocated. |
| readonly_root_filesystem |  | When this parameter is true, the container is given read-only access to its root file system. |
| region |  | The region of the container definition. |
| start_timeout |  | Time duration (in seconds) to wait before giving up on resolving dependencies for a container. |
| stop_timeout |  | Time duration (in seconds) to wait before the container is forcefully killed if it doesn't exit normally on its own. |
| task_definition_arn |  | ARN of the task definition linked to this `AWSECSContainerDefinition` node. |
| user |  | The user to use inside the container. |
| working_directory |  | The working directory to run commands inside the container in. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSECSContainerDefinition)`

- `(:AWSECSTaskDefinition)-[:HAS_CONTAINER_DEFINITION]->(:AWSECSContainerDefinition)`

### AWSECSContainerInstance

Representation of an AWS ECS [Container Instance](https://docs.aws.amazon.com/AmazonECS/latest/APIReference/API_ContainerInstance.html)

> **Additional Labels**: This node also uses `ECSContainerInstance`.

> **Additional Label Definitions**:
>
> - `ECSContainerInstance`: Compatibility label for the deprecated `ECSContainerInstance` aws node label. Use `AWSECSContainerInstance` instead. Scheduled for removal in v1.0.0.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The ARN of the container instance |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| agent_connected |  | This parameter returns true if the agent is connected to Amazon ECS. Registered instances with an agent that may be unhealthy or stopped return false. |
| agent_update_status |  | The status of the most recent agent update. If an update wasn't ever requested, this value is NULL. |
| arn | Yes | The ARN of the container instance |
| capacity_provider_name |  | The capacity provider that's associated with the container instance. |
| ec2_instance_id |  | The ID of the container instance. For Amazon EC2 instances, this value is the Amazon EC2 instance ID. For external instances, this value is the AWS Systems Manager managed instance ID. |
| region |  | The region of the container instance. |
| registered_at |  | The Unix timestamp for the time when the container instance was registered. |
| status |  | The status of the container instance. |
| status_reason |  | The reason that the container instance reached its current status. |
| version |  | The version counter for the container instance. |
| version_info_agent_docker_version |  | The Docker version that's running on the container instance. |
| version_info_agent_hash |  | The Git commit hash for the Amazon ECS container agent build on the amazon-ecs-agent  GitHub repository. |
| version_info_agent_version |  | The version number of the Amazon ECS container agent. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSECSContainerInstance)`

- `(:AWSECSCluster)-[:HAS_CONTAINER_INSTANCE]->(:AWSECSContainerInstance)`

- `(:AWSECSContainerInstance)-[:HAS_TASK]->(:AWSECSTask)`

- `(:AWSECSContainerInstance)-[:IS_INSTANCE]->(:AWSEC2Instance)`

- `(:AWSECSContainerInstance)-[:TAGGED]->(:AWSTag)`: `AWSECSContainerInstance` is tagged with an `AWSTag` discovered by the AWS Resource Groups Tagging API.

### AWSECSService

Representation of an AWS ECS [Service](https://docs.aws.amazon.com/AmazonECS/latest/APIReference/API_Service.html)

> **Ontology Mapping**: This node uses the ontology label [`ComputeService`](#ontology-computeservice).

> **Additional Labels**: This node also uses `ECSService`.

> **Additional Label Definitions**:
>
> - `ECSService`: Compatibility label for the deprecated `ECSService` aws node label. Use `AWSECSService` instead. Scheduled for removal in v1.0.0.

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The ARN of the service |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| arn | Yes | The ARN of the service |
| cluster_arn |  | The Amazon Resource Name (ARN) of the cluster that hosts the service. |
| created_at |  | The Unix timestamp for the time when the service was created. |
| created_by |  | The principal that created the service. |
| deployment_config_circuit_breaker_enable |  | Determines whether to enable the deployment circuit breaker logic for the service. |
| deployment_config_circuit_breaker_rollback |  | Determines whether to enable Amazon ECS to roll back the service if a service deployment fails. |
| deployment_config_maximum_percent |  | If a service is using the rolling update (ECS) deployment type, the maximum percent parameter represents an upper limit on the number of tasks in a service that are allowed in the RUNNING or PENDING state during a deployment, as a percentage of the desired number of tasks (rounded down to the nearest integer), and while any container instances are in the DRAINING state if the service contains tasks using the EC2 launch type. |
| deployment_config_minimum_healthy_percent |  | If a service is using the rolling update (ECS) deployment type, the minimum healthy percent represents a lower limit on the number of tasks in a service that must remain in the RUNNING state during a deployment, as a percentage of the desired number of tasks (rounded up to the nearest integer), and while any container instances are in the DRAINING state if the service contains tasks using the EC2 launch type. |
| desired_count |  | The desired number of instantiations of the task definition to keep running on the service. |
| enable_ecs_managed_tags |  | Determines whether to enable Amazon ECS managed tags for the tasks in the service. |
| enable_execute_command |  | Determines whether the execute command functionality is enabled for the service. |
| health_check_grace_period_seconds |  | The period of time, in seconds, that the Amazon ECS service scheduler ignores unhealthy Elastic Load Balancing target health checks after a task has first started. |
| launch_type |  | The launch type the service is using. |
| name |  | The name of your service. |
| pending_count |  | The number of tasks in the cluster that are in the PENDING state. |
| platform_family |  | The operating system that your tasks in the service run on. A platform family is specified only for tasks using the Fargate launch type. |
| platform_version |  | The platform version to run your service on. A platform version is only specified for tasks that are hosted on AWS Fargate. |
| propagate_tags |  | Determines whether to propagate the tags from the task definition or the service to the task. |
| region |  | The region of the service. |
| role_arn |  | The ARN of the IAM role that's associated with the service. |
| running_count |  | The number of tasks in the cluster that are in the RUNNING state. |
| status |  | The status of the service. |
| task_definition |  | The task definition to use for tasks in the service. |
| *_ont_name* | Yes | Normalized field sourced from `name`. |
| *_ont_region* | Yes | Normalized field sourced from `region`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |
| *_ont_status* | Yes | Normalized field sourced from `status`. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSECSService)`

- `(:AWSECSCluster)-[:HAS_SERVICE]->(:AWSECSService)`

- `(:AWSECSService)-[:HAS_TASK]->(:AWSECSTask)`

- `(:AWSECSService)-[:HAS_TASK_DEFINITION]->(:AWSECSTaskDefinition)`

- `(:AWSECSService)-[:WORKLOAD_PARENT]->(:AWSECSCluster)`

- `(:AWSECSTask)-[:WORKLOAD_PARENT]->(:AWSECSService)`

- `(:AWSELBV2TargetGroup)-[:TARGETS]->(:AWSECSService)`: Indicates that the target group routes traffic to an ECS service.
  - Properties:

    | Field | Description |
    |-------|-------------|
    | container_name | Name of the container reached through this relationship. |
    | container_port | Container port reached through this relationship. |

- `(:ComputeService)-[:HAS_RUNTIME_IMAGE]->(:Image)`: generated by analysis job `Workload HAS_RUNTIME_IMAGE inventory analysis`.
  - Properties:

    | Field | Description |
    |-------|-------------|
    | exposed_internet | Property generated by analysis job: `Workload HAS_RUNTIME_IMAGE inventory analysis`. |

### AWSECSTask

Representation of an AWS ECS [Task](https://docs.aws.amazon.com/AmazonECS/latest/APIReference/API_Task.html)

> **Ontology Mapping**: This node uses the ontology label [`ComputePod`](#ontology-computepod).

> **Additional Labels**: This node also uses `ECSTask`.

> **Additional Label Definitions**:
>
> - `ECSTask`: Compatibility label for the deprecated `ECSTask` aws node label. Use `AWSECSTask` instead. Scheduled for removal in v1.0.0.

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The ARN of the task |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| arn | Yes | The arn of the task. |
| availability_zone |  | The Availability Zone for the task. |
| capacity_provider_name |  | The capacity provider that's associated with the task. |
| cluster_arn |  | The ARN of the cluster that hosts the task. |
| connectivity |  | The connectivity status of a task. |
| connectivity_at |  | The Unix timestamp for the time when the task last went into CONNECTED status. |
| container_instance_arn |  | The ARN of the container instances that host the task. |
| cpu |  | The number of CPU units used by the task as expressed in a task definition. |
| created_at |  | The Unix timestamp for the time when the task was created. More specifically, it's for the time when the task entered the PENDING state. |
| desired_status |  | The desired status of the task. |
| enable_execute_command | Yes | Determines whether execute command functionality is enabled for this task. |
| ephemeral_storage_size_in_gib |  | The total amount, in GiB, of ephemeral storage to set for the task. |
| execution_stopped_at |  | The Unix timestamp for the time when the task execution stopped. |
| group |  | The name of the task group that's associated with the task. |
| health_status |  | The health status for the task. |
| last_status |  | The last known status for the task. |
| launch_type |  | The infrastructure where your task runs on. |
| memory |  | The amount of memory (in MiB) that the task uses as expressed in a task definition. |
| network_interface_id |  | The network interface ID for tasks running in awsvpc network mode. |
| platform_family |  | The operating system that your tasks are running on. |
| platform_version |  | The platform version where your task runs on. |
| pull_started_at |  | The Unix timestamp for the time when the container image pull began. |
| pull_stopped_at |  | The Unix timestamp for the time when the container image pull completed. |
| region |  | The region of the task. |
| service_name |  | Name of the ECS service that launched the task. |
| started_at |  | The Unix timestamp for the time when the task started. More specifically, it's for the time when the task transitioned from the PENDING state to the RUNNING state. |
| started_by |  | The tag specified when a task is started. If an Amazon ECS service started the task, the startedBy parameter contains the deployment ID of that service. |
| stop_code |  | The stop code indicating why a task was stopped. |
| stopped_at |  | The Unix timestamp for the time when the task was stopped. More specifically, it's for the time when the task transitioned from the RUNNING state to the STOPPED state. |
| stopped_reason |  | The reason that the task was stopped. |
| stopping_at |  | The Unix timestamp for the time when the task stops. More specifically, it's for the time when the task transitions from the RUNNING state to STOPPED. |
| task_definition_arn |  | The ARN of the task definition that creates the task. |
| version |  | The version counter for the task. |
| *_ont_source* |  | Module that populated this node's ontology fields. |
| *_ont_status* | Yes | Normalized field sourced from `last_status`. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSECSTask)`

- `(:AWSECSCluster)-[:HAS_TASK]->(:AWSECSTask)`

- `(:AWSECSContainer)-[:WORKLOAD_PARENT]->(:AWSECSTask)`

- `(:AWSECSContainerInstance)-[:HAS_TASK]->(:AWSECSTask)`

- `(:AWSECSService)-[:HAS_TASK]->(:AWSECSTask)`

- `(:AWSECSTask)-[:HAS_CONTAINER]->(:AWSECSContainer)`

- `(:AWSECSTask)-[:HAS_TASK_DEFINITION]->(:AWSECSTaskDefinition)`

- `(:AWSECSTask)-[:NETWORK_INTERFACE]->(:AWSNetworkInterface)`

- `(:AWSECSTask)-[:TAGGED]->(:AWSTag)`: `AWSECSTask` is tagged with an `AWSTag` discovered by the AWS Resource Groups Tagging API.

- `(:AWSECSTask)-[:WORKLOAD_PARENT]->(:AWSECSCluster)`

- `(:AWSECSTask)-[:WORKLOAD_PARENT]->(:AWSECSService)`

- `(:AWSPrincipal)-[:CAN_EXECUTE_COMMAND]->(:AWSECSTask)`: `AWSPrincipal` receives evaluated `CAN_EXECUTE_COMMAND` access to `AWSECSTask` from AWS IAM policies.
  - Evaluated permissions: `ecs:ExecuteCommand`
  - Properties:

    | Field | Description |
    |-------|-------------|
    | condition_keys | IAM condition context keys used by the permission. |
    | conditions | IAM conditions that restrict this permission. |
    | has_condition | Whether an IAM condition restricts this permission. |

### AWSECSTaskDefinition

Representation of an AWS ECS [Task Definition](https://docs.aws.amazon.com/AmazonECS/latest/APIReference/API_TaskDefinition.html)

> **Additional Labels**: This node also uses `ECSTaskDefinition`.

> **Additional Label Definitions**:
>
> - `ECSTaskDefinition`: Compatibility label for the deprecated `ECSTaskDefinition` aws node label. Use `AWSECSTaskDefinition` instead. Scheduled for removal in v1.0.0.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The ARN of the task definition |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| arn | Yes | Amazon Resource Name (ARN) of this `AWSECSTaskDefinition` node. |
| compatibilities |  | The task launch types the task definition validated against during task definition registration. |
| cpu |  | The number of cpu units used by the task. |
| deregistered_at |  | The Unix timestamp for the time when the task definition was deregistered. |
| ephemeral_storage_size_in_gib |  | The total amount, in GiB, of ephemeral storage to set for the task. |
| execution_role_arn |  | The Amazon Resource Name (ARN) of the task execution role that grants the Amazon ECS container agent permission to make AWS API calls on your behalf. |
| family |  | The name of a family that this task definition is registered to. |
| ipc_mode |  | The IPC resource namespace to use for the containers in the task. |
| memory |  | The amount (in MiB) of memory used by the task. |
| network_mode |  | The Docker networking mode to use for the containers in the task. The valid values are none, bridge, awsvpc, and host. If no network mode is specified, the default is bridge. |
| pid_mode |  | The process namespace to use for the containers in the task. |
| proxy_configuration_container_name |  | The name of the container that will serve as the App Mesh proxy. |
| proxy_configuration_type |  | The proxy type. |
| region |  | The region of the task definition. |
| registered_at |  | The Unix timestamp for the time when the task definition was registered. |
| registered_by |  | The principal that registered the task definition. |
| requires_compatibilities |  | The task launch types the task definition was validated against. |
| revision |  | The revision of the task in a particular family. |
| runtime_platform_cpu_architecture |  | The CPU architecture. |
| runtime_platform_operating_system_family |  | The operating system. |
| status |  | The status of the task definition. |
| task_role_arn |  | The short name or full Amazon Resource Name (ARN) of the AWS Identity and Access Management role that grants containers in the task permission to call AWS APIs on your behalf. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSECSTaskDefinition)`

- `(:AWSECSService)-[:HAS_TASK_DEFINITION]->(:AWSECSTaskDefinition)`

- `(:AWSECSTask)-[:HAS_TASK_DEFINITION]->(:AWSECSTaskDefinition)`

- `(:AWSECSTaskDefinition)-[:HAS_CONTAINER_DEFINITION]->(:AWSECSContainerDefinition)`

- `(:AWSECSTaskDefinition)-[:HAS_EXECUTION_ROLE]->(:AWSRole)`

- `(:AWSECSTaskDefinition)-[:HAS_TASK_ROLE]->(:AWSRole)`

- `(:AWSECSTaskDefinition)-[:TAGGED]->(:AWSTag)`: `AWSECSTaskDefinition` is tagged with an `AWSTag` discovered by the AWS Resource Groups Tagging API.

### AWSEfsAccessPoint

Representation of an AWS [EFS Access Point](https://docs.aws.amazon.com/efs/latest/ug/API_AccessPointDescription.html)

> **Additional Labels**: This node also uses `EfsAccessPoint`.

> **Additional Label Definitions**:
>
> - `EfsAccessPoint`: Compatibility label for the deprecated `EfsAccessPoint` aws node label. Use `AWSEfsAccessPoint` instead. Scheduled for removal in v1.0.0.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | System-assigned access point ARN |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| access_point_id |  | The ID of the access point, assigned by Amazon EFS |
| arn | Yes | The unique Amazon Resource Name (ARN) associated with the access point |
| file_system_id |  | The ID of the EFS file system that the access point applies to |
| lifecycle_state |  | Identifies the lifecycle phase of the access point |
| name |  | The name of the access point |
| owner_id |  | AWS account ID that owns the resource |
| posix_gid |  | The POSIX group ID used for all file system operations using this access point |
| posix_uid |  | The POSIX user ID used for all file system operations using this access point |
| region |  | The region of the access point |
| root_directory_path |  | Specifies the path on the EFS file system to expose as the root directory to NFS clients using the access point to access the EFS file system |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSEfsAccessPoint)`

- `(:AWSEfsAccessPoint)-[:ACCESS_POINT_OF]->(:AWSEfsFileSystem)`

### AWSEfsFileSystem

Representation of an AWS [EFS File System](https://docs.aws.amazon.com/efs/latest/ug/API_FileSystemDescription.html)

> **Ontology Mapping**: This node uses the ontology label [`FileStorage`](#ontology-filestorage).

> **Additional Labels**: This node also uses `EfsFileSystem`.

> **Additional Label Definitions**:
>
> - `EfsFileSystem`: Compatibility label for the deprecated `EfsFileSystem` aws node label. Use `AWSEfsFileSystem` instead. Scheduled for removal in v1.0.0.

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The ID of the file system, assigned by Amazon EFS |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| arn | Yes | Amazon Resource Name (ARN) for the EFS file system |
| availability_zone_id |  | The unique and consistent identifier of the Availability Zone in which the file system is located |
| availability_zone_name |  | Describes the AWS Availability Zone in which the file system is located |
| creation_time |  | The time that the file system was created, in seconds |
| creation_token |  | The opaque string specified in the request |
| encrypted |  | A Boolean value that, if true, indicates that the file system is encrypted |
| file_system_protection |  | Describes the protection on the file system |
| kms_key_id |  | The ID of an AWS KMS key used to protect the encrypted file system |
| lifecycle_state |  | The lifecycle phase of the file system |
| name |  | If the file system has a name tag, Amazon EFS returns the value in this field |
| number_of_mount_targets |  | The current number of mount targets that the file system has |
| owner_id |  | The AWS account that created the file system |
| performance_mode |  | The performance mode of the file system |
| region |  | The region of the file system |
| size_in_bytes_timestamp |  | Time at which that size was determined |
| size_in_bytes_value |  | Latest known metered size (in bytes) of data stored in the file system |
| throughput_mode |  | Displays the file system's throughput mode |
| *_ont_encrypted* | Yes | Normalized field sourced from `encrypted`. |
| *_ont_location* | Yes | Normalized field sourced from `region`. |
| *_ont_name* | Yes | Normalized field sourced from `name`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSEfsFileSystem)`

- `(:AWSEfsAccessPoint)-[:ACCESS_POINT_OF]->(:AWSEfsFileSystem)`

- `(:AWSEfsFileSystem)-[:ENCRYPTED_BY]->(:AWSKMSKey)`

- `(:AWSEfsMountTarget)-[:ATTACHED_TO]->(:AWSEfsFileSystem)`

### AWSEfsMountTarget

Representation of an AWS [EFS Mount Target](https://docs.aws.amazon.com/efs/latest/ug/API_MountTargetDescription.html)

> **Additional Labels**: This node also uses `EfsMountTarget`.

> **Additional Label Definitions**:
>
> - `EfsMountTarget`: Compatibility label for the deprecated `EfsMountTarget` aws node label. Use `AWSEfsMountTarget` instead. Scheduled for removal in v1.0.0.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | System-assigned mount target ID |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| arn | Yes | System-assigned mount target ID |
| availability_zone_id |  | The unique and consistent identifier of the Availability Zone that the mount target resides in |
| availability_zone_name |  | The name of the Availability Zone in which the mount target is located |
| fileSystem_id |  | The ID of the file system for which the mount target is intended |
| ip_address |  | Address at which the file system can be mounted by using the mount target |
| lifecycle_state |  | Lifecycle state of the mount target |
| mount_target_id |  | System-assigned mount target ID |
| network_interface_id |  | The ID of the network interface that Amazon EFS created when it created the mount target |
| owner_id |  | AWS account ID that owns the resource |
| region |  | The region of the mount target |
| subnet_id |  | The ID of the mount target's subnet |
| vpc_id |  | The virtual private cloud (VPC) ID that the mount target is configured in |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSEfsMountTarget)`

- `(:AWSEfsMountTarget)-[:ATTACHED_TO]->(:AWSEfsFileSystem)`

### AWSEKSAccessEntry

Representation of an AWS [EKS Access Entry](https://docs.aws.amazon.com/eks/latest/userguide/access-entries.html), which grants an IAM principal access to an EKS cluster through the EKS API authentication mode.

> **Additional Labels**: This node also uses `EKSAccessEntry`.

> **Additional Label Definitions**:
>
> - `EKSAccessEntry`: Compatibility label for the deprecated `EKSAccessEntry` aws node label. Use `AWSEKSAccessEntry` instead. Scheduled for removal in v1.0.0.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | EKS access entry ARN. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| arn | Yes | EKS access entry ARN. |
| cluster_name |  | Name of the EKS cluster that contains the access entry. |
| created_at |  | Timestamp when the access entry was created. |
| kubernetes_groups |  | Kubernetes groups assigned to the IAM principal. |
| modified_at |  | Timestamp when the access entry was last modified. |
| principal_arn | Yes | ARN of the IAM principal granted cluster access. |
| type |  | EKS access entry type. |
| username |  | Kubernetes username associated with the IAM principal. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSEKSAccessEntry)`: An EKS access entry is a resource within an AWS account.

- `(:AWSEKSCluster)-[:HAS_ACCESS_ENTRY]->(:AWSEKSAccessEntry)`: An EKS cluster contains an access entry.

- `(:AWSPrincipal)-[:GRANTED_ACCESS_TO]->(:AWSEKSAccessEntry)`: An AWS principal is granted cluster access through an EKS access entry.

### AWSEKSCluster

Representation of an AWS [EKS Cluster](https://docs.aws.amazon.com/eks/latest/APIReference/API_Cluster.html).

> **Ontology Mapping**: This node uses the ontology label [`ComputeCluster`](#ontology-computecluster).

> **Additional Labels**: This node also uses `EKSCluster`.

> **Additional Label Definitions**:
>
> - `EKSCluster`: Compatibility label for the deprecated `EKSCluster` aws node label. Use `AWSEKSCluster` instead. Scheduled for removal in v1.0.0.

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | same as `arn` |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| arn | Yes | AWS-unique identifier for this object |
| audit_logging |  | Whether audit logging is enabled |
| authentication_mode |  | Authentication mode used by the EKS cluster |
| certificate_authority_authority_key_identifier |  | Authority Key Identifier (AKI) extension key identifier value in hex if present. `null` when the extension or key identifier is absent |
| certificate_authority_data_present |  | Whether the EKS API server certificate authority data was returned by AWS |
| certificate_authority_issuer |  | Issuer DN of the EKS API server certificate authority certificate |
| certificate_authority_not_after |  | Certificate validity end time (Neo4j datetime) |
| certificate_authority_not_before |  | Certificate validity start time (Neo4j datetime) |
| certificate_authority_parse_error |  | Parse/decode error message when certificate authority data cannot be parsed |
| certificate_authority_parse_status |  | Parse status of the certificate authority data (`parsed`, `missing`, `invalid_base64`, `invalid_certificate`) |
| certificate_authority_sha256_fingerprint | Yes | SHA256 fingerprint of the decoded EKS API server certificate authority certificate |
| certificate_authority_subject |  | Subject DN of the EKS API server certificate authority certificate |
| certificate_authority_subject_key_identifier |  | Subject Key Identifier (SKI) extension value in hex if present. `null` when the extension is absent (not derived from the public key) |
| created_at |  | The date and time the cluster was created |
| endpoint |  | The endpoint for the Kubernetes API server. |
| endpoint_public_access | Yes | Indicates whether the Amazon EKS public API server endpoint is enabled |
| exposed_internet | Yes | Set to True if the EKS Cluster public API server endpoint is enabled |
| name | Yes | Name of the EKS Cluster |
| platform_version |  | Version of EKS |
| region |  | The AWS region |
| rolearn |  | The ARN of the IAM role that provides permissions for the Kubernetes control plane to make calls to AWS API |
| status |  | Status of the cluster. Valid Values: creating, active, deleting, failed, updating |
| version |  | Kubernetes version running |
| *_ont_control_plane_public_access* | Yes | Normalized field sourced from `endpoint_public_access`. |
| *_ont_endpoint* | Yes | Normalized field sourced from `endpoint`. |
| *_ont_name* | Yes | Normalized field sourced from `name`. |
| *_ont_region* | Yes | Normalized field sourced from `region`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |
| *_ont_status* | Yes | Normalized field sourced from `status`. |
| *_ont_version* | Yes | Normalized field sourced from `version`. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSEKSCluster)`

- `(:AWSEC2Instance)-[:MEMBER_OF_EKS_CLUSTER]->(:AWSEKSCluster)`

- `(:AWSEKSCluster)-[:HAS_ACCESS_ENTRY]->(:AWSEKSAccessEntry)`: An EKS cluster contains an access entry.

- `(:AWSEKSCluster)-[:MAPS_TO]->(:KubernetesCluster)`: Links an EKS cluster to the Kubernetes cluster it hosts.

- `(:AWSEKSCluster)-[:TAGGED]->(:AWSTag)`: `AWSEKSCluster` is tagged with an `AWSTag` discovered by the AWS Resource Groups Tagging API.

- `(:AWSGuardDutyFinding)-[:AFFECTS]->(:AWSEKSCluster)`

### AWSElasticacheCluster

Representation of an AWS [ElastiCache Cluster](https://docs.aws.amazon.com/AmazonElastiCache/latest/APIReference/API_CacheCluster.html).

> **Additional Labels**: This node also uses `ElasticacheCluster`.

> **Additional Label Definitions**:
>
> - `ElasticacheCluster`: Compatibility label for the deprecated `ElasticacheCluster` aws node label. Use `AWSElasticacheCluster` instead. Scheduled for removal in v1.0.0.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Same as ARN |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| arn | Yes | The Amazon Resource Name (ARN) for the ElastiCache cluster |
| at_rest_encryption_enabled |  | Indicates whether the cache cluster is encrypted at rest |
| auth_token_enabled |  | Indicates whether an authentication token is enabled for the cache cluster |
| auto_minor_version_upgrade |  | Indicates whether minor version patches are applied automatically |
| cache_cluster_create_time |  | The date and time when the cache cluster was created |
| cache_cluster_id |  | The unique identifier for the cache cluster |
| cache_cluster_status |  | The current state of the cache cluster |
| cache_node_type |  | The compute and memory capacity of the nodes in the cluster |
| cache_subnet_group_name |  | The name of the cache subnet group associated with the cache cluster |
| engine |  | The name of the cache engine (redis, memcached) |
| engine_version |  | The version of the cache engine |
| num_cache_nodes |  | The number of cache nodes in the cluster |
| preferred_availability_zone |  | The name of the Availability Zone in which the cache cluster is located |
| preferred_maintenance_window |  | The weekly time range during which maintenance on the cache cluster is performed |
| region |  | The AWS region where the cache cluster is located |
| replication_group_id |  | The replication group to which this cache cluster belongs |
| snapshot_retention_limit |  | The number of days for which ElastiCache will retain automatic cache cluster snapshots |
| snapshot_window |  | The daily time range during which ElastiCache will take a snapshot of the cache cluster |
| topic_arn |  | The ARN of the SNS topic to which notifications are sent |
| transit_encryption_enabled |  | Indicates whether the cache cluster is encrypted in transit |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSElasticacheCluster)`

- `(:AWSElasticacheCluster)-[:TAGGED]->(:AWSTag)`: `AWSElasticacheCluster` is tagged with an `AWSTag` discovered by the AWS Resource Groups Tagging API.

- `(:AWSElasticacheTopic)-[:CACHE_CLUSTER]->(:AWSElasticacheCluster)`

### AWSElasticacheTopic

Representation of the SNS topic an ElastiCache cluster publishes to, as reported by the cluster's [NotificationConfiguration](https://docs.aws.amazon.com/AmazonElastiCache/latest/APIReference/API_NotificationConfiguration.html).

> **Additional Labels**: This node also uses `ElasticacheTopic`.

> **Additional Label Definitions**:
>
> - `ElasticacheTopic`: Compatibility label for the deprecated `ElasticacheTopic` aws node label. Use `AWSElasticacheTopic` instead. Scheduled for removal in v1.0.0.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Same as ARN |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| arn | Yes | The Amazon Resource Name (ARN) for the SNS topic |
| status |  | The status of the SNS topic (active, inactive) |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSElasticacheTopic)`

- `(:AWSElasticacheTopic)-[:CACHE_CLUSTER]->(:AWSElasticacheCluster)`

### AWSElasticIPAddress

Representation of an AWS EC2 [Elastic IP address](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_Address.html)

> **Additional Labels**: This node also uses `ElasticIPAddress`.

> **Additional Label Definitions**:
>
> - `ElasticIPAddress`: Compatibility label for the deprecated `ElasticIPAddress` aws node label. Use `AWSElasticIPAddress` instead. Scheduled for removal in v1.0.0.

> **Ontology Projection**: `AWSElasticIPAddress` contributes data to canonical [`PublicIP`](#ontology-publicip) nodes.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The Elastic IP address |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| allocation_id |  | The ID representing the allocation of the address for use with EC2-VPC. |
| association_id |  | The ID representing the association of the address with an instance in a VPC. |
| carrier_ip |  | The carrier IP address associated. This option is only available for network interfaces which reside in a subnet in a Wavelength Zone (for example an EC2 instance). |
| customer_owned_ip |  | The customer-owned IP address. |
| customer_owned_ipv4_pool |  | The ID of the customer-owned address pool. |
| domain |  | Indicates whether this Elastic IP address is for use with instances in EC2-Classic (standard) or instances in a VPC (vpc). |
| instance_id |  | The ID of the instance that the address is associated with (if any). |
| network_border_group |  | The name of the unique set of Availability Zones, Local Zones, or Wavelength Zones from which AWS advertises IP addresses. |
| network_interface_id |  | The ID of the network interface. |
| network_interface_owner_id |  | Identifier of the network interface owner linked to this `AWSElasticIPAddress` node. |
| private_ip_address |  | The private IP address associated with the Elastic IP address. |
| public_ip | Yes | The Elastic IP address. |
| public_ipv4_pool |  | The ID of an address pool. |
| region |  | The region of the IP. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSElasticIPAddress)`

- `(:AWSDNSRecord)-[:DNS_POINTS_TO]->(:AWSElasticIPAddress)`

- `(:AWSEC2Instance)-[:ELASTIC_IP_ADDRESS]->(:AWSElasticIPAddress)`

- `(:AWSElasticIPAddress)-[:TAGGED]->(:AWSTag)`: `AWSElasticIPAddress` is tagged with an `AWSTag` discovered by the AWS Resource Groups Tagging API.

- `(:AWSNetworkInterface)-[:ELASTIC_IP_ADDRESS]->(:AWSElasticIPAddress)`

- `(:PublicIP)-[:RESERVED_BY]->(:AWSElasticIPAddress)`

### AWSELBListener

Representation of an AWS Elastic Load Balancer [Listener](https://docs.aws.amazon.com/elasticloadbalancing/2012-06-01/APIReference/API_Listener.html).  Here, an AWSELBListener is a more specific type of Endpoint.  Here'a [good introduction](https://docs.aws.amazon.com/elasticloadbalancing/2012-06-01/APIReference/Welcome.html).

> **Additional Labels**: This node also uses `ELBListener`, `Endpoint`.

> **Additional Label Definitions**:
>
> - `ELBListener`: Compatibility label for the deprecated `ELBListener` aws node label. Use `AWSELBListener` instead. Scheduled for removal in v1.0.0.
> - `Endpoint`: A aws node participating in the shared Endpoint graph interface.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Unique identifier for this `AWSELBListener` node. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| instance_port |  | Backend instance port to which the listener forwards traffic. |
| instance_protocol |  | Protocol used to forward listener traffic to backend instances. |
| policy_names |  | Names of load balancer policies enabled on the listener. |
| port |  | Load balancer port on which the listener accepts connections. |
| protocol |  | Protocol used by the load balancer listener. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSELBListener)`

- `(:AWSLoadBalancer)-[:ELB_LISTENER]->(:AWSELBListener)`

### AWSELBV2Listener

Representation of an AWS Elastic Load Balancer V2 [Listener](https://docs.aws.amazon.com/elasticloadbalancing/latest/APIReference/API_Listener.html).

> **Additional Labels**: This node also uses `ELBV2Listener`, `Endpoint`.

> **Additional Label Definitions**:
>
> - `ELBV2Listener`: Compatibility label for the deprecated `ELBV2Listener` aws node label. Use `AWSELBV2Listener` instead. Scheduled for removal in v1.0.0.
> - `Endpoint`: A aws node participating in the shared Endpoint graph interface.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Unique identifier for this `AWSELBV2Listener` node. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| advertise_trust_store_ca_names |  | Whether the listener advertises certificate-authority names from its trust store. |
| ignore_client_certificate_expiry |  | Whether this `AWSELBV2Listener` node ignores client certificate expiry. |
| mutual_authentication_mode |  | Mutual TLS authentication mode configured on the listener. |
| port |  | Port on which the listener or target group receives traffic. |
| protocol |  | Protocol used by the listener or target group. |
| ssl_policy |  | TLS security policy configured on the listener. |
| targetgrouparn |  | ARN of the targetgrouparn linked to this `AWSELBV2Listener` node. |
| trust_store_arn |  | ARN of the trust store linked to this `AWSELBV2Listener` node. |
| trust_store_association_status |  | Current status of the listener trust-store association. |

#### Relationships

- `(:AWSACMCertificate)-[:USED_BY]->(:AWSELBV2Listener)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSELBV2Listener)`

- `(:AWSLoadBalancerV2)-[:ELBV2_LISTENER]->(:AWSELBV2Listener)`

### AWSELBV2TargetGroup

Representation of an AWS Elastic Load Balancing v2 [Target Group](https://docs.aws.amazon.com/elasticloadbalancing/latest/APIReference/API_TargetGroup.html).

> **Additional Labels**: This node also uses `ELBV2TargetGroup`.

> **Additional Label Definitions**:
>
> - `ELBV2TargetGroup`: Compatibility label for the deprecated `ELBV2TargetGroup` aws node label. Use `AWSELBV2TargetGroup` instead. Scheduled for removal in v1.0.0.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Unique identifier for this `AWSELBV2TargetGroup` node. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| arn | Yes | Amazon Resource Name (ARN) of this `AWSELBV2TargetGroup` node. |
| name |  | Name of this `AWSELBV2TargetGroup` node. |
| port |  | Port on which the listener or target group receives traffic. |
| protocol |  | Protocol used by the listener or target group. |
| region |  | AWS Region containing this `AWSELBV2TargetGroup` node. |
| target_type |  | Type of resource registered as a target in the target group. |
| vpc_id |  | Identifier of the VPC linked to this `AWSELBV2TargetGroup` node. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSELBV2TargetGroup)`

- `(:AWSELBV2TargetGroup)-[:TARGETS]->(:AWSECSService)`: Indicates that the target group routes traffic to an ECS service.
  - Properties:

    | Field | Description |
    |-------|-------------|
    | container_name | Name of the container reached through this relationship. |
    | container_port | Container port reached through this relationship. |

- `(:AWSLoadBalancerV2)-[:ELBV2_TARGET_GROUP]->(:AWSELBV2TargetGroup)`

### AWSEMRCluster

Representation of an AWS [EMR Cluster](https://docs.aws.amazon.com/emr/latest/APIReference/API_Cluster.html).

> **Ontology Mapping**: This node uses the ontology label [`ComputeCluster`](#ontology-computecluster).

> **Additional Labels**: This node also uses `EMRCluster`.

> **Additional Label Definitions**:
>
> - `EMRCluster`: Compatibility label for the deprecated `EMRCluster` aws node label. Use `AWSEMRCluster` instead. Scheduled for removal in v1.0.0.

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The Id of the EMR Cluster. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| arn | Yes | AWS-unique identifier for this object |
| auto_terminate |  | Specifies whether the cluster should terminate after completing all steps. |
| autoscaling_role |  | An IAM role for automatic scaling policies. |
| custom_ami_id |  | The ID of a custom Amazon EBS-backed Linux AMI if the cluster uses a custom AMI. |
| instance_collection_type |  | The instance group configuration of the cluster. A value of INSTANCE\_GROUP indicates a uniform instance group configuration. A value of INSTANCE\_FLEET indicates an instance fleets configuration. |
| log_encryption_kms_key_id |  | The KMS key used for encrypting log files. |
| log_uri |  | The path to the Amazon S3 location where logs for this cluster are stored. |
| master_public_dns_name |  | The DNS name of the master node. If the cluster is on a private subnet, this is the private DNS name. On a public subnet, this is the public DNS name. |
| name |  | Name of this `AWSEMRCluster` node. |
| outpost_arn |  | The Amazon Resource Name (ARN) of the Outpost where the cluster is launched. |
| region |  | The AWS region |
| release_label |  | The Amazon EMR release label, which determines the version of open-source application packages installed on the cluster. |
| repo_upgrade_on_boot |  | Specifies the type of updates that are applied from the Amazon Linux AMI package repositories when an instance boots using the AMI. |
| requested_ami_version |  | The AMI version requested for this cluster. |
| running_ami_version |  | The AMI version running on this cluster. |
| scale_down_behavior |  | The way that individual Amazon EC2 instances terminate when an automatic scale-in activity occurs or an instance group is resized. |
| security_configuration |  | The name of the security configuration applied to the cluster. |
| servicerole |  | Service Role of the EMR Cluster |
| termination_protected |  | Indicates whether Amazon EMR will lock the cluster to prevent the EC2 instances from being terminated by an API call or user intervention, or in the event of a cluster error. |
| visible_to_all_users |  | Indicates whether the cluster is visible to IAM principals in the Amazon Web Services account associated with the cluster. |
| *_ont_name* | Yes | Normalized field sourced from `name`. |
| *_ont_region* | Yes | Normalized field sourced from `region`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |
| *_ont_version* | Yes | Normalized field sourced from `release_label`. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSEMRCluster)`

- `(:AWSEMRCluster)-[:TAGGED]->(:AWSTag)`: `AWSEMRCluster` is tagged with an `AWSTag` discovered by the AWS Resource Groups Tagging API.

### AWSESDomain

Representation of an AWS [ElasticSearch Domain](https://docs.aws.amazon.com/elasticsearch-service/latest/developerguide/es-configuration-api.html#es-configuration-api-datatypes) (see ElasticsearchDomainConfig).

For domains with multiple subnets or security groups, the data should be
flattened so each combination is a separate row.

> **Ontology Mapping**: This node uses the ontology label [`Database`](#ontology-database).

> **Additional Labels**: This node also uses `ESDomain`.

> **Additional Label Definitions**:
>
> - `ESDomain`: Compatibility label for the deprecated `ESDomain` aws node label. Use `AWSESDomain` instead. Scheduled for removal in v1.0.0.

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Unique identifier for this `AWSESDomain` node. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| arn | Yes | Amazon Resource Name (ARN) of this `AWSESDomain` node. |
| created |  | Whether this `AWSESDomain` node has been created. |
| deleted |  | Whether this `AWSESDomain` node is marked as deleted. |
| domainid | Yes | Identifier of the domain linked to this `AWSESDomain` node. |
| ebs_options_ebsenabled |  | Whether ebs options ebs is enabled for this `AWSESDomain` node. |
| ebs_options_iops |  | Provisioned IOPS configured for each search data-node volume. |
| ebs_options_volumesize |  | EBS storage size in GiB allocated to each search data node. |
| ebs_options_volumetype |  | EBS volume type attached to each search data node. |
| elasticsearch_cluster_config_dedicatedmastercount |  | Number of dedicated master nodes in the search cluster. |
| elasticsearch_cluster_config_dedicatedmasterenabled |  | Whether elasticsearch cluster config dedicated master is enabled for this `AWSESDomain` node. |
| elasticsearch_cluster_config_dedicatedmastertype |  | EC2 instance type used by dedicated master nodes. |
| elasticsearch_cluster_config_instancecount |  | Number of data-node instances in the search cluster. |
| elasticsearch_cluster_config_instancetype |  | EC2 instance type used by data nodes in the search cluster. |
| elasticsearch_cluster_config_zoneawarenessenabled |  | Whether elasticsearch cluster config zone awareness is enabled for this `AWSESDomain` node. |
| elasticsearch_version |  | Elasticsearch engine version running on the domain. |
| encryption_at_rest_options_enabled |  | Whether encryption at rest options is enabled for this `AWSESDomain` node. |
| encryption_at_rest_options_kms_key_id |  | Identifier of the encryption at rest options KMS key linked to this `AWSESDomain` node. |
| endpoint |  | Network endpoint used to access the search domain. |
| engine |  | Search engine family running on the domain. |
| exposed_internet |  | Whether this `AWSESDomain` node is exposed to the public internet. |
| log_publishing_audit_logs_arn |  | ARN of the log publishing audit logs linked to this `AWSESDomain` node. |
| log_publishing_audit_logs_enabled |  | Whether log publishing audit logs is enabled for this `AWSESDomain` node. |
| log_publishing_es_application_logs_arn |  | ARN of the log publishing Elasticsearch application logs linked to this `AWSESDomain` node. |
| log_publishing_es_application_logs_enabled |  | Whether log publishing elasticsearch application logs is enabled for this `AWSESDomain` node. |
| log_publishing_index_slow_logs_arn |  | ARN of the log publishing index slow logs linked to this `AWSESDomain` node. |
| log_publishing_index_slow_logs_enabled |  | Whether log publishing index slow logs is enabled for this `AWSESDomain` node. |
| log_publishing_search_slow_logs_arn |  | ARN of the log publishing search slow logs linked to this `AWSESDomain` node. |
| log_publishing_search_slow_logs_enabled |  | Whether log publishing search slow logs is enabled for this `AWSESDomain` node. |
| name | Yes | Name of this `AWSESDomain` node. |
| *_ont_encrypted* | Yes | Normalized field sourced from `encryption_at_rest_options_enabled`. |
| *_ont_endpoint* | Yes | Normalized field sourced from `endpoint`. |
| *_ont_name* | Yes | Normalized field sourced from `name`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |
| *_ont_type* | Yes | Normalized field sourced from `engine`. |
| *_ont_version* | Yes | Normalized field sourced from `elasticsearch_version`. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSESDomain)`

- `(:AWSDNSRecord)-[:DNS_POINTS_TO]->(:AWSESDomain)`

- `(:AWSESDomain)-[:MEMBER_OF_EC2_SECURITY_GROUP]->(:AWSEC2SecurityGroup)`

- `(:AWSESDomain)-[:PART_OF_SUBNET]->(:AWSEC2Subnet)`

- `(:AWSESDomain)-[:TAGGED]->(:AWSTag)`: `AWSESDomain` is tagged with an `AWSTag` discovered by the AWS Resource Groups Tagging API.

### AWSEventBridgeRule

Representation of an AWS [EventBridge Rule](https://docs.aws.amazon.com/eventbridge/latest/APIReference/API_ListRules.html)

> **Additional Labels**: This node also uses `EventBridgeRule`.

> **Additional Label Definitions**:
>
> - `EventBridgeRule`: Compatibility label for the deprecated `EventBridgeRule` aws node label. Use `AWSEventBridgeRule` instead. Scheduled for removal in v1.0.0.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | System-assigned eventbridge rule ID |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| arn | Yes | The Amazon Resource Name (ARN) of the rule |
| description |  | The description of the rule |
| event_bus_name |  | The name or ARN of the event bus associated with the rule |
| event_pattern |  | The event pattern of the rule |
| managed_by |  | If the rule was created on behalf of your account by an AWS service, this field displays the principal name of the service that created the rule |
| name |  | The name of the rule |
| region |  | The region of the rule |
| role_arn |  | The Amazon Resource Name (ARN) of the role that is used for target invocation |
| schedule_expression |  | The scheduling expression |
| state |  | The state of the rule, Valid Values: ENABLED, DISABLED, ENABLED_WITH_ALL_CLOUDTRAIL_MANAGEMENT_EVENTS |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSEventBridgeRule)`

- `(:AWSEventBridgeRule)-[:ASSOCIATED_WITH]->(:AWSRole)`

- `(:AWSEventBridgeTarget)-[:LINKED_TO_RULE]->(:AWSEventBridgeRule)`

### AWSEventBridgeTarget

Representation of an AWS [EventBridge Target](https://docs.aws.amazon.com/eventbridge/latest/APIReference/API_ListTargetsByRule.html)

> **Additional Labels**: This node also uses `EventBridgeTarget`.

> **Additional Label Definitions**:
>
> - `EventBridgeTarget`: Compatibility label for the deprecated `EventBridgeTarget` aws node label. Use `AWSEventBridgeTarget` instead. Scheduled for removal in v1.0.0.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | System-assigned eventbridge target ID |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| arn | Yes | The Amazon Resource Name (ARN) of the target |
| region |  | The region of the target |
| role_arn |  | The Amazon Resource Name (ARN) of the role that is used for target invocation |
| rule_arn |  | The arn of the rule which is associated with target |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSEventBridgeTarget)`

- `(:AWSEventBridgeTarget)-[:LINKED_TO_RULE]->(:AWSEventBridgeRule)`

### AWSFederatedPrincipal

Representation of a federated principal e.g. "arn:aws:iam::123456789012:saml-provider/my-saml-provider". Federated principals are used for authentication to AWS using SAML or OpenID Connect. Federated principals are only discoverable from AWS role trust relationships.

> **Additional Labels**: This node also uses `AWSPrincipal`.

> **Additional Label Definitions**:
>
> - `AWSPrincipal`: A aws node participating in the shared AWSPrincipal graph interface.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Unique identifier for this `AWSFederatedPrincipal` node. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| arn | Yes | Amazon Resource Name (ARN) of this `AWSFederatedPrincipal` node. |
| type |  | Type of this `AWSFederatedPrincipal` node. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSFederatedPrincipal)`

### AWSGlueConnection

Representation of an AWS [Glue Connection](https://docs.aws.amazon.com/glue/latest/webapi/API_GetConnections.html)

> **Additional Labels**: This node also uses `GlueConnection`.

> **Additional Label Definitions**:
>
> - `GlueConnection`: Compatibility label for the deprecated `GlueConnection` aws node label. Use `AWSGlueConnection` instead. Scheduled for removal in v1.0.0.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The name of the Glue connection definition |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| arn | Yes | The name of the Glue connection definition |
| authentication_type |  | A structure containing the authentication configuration |
| connection_type |  | The type of the connection. Currently, SFTP is not supported |
| description |  | The description of the connection |
| region |  | The region of the Glue Connection |
| secret_arn |  | The secret manager ARN to store credentials |
| status |  | The status of the connection. Can be one of: READY, IN_PROGRESS, or FAILED |
| status_reason |  | The reason for the connection status |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSGlueConnection)`

- `(:AWSGlueJob)-[:USES]->(:AWSGlueConnection)`

### AWSGlueJob

Representation of an AWS [Glue Job](https://docs.aws.amazon.com/glue/latest/webapi/API_GetJobs.html)

> **Additional Labels**: This node also uses `GlueJob`.

> **Additional Label Definitions**:
>
> - `GlueJob`: Compatibility label for the deprecated `GlueJob` aws node label. Use `AWSGlueJob` instead. Scheduled for removal in v1.0.0.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The name you assign to this job definition |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| arn | Yes | The name you assign to this job definition |
| connections |  | The connections used for this job |
| description |  | The description of the job |
| job_mode |  | A mode that describes how a job was created |
| profile_name |  | The name of an AWS Glue usage profile associated with the job |
| region |  | The region of the Glue job |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSGlueJob)`

- `(:AWSGlueJob)-[:USES]->(:AWSGlueConnection)`

### AWSGroup

Representation of AWS [IAM Groups](https://docs.aws.amazon.com/IAM/latest/APIReference/API_Group.html).

> **Ontology Mapping**: This node uses the ontology label [`UserGroup`](#ontology-usergroup).

> **Additional Labels**: This node also uses `AWSPrincipal`.

> **Additional Label Definitions**:
>
> - `AWSPrincipal`: A aws node participating in the shared AWSPrincipal graph interface.

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Unique identifier for this `AWSGroup` node. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| arn | Yes | Amazon Resource Name (ARN) of this `AWSGroup` node. |
| createdate |  | Timestamp when the IAM group was created. |
| createdate_dt |  | Creation timestamp for the IAM group normalized as a Neo4j datetime. |
| groupid |  | Identifier of the group linked to this `AWSGroup` node. |
| name |  | Name of this `AWSGroup` node. |
| path |  | IAM path under which the IAM group is organized. |
| *_ont_name* | Yes | Normalized field sourced from `name`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSGroup)`

- `(:AWSUser)-[:MEMBER_AWS_GROUP]->(:AWSGroup)`

- `(:AWSUser)-[:MEMBER_OF]->(:AWSGroup)`

### AWSGuardDutyDetector

Representation of an AWS [GuardDuty Detector](https://docs.aws.amazon.com/guardduty/latest/APIReference/API_GetDetector.html).

> **Additional Labels**: This node also uses `GuardDutyDetector`.

> **Additional Label Definitions**:
>
> - `GuardDutyDetector`: Compatibility label for the deprecated `GuardDutyDetector` aws node label. Use `AWSGuardDutyDetector` instead. Scheduled for removal in v1.0.0.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The unique identifier for the GuardDuty detector |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| accountid |  | The AWS Account ID the detector belongs to |
| createdat |  | Timestamp when the detector was created |
| findingpublishingfrequency |  | Frequency with which GuardDuty publishes findings |
| region |  | The AWS Region where the detector is deployed |
| service_role |  | IAM service role used by GuardDuty |
| status |  | Whether the detector is enabled or disabled |
| updatedat |  | Timestamp when the detector was last updated |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSGuardDutyDetector)`

- `(:AWSGuardDutyFinding)-[:DETECTED_BY]->(:AWSGuardDutyDetector)`

### AWSGuardDutyFinding

Representation of an AWS [GuardDuty Finding](https://docs.aws.amazon.com/guardduty/latest/APIReference/API_Finding.html).

> **Ontology Mapping**: This node uses the ontology label [`SecurityIssue`](#ontology-securityissue).

> **Additional Labels**: This node also uses `GuardDutyFinding`, `Risk`.

> **Additional Label Definitions**:
>
> - `GuardDutyFinding`: Compatibility label for the deprecated `GuardDutyFinding` aws node label. Use `AWSGuardDutyFinding` instead. Scheduled for removal in v1.0.0.
> - `Risk`: A node participating in the shared Risk graph interface.

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Unique identifier for this `AWSGuardDutyFinding` node. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| access_key_id | Yes | Identifier of the access key linked to this `AWSGuardDutyFinding` node. |
| accountid |  | Identifier of the account linked to this `AWSGuardDutyFinding` node. |
| api_call_caller_type |  | Identity category of the API caller. |
| api_call_error_code |  | Error code returned by the API operation, when present. |
| api_call_name |  | Name of the API operation associated with the finding. |
| api_call_remote_account_affiliated |  | Whether the remote AWS account is affiliated with the affected account. |
| api_call_remote_account_id | Yes | Identifier of the API call remote account linked to this `AWSGuardDutyFinding` node. |
| api_call_remote_asn |  | Autonomous system number associated with the remote API caller. |
| api_call_remote_asn_org |  | Organization registered to the remote caller's autonomous system. |
| api_call_remote_city |  | City associated with the remote API caller. |
| api_call_remote_country |  | Country associated with the remote API caller. |
| api_call_remote_ip |  | Remote IP address from which the API operation originated. |
| api_call_remote_isp |  | Internet service provider associated with the remote API caller. |
| api_call_remote_lat |  | Latitude associated with the remote API caller. |
| api_call_remote_lon |  | Longitude associated with the remote API caller. |
| api_call_remote_org |  | Organization associated with the remote API caller. |
| api_call_service_name |  | AWS service on which the API operation was invoked. |
| archived | Yes | Whether this `AWSGuardDutyFinding` node is archived. |
| arn | Yes | Amazon Resource Name (ARN) of this `AWSGuardDutyFinding` node. |
| confidence |  | Confidence score assigned to the GuardDuty finding. |
| createdat |  | Timestamp when GuardDuty created the finding. |
| description |  | Description of this `AWSGuardDutyFinding` node. |
| detectorid |  | Identifier of the detector linked to this `AWSGuardDutyFinding` node. |
| eks_cluster_arn | Yes | ARN of the EKS cluster linked to this `AWSGuardDutyFinding` node. |
| eventfirstseen |  | Timestamp when the activity that produced the finding was first observed. |
| eventlastseen |  | Timestamp when the activity that produced the finding was last observed. |
| principal_role_id | Yes | Identifier of the principal role linked to this `AWSGuardDutyFinding` node. |
| principal_user_id | Yes | Identifier of the principal user linked to this `AWSGuardDutyFinding` node. |
| region |  | AWS Region containing this `AWSGuardDutyFinding` node. |
| resource_id |  | Identifier of the resource linked to this `AWSGuardDutyFinding` node. |
| resource_type |  | AWS resource type affected by the finding. |
| sample |  | Whether this `AWSGuardDutyFinding` node is a sample finding. |
| service_action_type |  | GuardDuty action category associated with the finding. |
| service_count |  | Number of times GuardDuty observed the activity. |
| service_resource_role |  | Role of the affected resource in the observed activity. |
| severity | Yes | GuardDuty finding severity on its numeric severity scale. |
| severity_label |  | Normalized severity label derived from the numeric severity. |
| title |  | Human-readable title of the GuardDuty finding. |
| type |  | Type of this `AWSGuardDutyFinding` node. |
| updatedat |  | Timestamp when GuardDuty last updated the finding. |
| *_ont_first_seen* | Yes | Normalized field sourced from `eventfirstseen`. |
| *_ont_severity* | Yes | Normalized field sourced from `severity_label`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |
| *_ont_title* | Yes | Normalized field sourced from `title`. |
| *_ont_type* | Yes | Normalized field sourced from `type`. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSGuardDutyFinding)`

- `(:AWSGuardDutyFinding)-[:AFFECTS]->(:AWSAccountAccessKey)`

- `(:AWSGuardDutyFinding)-[:AFFECTS]->(:AWSEC2Instance)`

- `(:AWSGuardDutyFinding)-[:AFFECTS]->(:AWSEKSCluster)`

- `(:AWSGuardDutyFinding)-[:AFFECTS]->(:AWSRole)`

- `(:AWSGuardDutyFinding)-[:AFFECTS]->(:AWSS3Bucket)`

- `(:AWSGuardDutyFinding)-[:AFFECTS]->(:AWSUser)`

- `(:AWSGuardDutyFinding)-[:DETECTED_BY]->(:AWSGuardDutyDetector)`

- `(:AWSGuardDutyFinding)-[:REMOTE_ACCOUNT]->(:AWSAccount)`

### AWSIdentityCenter

Representation of an AWS Identity Center.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Unique identifier for the Identity Center instance |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| arn |  | The Amazon Resource Name (ARN) of the Identity Center instance |
| created_date |  | The date the Identity Center instance was created |
| identity_store_id |  | The identity store ID of the Identity Center instance |
| region |  | The AWS region where the Identity Center instance is located |
| status |  | The status of the Identity Center instance |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSIdentityCenter)`

- `(:AWSIdentityCenter)-[:HAS_PERMISSION_SET]->(:AWSPermissionSet)`

- `(:EntraServicePrincipal)-[:FEDERATES_TO]->(:AWSIdentityCenter)`: Links an Entra service principal to its federated AWS Identity Center.

### AWSInlinePolicy

Representation of an [AWS Policy](https://docs.aws.amazon.com/IAM/latest/APIReference/API_Policy.html) of type "inline". An inline policy is a policy that is defined on a principal. Inline policies cannot be shared across principals.

> **Additional Labels**: This node also uses `AWSPolicy`.

> **Additional Label Definitions**:
>
> - `AWSPolicy`: A aws node participating in the shared AWSPolicy graph interface.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Unique identifier for this `AWSInlinePolicy` node. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| arn | Yes | Amazon Resource Name (ARN) of this `AWSInlinePolicy` node. |
| name |  | Name of this `AWSInlinePolicy` node. |
| type |  | Type of this `AWSInlinePolicy` node. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSInlinePolicy)`

- `(:AWSPrincipal)-[:POLICY]->(:AWSInlinePolicy)`

### AWSInspectorFinding

Representation of an AWS [Inspector Finding](https://docs.aws.amazon.com/inspector/v2/APIReference/API_Finding.html)

Depending on its `type`, the finding also carries an ontology finding label: `PACKAGE_VULNERABILITY` findings are labeled [`CVE`](#ontology-cve), and `NETWORK_REACHABILITY` findings are labeled `:SecurityIssue`.

> **Additional Labels**: This node also uses `Risk`.

> **Additional Label Definitions**:
>
> - `Risk`: A node participating in the shared Risk graph interface.

> **Conditional Labels**:
>
> - [`CVE`](#ontology-cve) (ontology label) when `type` equals `PACKAGE_VULNERABILITY`. A cross-provider CVE resource in Cartography's ontology.
> - [`SecurityIssue`](#ontology-securityissue) (ontology label) when `type` equals `NETWORK_REACHABILITY`. A cross-provider SecurityIssue resource in Cartography's ontology.

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Unique identifier for this `AWSInspectorFinding` node. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| arn | Yes | Amazon Resource Name (ARN) of this `AWSInspectorFinding` node. |
| awsaccount |  | AWS account ID containing the affected resource. |
| cve_id | Yes | Normalized CVE identifier for package vulnerability findings. |
| cvssscore | Yes | CVSS base score assigned to the vulnerability. |
| description |  | Description of this `AWSInspectorFinding` node. |
| ecrimageid |  | Identifier of the ecrimageid linked to this `AWSInspectorFinding` node. |
| ecrrepositoryid |  | Identifier of the ecrrepositoryid linked to this `AWSInspectorFinding` node. |
| epss_score_inspector |  | Exploit Prediction Scoring System (EPSS) score for the finding, as reported by Inspector. |
| exploitavailable |  | Whether an exploit is available for the finding: `YES` or `NO`. |
| firstobservedat |  | Timestamp when Inspector first observed the vulnerability. |
| fixavailable |  | Whether a fix is available through a version update: `YES`, `NO`, or `PARTIAL`. |
| instanceid |  | Identifier of the instance linked to this `AWSInspectorFinding` node. |
| lastknownexploitat |  | Timestamp of the last known exploit associated with the finding. |
| name |  | Name of this `AWSInspectorFinding` node. |
| portrange |  | Formatted network port range associated with the finding. |
| portrangebegin |  | Lowest network port associated with the finding. |
| portrangeend |  | Highest network port associated with the finding. |
| protocol |  | Network protocol associated with the exposed port range. |
| referenceurls |  | Reference URLs describing the vulnerability. |
| region |  | AWS Region containing this `AWSInspectorFinding` node. |
| relatedvulnerabilities |  | Identifiers of vulnerabilities related to this finding. |
| severity |  | Inspector severity assigned to the finding. |
| source |  | Advisory source that reported the vulnerability. |
| sourceurl |  | URL of the source advisory for the vulnerability. |
| status |  | Current status of this `AWSInspectorFinding` node. |
| type |  | Type of this `AWSInspectorFinding` node. |
| updatedat |  | Timestamp when Inspector last updated the finding. |
| vendorcreatedat |  | Timestamp when the package vendor created the advisory. |
| vendorseverity |  | Severity assigned by the package vendor. |
| vendorupdatedat |  | Timestamp when the package vendor last updated the advisory. |
| vulnerabilityid |  | Identifier of the vulnerabilityid linked to this `AWSInspectorFinding` node. |
| vulnerablepackageids |  | Identifiers of packages affected by the vulnerability. |
| *_ont_base_score* | Yes | Normalized field sourced from `cvssscore`. |
| *_ont_base_severity* | Yes | Normalized field sourced from `severity`. |
| *_ont_cve_id* | Yes | Normalized field sourced from `cve_id`. |
| *_ont_description* |  | Normalized field sourced from `description`. |
| *_ont_references* |  | Normalized field sourced from `referenceurls`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |

#### Relationships

- `(:AWSAccount)-[:MEMBER]->(:AWSInspectorFinding)`

- `(:AWSAccount)-[:RESOURCE]->(:AWSInspectorFinding)`

- `(:AWSInspectorFinding)-[:AFFECTS]->(:AWSEC2Instance)`

- `(:AWSInspectorFinding)-[:AFFECTS]->(:AWSECRImage)`

- `(:AWSInspectorFinding)-[:AFFECTS]->(:AWSECRRepository)`

- `(:AWSInspectorFinding)-[:HAS]->(:AWSInspectorPackage)`
  - Properties:

    | Field | Description |
    |-------|-------------|
    | filepath | Path of the vulnerable file associated with this relationship. |
    | fixedinversion | Package version that fixes the vulnerability represented by this relationship. |
    | remediation | Recommended remediation for the finding in this relationship. |
    | sourcelambdalayerarn | ARN of the Lambda layer from which this relationship originated. |
    | sourcelayerhash | Content hash of the Lambda layer from which this relationship originated. |

### AWSInspectorPackage

Representation of an AWS [Inspector Finding Package](https://docs.aws.amazon.com/inspector/v2/APIReference/API_Finding.html)

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Uses the format of `name\|epoch:version-release.arch` to uniquely identify packages |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| arch |  | Architecture for the package |
| epoch |  | Package epoch used for version ordering. |
| manager |  | Related package manager |
| name | Yes | The package name |
| release | Yes | Release of the package |
| version | Yes | Version of the package |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSInspectorPackage)`

- `(:AWSInspectorFinding)-[:HAS]->(:AWSInspectorPackage)`
  - Properties:

    | Field | Description |
    |-------|-------------|
    | filepath | Path of the vulnerable file associated with this relationship. |
    | fixedinversion | Package version that fixes the vulnerability represented by this relationship. |
    | remediation | Recommended remediation for the finding in this relationship. |
    | sourcelambdalayerarn | ARN of the Lambda layer from which this relationship originated. |
    | sourcelayerhash | Content hash of the Lambda layer from which this relationship originated. |

### AWSInstanceProfile

Representation of an AWS [IAM Instance Profile](https://docs.aws.amazon.com/IAM/latest/APIReference/API_InstanceProfile.html)

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The arn |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| arn |  | The arn |
| createdate |  | Timestamp when the IAM instance profile was created. |
| instance_profile_id |  | The instance profile id |
| instance_profile_name |  | The instance profile name |
| path |  | IAM path under which the IAM instance profile is organized. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSInstanceProfile)`

- `(:AWSEC2Instance)-[:INSTANCE_PROFILE]->(:AWSInstanceProfile)`

- `(:AWSInstanceProfile)-[:ASSOCIATED_WITH]->(:AWSRole)`

### AWSInternetGateway

Representation of an AWS [Interent Gateway](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_InternetGateway.html).

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Unique identifier for this `AWSInternetGateway` node. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| arn | Yes | Amazon Resource Name (ARN) of this `AWSInternetGateway` node. |
| ownerid |  | Identifier of the owner linked to this `AWSInternetGateway` node. |
| region |  | AWS Region containing this `AWSInternetGateway` node. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSInternetGateway)`

- `(:AWSEC2Route)-[:ROUTES_TO_GATEWAY]->(:AWSInternetGateway)`

- `(:AWSEC2RouteTableAssociation)-[:ASSOCIATED_IGW_FOR_INGRESS]->(:AWSInternetGateway)`

- `(:AWSInternetGateway)-[:ATTACHED_TO]->(:AWSVpc)`

- `(:AWSInternetGateway)-[:TAGGED]->(:AWSTag)`: `AWSInternetGateway` is tagged with an `AWSTag` discovered by the AWS Resource Groups Tagging API.

### AWSIpPermissionInbound

An AWSIpPermissionInbound node is a specific type of AWSIpRule. It represents inbound IP-based rules derived from `AWSEC2SecurityGroup` rules.

> **Additional Labels**: This node also uses `AWSIpRule`, `IpPermissionInbound`, `IpRule`.

> **Additional Label Definitions**:
>
> - `AWSIpRule`: A aws node participating in the shared AWSIpRule graph interface.
> - `IpPermissionInbound`: A node participating in the shared IpPermissionInbound graph interface.
> - `IpRule`: A node participating in the shared IpRule graph interface.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Unique identifier for this `AWSIpRule` node. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| fromport |  | Lowest transport-layer port allowed by the security-group rule. |
| groupid | Yes | Identifier of the group linked to this `AWSIpRule` node. |
| protocol |  | IP protocol matched by the security-group rule. |
| ruleid | Yes | Identifier of the ruleid linked to this `AWSIpRule` node. |
| toport |  | Highest transport-layer port allowed by the security-group rule. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSIpPermissionInbound)`

- `(:AWSIpPermissionInbound)-[:MEMBER_OF_EC2_SECURITY_GROUP]->(:AWSEC2SecurityGroup)`

### AWSIpRange

Represents an IP address range (CIDR block) associated with an EC2 Security Group rule. IpRange nodes define the source or destination IP addresses that a security group rule applies to.

> **Additional Labels**: This node also uses `IpRange`.

> **Additional Label Definitions**:
>
> - `IpRange`: A node participating in the shared IpRange graph interface.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Unique identifier for this `AWSIpRange` node. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| range |  | Stable identifier derived from the security-group rule IP range. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSIpRange)`

- `(:AWSIpRange)-[:MEMBER_OF_IP_RULE]->(:AWSIpRule)`

### AWSIpRule

Represents a generic IP rule.  The creation of this node is currently derived from ingesting `AWSEC2SecurityGroup` rules.

> **Additional Labels**: This node also uses `IpRule`.

> **Additional Label Definitions**:
>
> - `IpRule`: A node participating in the shared IpRule graph interface.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Unique identifier for this `AWSIpRule` node. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| fromport |  | Lowest transport-layer port allowed by the security-group rule. |
| groupid | Yes | Identifier of the group linked to this `AWSIpRule` node. |
| protocol |  | IP protocol matched by the security-group rule. |
| ruleid | Yes | Identifier of the ruleid linked to this `AWSIpRule` node. |
| toport |  | Highest transport-layer port allowed by the security-group rule. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSIpRule)`

- `(:AWSIpRange)-[:MEMBER_OF_IP_RULE]->(:AWSIpRule)`

- `(:AWSIpRule)-[:MEMBER_OF_EC2_SECURITY_GROUP]->(:AWSEC2SecurityGroup)`

### AWSKMSAlias

Representation of an AWS [KMS Key Alias](https://docs.aws.amazon.com/kms/latest/APIReference/API_AliasListEntry.html).

> **Additional Labels**: This node also uses `KMSAlias`.

> **Additional Label Definitions**:
>
> - `KMSAlias`: Compatibility label for the deprecated `KMSAlias` aws node label. Use `AWSKMSAlias` instead. Scheduled for removal in v1.0.0.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The ARN of the alias |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| alias_name | Yes | The name of the alias |
| arn | Yes | The ARN of the alias |
| creation_date |  | The date the alias was created |
| last_updated_date |  | The date the alias was last updated by AWS |
| region |  | The AWS region where the alias is located |
| target_key_id |  | The KMS key id associated via this alias |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSKMSAlias)`: Relationship between KMS Alias and AWS Account

- `(:AWSKMSAlias)-[:KNOWN_AS]->(:AWSKMSKey)`: Relationship between KMS Alias and its associated KMS Key

### AWSKMSGrant

Representation of an AWS [KMS Key Grant](https://docs.aws.amazon.com/kms/latest/APIReference/API_GrantListEntry.html).

> **Additional Labels**: This node also uses `KMSGrant`.

> **Additional Label Definitions**:
>
> - `KMSGrant`: Compatibility label for the deprecated `KMSGrant` aws node label. Use `AWSKMSGrant` instead. Scheduled for removal in v1.0.0.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The unique identifier of the key grant |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| creation_date |  | Epoch timestamp when the grant was created |
| grant_id | Yes | The grant identifier (indexed for performance) |
| grantee_principal |  | The principal associated with the key grant |
| issuing_account |  | The AWS account that issued the grant |
| key_id |  | The key identifier that the grant applies to |
| name |  | The name of the key grant |
| operations |  | List of operations that the grant allows |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSKMSGrant)`: Relationship between AWSKMSGrant and AWS Account

- `(:AWSKMSGrant)-[:APPLIED_ON]->(:AWSKMSKey)`

### AWSKMSKey

Representation of an AWS [KMS Key](https://docs.aws.amazon.com/kms/latest/APIReference/API_KeyListEntry.html).

> **Ontology Mapping**: This node uses the ontology label [`EncryptionKey`](#ontology-encryptionkey).

> **Additional Labels**: This node also uses `KMSKey`.

> **Additional Label Definitions**:
>
> - `KMSKey`: Compatibility label for the deprecated `KMSKey` aws node label. Use `AWSKMSKey` instead. Scheduled for removal in v1.0.0.

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The KeyId of the key |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| anonymous_access |  | True if this key has a policy applied to it that allows anonymous access or if it is open to the internet. |
| anonymous_actions |  | List of anonymous internet accessible actions that may be run on the key. |
| arn | Yes | The ARN of the key |
| cloud_hsm_cluster_id |  | The cluster ID of the AWS CloudHSM cluster that contains the key material |
| creation_date |  | The date the key was created |
| custom_key_store_id |  | The ID of the custom key store that contains the key |
| customer_master_key_spec |  | The type of key material in the CMK |
| deletion_date |  | The date the key is scheduled for deletion |
| description |  | The description of the key |
| enabled |  | Whether the key is enabled |
| encryption_algorithms |  | The encryption algorithms that AWS KMS supports for this key |
| expiration_model |  | Specifies whether key material expires |
| key_id | Yes | The KeyId of the key |
| key_manager |  | The manager of the key (AWS or CUSTOMER) |
| key_state |  | The current state of the key (e.g., Enabled, Disabled, PendingDeletion) |
| key_usage |  | The permitted use of the key (e.g., ENCRYPT_DECRYPT, SIGN_VERIFY) |
| origin |  | The source of the key material (AWS_KMS, EXTERNAL, AWS_CLOUDHSM) |
| region |  | The region where key is created |
| signing_algorithms |  | The signing algorithms that AWS KMS supports for this key |
| valid_to |  | The expiration date for the key material |
| *_ont_enabled* | Yes | Normalized field sourced from `enabled`. |
| *_ont_key_type* | Yes | Normalized field sourced from `key_usage`. |
| *_ont_name* | Yes | Normalized field sourced from `arn`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSKMSKey)`: Relationship between AWSKMSKey and AWS Account

- `(:AWSDynamoDBSSEDescription)-[:USES_KMS_KEY]->(:AWSKMSKey)`: Relationship to AWSKMSKey. Only created when SSEType is "KMS" and KMSMasterKeyArn exists.

- `(:AWSEfsFileSystem)-[:ENCRYPTED_BY]->(:AWSKMSKey)`

- `(:AWSKMSAlias)-[:KNOWN_AS]->(:AWSKMSKey)`: Relationship between KMS Alias and its associated KMS Key

- `(:AWSKMSGrant)-[:APPLIED_ON]->(:AWSKMSKey)`

- `(:AWSKMSKey)-[:TAGGED]->(:AWSTag)`: `AWSKMSKey` is tagged with an `AWSTag` discovered by the AWS Resource Groups Tagging API.

- `(:AWSRDSInstance)-[:ENCRYPTED_BY]->(:AWSKMSKey)`

- `(:AWSS3Bucket)-[:ENCRYPTED_BY]->(:AWSKMSKey)`

- `(:AWSSSMParameter)-[:ENCRYPTED_BY]->(:AWSKMSKey)`

- `(:AWSSecretsManagerSecret)-[:ENCRYPTED_BY]->(:AWSKMSKey)`: Relationship between Secret and its KMS key
Only created when kms_key_id is present

- `(:AWSSecretsManagerSecretVersion)-[:ENCRYPTED_BY]->(:AWSKMSKey)`: Relationship between Secret Version and its KMS key
Only created when kms_key_ids is present

- `(:DatabricksEncryptionKey)-[:REFERENCES_KEY]->(:AWSKMSKey)`: A Databricks encryption key references an AWS KMS key.

### AWSLambda

Representation of an AWS [Lambda Function](https://docs.aws.amazon.com/lambda/latest/dg/API_FunctionConfiguration.html).

> **Ontology Mapping**: This node uses the ontology label [`Function`](#ontology-function).

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The arn of the lambda function |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| anonymous_access |  | True if this function has a policy applied to it that allows anonymous access or if it is open to the internet. |
| anonymous_actions |  | List of anonymous internet accessible actions that may be run on the function. |
| architecture_normalized |  | Canonical architecture (`amd64`, `arm64`) derived from `architectures[0]`. Used by `RESOLVED_IMAGE` to pick the right child image when the Lambda runs a multi-architecture manifest list. |
| architectures |  | The instruction set architecture that the function supports. Architecture is a string array with one of the valid values. |
| arn | Yes | The Amazon Resource Name (ARN) of the lambda function |
| codesha256 |  | The SHA256 hash of the function's deployment package. |
| codesize |  | The size of the function's deployment package, in bytes. |
| description |  | The description of the Lambda function |
| handler |  | The function that Lambda calls to begin executing your function. |
| image_digest |  | Content-addressable digest (`sha256:...`) extracted from `image_uri` when the reference is digest-pinned. |
| image_uri |  | Container image reference (e.g., `123.dkr.ecr.us-east-1.amazonaws.com/repo@sha256:...`). Populated when `packagetype=Image`. |
| kmskeyarn |  | The KMS key that's used to encrypt the function's environment variables. This key is only returned if you've configured a customer managed key. |
| lastupdatestatus |  | The status of the last update that was performed on the function. |
| lastupdatestatusreason |  | The reason for the last update that was performed on the function. |
| lastupdatestatusreasoncode |  | The reason code for the last update that was performed on the function. |
| masterarn |  | For Lambda@Edge functions, the ARN of the main function. |
| memory |  | The memory that's allocated to the function |
| modifieddate |  | Timestamp of the last time the function was last updated |
| name |  | The name of the lambda function |
| packagetype |  | The type of deployment package (`Zip` for source code, `Image` for container). |
| region |  | The AWS region where the Lambda function is deployed. |
| revisionid |  | The latest updated revision of the function or alias. |
| runtime |  | The runtime environment for the Lambda function |
| signingjobarn |  | The ARN of the signing job. |
| signingprofileversionarn |  | The ARN of the signing profile version. |
| state |  | The current state of the function. |
| statereason |  | The reason for the function's current state. |
| statereasoncode |  | The reason code for the function's current state. |
| timeout |  | The amount of time in seconds that Lambda allows a function to run before stopping it |
| tracingconfigmode |  | The function's AWS X-Ray tracing configuration mode. |
| version |  | The version of the Lambda function. |
| *_ont_deployment_type* | Yes | Normalized field sourced from `packagetype`. |
| *_ont_image* | Yes | Normalized field sourced from `image_uri`. |
| *_ont_image_digest* | Yes | Normalized field sourced from `image_digest`. |
| *_ont_memory* | Yes | Normalized field sourced from `memory`. |
| *_ont_name* | Yes | Normalized field sourced from `name`. |
| *_ont_runtime* | Yes | Normalized field sourced from `runtime`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |
| *_ont_timeout* | Yes | Normalized field sourced from `timeout`. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSLambda)`

- `(:AWSBedrockAgent)-[:INVOKES]->(:AWSLambda)`: Defines the relationship from AWSBedrockAgent to AWSLambda (existing Lambda function nodes).

- `(:AWSCloudFrontDistribution)-[:USES_LAMBDA_EDGE]->(:AWSLambda)`: Indicates that the CloudFront distribution uses a Lambda function for Lambda@Edge processing.

- `(:AWSLambda)-[:ASSUMES]->(:AWSRole)`

- `(:AWSLambda)-[:HAS]->(:AWSECRImage)`: generated by analysis job `Lambda functions with ECR images`.

- `(:AWSLambda)-[:HAS]->(:AWSLambdaLayer)`

- `(:AWSLambda)-[:HAS_IMAGE]->(:AWSECRImage)`

- `(:AWSLambda)-[:HAS_IMAGE]->(:GCPArtifactRegistryImage)`

- `(:AWSLambda)-[:HAS_IMAGE]->(:GitHubContainerImage)`

- `(:AWSLambda)-[:HAS_IMAGE]->(:GitLabContainerImage)`

- `(:AWSLambda)-[:KNOWN_AS]->(:AWSLambdaFunctionAlias)`

- `(:AWSLambda)-[:RESOURCE]->(:AWSLambdaEventSourceMapping)`

- `(:AWSLambda)-[:STS_ASSUMEROLE_ALLOW]->(:AWSPrincipal)`

- `(:AWSLambda)-[:TAGGED]->(:AWSTag)`: `AWSLambda` is tagged with an `AWSTag` discovered by the AWS Resource Groups Tagging API.

- `(:AWSLoadBalancerV2)-[:EXPOSE]->(:AWSLambda)`: Indicates that the load balancer exposes a Lambda function as a traffic target.
  - Properties:

    | Field | Description |
    |-------|-------------|
    | port | Port on which the listener or target group receives traffic. |
    | protocol | Protocol used by the listener or target group. |
    | target_group_arn | ARN of the Elastic Load Balancing target group represented by this relationship. |

- `(:Function)-[:RESOLVED_IMAGE]->(:Image)`: generated by analysis job `Function RESOLVED_IMAGE analysis`.

### AWSLambdaEventSourceMapping

Representation of an [AWSLambdaEventSourceMapping](https://docs.aws.amazon.com/lambda/latest/dg/API_ListEventSourceMappings.html).

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The id of the event source mapping |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| batchsize |  | The maximum number of items to retrieve in a single batch. |
| bisectbatchonfunctionerror |  | If the function returns an error, split the batch in two and retry. |
| eventsourcearn |  | The Amazon Resource Name (ARN) of the event source. |
| functionarn |  | The ARN of the Lambda function |
| lastmodified |  | The date that the event source mapping was last updated, or its state changed. |
| lastprocessingresult |  | The result of the last AWS Lambda invocation of your Lambda function. |
| maximumbatchingwindowinseconds |  | The maximum amount of time to gather records before invoking the function, in seconds. |
| maximumrecordage |  | Discard records older than the specified age. |
| maximumretryattempts |  | Discard records after the specified number of retries. |
| parallelizationfactor |  | The number of batches to process from each shard concurrently. |
| startingposition |  | The position in a stream from which to start reading. |
| startingpositiontimestamp |  | The time from which to start reading. |
| state |  | The state of the event source mapping. |
| tumblingwindowinseconds |  | The duration in seconds of a processing window. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSLambdaEventSourceMapping)`

- `(:AWSLambda)-[:RESOURCE]->(:AWSLambdaEventSourceMapping)`

### AWSLambdaFunctionAlias

Representation of an [AWSLambdaFunctionAlias](https://docs.aws.amazon.com/lambda/latest/dg/configuration-aliases.html).

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The arn of the lambda function alias |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| aliasname |  | The name of the lambda function alias |
| arn | Yes | The arn of the lambda function alias |
| description |  | The description of the alias. |
| functionarn |  | The ARN of the Lambda function this alias points to |
| functionversion |  | The function version that the alias invokes. |
| revisionid |  | A unique identifier that changes when you update the alias. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSLambdaFunctionAlias)`

- `(:AWSLambda)-[:KNOWN_AS]->(:AWSLambdaFunctionAlias)`

### AWSLambdaLayer

Representation of an [AWSLambdaLayer](https://docs.aws.amazon.com/lambda/latest/dg/configuration-layers.html).

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The arn of the lambda function layer |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| arn |  | The arn of the lambda function layer |
| codesize |  | The size of the layer archive in bytes. |
| functionarn |  | The ARN of the Lambda function this layer belongs to |
| signingjobarn |  | The Amazon Resource Name (ARN) of a signing job. |
| signingprofileversionarn |  | The Amazon Resource Name (ARN) for a signing profile version. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSLambdaLayer)`

- `(:AWSLambda)-[:HAS]->(:AWSLambdaLayer)`

### AWSLaunchConfiguration

Representation of an AWS [Launch Configuration](https://docs.aws.amazon.com/autoscaling/ec2/APIReference/API_LaunchConfiguration.html)

> **Additional Labels**: This node also uses `LaunchConfiguration`.

> **Additional Label Definitions**:
>
> - `LaunchConfiguration`: Compatibility label for the deprecated `LaunchConfiguration` aws node label. Use `AWSLaunchConfiguration` instead. Scheduled for removal in v1.0.0.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The ARN of the launch configuration. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| arn |  | The ARN of the launch configuration. |
| associate_public_ip_address |  | For Auto Scaling groups that are running in a VPC, specifies whether to assign a public IP address to the group's instances. |
| ebs_optimized |  | Specifies whether the launch configuration is optimized for EBS I/O (true) or not (false). |
| iam_instance_profile |  | The name or the Amazon Resource Name (ARN) of the instance profile associated with the IAM role for the instance. |
| image_id |  | The ID of the Amazon Machine Image (AMI) to use to launch your EC2 instances. |
| instance_monitoring_enabled |  | If true, detailed monitoring is enabled. Otherwise, basic monitoring is enabled. |
| instance_type |  | The instance type for the instances. |
| kernel_id |  | The ID of the kernel associated with the AMI. |
| key_name |  | The name of the key pair. |
| name | Yes | The name of the launch configuration. |
| placement_tenancy |  | The tenancy of the instance, either default or dedicated. An instance with dedicated tenancy runs on isolated, single-tenant hardware and can only be launched into a VPC. |
| ramdisk_id |  | The ID of the RAM disk associated with the AMI. |
| region |  | The region of the launch configuration. |
| security_groups |  | A list that contains the security groups to assign to the instances in the Auto Scaling group. |
| spot_price |  | The maximum hourly price to be paid for any Spot Instance launched to fulfill the request. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSLaunchConfiguration)`

- `(:AWSAutoScalingGroup)-[:HAS_LAUNCH_CONFIG]->(:AWSLaunchConfiguration)`

### AWSLaunchTemplate

Representation of an AWS [Launch Template](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_LaunchTemplate.html)

> **Additional Labels**: This node also uses `LaunchTemplate`.

> **Additional Label Definitions**:
>
> - `LaunchTemplate`: Compatibility label for the deprecated `LaunchTemplate` aws node label. Use `AWSLaunchTemplate` instead. Scheduled for removal in v1.0.0.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The ID of the launch template (same as launch_template_id) |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| create_time |  | The time launch template was created. |
| created_by |  | The principal that created the launch template. |
| default_version_number |  | The version number of the default version of the launch template. |
| latest_version_number |  | The version number of the latest version of the launch template. |
| launch_template_id |  | The ID of the launch template |
| name |  | The name of the launch template. |
| region |  | The region of the launch template. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSLaunchTemplate)`

- `(:AWSAutoScalingGroup)-[:HAS_LAUNCH_TEMPLATE]->(:AWSLaunchTemplate)`

- `(:AWSLaunchTemplate)-[:VERSION]->(:AWSLaunchTemplateVersion)`

### AWSLaunchTemplateVersion

Representation of an AWS [Launch Template Version](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_LaunchTemplateVersion.html)

> **Additional Labels**: This node also uses `LaunchTemplateVersion`.

> **Additional Label Definitions**:
>
> - `LaunchTemplateVersion`: Compatibility label for the deprecated `LaunchTemplateVersion` aws node label. Use `AWSLaunchTemplateVersion` instead. Scheduled for removal in v1.0.0.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The ID of the launch template version (ID-version). |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| create_time |  | The time the version was created. |
| created_by |  | The principal that created the version. |
| default_version |  | Indicates whether the version is the default version. |
| disable_api_termination |  | If set to true, indicates that the instance cannot be terminated using the Amazon EC2 console, command line tool, or API. |
| ebs_optimized |  | Indicates whether the instance is optimized for Amazon EBS I/O. |
| iam_instance_profile_arn |  | The Amazon Resource Name (ARN) of the instance profile. |
| iam_instance_profile_name |  | The name of the instance profile. |
| image_id |  | The ID of the AMI that was used to launch the instance. |
| instance_initiated_shutdown_behavior |  | Indicates whether an instance stops or terminates when you initiate shutdown from the instance (using the operating system command for system shutdown). |
| instance_type |  | The instance type. |
| kernel_id |  | The ID of the kernel, if applicable. |
| key_name |  | The name of the key pair. |
| monitoring_enabled |  | Indicates whether detailed monitoring is enabled. Otherwise, basic monitoring is enabled. |
| name |  | The name of the launch template. |
| ramdisk_id |  | The ID of the RAM disk, if applicable. |
| region |  | The region of the launch template. |
| security_group_ids |  | The security group IDs. |
| security_groups |  | The security group names. |
| version_description |  | The description of the version. |
| version_number |  | The version number. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSLaunchTemplateVersion)`

- `(:AWSLaunchTemplate)-[:VERSION]->(:AWSLaunchTemplateVersion)`

### AWSLoadBalancer

Represents a classic [AWS Elastic Load Balancer](https://docs.aws.amazon.com/elasticloadbalancing/2012-06-01/APIReference/API_LoadBalancerDescription.html).  See [spec for details](https://docs.aws.amazon.com/elasticloadbalancing/2012-06-01/APIReference/API_LoadBalancerDescription.html).

**Label rename:** in previous versions, classic ELB nodes used the label `LoadBalancer`. It was renamed to `AWSLoadBalancer` for consistency with other AWS resources, and existing nodes are relabeled automatically on upgrade.

> **Ontology Mapping**: This node uses the ontology label [`LoadBalancer`](#ontology-loadbalancer).

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The load balancer's DNS name exactly as AWS returned it, case preserved. Unlike `dnsname` it is not lowercased, because listeners and target groups join against it. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| canonicalhostedzonename |  | The DNS name of the load balancer |
| canonicalhostedzonenameid |  | The ID of the Amazon Route 53 hosted zone for the load balancer. |
| createdtime |  | The date and time the load balancer was created. |
| dnsname | Yes | The DNS name of the load balancer, lowercased at ingestion. AWS preserves the load balancer name's case here, while Route53 alias targets and Kubernetes load balancer status hostnames are lowercase, and those are matched against this property for equality. |
| exposed_internet |  | Property generated by analysis job: `AWS LoadBalancer internet exposure`. |
| exposed_internet_type |  | Property generated by analysis job: `AWS LoadBalancer internet exposure`. |
| name |  | The name of the load balancer |
| region |  | The region of the load balancer |
| scheme | Yes | The type of load balancer. Valid only for load balancers in a VPC. If scheme is `internet-facing`, the load balancer has a public DNS name that resolves to a public IP address.  If scheme is `internal`, the load balancer has a public DNS name that resolves to a private IP address. |
| *_ont_dns_name* | Yes | Normalized field sourced from `dnsname`. |
| *_ont_lb_type* | Yes | Property generated by the ontology mapping. |
| *_ont_name* | Yes | Normalized field sourced from `name`. |
| *_ont_region* | Yes | Normalized field sourced from `region`. |
| *_ont_scheme* | Yes | Normalized field sourced from `scheme`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSLoadBalancer)`

- `(:AWSDNSRecord)-[:DNS_POINTS_TO]->(:AWSLoadBalancer)`

- `(:AWSLoadBalancer)-[:ELB_LISTENER]->(:AWSELBListener)`

- `(:AWSLoadBalancer)-[:EXPOSE]->(:AWSEC2Instance)`

- `(:AWSLoadBalancer)-[:MEMBER_OF_EC2_SECURITY_GROUP]->(:AWSEC2SecurityGroup)`

- `(:AWSLoadBalancer)-[:NETWORK_INTERFACE]->(:AWSNetworkInterface)`

- `(:AWSLoadBalancer)-[:PART_OF_SUBNET]->(:AWSEC2Subnet)`

- `(:AWSLoadBalancer)-[:SOURCE_SECURITY_GROUP]->(:AWSEC2SecurityGroup)`

- `(:AWSLoadBalancer)-[:TAGGED]->(:AWSTag)`: `AWSLoadBalancer` is tagged with an `AWSTag` discovered by the AWS Resource Groups Tagging API.

- `(:DNSRecord)-[:DNS_POINTS_TO]->(:AWSLoadBalancer)`: generated by analysis job `Ontology - DNSRecord to AWSLoadBalancer linking`.

- `(:PublicIP)-[:POINTS_TO]->(:LoadBalancer)`

### AWSLoadBalancerV2

An AWS Application or Network Load Balancer that distributes traffic to targets. See the [Application Load Balancer](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/introduction.html) and [Network Load Balancer](https://docs.aws.amazon.com/elasticloadbalancing/latest/network/introduction.html) guides, and the [API reference](https://docs.aws.amazon.com/elasticloadbalancing/latest/APIReference/API_LoadBalancer.html).

**Label rename:** in previous versions, ALB/NLB nodes used the label `LoadBalancerV2`. It was renamed to `AWSLoadBalancerV2` for consistency with other AWS resources, and existing nodes are relabeled automatically on upgrade.

> **Ontology Mapping**: This node uses the ontology label [`LoadBalancer`](#ontology-loadbalancer).

> **Additional Labels**: This node also uses `LoadBalancerV2`.

> **Additional Label Definitions**:
>
> - `LoadBalancerV2`: A aws node participating in the shared LoadBalancerV2 graph interface.

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The load balancer's DNS name exactly as AWS returned it, case preserved. Unlike `dnsname` it is not lowercased, because listeners and target groups join against it. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| arn | Yes | The Amazon Resource Name (ARN) of the load balancer. |
| canonicalhostedzonenameid |  | The ID of the Amazon Route 53 hosted zone for the load balancer. |
| createdtime |  | The date and time the load balancer was created. |
| dnsname | Yes | The DNS name of the load balancer, lowercased at ingestion. AWS preserves the load balancer name's case here, while Route53 alias targets and Kubernetes load balancer status hostnames are lowercase, and those are matched against this property for equality. |
| exposed_internet | Yes | The `exposed_internet` flag is set to `True` by the `aws_ec2_asset_exposure` analysis job when internet reachability is inferred. For NLBs (`type='network'`), this is based on `scheme='internet-facing'` and listener presence. For ALBs, this requires `scheme='internet-facing'` plus a security group path open from `0.0.0.0/0` to a listener port. |
| exposed_internet_type |  | Property generated by analysis job: `AWS LoadBalancerV2 internet exposure`. |
| name |  | The name of the load balancer |
| region |  | The region of the load balancer |
| scheme |  | The type of load balancer.  If scheme is `internet-facing`, the load balancer has a public DNS name that resolves to a public IP address.  If scheme is `internal`, the load balancer has a public DNS name that resolves to a private IP address. |
| type |  | Can be `application` or `network` |
| *_ont_dns_name* | Yes | Normalized field sourced from `dnsname`. |
| *_ont_lb_type* | Yes | Normalized field sourced from `type`. |
| *_ont_name* | Yes | Normalized field sourced from `name`. |
| *_ont_region* | Yes | Normalized field sourced from `region`. |
| *_ont_scheme* | Yes | Normalized field sourced from `scheme`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSLoadBalancerV2)`

- `(:AWSDNSRecord)-[:DNS_POINTS_TO]->(:AWSLoadBalancerV2)`

- `(:AWSEC2NetworkAcl)-[:PROTECTS]->(:AWSLoadBalancerV2)`: generated by analysis job `AWS LoadBalancer to NACL direct relationship`.

- `(:AWSLoadBalancerV2)-[:ELBV2_LISTENER]->(:AWSELBV2Listener)`

- `(:AWSLoadBalancerV2)-[:ELBV2_TARGET_GROUP]->(:AWSELBV2TargetGroup)`

- `(:AWSLoadBalancerV2)-[:EXPOSE]->(:AWSEC2Instance)`: Indicates that the load balancer exposes an EC2 instance as a traffic target.
  - Properties:

    | Field | Description |
    |-------|-------------|
    | port | Port on which the listener or target group receives traffic. |
    | protocol | Protocol used by the listener or target group. |
    | target_group_arn | ARN of the Elastic Load Balancing target group represented by this relationship. |

- `(:AWSLoadBalancerV2)-[:EXPOSE]->(:AWSEC2PrivateIp)`: Indicates that the load balancer exposes a private IP address as a traffic target.
  - Properties:

    | Field | Description |
    |-------|-------------|
    | port | Port on which the listener or target group receives traffic. |
    | protocol | Protocol used by the listener or target group. |
    | target_group_arn | ARN of the Elastic Load Balancing target group represented by this relationship. |

- `(:AWSLoadBalancerV2)-[:EXPOSE]->(:AWSECSContainer)`: generated by analysis job `AWS LoadBalancer to ECS Container direct relationship`.
  - Properties:

    | Field | Description |
    |-------|-------------|
    | exposure_type | Property generated by analysis job: `AWS LoadBalancer to ECS Container direct relationship`. |

- `(:AWSLoadBalancerV2)-[:EXPOSE]->(:AWSLambda)`: Indicates that the load balancer exposes a Lambda function as a traffic target.
  - Properties:

    | Field | Description |
    |-------|-------------|
    | port | Port on which the listener or target group receives traffic. |
    | protocol | Protocol used by the listener or target group. |
    | target_group_arn | ARN of the Elastic Load Balancing target group represented by this relationship. |

- `(:AWSLoadBalancerV2)-[:EXPOSE]->(:AWSLoadBalancerV2)`: Indicates that the load balancer exposes another load balancer as a traffic target.
  - Properties:

    | Field | Description |
    |-------|-------------|
    | port | Port on which the listener or target group receives traffic. |
    | protocol | Protocol used by the listener or target group. |
    | target_group_arn | ARN of the Elastic Load Balancing target group represented by this relationship. |

- `(:AWSLoadBalancerV2)-[:EXPOSE]->(:KubernetesContainer)`: generated by analysis job `Kubernetes LoadBalancer to container EXPOSE relationships`.
  - Properties:

    | Field | Description |
    |-------|-------------|
    | exposure_type | Property generated by analysis job: `Kubernetes LoadBalancer to container EXPOSE relationships`. |

- `(:AWSLoadBalancerV2)-[:EXPOSE]->(:KubernetesPod)`: generated by analysis job `Kubernetes LoadBalancer to pod EXPOSE relationships`.
  - Properties:

    | Field | Description |
    |-------|-------------|
    | exposure_type | Property generated by analysis job: `Kubernetes LoadBalancer to pod EXPOSE relationships`. |

- `(:AWSLoadBalancerV2)-[:MEMBER_OF_EC2_SECURITY_GROUP]->(:AWSEC2SecurityGroup)`

- `(:AWSLoadBalancerV2)-[:NETWORK_INTERFACE]->(:AWSNetworkInterface)`

- `(:AWSLoadBalancerV2)-[:PART_OF_SUBNET]->(:AWSEC2Subnet)`

- `(:AWSLoadBalancerV2)-[:SUBNET]->(:AWSEC2Subnet)`

- `(:AWSLoadBalancerV2)-[:TAGGED]->(:AWSTag)`: `AWSLoadBalancerV2` is tagged with an `AWSTag` discovered by the AWS Resource Groups Tagging API.

- `(:DNSRecord)-[:DNS_POINTS_TO]->(:AWSLoadBalancerV2)`: generated by analysis job `Ontology - DNSRecord to AWSLoadBalancerV2 linking`.

- `(:KubernetesIngress)-[:USES_LOAD_BALANCER]->(:AWSLoadBalancerV2)`: Links an ingress to the AWS load balancer that exposes it, matched by the DNS hostname from the ingress status to the load balancer's DNS name; both are lowercased at ingestion.

- `(:KubernetesService)-[:USES_LOAD_BALANCER]->(:AWSLoadBalancerV2)`: Links a service of type `LoadBalancer` to the AWS load balancer that exposes it, matching the service's `status.loadBalancer.ingress[].hostname` against `AWSLoadBalancerV2.dnsname`. Both sides are lowercased at ingestion, since AWS preserves the load balancer name's case in the DNS name it hands to the in-cluster controller.

- `(:PublicIP)-[:POINTS_TO]->(:LoadBalancer)`

### AWSManagedPolicy

Representation of an [AWS Policy](https://docs.aws.amazon.com/IAM/latest/APIReference/API_Policy.html) of type "managed". A managed policy is a built-in policy created and maintained by AWS. Managed policies are shared across principals, and as such are not associated with a specific AWSAccount.

> **Additional Labels**: This node also uses `AWSPolicy`.

> **Additional Label Definitions**:
>
> - `AWSPolicy`: A aws node participating in the shared AWSPolicy graph interface.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Unique identifier for this `AWSManagedPolicy` node. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| arn | Yes | Amazon Resource Name (ARN) of this `AWSManagedPolicy` node. |
| name |  | Name of this `AWSManagedPolicy` node. |
| type |  | Type of this `AWSManagedPolicy` node. |

#### Relationships

- `(:AWSPrincipal)-[:POLICY]->(:AWSManagedPolicy)`

### AWSMfaDevice

Representation of an AWS [MFA Device](https://docs.aws.amazon.com/IAM/latest/APIReference/API_MFADevice.html).

> **Additional Labels**: This node also uses `MfaDevice`.

> **Additional Label Definitions**:
>
> - `MfaDevice`: A aws node participating in the shared MfaDevice graph interface.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The serial number of the MFA device (same as serialnumber) |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| enabledate |  | ISO 8601 date-time string when the MFA device was enabled |
| enabledate_dt |  | DateTime object representing when the MFA device was enabled |
| serialnumber | Yes | The serial number that uniquely identifies the MFA device |
| user_arn |  | The ARN of the IAM user associated with the MFA device |
| username |  | The username of the IAM user associated with the MFA device |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSMfaDevice)`

- `(:AWSUser)-[:MFA_DEVICE]->(:AWSMfaDevice)`

### AWSNameServer

Representation of a DNS name server associated with an AWS Route53 hosted zone.

> **Additional Labels**: This node also uses `NameServer`.

> **Additional Label Definitions**:
>
> - `NameServer`: Compatibility label for the deprecated `NameServer` aws node label. Use `AWSNameServer` instead. Scheduled for removal in v1.0.0.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The address of the nameserver |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| name | Yes | The name or address of the nameserver |
| zoneid |  | The ID of the Route53 hosted zone this name server belongs to |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSNameServer)`

- `(:AWSDNSRecord)-[:DNS_POINTS_TO]->(:AWSNameServer)`

- `(:AWSDNSZone)-[:NAMESERVER]->(:AWSNameServer)`

### AWSNetworkInterface

Representation of a generic Network Interface.  Currently however, we only create AWSNetworkInterface nodes from AWS [EC2 Instances](#awsec2instance).  The spec for an AWS EC2 network interface is [here](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_InstanceNetworkInterface.html).

> **Additional Labels**: This node also uses `NetworkInterface`.

> **Additional Label Definitions**:
>
> - `NetworkInterface`: A node participating in the shared NetworkInterface graph interface.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The ID of the network interface.  (known as `networkInterfaceId` in EC2) |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| attach_time |  | The timestamp when the network interface was attached to an EC2 instance. For primary interfaces (device_index=0), this reveals the first launch time of the instance [according to AWS](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_Instance.html). |
| description |  | Description of the network interface |
| device_index |  | The index of the device on the instance for the network interface attachment. A value of `0` indicates the primary (eth0) network interface, which is created when the instance is launched. |
| interface_type |  | Describes the type of network interface. Valid values: `` interface \| efa `` |
| mac_address | Yes | The MAC address of the network interface |
| private_dns_name | Yes | The private DNS name |
| private_ip_address | Yes | The primary IPv4 address of the network interface within the subnet |
| public_ip | Yes | Public IPv4 address attached to the interface |
| region |  | The AWS region |
| requester_id | Yes | Id of the requester, e.g. `amazon-elb` for ELBs |
| requester_managed |  | Indicates whether the interface is managed by the requester |
| source_dest_check |  | Indicates whether to validate network traffic to or from this network interface. |
| status |  | Status of the network interface.  Valid Values: ``available \| associated \| attaching \| in-use \| detaching `` |
| subnet_id | Yes | The ID of the subnet |
| subnetid | Yes | The ID of the subnet |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSNetworkInterface)`

- `(:AWSEC2Instance)-[:NETWORK_INTERFACE]->(:AWSNetworkInterface)`

- `(:AWSECSTask)-[:NETWORK_INTERFACE]->(:AWSNetworkInterface)`

- `(:AWSLoadBalancer)-[:NETWORK_INTERFACE]->(:AWSNetworkInterface)`

- `(:AWSLoadBalancerV2)-[:NETWORK_INTERFACE]->(:AWSNetworkInterface)`

- `(:AWSNetworkInterface)-[:ELASTIC_IP_ADDRESS]->(:AWSElasticIPAddress)`

- `(:AWSNetworkInterface)-[:IPV6_ADDRESS]->(:AWSEC2Ipv6Address)`

- `(:AWSNetworkInterface)-[:MEMBER_OF_EC2_SECURITY_GROUP]->(:AWSEC2SecurityGroup)`

- `(:AWSNetworkInterface)-[:PART_OF_SUBNET]->(:AWSEC2Subnet)`

- `(:AWSNetworkInterface)-[:PRIVATE_IP_ADDRESS]->(:AWSEC2PrivateIp)`

- `(:AWSNetworkInterface)-[:TAGGED]->(:AWSTag)`: `AWSNetworkInterface` is tagged with an `AWSTag` discovered by the AWS Resource Groups Tagging API.

### AWSOrganization

Representation of an AWS Organization.

> **Ontology Mapping**: This node uses the ontology label [`Tenant`](#ontology-tenant).

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The AWS Organization ID. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| arn | Yes | The AWS Organization ARN. |
| feature_set |  | The feature set of the organization, such as `ALL` or `CONSOLIDATED_BILLING`. |
| management_account_arn |  | The ARN of the organization's management account. |
| management_account_email |  | The email address of the organization's management account. |
| management_account_id | Yes | The ID of the organization's management account. |
| *_ont_name* | Yes | Normalized field sourced from `id`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |

#### Relationships

- `(:AWSOrganization)-[:RESOURCE]->(:AWSOrganizationRoot)`

- `(:AWSOrganizationRoot)-[:PARENT]->(:AWSOrganization)`

### AWSOrganizationalUnit

Representation of an AWS Organizations organizational unit.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Cartography ID for this organizational unit, formatted as `{org_id}/{ou_id}` because AWS organizational unit IDs are unique only within an organization. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| arn | Yes | The AWS Organizations organizational unit ARN. |
| name |  | The AWS Organizations organizational unit name. |
| org_id | Yes | The AWS Organization ID. |
| ou_id | Yes | The raw AWS Organizations organizational unit ID. |
| parent_ou_id |  | The Cartography parent organizational unit ID, when the organizational unit is nested under another organizational unit. |
| parent_root_id |  | The Cartography parent root ID, when the organizational unit is directly under a root. |
| root_id | Yes | The Cartography root ID that scopes the organizational unit, formatted as `{org_id}/{root_id}`. |

#### Relationships

- `(:AWSAccount)-[:PARENT]->(:AWSOrganizationalUnit)`

- `(:AWSOrganizationRoot)-[:RESOURCE]->(:AWSOrganizationalUnit)`

- `(:AWSOrganizationalUnit)-[:PARENT]->(:AWSOrganizationRoot)`

- `(:AWSOrganizationalUnit)-[:PARENT]->(:AWSOrganizationalUnit)`

- `(:AWSOrganizationalUnit)-[:RESOURCE]->(:AWSAccount)`

- `(:AWSOrganizationalUnit)-[:RESOURCE]->(:AWSOrganizationalUnit)`

### AWSOrganizationRoot

Representation of an AWS Organizations root.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Cartography ID for this root, formatted as `{org_id}/{root_id}` because AWS root IDs are unique only within an organization. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| arn | Yes | The AWS Organizations root ARN. |
| name |  | The AWS Organizations root name. |
| org_id | Yes | The AWS Organization ID. |
| root_id | Yes | The raw AWS Organizations root ID. |

#### Relationships

- `(:AWSAccount)-[:PARENT]->(:AWSOrganizationRoot)`

- `(:AWSOrganization)-[:RESOURCE]->(:AWSOrganizationRoot)`

- `(:AWSOrganizationRoot)-[:PARENT]->(:AWSOrganization)`

- `(:AWSOrganizationRoot)-[:RESOURCE]->(:AWSAccount)`

- `(:AWSOrganizationRoot)-[:RESOURCE]->(:AWSOrganizationalUnit)`

- `(:AWSOrganizationalUnit)-[:PARENT]->(:AWSOrganizationRoot)`

### AWSPeeringConnection

Representation of an AWS [PeeringConnection](https://docs.aws.amazon.com/vpc/latest/peering/what-is-vpc-peering.html) implementing an AWS [VpcPeeringConnection](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_VpcPeeringConnection.html) object.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | vpcPeeringConnectionId, The ID of the VPC peering connection. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| accepter_region |  | Peering accepter region |
| allow_dns_resolution_from_remote_vpc |  | Indicates whether a local VPC can resolve public DNS hostnames to private IP addresses when queried from instances in a peer VPC. |
| allow_egress_from_local_classic_link_to_remote_vpc |  | Indicates whether a local ClassicLink connection can communicate with the peer VPC over the VPC peering connection. |
| allow_egress_from_local_vpc_to_remote_classic_link |  | Indicates whether a local VPC can communicate with a ClassicLink connection in the peer VPC over the VPC peering connection. |
| requester_region |  | Peering requester region |
| status_code |  | The status of the VPC peering connection. |
| status_message |  | A message that provides more information about the status, if applicable. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSPeeringConnection)`

- `(:AWSPeeringConnection)-[:ACCEPTER_CIDR]->(:AWSCidrBlock)`

- `(:AWSPeeringConnection)-[:ACCEPTER_VPC]->(:AWSVpc)`

- `(:AWSPeeringConnection)-[:REQUESTER_CIDR]->(:AWSCidrBlock)`

- `(:AWSPeeringConnection)-[:REQUESTER_VPC]->(:AWSVpc)`

### AWSPermissionSet

Representation of an AWS Identity Center Permission Set.

> **Ontology Mapping**: This node uses the ontology label [`PermissionRole`](#ontology-permissionrole).

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Unique identifier for the Permission Set |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| arn |  | The Amazon Resource Name (ARN) of the Permission Set |
| description |  | The description of the Permission Set |
| instance_arn |  | The ARN of the Identity Center instance the Permission Set belongs to |
| name |  | The name of the Permission Set |
| region |  | The AWS region where the Permission Set is located |
| session_duration |  | The session duration of the Permission Set |
| *_ont_name* | Yes | Normalized field sourced from `name`. |
| *_ont_scope* | Yes | Property generated by the ontology mapping. |
| *_ont_source* |  | Module that populated this node's ontology fields. |
| *_ont_type* | Yes | Property generated by the ontology mapping. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSPermissionSet)`

- `(:AWSIdentityCenter)-[:HAS_PERMISSION_SET]->(:AWSPermissionSet)`

- `(:AWSPermissionSet)-[:ASSIGNED_TO_ROLE]->(:AWSRole)`

- `(:AWSSSOGroup)-[:HAS_PERMISSION_SET]->(:AWSPermissionSet)`

- `(:AWSSSOGroup)-[:HAS_ROLE]->(:AWSPermissionSet)`

- `(:AWSSSOUser)-[:HAS_PERMISSION_SET]->(:AWSPermissionSet)`

- `(:AWSSSOUser)-[:HAS_ROLE]->(:AWSPermissionSet)`

### AWSPolicyStatement

Representation of an [AWS Policy Statement](https://docs.aws.amazon.com/IAM/latest/APIReference/API_Statement.html).

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The unique identifier for a statement. <br>If the statement has an Sid the id will be calculated as _AWSPolicy.id_/statements/_Sid_. <br>If the statement has no Sid the id will be calculated as  _AWSPolicy.id_/statements/_index of statement in statement list_ |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| action |  | (array) The permissions allowed or denied by the statement. Can contain wildcards |
| condition |  | Conditions under which the statement applies |
| effect |  | "Allow" or "Deny" - the effect of this statement |
| notaction |  | (array) The permissions explicitly not matched by the statement |
| notresource |  | (array) The resources explicitly not matched by the statement |
| resource |  | (array) The resources the statement is applied to. Can contain wildcards |
| sid |  | Statement ID - an optional identifier for the policy statement |

#### Relationships

- `(:AWSPolicy)-[:STATEMENT]->(:AWSPolicyStatement)`

### AWSPrincipal

Representation of an [AWSPrincipal](https://docs.aws.amazon.com/IAM/latest/APIReference/API_User.html).

This composite schema adds service access properties to AWSPrincipal nodes. It uses
the same label as existing AWSUser/AWSRole/AWSGroup to merge properties.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Unique identifier for this `AWSPrincipal` node. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| arn | Yes | AWS-unique identifier for this object |
| last_accessed_service_name |  | Display name of the AWS service most recently accessed by the principal. |
| last_accessed_service_namespace |  | Namespace of the AWS service most recently accessed by the principal. |
| last_authenticated |  | Timestamp when the principal last authenticated to the service. |
| last_authenticated_entity |  | ARN of the principal entity that last authenticated to the service. |
| last_authenticated_region |  | AWS Region in which the principal last authenticated to the service. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSPrincipal)`

- `(:AWSLambda)-[:STS_ASSUMEROLE_ALLOW]->(:AWSPrincipal)`

- `(:AWSPrincipal)-[:ASSUMED_ROLE]->(:AWSRole)`: MatchLink schema for ASSUMED_ROLE relationships from CloudTrail events.
Creates relationships like: (AWSUser|AWSRole|AWSPrincipal)-[:ASSUMED_ROLE]->(AWSRole)

This MatchLink handles role assumption relationships discovered via CloudTrail management events.
It supports multiple source node types and aggregated relationship properties.
  - Properties:

    | Field | Description |
    |-------|-------------|
    | first_seen_in_time_window | Timestamp when this relationship was first observed in the current time window. |
    | last_used | Timestamp when this relationship was last observed in use. |
    | times_used | Number of times this relationship was observed in use. |

- `(:AWSPrincipal)-[:CAN_ADMINISTER]->(:AWSRDSInstance)`: `AWSPrincipal` receives evaluated `CAN_ADMINISTER` access to `AWSRDSInstance` from AWS IAM policies.
  - Evaluated permissions: `rds:*`, `rds:DeleteDBInstance`, `rds:ModifyDBInstance`, `rds:RebootDBInstance`, `rds:StartDBInstance`, `rds:StopDBInstance`
  - Properties:

    | Field | Description |
    |-------|-------------|
    | condition_keys | IAM condition context keys used by the permission. |
    | conditions | IAM conditions that restrict this permission. |
    | has_condition | Whether an IAM condition restricts this permission. |

- `(:AWSPrincipal)-[:CAN_ADMINISTER]->(:AWSRedshiftCluster)`: `AWSPrincipal` receives evaluated `CAN_ADMINISTER` access to `AWSRedshiftCluster` from AWS IAM policies.
  - Evaluated permissions: `redshift:*`, `redshift:CreateClusterUser`, `redshift:GetClusterCredentials`, `redshift:JoinGroup`
  - Properties:

    | Field | Description |
    |-------|-------------|
    | condition_keys | IAM condition context keys used by the permission. |
    | conditions | IAM conditions that restrict this permission. |
    | has_condition | Whether an IAM condition restricts this permission. |

- `(:AWSPrincipal)-[:CAN_EXEC]->(:AWSCloudFormationStack)`: `AWSPrincipal` receives evaluated `CAN_EXEC` access to `AWSCloudFormationStack` from AWS IAM policies.
  - Evaluated permissions: `cloudformation:UpdateStack`
  - Properties:

    | Field | Description |
    |-------|-------------|
    | condition_keys | IAM condition context keys used by the permission. |
    | conditions | IAM conditions that restrict this permission. |
    | has_condition | Whether an IAM condition restricts this permission. |

- `(:AWSPrincipal)-[:CAN_EXECUTE_COMMAND]->(:AWSECSTask)`: `AWSPrincipal` receives evaluated `CAN_EXECUTE_COMMAND` access to `AWSECSTask` from AWS IAM policies.
  - Evaluated permissions: `ecs:ExecuteCommand`
  - Properties:

    | Field | Description |
    |-------|-------------|
    | condition_keys | IAM condition context keys used by the permission. |
    | conditions | IAM conditions that restrict this permission. |
    | has_condition | Whether an IAM condition restricts this permission. |

- `(:AWSPrincipal)-[:CAN_PASS_ROLE]->(:AWSRole)`: `AWSPrincipal` receives evaluated `CAN_PASS_ROLE` access to `AWSRole` from AWS IAM policies.
  - Evaluated permissions: `iam:PassRole`
  - Properties:

    | Field | Description |
    |-------|-------------|
    | condition_keys | IAM condition context keys used by the permission. |
    | conditions | IAM conditions that restrict this permission. |
    | has_condition | Whether an IAM condition restricts this permission. |

- `(:AWSPrincipal)-[:CAN_QUERY]->(:AWSDynamoDBTable)`: `AWSPrincipal` receives evaluated `CAN_QUERY` access to `AWSDynamoDBTable` from AWS IAM policies.
  - Evaluated permissions: `dynamodb:BatchGetItem`, `dynamodb:GetItem`, `dynamodb:GetRecords`, `dynamodb:Query`, `dynamodb:Scan`
  - Properties:

    | Field | Description |
    |-------|-------------|
    | condition_keys | IAM condition context keys used by the permission. |
    | conditions | IAM conditions that restrict this permission. |
    | has_condition | Whether an IAM condition restricts this permission. |

- `(:AWSPrincipal)-[:CAN_QUERY]->(:AWSRDSInstance)`: `AWSPrincipal` receives evaluated `CAN_QUERY` access to `AWSRDSInstance` from AWS IAM policies.
  - Evaluated permissions: `rds-db:connect`
  - Properties:

    | Field | Description |
    |-------|-------------|
    | condition_keys | IAM condition context keys used by the permission. |
    | conditions | IAM conditions that restrict this permission. |
    | has_condition | Whether an IAM condition restricts this permission. |

- `(:AWSPrincipal)-[:CAN_READ]->(:AWSS3Bucket)`: `AWSPrincipal` receives evaluated `CAN_READ` access to `AWSS3Bucket` from AWS IAM policies.
  - Evaluated permissions: `S3:GetObject`
  - Properties:

    | Field | Description |
    |-------|-------------|
    | condition_keys | IAM condition context keys used by the permission. |
    | conditions | IAM conditions that restrict this permission. |
    | has_condition | Whether an IAM condition restricts this permission. |

- `(:AWSPrincipal)-[:CAN_START_SESSION]->(:AWSEC2Instance)`: `AWSPrincipal` receives evaluated `CAN_START_SESSION` access to `AWSEC2Instance` from AWS IAM policies.
  - Evaluated permissions: `ssm:StartSession`
  - Target precondition: `(:AWSEC2Instance)-[:HAS_INFORMATION]->(:AWSSSMInstanceInformation)` must exist
  - Properties:

    | Field | Description |
    |-------|-------------|
    | condition_keys | IAM condition context keys used by the permission. |
    | conditions | IAM conditions that restrict this permission. |
    | has_condition | Whether an IAM condition restricts this permission. |

- `(:AWSPrincipal)-[:CAN_WRITE]->(:AWSDynamoDBTable)`: `AWSPrincipal` receives evaluated `CAN_WRITE` access to `AWSDynamoDBTable` from AWS IAM policies.
  - Evaluated permissions: `dynamodb:BatchWriteItem`, `dynamodb:DeleteItem`, `dynamodb:PutItem`, `dynamodb:UpdateItem`
  - Properties:

    | Field | Description |
    |-------|-------------|
    | condition_keys | IAM condition context keys used by the permission. |
    | conditions | IAM conditions that restrict this permission. |
    | has_condition | Whether an IAM condition restricts this permission. |

- `(:AWSPrincipal)-[:CAN_WRITE]->(:AWSS3Bucket)`: `AWSPrincipal` receives evaluated `CAN_WRITE` access to `AWSS3Bucket` from AWS IAM policies.
  - Evaluated permissions: `S3:PutObject`
  - Properties:

    | Field | Description |
    |-------|-------------|
    | condition_keys | IAM condition context keys used by the permission. |
    | conditions | IAM conditions that restrict this permission. |
    | has_condition | Whether an IAM condition restricts this permission. |

- `(:AWSPrincipal)-[:GET_SECRET]->(:AWSSecretsManagerSecret)`: `AWSPrincipal` receives evaluated `GET_SECRET` access to `AWSSecretsManagerSecret` from AWS IAM policies.
  - Evaluated permissions: `secretsmanager:GetSecretValue`
  - Properties:

    | Field | Description |
    |-------|-------------|
    | condition_keys | IAM condition context keys used by the permission. |
    | conditions | IAM conditions that restrict this permission. |
    | has_condition | Whether an IAM condition restricts this permission. |

- `(:AWSPrincipal)-[:GRANTED_ACCESS_TO]->(:AWSEKSAccessEntry)`: An AWS principal is granted cluster access through an EKS access entry.

- `(:AWSPrincipal)-[:POLICY]->(:AWSInlinePolicy)`

- `(:AWSPrincipal)-[:POLICY]->(:AWSManagedPolicy)`

- `(:AWSPrincipal)-[:STS_ASSUMEROLE_ALLOW]->(:AWSRole)`

- `(:AWSRedshiftCluster)-[:STS_ASSUMEROLE_ALLOW]->(:AWSPrincipal)`

- `(:AWSRole)-[:TRUSTS_AWS_PRINCIPAL]->(:AWSPrincipal)`: Trust relationship with principals of type "AWS".

- `(:DatabricksCredentialConfig)-[:ASSUMES_ROLE]->(:AWSPrincipal)`: A Databricks credential configuration assumes an AWS IAM role.

- `(:DatabricksStorageCredential)-[:ASSUMES_ROLE]->(:AWSPrincipal)`: A Databricks storage credential assumes an AWS IAM role.

### AWSPublicSSMParameter

Representation of an AWS-managed public [Systems Manager Parameter Store parameter](https://docs.aws.amazon.com/systems-manager/latest/userguide/parameter-store-public-parameters.html). These parameters are shared regional catalog data and are not owned by an individual AWS Account.

> **Additional Labels**: This node also uses `PublicSSMParameter`, `SSMParameter`.

> **Additional Label Definitions**:
>
> - `PublicSSMParameter`: Compatibility label for the deprecated `PublicSSMParameter` aws node label. Use `AWSPublicSSMParameter` instead. Scheduled for removal in v1.0.0.
> - `SSMParameter`: A aws node participating in the shared SSMParameter graph interface.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The AWS parameter ARN. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| allowedpattern |  | A regular expression that defines the constraints on the parameter value. |
| arn | Yes | The Amazon Resource Name (ARN) of the parameter. |
| datatype |  | The data type of the parameter, such as text or aws:ec2:image. |
| description |  | Description of the parameter actions. |
| keyid |  | The alias or ARN of the Key Management Service (KMS) key used to encrypt the parameter. Applies to SecureString parameters only. |
| kms_key_id_short |  | The shortened KMS Key ID used to encrypt the parameter. |
| lastmodifieddate |  | Date the parameter was last changed or updated (stored as epoch time). |
| lastmodifieduser |  | Amazon Resource Name (ARN) of the AWS user who last changed the parameter. |
| name |  | The parameter name. |
| policies_json |  | A JSON string representation of the list of policies associated with the parameter. |
| region |  | The region of the parameter. |
| tier |  | The parameter tier. |
| type |  | The type of parameter. Valid parameter types include String, StringList, and SecureString. |
| value |  | The parameter value for AWS-managed public parameters fetched with `GetParametersByPath`. Private parameters discovered with `DescribeParameters` have no value. |
| version |  | The parameter version. |

#### Relationships

No relationships.

### AWSRDSCluster

Representation of an AWS Relational Database Service [DBCluster](https://docs.aws.amazon.com/AmazonRDS/latest/APIReference/API_DBCluster.html)

> **Additional Labels**: This node also uses `RDSCluster`.

> **Additional Label Definitions**:
>
> - `RDSCluster`: Compatibility label for the deprecated `RDSCluster` aws node label. Use `AWSRDSCluster` instead. Scheduled for removal in v1.0.0.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Same as ARN |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| allocated_storage |  | For all database engines except Amazon Aurora, AllocatedStorage specifies the allocated storage size in gibibytes (GiB). For Aurora, AllocatedStorage always returns 1, because Aurora DB cluster storage size isn't fixed, but instead automatically adjusts as needed. |
| arn | Yes | The Amazon Resource Name (ARN) for the DB cluster. |
| availability_zones |  | Provides the list of Availability Zones (AZs) where instances in the DB cluster can be created. |
| backtrack_consumed_change_records |  | The number of change records stored for Backtrack. |
| backtrack_window |  | The target backtrack window, in seconds. If this value is set to 0, backtracking is disabled for the DB cluster. Otherwise, backtracking is enabled. |
| backup_retention_period |  | Specifies the number of days for which automatic DB snapshots are retained. |
| capacity |  | The current capacity of an Aurora Serverless DB cluster. The capacity is 0 (zero) when the cluster is paused. |
| character_set_name |  | If present, specifies the name of the character set that this cluster is associated with. |
| clone_group_id |  | Identifies the clone group to which the DB cluster is associated. |
| cluster_create_time |  | Specifies the time when the DB cluster was created, in Universal Coordinated Time (UTC). |
| database_name |  | Contains the name of the initial database of this DB cluster that was provided at create time, if one was specified when the DB cluster was created. This same name is returned for the life of the DB cluster. |
| db_cluster_identifier | Yes | Contains a user-supplied DB cluster identifier. This identifier is the unique key that identifies a DB cluster. |
| db_cluster_resource_id |  | The AWS Region-unique, immutable identifier for the DB cluster. This identifier is found in AWS CloudTrail log entries whenever the AWS KMS CMK for the DB cluster is accessed. |
| db_parameter_group |  | Specifies the name of the DB cluster parameter group for the DB cluster. |
| deletion_protection |  | Indicates if the DB cluster has deletion protection enabled. The database can't be deleted when deletion protection is enabled. |
| earliest_backtrack_time |  | The earliest time to which a DB cluster can be backtracked. |
| earliest_restorable_time |  | The earliest time to which a database can be restored with point-in-time restore. |
| endpoint |  | Specifies the connection endpoint for the primary instance of the DB cluster. |
| engine |  | The name of the database engine to be used for this DB cluster. |
| engine_mode |  | The DB engine mode of the DB cluster, either provisioned, serverless, parallelquery, global, or multimaster. |
| engine_version |  | Indicates the database engine version. |
| hosted_zone_id |  | Specifies the ID that Amazon Route 53 assigns when you create a hosted zone. |
| kms_key_id |  | If StorageEncrypted is enabled, the AWS KMS key identifier for the encrypted DB cluster. The AWS KMS key identifier is the key ARN, key ID, alias ARN, or alias name for the AWS KMS customer master key (CMK). |
| latest_restorable_time |  | Specifies the latest time to which a database can be restored with point-in-time restore. |
| master_username |  | Contains the master username for the DB cluster. |
| multi_az |  | Specifies whether the DB cluster has instances in multiple Availability Zones. |
| port |  | Specifies the port that the database engine is listening on. |
| preferred_backup_window |  | Specifies the daily time range during which automated backups are created if automated backups are enabled, as determined by the BackupRetentionPeriod. |
| preferred_maintenance_window |  | Specifies the weekly time range during which system maintenance can occur, in Universal Coordinated Time (UTC). |
| reader_endpoint |  | The reader endpoint for the DB cluster. The reader endpoint for a DB cluster load-balances connections across the Aurora Replicas that are available in a DB cluster. As clients request new connections to the reader endpoint, Aurora distributes the connection requests among the Aurora Replicas in the DB cluster. This functionality can help balance your read workload across multiple Aurora Replicas in your DB cluster. If a failover occurs, and the Aurora Replica that you are connected to is promoted to be the primary instance, your connection is dropped. To continue sending your read workload to other Aurora Replicas in the cluster, you can then reconnect to the reader endpoint. |
| region |  | AWS Region containing this `AWSRDSCluster` node. |
| scaling_configuration_info_auto_pause |  | A value that indicates whether automatic pause is allowed for the Aurora DB cluster in serverless DB engine mode. |
| scaling_configuration_info_max_capacity |  | The maximum capacity for an Aurora DB cluster in serverless DB engine mode. |
| scaling_configuration_info_min_capacity |  | The minimum capacity for the Aurora DB cluster in serverless DB engine mode. |
| status |  | Specifies the current state of this DB cluster. |
| storage_encrypted |  | Specifies whether the DB cluster is encrypted. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSRDSCluster)`

- `(:AWSRDSCluster)-[:TAGGED]->(:AWSTag)`: `AWSRDSCluster` is tagged with an `AWSTag` discovered by the AWS Resource Groups Tagging API.

- `(:AWSRDSEventSubscription)-[:MONITORS]->(:AWSRDSCluster)`

- `(:AWSRDSInstance)-[:IS_CLUSTER_MEMBER_OF]->(:AWSRDSCluster)`

### AWSRDSEventSubscription

Representation of an AWS Relational Database Service [EventSubscription](https://docs.aws.amazon.com/AmazonRDS/latest/APIReference/API_EventSubscription.html).

> **Additional Labels**: This node also uses `RDSEventSubscription`.

> **Additional Label Definitions**:
>
> - `RDSEventSubscription`: Compatibility label for the deprecated `RDSEventSubscription` aws node label. Use `AWSRDSEventSubscription` instead. Scheduled for removal in v1.0.0.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The customer subscription identifier |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| arn | Yes | The Amazon Resource Name (ARN) for the event subscription |
| customer_aws_id |  | The AWS customer account associated with the event subscription |
| enabled |  | Whether the event subscription is enabled |
| event_categories |  | List of event categories for which to receive notifications |
| region |  | The AWS region where the event subscription is located |
| sns_topic_arn |  | The ARN of the SNS topic to which notifications are sent |
| source_ids |  | List of source identifiers for which to receive notifications |
| source_type |  | The type of source that is generating the events (db-instance, db-cluster, db-snapshot) |
| status |  | The status of the event subscription (active, inactive) |
| subscription_creation_time |  | The time the event subscription was created |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSRDSEventSubscription)`

- `(:AWSRDSEventSubscription)-[:MONITORS]->(:AWSRDSCluster)`

- `(:AWSRDSEventSubscription)-[:MONITORS]->(:AWSRDSInstance)`

- `(:AWSRDSEventSubscription)-[:MONITORS]->(:AWSRDSSnapshot)`

- `(:AWSRDSEventSubscription)-[:NOTIFIES]->(:AWSSNSTopic)`

### AWSRDSInstance

Representation of an AWS Relational Database Service [DBInstance](https://docs.aws.amazon.com/AmazonRDS/latest/APIReference/API_DBInstance.html).

> **Ontology Mapping**: This node uses the ontology label [`Database`](#ontology-database).

> **Additional Labels**: This node also uses `RDSInstance`.

> **Additional Label Definitions**:
>
> - `RDSInstance`: Compatibility label for the deprecated `RDSInstance` aws node label. Use `AWSRDSInstance` instead. Scheduled for removal in v1.0.0.

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Same as ARN |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| arn | Yes | The Amazon Resource Name (ARN) for the DB instance. |
| auto_minor_version_upgrade |  | Specifies whether minor version upgrades are applied automatically to the DB instance during the maintenance window |
| availability_zone |  | Specifies the name of the Availability Zone the DB instance is located in. |
| backup_retention_period |  | Specifies the number of days for which automatic DB snapshots are retained. |
| ca_certificate_identifier |  | The identifier of the CA certificate for this DB instance. |
| db_cluster_identifier |  | If the DB instance is a member of a DB cluster, contains the name of the DB cluster that the DB instance is a member of. |
| db_instance_class |  | Contains the name of the compute and memory capacity class of the DB instance. |
| db_instance_identifier | Yes | Contains a user-supplied database identifier. This identifier is the unique key that identifies a DB instance. |
| db_name |  | The meaning of this parameter differs according to the database engine you use. For example, this value returns MySQL, MariaDB, or PostgreSQL information when returning values from CreateDBInstanceReadReplica since Read Replicas are only supported for these engines.<br><br>**MySQL, MariaDB, SQL Server, PostgreSQL:** Contains the name of the initial database of this instance that was provided at create time, if one was specified when the DB instance was created. This same name is returned for the life of the DB instance.<br><br>**Oracle:** Contains the Oracle System ID (SID) of the created DB instance. Not shown when the returned parameters do not apply to an Oracle DB instance. |
| dbi_resource_id |  | The AWS Region-unique, immutable identifier for the DB instance. This identifier is found in AWS CloudTrail log entries whenever the AWS KMS key for the DB instance is accessed. |
| deletion_protection |  | Whether deletion protection is enabled for the DB instance. |
| endpoint_address |  | DNS name of the RDS instance |
| endpoint_hostedzoneid |  | The AWS DNS Zone ID that is associated with the RDS instance's DNS entry |
| endpoint_port |  | The port that the RDS instance is listening on |
| engine |  | Provides the name of the database engine to be used for this DB instance. |
| engine_version |  | Indicates the database engine version. |
| enhanced_monitoring_resource_arn |  | The Amazon Resource Name (ARN) of the Amazon CloudWatch Logs log stream that receives the Enhanced Monitoring metrics data for the DB instance. |
| iam_database_authentication_enabled |  | Specifies if mapping of AWS Identity and Access Management (IAM) accounts to database accounts is enabled |
| instance_create_time |  | Provides the date and time the DB instance was created. |
| kms_key_id |  | If StorageEncrypted is true, the AWS KMS key identifier for the encrypted DB instance. |
| latest_restorable_time |  | Latest timestamp to which the DB instance can be restored. |
| master_username |  | Contains the master username for the DB instance. |
| monitoring_role_arn |  | The ARN for the IAM role that permits RDS to send Enhanced Monitoring metrics to Amazon CloudWatch Logs. |
| multi_az |  | Specifies if the DB instance is a Multi-AZ deployment. |
| performance_insights_enabled |  | True if Performance Insights is enabled for the DB instance, and otherwise false. |
| performance_insights_kms_key_id |  | Identifier of the performance insights KMS key linked to this `AWSRDSInstance` node. |
| preferred_backup_window |  | Specifies the daily time range during which automated backups are created if automated backups are enabled, as determined by the BackupRetentionPeriod. |
| preferred_maintenance_window |  | Specifies the weekly time range during which system maintenance can occur, in Universal Coordinated Time (UTC). |
| publicly_accessible |  | Specifies the accessibility options for the DB instance. A value of true specifies an Internet-facing instance with a publicly resolvable DNS name, which resolves to a public IP address. A value of false specifies an internal instance with a DNS name that resolves to a private IP address. |
| region |  | AWS Region containing this `AWSRDSInstance` node. |
| storage_encrypted |  | Specifies whether the DB instance is encrypted. |
| *_ont_encrypted* | Yes | Normalized field sourced from `storage_encrypted`. |
| *_ont_endpoint* | Yes | Normalized field sourced from `endpoint_address`. |
| *_ont_location* | Yes | Normalized field sourced from `region`. |
| *_ont_name* | Yes | Normalized field sourced from `db_instance_identifier`. |
| *_ont_port* | Yes | Normalized field sourced from `endpoint_port`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |
| *_ont_type* | Yes | Normalized field sourced from `engine`. |
| *_ont_version* | Yes | Normalized field sourced from `engine_version`. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSRDSInstance)`

- `(:AWSPrincipal)-[:CAN_ADMINISTER]->(:AWSRDSInstance)`: `AWSPrincipal` receives evaluated `CAN_ADMINISTER` access to `AWSRDSInstance` from AWS IAM policies.
  - Evaluated permissions: `rds:*`, `rds:DeleteDBInstance`, `rds:ModifyDBInstance`, `rds:RebootDBInstance`, `rds:StartDBInstance`, `rds:StopDBInstance`
  - Properties:

    | Field | Description |
    |-------|-------------|
    | condition_keys | IAM condition context keys used by the permission. |
    | conditions | IAM conditions that restrict this permission. |
    | has_condition | Whether an IAM condition restricts this permission. |

- `(:AWSPrincipal)-[:CAN_QUERY]->(:AWSRDSInstance)`: `AWSPrincipal` receives evaluated `CAN_QUERY` access to `AWSRDSInstance` from AWS IAM policies.
  - Evaluated permissions: `rds-db:connect`
  - Properties:

    | Field | Description |
    |-------|-------------|
    | condition_keys | IAM condition context keys used by the permission. |
    | conditions | IAM conditions that restrict this permission. |
    | has_condition | Whether an IAM condition restricts this permission. |

- `(:AWSRDSEventSubscription)-[:MONITORS]->(:AWSRDSInstance)`

- `(:AWSRDSInstance)-[:ENCRYPTED_BY]->(:AWSKMSKey)`

- `(:AWSRDSInstance)-[:IS_CLUSTER_MEMBER_OF]->(:AWSRDSCluster)`

- `(:AWSRDSInstance)-[:IS_READ_REPLICA_OF]->(:AWSRDSInstance)`

- `(:AWSRDSInstance)-[:MEMBER_OF_DB_SUBNET_GROUP]->(:AWSDBSubnetGroup)`

- `(:AWSRDSInstance)-[:MEMBER_OF_EC2_SECURITY_GROUP]->(:AWSEC2SecurityGroup)`

- `(:AWSRDSInstance)-[:TAGGED]->(:AWSTag)`: `AWSRDSInstance` is tagged with an `AWSTag` discovered by the AWS Resource Groups Tagging API.

- `(:AWSRDSSnapshot)-[:IS_SNAPSHOT_SOURCE]->(:AWSRDSInstance)`

### AWSRDSSnapshot

Representation of an AWS Relational Database Service [DBSnapshot](https://docs.aws.amazon.com/AmazonRDS/latest/APIReference/API_DBSnapshot.html).

> **Ontology Mapping**: This node uses the ontology label [`Snapshot`](#ontology-snapshot).

> **Additional Labels**: This node also uses `RDSSnapshot`.

> **Additional Label Definitions**:
>
> - `RDSSnapshot`: Compatibility label for the deprecated `RDSSnapshot` aws node label. Use `AWSRDSSnapshot` instead. Scheduled for removal in v1.0.0.

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Same as ARN |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| allocated_storage |  | Specifies the allocated storage size in gibibytes (GiB). |
| arn | Yes | The Amazon Resource Name (ARN) for the DB snapshot. |
| availability_zone |  | Specifies the name of the Availability Zone the DB instance was located in at the time of the DB snapshot. |
| db_instance_identifier |  | Specifies the DB instance identifier of the DB instance this DB snapshot was created from. |
| db_snapshot_identifier | Yes | Specifies the identifier for the DB snapshot. |
| dbi_resource_id |  | The identifier for the source DB instance, which can't be changed and which is unique to an AWS Region. |
| encrypted |  | Specifies whether the DB snapshot is encrypted. |
| engine |  | Specifies the name of the database engine. |
| engine_version |  | Specifies the version of the database engine. |
| iam_database_authentication_enabled |  | True if mapping of AWS Identity and Access Management (IAM) accounts to database accounts is enabled, and otherwise false. |
| instance_create_time |  | Specifies the time in Coordinated Universal Time (UTC) when the DB instance, from which the snapshot was taken, was created. |
| iops |  | Specifies the Provisioned IOPS (I/O operations per second) value of the DB instance at the time of the snapshot. |
| ispublic |  | Whether this `AWSRDSSnapshot` node is publicly accessible. |
| kms_key_id |  | If Encrypted is true, the AWS KMS key identifier for the encrypted DB snapshot. The AWS KMS key identifier is the key ARN, key ID, alias ARN, or alias name for the KMS key. |
| license_model |  | License model information for the restored DB instance. |
| master_username |  | Provides the master username for the DB snapshot. |
| option_group_name |  | Provides the option group name for the DB snapshot. |
| original_snapshot_create_time |  | Specifies the time of the CreateDBSnapshot operation in Coordinated Universal Time (UTC). Doesn't change when the snapshot is copied. |
| percent_progress |  | The percentage of the estimated data that has been transferred. |
| port |  | Specifies the port that the database engine was listening on at the time of the snapshot. |
| processor_features |  | The number of CPU cores and the number of threads per core for the DB instance class of the DB instance when the DB snapshot was created. |
| region |  | The AWS region of the snapshot |
| snapshot_create_time |  | Specifies when the snapshot was taken in Coordinated Universal Time (UTC). Changes for the copy when the snapshot is copied. |
| snapshot_database_time |  | The timestamp of the most recent transaction applied to the database that you're backing up. Thus, if you restore a snapshot, SnapshotDatabaseTime is the most recent transaction in the restored DB instance. In contrast, originalSnapshotCreateTime specifies the system time that the snapshot completed. If you back up a read replica, you can determine the replica lag by comparing SnapshotDatabaseTime with originalSnapshotCreateTime. For example, if originalSnapshotCreateTime is two hours later than SnapshotDatabaseTime, then the replica lag is two hours. |
| snapshot_target |  | Specifies where manual snapshots are stored: AWS Outposts or the AWS Region. |
| snapshot_type |  | Provides the type of the DB snapshot. |
| source_db_snapshot_identifier |  | The DB snapshot Amazon Resource Name (ARN) that the DB snapshot was copied from. It only has a value in the case of a cross-account or cross-Region copy. |
| source_region |  | The AWS Region that the DB snapshot was created in or copied from. |
| status |  | Specifies the status of this DB snapshot. |
| storage_throughput |  | The storage throughput of the DB snapshot, in mebibytes per second (MiBps). |
| storage_type |  | Specifies the storage type associated with DB snapshot. |
| tde_credential_arn |  | The ARN from the key store with which to associate the instance for TDE encryption. |
| timezone |  | The time zone of the DB snapshot. In most cases, the Timezone element is empty. Timezone content appears only for snapshots taken from Microsoft SQL Server DB instances that were created with a time zone specified. |
| vpc_id |  | Provides the VPC ID associated with the DB snapshot. |
| *_ont_created_at* | Yes | Normalized field sourced from `snapshot_create_time`. |
| *_ont_encrypted* | Yes | Normalized field sourced from `encrypted`. |
| *_ont_name* | Yes | Normalized field sourced from `db_snapshot_identifier`. |
| *_ont_public* | Yes | Normalized field sourced from `ispublic`. |
| *_ont_region* | Yes | Normalized field sourced from `region`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |
| *_ont_source_id* | Yes | Normalized field sourced from `db_instance_identifier`. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSRDSSnapshot)`

- `(:AWSRDSEventSubscription)-[:MONITORS]->(:AWSRDSSnapshot)`

- `(:AWSRDSSnapshot)-[:IS_SNAPSHOT_SOURCE]->(:AWSRDSInstance)`

- `(:AWSRDSSnapshot)-[:TAGGED]->(:AWSTag)`: `AWSRDSSnapshot` is tagged with an `AWSTag` discovered by the AWS Resource Groups Tagging API.

### AWSRedshiftCluster

Representation of an AWS [AWSRedshiftCluster](https://docs.aws.amazon.com/redshift/latest/APIReference/API_Cluster.html).

> **Additional Labels**: This node also uses `RedshiftCluster`.

> **Additional Label Definitions**:
>
> - `RedshiftCluster`: Compatibility label for the deprecated `RedshiftCluster` aws node label. Use `AWSRedshiftCluster` instead. Scheduled for removal in v1.0.0.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Same as arn |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| arn | Yes | The Amazon Resource Name (ARN) for the Redshift cluster |
| availability_zone |  | Specifies the name of the Availability Zone the cluster is located in |
| cluster_create_time |  | Provides the date and time the cluster was created |
| cluster_identifier |  | The unique identifier of the cluster. |
| cluster_revision_number |  | The specific revision number of the database in the cluster. |
| cluster_status |  | The current state of the cluster. |
| db_name |  | The name of the initial database that was created when the cluster was created. This same name is returned for the life of the cluster. If an initial database was not specified, a database named dev was created by default. |
| encrypted |  | Specifies whether the cluster has encryption enabled |
| endpoint_address |  | DNS name of the Redshift cluster endpoint |
| endpoint_port |  | The port that the Redshift cluster's endpoint is listening on |
| master_username |  | The master user name for the cluster. This name is used to connect to the database that is specified in the DBName parameter. |
| node_type |  | The node type for the nodes in the cluster. |
| number_of_nodes |  | The number of compute nodes in the cluster. |
| publicly_accessible |  | A boolean value that, if true, indicates that the cluster can be accessed from a public network. |
| region |  | AWS Region containing this `AWSRedshiftCluster` node. |
| vpc_id |  | The identifier of the VPC the cluster is in, if the cluster is in a VPC. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSRedshiftCluster)`

- `(:AWSPrincipal)-[:CAN_ADMINISTER]->(:AWSRedshiftCluster)`: `AWSPrincipal` receives evaluated `CAN_ADMINISTER` access to `AWSRedshiftCluster` from AWS IAM policies.
  - Evaluated permissions: `redshift:*`, `redshift:CreateClusterUser`, `redshift:GetClusterCredentials`, `redshift:JoinGroup`
  - Properties:

    | Field | Description |
    |-------|-------------|
    | condition_keys | IAM condition context keys used by the permission. |
    | conditions | IAM conditions that restrict this permission. |
    | has_condition | Whether an IAM condition restricts this permission. |

- `(:AWSRedshiftCluster)-[:MEMBER_OF_AWS_VPC]->(:AWSVpc)`

- `(:AWSRedshiftCluster)-[:MEMBER_OF_EC2_SECURITY_GROUP]->(:AWSEC2SecurityGroup)`

- `(:AWSRedshiftCluster)-[:STS_ASSUMEROLE_ALLOW]->(:AWSPrincipal)`

- `(:AWSRedshiftCluster)-[:TAGGED]->(:AWSTag)`: `AWSRedshiftCluster` is tagged with an `AWSTag` discovered by the AWS Resource Groups Tagging API.

### AWSRole

Representation of an AWS [IAM Role](https://docs.aws.amazon.com/IAM/latest/APIReference/API_Role.html). An AWS Role is a type of AWS Principal.

> **Ontology Mapping**: This node uses the ontology label [`PermissionRole`](#ontology-permissionrole).

> **Additional Labels**: This node also uses `AWSPrincipal`.

> **Additional Label Definitions**:
>
> - `AWSPrincipal`: A aws node participating in the shared AWSPrincipal graph interface.

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Unique identifier for this `AWSRole` node. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| arn | Yes | Amazon Resource Name (ARN) of this `AWSRole` node. |
| createdate |  | Timestamp when the IAM role was created. |
| createdate_dt |  | Creation timestamp for the IAM role normalized as a Neo4j datetime. |
| name |  | Name of this `AWSRole` node. |
| path |  | IAM path under which the IAM role is organized. |
| roleid | Yes | Identifier of the roleid linked to this `AWSRole` node. |
| *_ont_name* | Yes | Normalized field sourced from `name`. |
| *_ont_scope* | Yes | Property generated by the ontology mapping. |
| *_ont_source* |  | Module that populated this node's ontology fields. |
| *_ont_type* | Yes | Property generated by the ontology mapping. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSRole)`

- `(:AWSBedrockAgent)-[:HAS_ROLE]->(:AWSRole)`: Defines the relationship from AWSBedrockAgent to AWSRole (existing IAM role nodes).

- `(:AWSCloudFormationStack)-[:HAS_EXECUTION_ROLE]->(:AWSRole)`

- `(:AWSCognitoIdentityPool)-[:ASSOCIATED_WITH]->(:AWSRole)`

- `(:AWSEC2Instance)-[:ASSUMES]->(:AWSRole)`

- `(:AWSEC2Instance)-[:STS_ASSUMEROLE_ALLOW]->(:AWSRole)`: generated by analysis job `EC2 Instances assume IAM roles`.

- `(:AWSECRPullThroughCacheRule)-[:ASSOCIATED_WITH]->(:AWSRole)`

- `(:AWSECSTaskDefinition)-[:HAS_EXECUTION_ROLE]->(:AWSRole)`

- `(:AWSECSTaskDefinition)-[:HAS_TASK_ROLE]->(:AWSRole)`

- `(:AWSEventBridgeRule)-[:ASSOCIATED_WITH]->(:AWSRole)`

- `(:AWSGuardDutyFinding)-[:AFFECTS]->(:AWSRole)`

- `(:AWSInstanceProfile)-[:ASSOCIATED_WITH]->(:AWSRole)`

- `(:AWSLambda)-[:ASSUMES]->(:AWSRole)`

- `(:AWSPermissionSet)-[:ASSIGNED_TO_ROLE]->(:AWSRole)`

- `(:AWSPrincipal)-[:ASSUMED_ROLE]->(:AWSRole)`: MatchLink schema for ASSUMED_ROLE relationships from CloudTrail events.
Creates relationships like: (AWSUser|AWSRole|AWSPrincipal)-[:ASSUMED_ROLE]->(AWSRole)

This MatchLink handles role assumption relationships discovered via CloudTrail management events.
It supports multiple source node types and aggregated relationship properties.
  - Properties:

    | Field | Description |
    |-------|-------------|
    | first_seen_in_time_window | Timestamp when this relationship was first observed in the current time window. |
    | last_used | Timestamp when this relationship was last observed in use. |
    | times_used | Number of times this relationship was observed in use. |

- `(:AWSPrincipal)-[:CAN_PASS_ROLE]->(:AWSRole)`: `AWSPrincipal` receives evaluated `CAN_PASS_ROLE` access to `AWSRole` from AWS IAM policies.
  - Evaluated permissions: `iam:PassRole`
  - Properties:

    | Field | Description |
    |-------|-------------|
    | condition_keys | IAM condition context keys used by the permission. |
    | conditions | IAM conditions that restrict this permission. |
    | has_condition | Whether an IAM condition restricts this permission. |

- `(:AWSPrincipal)-[:STS_ASSUMEROLE_ALLOW]->(:AWSRole)`

- `(:AWSRole)-[:ALLOWED_BY]->(:AWSSSOGroup)`: MatchLink for (AWSRole)-[:ALLOWED_BY]->(AWSSSOGroup).

See schema documentation for details.
  - Properties:

    | Field | Description |
    |-------|-------------|
    | permission_set_arn | ARN of the IAM Identity Center permission set that grants this relationship. |

- `(:AWSRole)-[:ALLOWED_BY]->(:AWSSSOUser)`: MatchLink for (AWSRole)-[:ALLOWED_BY]->(AWSSSOUser).

See schema documentation for details.
  - Properties:

    | Field | Description |
    |-------|-------------|
    | permission_set_arn | ARN of the IAM Identity Center permission set that grants this relationship. |

- `(:AWSRole)-[:MAPS_TO]->(:KubernetesGroup)`: Links an AWS IAM role to the Kubernetes group it maps to.

- `(:AWSRole)-[:MAPS_TO]->(:KubernetesUser)`: Links an AWS IAM role to the Kubernetes user it maps to.

- `(:AWSRole)-[:TAGGED]->(:AWSTag)`: `AWSRole` is tagged with an `AWSTag` discovered by the AWS Resource Groups Tagging API.

- `(:AWSRole)-[:TRUSTS_AWS_PRINCIPAL]->(:AWSPrincipal)`: Trust relationship with principals of type "AWS".

- `(:AWSSSOUser)-[:ASSUMED_ROLE_WITH_SAML]->(:AWSRole)`: MatchLink schema for ASSUMED_ROLE_WITH_SAML relationships from CloudTrail SAML events.
Creates relationships like: (AWSRole)-[:ASSUMED_ROLE_WITH_SAML]->(AWSRole)

This MatchLink handles SAML-based role assumption relationships discovered via CloudTrail
AssumeRoleWithSAML events. It creates separate relationships from regular AssumeRole events
to preserve visibility into authentication methods used.
  - Properties:

    | Field | Description |
    |-------|-------------|
    | first_seen_in_time_window | Timestamp when this relationship was first observed in the current time window. |
    | last_used | Timestamp when this relationship was last observed in use. |
    | times_used | Number of times this relationship was observed in use. |

- `(:AWSSageMakerModel)-[:HAS_EXECUTION_ROLE]->(:AWSRole)`

- `(:AWSSageMakerNotebookInstance)-[:HAS_EXECUTION_ROLE]->(:AWSRole)`

- `(:AWSSageMakerTrainingJob)-[:HAS_EXECUTION_ROLE]->(:AWSRole)`

- `(:AWSSageMakerUserProfile)-[:HAS_EXECUTION_ROLE]->(:AWSRole)`

- `(:GCPBigQueryConnection)-[:CONNECTS_WITH]->(:AWSRole)`

- `(:GitHubRepository)-[:ASSUMED_ROLE_WITH_WEB_IDENTITY]->(:AWSRole)`: MatchLink schema for ASSUMED_ROLE_WITH_WEB_IDENTITY relationships from GitHub Actions to AWS roles.
Creates relationships like: (GitHubRepository)-[:ASSUMED_ROLE_WITH_WEB_IDENTITY]->(AWSRole)

This MatchLink provides granular visibility into which specific GitHub repositories are assuming
AWS roles via GitHub Actions OIDC, rather than just showing provider-level relationships.
  - Properties:

    | Field | Description |
    |-------|-------------|
    | first_seen_in_time_window | Timestamp when this relationship was first observed in the current time window. |
    | last_used | Timestamp when this relationship was last observed in use. |
    | times_used | Number of times this relationship was observed in use. |

- `(:KubernetesServiceAccount)-[:ASSUMES_ROLE]->(:AWSRole)`: Links a service account to the AWS IAM role it can assume through IRSA.

- `(:SpaceliftStack)-[:ASSUMES]->(:AWSRole)`: A Spacelift stack assumes an AWS IAM role at runtime.

### AWSRootPrincipal

Represents the AWS root principal for an AWS account

> **Additional Labels**: This node also uses `AWSPrincipal`.

> **Additional Label Definitions**:
>
> - `AWSPrincipal`: A aws node participating in the shared AWSPrincipal graph interface.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Unique identifier for this `AWSRootPrincipal` node. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| arn | Yes | Amazon Resource Name (ARN) of this `AWSRootPrincipal` node. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSRootPrincipal)`

- `(:AWSRootPrincipal)-[:MAPS_TO]->(:KubernetesUser)`: Links an AWS account root principal to the Kubernetes user it maps to.

### AWSRouteTable

Route tables as known by describe-vpc-endpoints.
Creates stub route table nodes and ROUTES_THROUGH relationships from Gateway VPC endpoints.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Unique identifier for this `AWSRouteTable` node. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| region |  | AWS Region containing this `AWSRouteTable` node. |
| route_table_id | Yes | Identifier of the route table linked to this `AWSRouteTable` node. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSRouteTable)`

- `(:AWSVpcEndpoint)-[:ROUTES_THROUGH]->(:AWSRouteTable)`

### AWSS3AccountPublicAccessBlock

Representation of an AWS [S3 Account Public Access Block](https://docs.aws.amazon.com/AmazonS3/latest/dev/access-control-block-public-access.html) configuration, which provides account-level settings to block public access to S3 resources.

> **Additional Labels**: This node also uses `S3AccountPublicAccessBlock`.

> **Additional Label Definitions**:
>
> - `S3AccountPublicAccessBlock`: Compatibility label for the deprecated `S3AccountPublicAccessBlock` aws node label. Use `AWSS3AccountPublicAccessBlock` instead. Scheduled for removal in v1.0.0.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Unique identifier in the format: `{account_id}:{region}` |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| account_id |  | The AWS account ID |
| block_public_acls |  | Whether Amazon S3 blocks public access control lists (ACLs) for every bucket and object in the account |
| block_public_policy |  | Whether Amazon S3 blocks public bucket policies for every bucket in the account |
| ignore_public_acls |  | Whether Amazon S3 ignores public ACLs for every bucket and object in the account |
| region |  | The AWS region |
| restrict_public_buckets |  | Whether Amazon S3 restricts public policies for every bucket in the account |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSS3AccountPublicAccessBlock)`

### AWSS3Acl

Representation of an AWS S3 [Access Control List](https://docs.aws.amazon.com/AmazonS3/latest/API/API_control_S3AccessControlList.html).

> **Additional Labels**: This node also uses `S3Acl`.

> **Additional Label Definitions**:
>
> - `S3Acl`: Compatibility label for the deprecated `S3Acl` aws node label. Use `AWSS3Acl` instead. Scheduled for removal in v1.0.0.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The ID of this ACL |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| displayname |  | Optional display name for the ACL |
| granteeid |  | The ID of the grantee as defined [here](https://docs.aws.amazon.com/AmazonS3/latest/API/API_control_S3Grantee.html) |
| owner |  | Display name of the S3 bucket owner. |
| ownerid |  | The ACL's owner ID as defined [here](https://docs.aws.amazon.com/AmazonS3/latest/API/API_control_S3ObjectOwner.html) |
| permission |  | Valid values: ``FULL_CONTROL \| READ \| WRITE \| READ_ACP \| WRITE_ACP`` (ACP = Access Control Policy) |
| type |  | The type of the [grantee](https://docs.aws.amazon.com/AmazonS3/latest/API/API_Grantee.html).  Either ``CanonicalUser \| AmazonCustomerByEmail \| Group``. |
| uri |  | URI identifying the predefined S3 grantee group. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSS3Acl)`

- `(:AWSS3Acl)-[:APPLIES_TO]->(:AWSS3Bucket)`

### AWSS3Bucket

Representation of an AWS S3 [Bucket](https://docs.aws.amazon.com/AmazonS3/latest/API/API_Bucket.html).

> **Ontology Mapping**: Some schema variants may also use the ontology label [`ObjectStorage`](#ontology-objectstorage).

> **Additional Labels**: This node also uses `S3Bucket`.

> **Additional Label Definitions**:
>
> - `S3Bucket`: Compatibility label for the deprecated `S3Bucket` aws node label. Use `AWSS3Bucket` instead. Scheduled for removal in v1.0.0.

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Same as `name`, as seen below |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| anonymous_access | Yes | True if this bucket has a policy applied to it that allows anonymous access or if it is open to the internet.  These policy determinations are made by using the [policyuniverse](https://github.com/Netflix-Skunkworks/policyuniverse) library. |
| anonymous_actions |  | List of anonymous internet accessible actions that may be run on the bucket.  This list is taken by running [policyuniverse](https://github.com/Netflix-Skunkworks/policyuniverse#internet-accessible-policy) on the policy that applies to the bucket. |
| arn | Yes | Amazon Resource Name (ARN) of this `AWSS3Bucket` node. |
| block_public_acls |  | Specifies whether Amazon S3 should block public bucket policies for this bucket. |
| block_public_policy |  | Whether this `AWSS3Bucket` node is configured to block public policy. |
| bucket_key_enabled |  | True if a bucket key is enabled, when using SSE-KMS as the default encryption method. |
| creationdate |  | Date-time when the bucket was created |
| default_encryption |  | True if this bucket has [default encryption](https://docs.aws.amazon.com/AmazonS3/latest/userguide/bucket-encryption.html) enabled. |
| encryption_algorithm |  | The encryption algorithm used for default encryption. Only defined if the S3 bucket has default encryption enabled. |
| encryption_key_id |  | The KMS key ID used for default encryption. Only defined if the S3 bucket has SSE-KMS enabled as the default encryption method. |
| ignore_public_acls |  | Specifies whether Amazon S3 should ignore public ACLs for this bucket and objects in this bucket. |
| logging_enabled |  | True if this bucket has [logging enabled](https://docs.aws.amazon.com/AmazonS3/latest/API/API_GetBucketLogging.html) enabled. |
| logging_target_bucket |  | The name of the target bucket where access logs are stored. Only defined if logging is enabled. |
| mfa_delete |  | Specifies whether MFA delete is enabled in the bucket versioning configuration. |
| name |  | The name of the bucket.  This is guaranteed to be [globally unique](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html#S3.Client.list_buckets) |
| object_ownership |  | The bucket's [Object Ownership](https://docs.aws.amazon.com/AmazonS3/latest/userguide/about-object-ownership.html) setting. `BucketOwnerEnforced` indicates that ACLs on the bucket and its objects are ignored. `BucketOwnerPreferred` and `ObjectWriter` indicate that ACLs still function; see [the AWS documentation](https://docs.aws.amazon.com/AmazonS3/latest/userguide/about-object-ownership.html#object-ownership-overview) for details. |
| region |  | The region that the bucket is in. Only defined if the S3 bucket has a [location constraint](https://docs.aws.amazon.com/AmazonS3/latest/dev/UsingBucket.html#access-bucket-intro) |
| restrict_public_buckets |  | Specifies whether Amazon S3 should restrict public bucket policies for this bucket. |
| versioning_status |  | The versioning state of the bucket. |
| *_ont_encrypted* | Yes | Normalized field sourced from `default_encryption`. |
| *_ont_location* | Yes | Normalized field sourced from `region`. |
| *_ont_name* | Yes | Normalized field sourced from `name`. |
| *_ont_public* | Yes | Normalized field sourced from `anonymous_access`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |
| *_ont_versioning* | Yes | Normalized field sourced from `versioning_status`. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSS3Bucket)`

- `(:AWSBedrockCustomModel)-[:TRAINED_FROM]->(:AWSS3Bucket)`: Defines the relationship from AWSBedrockCustomModel to AWSS3Bucket (training data source).

- `(:AWSBedrockKnowledgeBase)-[:SOURCES_DATA_FROM]->(:AWSS3Bucket)`: Defines the relationship from AWSBedrockKnowledgeBase to AWSS3Bucket.

- `(:AWSCloudFrontDistribution)-[:SERVES_FROM]->(:AWSS3Bucket)`: Indicates that the CloudFront distribution serves content from an S3 bucket origin.

- `(:AWSCloudTrailTrail)-[:LOGS_TO]->(:AWSS3Bucket)`

- `(:AWSGuardDutyFinding)-[:AFFECTS]->(:AWSS3Bucket)`

- `(:AWSPrincipal)-[:CAN_READ]->(:AWSS3Bucket)`: `AWSPrincipal` receives evaluated `CAN_READ` access to `AWSS3Bucket` from AWS IAM policies.
  - Evaluated permissions: `S3:GetObject`
  - Properties:

    | Field | Description |
    |-------|-------------|
    | condition_keys | IAM condition context keys used by the permission. |
    | conditions | IAM conditions that restrict this permission. |
    | has_condition | Whether an IAM condition restricts this permission. |

- `(:AWSPrincipal)-[:CAN_WRITE]->(:AWSS3Bucket)`: `AWSPrincipal` receives evaluated `CAN_WRITE` access to `AWSS3Bucket` from AWS IAM policies.
  - Evaluated permissions: `S3:PutObject`
  - Properties:

    | Field | Description |
    |-------|-------------|
    | condition_keys | IAM condition context keys used by the permission. |
    | conditions | IAM conditions that restrict this permission. |
    | has_condition | Whether an IAM condition restricts this permission. |

- `(:AWSS3Acl)-[:APPLIES_TO]->(:AWSS3Bucket)`

- `(:AWSS3Bucket)-[:ENCRYPTED_BY]->(:AWSKMSKey)`

- `(:AWSS3Bucket)-[:NOTIFIES]->(:AWSSNSTopic)`

- `(:AWSS3Bucket)-[:POLICY_STATEMENT]->(:AWSS3PolicyStatement)`

- `(:AWSS3Bucket)-[:TAGGED]->(:AWSTag)`: `AWSS3Bucket` is tagged with an `AWSTag` discovered by the AWS Resource Groups Tagging API.

- `(:AWSSageMakerModel)-[:REFERENCES_ARTIFACTS_IN]->(:AWSS3Bucket)`

- `(:AWSSageMakerModelPackage)-[:REFERENCES_ARTIFACTS_IN]->(:AWSS3Bucket)`

- `(:AWSSageMakerTrainingJob)-[:PRODUCES_MODEL_ARTIFACT]->(:AWSS3Bucket)`

- `(:AWSSageMakerTrainingJob)-[:READS_FROM]->(:AWSS3Bucket)`

- `(:AWSSageMakerTransformJob)-[:WRITES_TO]->(:AWSS3Bucket)`

- `(:DatabricksExternalLocation)-[:BACKED_BY]->(:AWSS3Bucket)`: A Databricks external location is backed by an Amazon S3 bucket.

- `(:DatabricksLogDelivery)-[:DELIVERS_TO]->(:AWSS3Bucket)`: A Databricks log delivery configuration delivers logs to an S3 bucket.

- `(:DatabricksStorageConfig)-[:BACKED_BY]->(:AWSS3Bucket)`: A Databricks storage configuration is backed by an S3 bucket.

- `(:DatabricksTable)-[:BACKED_BY]->(:AWSS3Bucket)`: A Databricks table is backed by an Amazon S3 bucket.

- `(:DatabricksVolume)-[:BACKED_BY]->(:AWSS3Bucket)`: A Databricks volume is backed by an Amazon S3 bucket.

### AWSS3PolicyStatement

Representation of an AWS S3 [Bucket Policy Statements](https://docs.aws.amazon.com/AmazonS3/latest/userguide/bucket-policies.html) for controlling ownership of objects and ACLs of the bucket.

> **Additional Labels**: This node also uses `S3PolicyStatement`.

> **Additional Label Definitions**:
>
> - `S3PolicyStatement`: Compatibility label for the deprecated `S3PolicyStatement` aws node label. Use `AWSS3PolicyStatement` instead. Scheduled for removal in v1.0.0.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The unique identifier for a bucket policy statement. <br>If the statement has an Sid the id will be calculated as _S3Bucket.id_/policy_statement/_index of statement in statement_/_Sid_. <br>If the statement has no Sid the id will be calculated as  _S3Bucket.id_/policy_statement/_index of statement in statement_/ |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| action |  | Specifies permissions that policy statement applies to, as defined [here](https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-with-s3-actions.html) |
| bucket |  | Name of the S3 bucket governed by the policy statement. |
| condition |  | Specifies conditions where permissions are granted: [examples](https://docs.aws.amazon.com/AmazonS3/latest/userguide/amazon-s3-policy-keys.html) |
| effect |  | Specifies "Deny" or "Allow" for the policy statement |
| policy_id |  | Optional string "Id" for the bucket's policy |
| policy_version |  | Version of the bucket's policy |
| principal |  | Principal expression granted or denied access by the policy statement. |
| resource |  | Specifies the resource the bucket policy statement is based on |
| sid |  | Optional string to label the specific bucket policy statement |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSS3PolicyStatement)`

- `(:AWSS3Bucket)-[:POLICY_STATEMENT]->(:AWSS3PolicyStatement)`

### AWSSageMakerDomain

Represents an [AWS SageMaker Domain](https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_DescribeDomain.html). A Domain is a centralized environment for SageMaker Studio users and their resources.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The ARN of the Domain |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| arn | Yes | The ARN of the Domain |
| auth_mode |  | Authentication mode used by the SageMaker domain. |
| creation_time |  | When the Domain was created |
| domain_id |  | The Domain ID |
| domain_name |  | The name of the Domain |
| home_efs_file_system_id |  | Identifier of the home efs file system linked to this `AWSSageMakerDomain` node. |
| last_modified_time |  | When the Domain was last modified |
| region |  | The AWS region where the Domain exists |
| status |  | The status of the Domain |
| url |  | URL of the SageMaker domain. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSSageMakerDomain)`

- `(:AWSSageMakerDomain)-[:CONTAINS]->(:AWSSageMakerUserProfile)`

### AWSSageMakerEndpoint

Represents an [AWS SageMaker Endpoint](https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_DescribeEndpoint.html). An Endpoint provides a persistent HTTPS endpoint for real-time inference.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The ARN of the Endpoint |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| arn | Yes | The ARN of the Endpoint |
| creation_time |  | When the Endpoint was created |
| endpoint_config_name |  | The name of the Endpoint Config used |
| endpoint_name |  | The name of the Endpoint |
| endpoint_status |  | The status of the Endpoint |
| last_modified_time |  | When the Endpoint was last modified |
| region |  | The AWS region where the Endpoint exists |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSSageMakerEndpoint)`

- `(:AWSSageMakerEndpoint)-[:USES]->(:AWSSageMakerEndpointConfig)`

### AWSSageMakerEndpointConfig

Represents an [AWS SageMaker Endpoint Configuration](https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_DescribeEndpointConfig.html). An Endpoint Config specifies the ML compute instances and model variants for deploying models. Allows for a model to provide a prediction to a request in real time.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The ARN of the Endpoint Config |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| arn | Yes | The ARN of the Endpoint Config |
| creation_time |  | When the Endpoint Config was created |
| endpoint_config_name |  | The name of the Endpoint Config |
| kms_key_id |  | Identifier of the KMS key linked to this `AWSSageMakerEndpointConfig` node. |
| model_name |  | The name of the model to deploy |
| region |  | The AWS region where the Endpoint Config exists |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSSageMakerEndpointConfig)`

- `(:AWSSageMakerEndpoint)-[:USES]->(:AWSSageMakerEndpointConfig)`

- `(:AWSSageMakerEndpointConfig)-[:USES]->(:AWSSageMakerModel)`

### AWSSageMakerModel

Represents an [AWS SageMaker Model](https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_DescribeModel.html). A Model contains the information needed to deploy ML models for inference.

> **Ontology Mapping**: This node uses the ontology label [`AIModel`](#ontology-aimodel).

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The ARN of the Model |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| arn | Yes | The ARN of the Model |
| creation_time |  | When the Model was created |
| enable_network_isolation |  | Whether network isolation is enabled for model containers. |
| execution_role_arn |  | The IAM role ARN that SageMaker assumes to perform operations |
| model_artifacts_s3_bucket_id |  | The S3 bucket ID where model artifacts are stored |
| model_name |  | The name of the Model |
| model_package_name |  | The Model Package name if the model is based on one |
| primary_container_image |  | The Docker image for the primary container |
| region |  | The AWS region where the Model exists |
| vpc_config_security_group_ids |  | Identifiers of the VPC config security group linked to this `AWSSageMakerModel` node. |
| vpc_config_subnets |  | Subnet IDs used by the model's VPC configuration. |
| *_ont_name* | Yes | Normalized field sourced from `model_name`. |
| *_ont_provider* | Yes | Property generated by the ontology mapping. |
| *_ont_source* |  | Module that populated this node's ontology fields. |
| *_ont_type* | Yes | Property generated by the ontology mapping. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSSageMakerModel)`

- `(:AWSSageMakerEndpointConfig)-[:USES]->(:AWSSageMakerModel)`

- `(:AWSSageMakerModel)-[:DERIVES_FROM]->(:AWSSageMakerModelPackage)`

- `(:AWSSageMakerModel)-[:HAS_EXECUTION_ROLE]->(:AWSRole)`

- `(:AWSSageMakerModel)-[:REFERENCES_ARTIFACTS_IN]->(:AWSS3Bucket)`

- `(:AWSSageMakerTransformJob)-[:USES]->(:AWSSageMakerModel)`

### AWSSageMakerModelPackage

Represents an [AWS SageMaker Model Package](https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_DescribeModelPackage.html). A Model Package is a versioned model in the SageMaker Model Registry that acts as a blueprint for a deployed model.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The ARN of the Model Package |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| arn | Yes | The ARN of the Model Package |
| creation_time |  | When the Model Package was created |
| last_modified_time |  | Timestamp when the model package was last modified. |
| model_approval_status |  | The approval status of the Model Package |
| model_artifacts_s3_bucket_id |  | The S3 bucket ID where model artifacts are stored |
| model_package_description |  | Human-readable description of the model package. |
| model_package_group_name |  | The name of the group this package belongs to |
| model_package_name |  | The name of the Model Package |
| model_package_status |  | The status of the Model Package |
| model_package_version |  | The version number of the Model Package |
| region |  | The AWS region where the Model Package exists |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSSageMakerModelPackage)`

- `(:AWSSageMakerModel)-[:DERIVES_FROM]->(:AWSSageMakerModelPackage)`

- `(:AWSSageMakerModelPackage)-[:MEMBER_OF]->(:AWSSageMakerModelPackageGroup)`

- `(:AWSSageMakerModelPackage)-[:REFERENCES_ARTIFACTS_IN]->(:AWSS3Bucket)`

### AWSSageMakerModelPackageGroup

Represents an [AWS SageMaker Model Package Group](https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_DescribeModelPackageGroup.html). A Model Package Group is a collection of versioned model packages in the SageMaker Model Registry.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The ARN of the Model Package Group |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| arn | Yes | The ARN of the Model Package Group |
| creation_time |  | When the Model Package Group was created |
| model_package_group_description |  | Human-readable description of the model package group. |
| model_package_group_name |  | The name of the Model Package Group |
| model_package_group_status |  | The status of the Model Package Group |
| region |  | The AWS region where the Model Package Group exists |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSSageMakerModelPackageGroup)`

- `(:AWSSageMakerModelPackage)-[:MEMBER_OF]->(:AWSSageMakerModelPackageGroup)`

### AWSSageMakerNotebookInstance

Represents an [AWS SageMaker Notebook Instance](https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_DescribeNotebookInstance.html). A Notebook Instance is a fully managed ML compute instance running Jupyter notebooks.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The ARN of the Notebook Instance |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| arn | Yes | The ARN of the Notebook Instance |
| creation_time |  | When the Notebook Instance was created |
| direct_internet_access |  | Whether the notebook instance has direct internet access. |
| instance_type |  | The ML compute instance type |
| kms_key_id |  | Identifier of the KMS key linked to this `AWSSageMakerNotebookInstance` node. |
| last_modified_time |  | When the Notebook Instance was last modified |
| network_interface_id |  | Identifier of the network interface linked to this `AWSSageMakerNotebookInstance` node. |
| notebook_instance_name |  | The name of the Notebook Instance |
| notebook_instance_status |  | The status of the Notebook Instance |
| platform_identifier |  | SageMaker notebook platform version identifier. |
| region |  | The AWS region where the Notebook Instance exists |
| role_arn |  | The IAM role ARN associated with the instance |
| root_access |  | Whether notebook users have root access. |
| security_groups |  | Security group IDs attached to the notebook instance. |
| subnet_id |  | Identifier of the subnet linked to this `AWSSageMakerNotebookInstance` node. |
| url |  | The URL to connect to the Jupyter notebook |
| volume_size_in_gb |  | Size in GiB of the notebook instance's attached storage volume. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSSageMakerNotebookInstance)`

- `(:AWSSageMakerNotebookInstance)-[:CAN_INVOKE]->(:AWSSageMakerTrainingJob)`

- `(:AWSSageMakerNotebookInstance)-[:HAS_EXECUTION_ROLE]->(:AWSRole)`

### AWSSageMakerTrainingJob

Represents an [AWS SageMaker Training Job](https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_DescribeTrainingJob.html). A Training Job trains ML models using specified algorithms and datasets.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The ARN of the Training Job |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| algorithm_specification_training_image |  | The Docker image for the training algorithm |
| algorithm_specification_training_input_mode |  | How the training algorithm consumes input data. |
| arn | Yes | The ARN of the Training Job |
| billable_time_in_seconds |  | Billable duration of the training job in seconds. |
| creation_time |  | When the Training Job was created |
| enable_inter_container_traffic_encryption |  | Whether traffic between distributed training containers is encrypted. |
| enable_managed_spot_training |  | Whether the job uses SageMaker managed spot training. |
| enable_network_isolation |  | Whether network isolation is enabled for training containers. |
| input_data_s3_bucket_id |  | The S3 bucket ID where input data is stored |
| last_modified_time |  | Timestamp when the training job was last modified. |
| output_data_s3_bucket_id |  | The S3 bucket ID where output artifacts are stored |
| region |  | The AWS region where the Training Job runs |
| role_arn |  | The IAM role ARN used by the training job |
| secondary_status |  | Detailed progress status of the training job. |
| training_end_time |  | When training ended |
| training_job_name |  | The name of the Training Job |
| training_job_status |  | The status of the Training Job |
| training_start_time |  | When training started |
| training_time_in_seconds |  | Total training duration in seconds. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSSageMakerTrainingJob)`

- `(:AWSSageMakerNotebookInstance)-[:CAN_INVOKE]->(:AWSSageMakerTrainingJob)`

- `(:AWSSageMakerTrainingJob)-[:HAS_EXECUTION_ROLE]->(:AWSRole)`

- `(:AWSSageMakerTrainingJob)-[:PRODUCES_MODEL_ARTIFACT]->(:AWSS3Bucket)`

- `(:AWSSageMakerTrainingJob)-[:READS_FROM]->(:AWSS3Bucket)`

### AWSSageMakerTransformJob

Represents an [AWS SageMaker Transform Job](https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_DescribeTransformJob.html). A Transform Job performs batch inference on datasets. Takes a large dataset and uses batch inference to write multiple predictions to an S3 Bucket.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The ARN of the Transform Job |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| arn | Yes | The ARN of the Transform Job |
| batch_strategy |  | Strategy used to split input records into transform batches. |
| creation_time |  | When the Transform Job was created |
| max_concurrent_transforms |  | Maximum number of concurrent transform requests. |
| max_payload_in_mb |  | Maximum transform request payload size in MiB. |
| model_name |  | The name of the model used for the transform |
| output_data_s3_bucket_id |  | The S3 bucket ID where transform output is stored |
| region |  | The AWS region where the Transform Job runs |
| transform_end_time |  | Timestamp when the batch transform job completed. |
| transform_job_name |  | The name of the Transform Job |
| transform_job_status |  | The status of the Transform Job |
| transform_start_time |  | Timestamp when the batch transform job started. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSSageMakerTransformJob)`

- `(:AWSSageMakerTransformJob)-[:USES]->(:AWSSageMakerModel)`

- `(:AWSSageMakerTransformJob)-[:WRITES_TO]->(:AWSS3Bucket)`

### AWSSageMakerUserProfile

Represents an [AWS SageMaker User Profile](https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_DescribeUserProfile.html). A User Profile represents a user within a SageMaker Studio Domain.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The ARN of the User Profile |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| arn | Yes | The ARN of the User Profile |
| creation_time |  | When the User Profile was created |
| domain_id |  | The Domain ID that this profile belongs to |
| execution_role |  | The IAM execution role ARN for the user |
| last_modified_time |  | When the User Profile was last modified |
| region |  | The AWS region where the User Profile exists |
| status |  | The status of the User Profile |
| user_profile_name |  | The name of the User Profile |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSSageMakerUserProfile)`

- `(:AWSSageMakerDomain)-[:CONTAINS]->(:AWSSageMakerUserProfile)`

- `(:AWSSageMakerUserProfile)-[:HAS_EXECUTION_ROLE]->(:AWSRole)`

### AWSSAMLProvider

> **Ontology Mapping**: This node uses the ontology label [`IdentityProvider`](#ontology-identityprovider).

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Unique identifier for this `AWSSAMLProvider` node. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| arn | Yes | Amazon Resource Name (ARN) of this `AWSSAMLProvider` node. |
| create_date |  | Timestamp when the IAM SAML provider was created. |
| name | Yes | Name of this `AWSSAMLProvider` node. |
| valid_until |  | Timestamp when the SAML provider metadata expires. |
| *_ont_name* | Yes | Normalized field sourced from `name`. |
| *_ont_protocol* | Yes | Property generated by the ontology mapping. |
| *_ont_source* |  | Module that populated this node's ontology fields. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSSAMLProvider)`

### AWSSecretsManagerSecret

Representation of an AWS [Secrets Manager Secret](https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_SecretListEntry.html)

> **Ontology Mapping**: This node uses the ontology label [`Secret`](#ontology-secret).

> **Additional Labels**: This node also uses `SecretsManagerSecret`.

> **Additional Label Definitions**:
>
> - `SecretsManagerSecret`: Compatibility label for the deprecated `SecretsManagerSecret` aws node label. Use `AWSSecretsManagerSecret` instead. Scheduled for removal in v1.0.0.

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The arn of the secret. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| arn | Yes | Amazon Resource Name (ARN) of this `AWSSecretsManagerSecret` node. |
| created_date |  | The date and time when a secret was created. |
| deleted_date |  | The date and time the deletion of the secret occurred. Not present on active secrets. The secret can be recovered until the number of days in the recovery window has passed, as specified in the RecoveryWindowInDays parameter of the DeleteSecret operation. |
| description |  | The user-provided description of the secret. |
| kms_key_id |  | The ARN or alias of the AWS KMS customer master key (CMK) used to encrypt the SecretString and SecretBinary fields in each version of the secret. If you don't provide a key, then Secrets Manager defaults to encrypting the secret fields with the default KMS CMK, the key named awssecretsmanager, for this account. |
| last_accessed_date |  | The last date that this secret was accessed. This value is truncated to midnight of the date and therefore shows only the date, not the time. |
| last_changed_date |  | The last date and time that this secret was modified in any way. |
| last_rotated_date |  | The most recent date and time that the Secrets Manager rotation process was successfully completed. This value is null if the secret hasn't ever rotated. |
| name | Yes | The friendly name of the secret. You can use forward slashes in the name to represent a path hierarchy. For example, /prod/databases/dbserver1 could represent the secret for a server named dbserver1 in the folder databases in the folder prod. |
| owning_service |  | Returns the name of the service that created the secret. |
| primary_region |  | The Region where Secrets Manager originated the secret. |
| region |  | AWS Region containing this `AWSSecretsManagerSecret` node. |
| rotation_enabled |  | Indicates whether automatic, scheduled rotation is enabled for this secret. |
| rotation_lambda_arn |  | The ARN of an AWS Lambda function invoked by Secrets Manager to rotate and expire the secret either automatically per the schedule or manually by a call to RotateSecret. |
| rotation_rules_automatically_after_days |  | Specifies the number of days between automatic scheduled rotations of the secret. |
| *_ont_created_at* | Yes | Normalized field sourced from `created_date`. |
| *_ont_name* | Yes | Normalized field sourced from `name`. |
| *_ont_rotation_enabled* | Yes | Normalized field sourced from `rotation_enabled`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |
| *_ont_updated_at* | Yes | Normalized field sourced from `last_changed_date`. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSSecretsManagerSecret)`: Relationship between Secret and AWS Account

- `(:AWSECRPullThroughCacheRule)-[:USES_SECRET]->(:AWSSecretsManagerSecret)`

- `(:AWSPrincipal)-[:GET_SECRET]->(:AWSSecretsManagerSecret)`: `AWSPrincipal` receives evaluated `GET_SECRET` access to `AWSSecretsManagerSecret` from AWS IAM policies.
  - Evaluated permissions: `secretsmanager:GetSecretValue`
  - Properties:

    | Field | Description |
    |-------|-------------|
    | condition_keys | IAM condition context keys used by the permission. |
    | conditions | IAM conditions that restrict this permission. |
    | has_condition | Whether an IAM condition restricts this permission. |

- `(:AWSSecretsManagerSecret)-[:ENCRYPTED_BY]->(:AWSKMSKey)`: Relationship between Secret and its KMS key
Only created when kms_key_id is present

- `(:AWSSecretsManagerSecret)-[:TAGGED]->(:AWSTag)`: `AWSSecretsManagerSecret` is tagged with an `AWSTag` discovered by the AWS Resource Groups Tagging API.

- `(:AWSSecretsManagerSecretVersion)-[:VERSION_OF]->(:AWSSecretsManagerSecret)`: Relationship between Secret Version and its parent Secret

### AWSSecretsManagerSecretVersion

Representation of an AWS [Secrets Manager Secret Version](https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_SecretVersionListEntry.html)

> **Additional Labels**: This node also uses `SecretsManagerSecretVersion`.

> **Additional Label Definitions**:
>
> - `SecretsManagerSecretVersion`: Compatibility label for the deprecated `SecretsManagerSecretVersion` aws node label. Use `AWSSecretsManagerSecretVersion` instead. Scheduled for removal in v1.0.0.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The ARN of the secret version. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| arn | Yes | The ARN of the secret version. |
| created_date |  | The date and time that this version of the secret was created. |
| kms_key_ids |  | A list of IDs of the AWS KMS keys used to encrypt the secret version. |
| region |  | The AWS region where the secret version exists. |
| secret_id |  | The ARN of the secret that this version belongs to. |
| tags |  | A list of tags attached to this secret version. |
| version_id |  | The unique identifier of this version of the secret. |
| version_stages |  | A list of staging labels that are currently attached to this version of the secret. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSSecretsManagerSecretVersion)`: Relationship between Secret Version and AWS Account

- `(:AWSSecretsManagerSecretVersion)-[:ENCRYPTED_BY]->(:AWSKMSKey)`: Relationship between Secret Version and its KMS key
Only created when kms_key_ids is present

- `(:AWSSecretsManagerSecretVersion)-[:VERSION_OF]->(:AWSSecretsManagerSecret)`: Relationship between Secret Version and its parent Secret

### AWSSecurityHub

Representation of the configuration of AWS [Security Hub](https://docs.aws.amazon.com/securityhub/1.0/APIReference/API_DescribeHub.html)

> **Additional Labels**: This node also uses `SecurityHub`.

> **Additional Label Definitions**:
>
> - `SecurityHub`: Compatibility label for the deprecated `SecurityHub` aws node label. Use `AWSSecurityHub` instead. Scheduled for removal in v1.0.0.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The arn of the hub resource. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| auto_enable_controls |  | Whether to automatically enable new controls when they are added to standards that are enabled. |
| subscribed_at |  | The date and time when Security Hub was enabled in the account. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSSecurityHub)`

### AWSServerCertificate

Representation of an AWS [IAM Server Certificate](https://docs.aws.amazon.com/IAM/latest/APIReference/API_ServerCertificateMetadata.html).

> **Ontology Mapping**: This node uses the ontology label [`Certificate`](#ontology-certificate).

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The server certificate ID |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| arn | Yes | The ARN of the server certificate |
| expiration |  | The date on which the certificate is set to expire |
| path |  | The path to the server certificate |
| server_certificate_id | Yes | The stable and unique ID for the server certificate |
| server_certificate_name | Yes | The name of the server certificate |
| upload_date |  | The date the server certificate was uploaded |
| *_ont_domain* | Yes | Normalized field sourced from `server_certificate_name`. |
| *_ont_expiry* | Yes | Normalized field sourced from `expiration`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSServerCertificate)`

### AWSServicePrincipal

Represents a global AWS service principal e.g. "ec2.amazonaws.com"

> **Ontology Mapping**: This node uses the ontology label [`ServiceAccount`](#ontology-serviceaccount).

> **Additional Labels**: This node also uses `AWSPrincipal`.

> **Additional Label Definitions**:
>
> - `AWSPrincipal`: A aws node participating in the shared AWSPrincipal graph interface.

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Unique identifier for this `AWSServicePrincipal` node. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| arn | Yes | Amazon Resource Name (ARN) of this `AWSServicePrincipal` node. |
| type |  | Type of this `AWSServicePrincipal` node. |
| *_ont_name* | Yes | Normalized field sourced from `arn`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |

#### Relationships

No relationships.

### AWSSESEmailIdentity

Representation of an AWS [SES Email Identity](https://docs.aws.amazon.com/ses/latest/APIReference-V2/API_GetEmailIdentity.html). An SES email identity is a domain or email address that you use to send email through Amazon Simple Email Service (SESv2).

> **Additional Labels**: This node also uses `SESEmailIdentity`.

> **Additional Label Definitions**:
>
> - `SESEmailIdentity`: Compatibility label for the deprecated `SESEmailIdentity` aws node label. Use `AWSSESEmailIdentity` instead. Scheduled for removal in v1.0.0.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The ARN of the SES email identity |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| arn | Yes | The ARN of the SES email identity |
| dkim_signing_enabled |  | Whether DKIM signing is enabled for this identity |
| dkim_status |  | The DKIM authentication status (e.g., `SUCCESS`, `PENDING`, `FAILED`) |
| identity |  | The name of the email identity (domain or email address) |
| identity_type |  | The type of the identity, either `EMAIL_ADDRESS` or `DOMAIN` |
| region |  | The AWS region where the SES email identity exists |
| sending_enabled |  | Whether email sending is enabled for this identity |
| verification_status |  | The verification status of the identity (e.g., `SUCCESS`, `PENDING`, `FAILED`) |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSSESEmailIdentity)`

### AWSSNSTopic

Representation of an AWS [SNS Topic](https://docs.aws.amazon.com/sns/latest/api/API_Topic.html)

> **Additional Labels**: This node also uses `SNSTopic`.

> **Additional Label Definitions**:
>
> - `SNSTopic`: Compatibility label for the deprecated `SNSTopic` aws node label. Use `AWSSNSTopic` instead. Scheduled for removal in v1.0.0.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The ARN of the SNS topic |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| arn | Yes | The Amazon Resource Name (ARN) of the topic |
| deliverypolicy |  | The JSON serialization of the topic's delivery policy |
| displayname |  | The display name of the topic |
| effectivedeliverypolicy |  | The JSON serialization of the effective delivery policy |
| kmsmasterkeyid |  | The ID of an AWS managed customer master key (CMK) for Amazon SNS or a custom CMK |
| name |  | The name of the topic |
| owner |  | The AWS account ID of the topic's owner |
| region |  | The AWS region where the topic is located |
| subscriptionsconfirmed |  | The number of confirmed subscriptions |
| subscriptionsdeleted |  | The number of deleted subscriptions |
| subscriptionspending |  | The number of subscriptions pending confirmation |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSSNSTopic)`

- `(:AWSRDSEventSubscription)-[:NOTIFIES]->(:AWSSNSTopic)`

- `(:AWSS3Bucket)-[:NOTIFIES]->(:AWSSNSTopic)`

- `(:AWSSNSTopicSubscription)-[:HAS_SUBSCRIPTION]->(:AWSSNSTopic)`

### AWSSNSTopicSubscription

Representation of an AWS [SNS Topic Subscription](https://docs.aws.amazon.com/sns/latest/api/API_GetSubscriptionAttributes.html)

> **Additional Labels**: This node also uses `SNSTopicSubscription`.

> **Additional Label Definitions**:
>
> - `SNSTopicSubscription`: Compatibility label for the deprecated `SNSTopicSubscription` aws node label. Use `AWSSNSTopicSubscription` instead. Scheduled for removal in v1.0.0.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The ARN of the SNS topic subscription |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| arn | Yes | The Amazon Resource Name (ARN) of the topic subscription |
| endpoint |  | The subscription's endpoint |
| owner |  | The subscription's owner |
| protocol |  | The subscription's protocol for messages |
| topic_arn |  | The topic ARN that the subscription is associated with |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSSNSTopicSubscription)`

- `(:AWSSNSTopicSubscription)-[:HAS_SUBSCRIPTION]->(:AWSSNSTopic)`

### AWSSQSQueue

Representation of an AWS [SQS Queue](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/APIReference/API_GetQueueAttributes.html)

> **Additional Labels**: This node also uses `SQSQueue`.

> **Additional Label Definitions**:
>
> - `SQSQueue`: Compatibility label for the deprecated `SQSQueue` aws node label. Use `AWSSQSQueue` instead. Scheduled for removal in v1.0.0.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The arn of the sqs queue. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| arn | Yes | The arn of the sqs queue. |
| content_based_deduplication |  | Whether or not content-based deduplication is enabled for the queue. |
| created_timestamp |  | The time when the queue was created in seconds |
| deduplication_scope |  | Specifies whether message deduplication occurs at the message group or queue level. |
| delay_seconds |  | The default delay on the queue in seconds. |
| fifo_queue |  | Whether or not the queue is FIFO. |
| fifo_throughput_limit |  | Specifies whether the FIFO queue throughput quota applies to the entire queue or per message group. |
| kms_data_key_reuse_period_seconds |  | The length of time, in seconds, for which Amazon SQS can reuse a data key to encrypt or decrypt messages before calling AWS KMS again. |
| kms_master_key_id |  | The ID of an AWS managed customer master key (CMK) for Amazon SQS or a custom CMK. |
| last_modified_timestamp |  | The time when the queue was last changed in seconds. |
| maximum_message_size |  | The limit of how many bytes a message can contain before Amazon SQS rejects it. |
| message_retention_period |  | he length of time, in seconds, for which Amazon SQS retains a message. |
| name |  | Name of this `AWSSQSQueue` node. |
| policy |  | The IAM policy of the queue. |
| receive_message_wait_time_seconds |  | The length of time, in seconds, for which the ReceiveMessage action waits for a message to arrive. |
| redrive_policy_dead_letter_target_arn |  | The Amazon Resource Name (ARN) of the dead-letter queue to which Amazon SQS moves messages after the value of maxReceiveCount is exceeded. |
| redrive_policy_max_receive_count |  | The number of times a message is delivered to the source queue before being moved to the dead-letter queue. When the ReceiveCount for a message exceeds the maxReceiveCount for a queue, Amazon SQS moves the message to the dead-letter-queue. |
| region |  | AWS Region containing this `AWSSQSQueue` node. |
| url |  | Service URL used to address the SQS queue. |
| visibility_timeout |  | The visibility timeout for the queue. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSSQSQueue)`

- `(:AWSSQSQueue)-[:HAS_DEADLETTER_QUEUE]->(:AWSSQSQueue)`

- `(:AWSSQSQueue)-[:TAGGED]->(:AWSTag)`: `AWSSQSQueue` is tagged with an `AWSTag` discovered by the AWS Resource Groups Tagging API.

### AWSSSMInstanceInformation

Representation of an AWS SSM [InstanceInformation](https://docs.aws.amazon.com/systems-manager/latest/APIReference/API_InstanceInformation.html)

> **Additional Labels**: This node also uses `SSMInstanceInformation`.

> **Additional Label Definitions**:
>
> - `SSMInstanceInformation`: Compatibility label for the deprecated `SSMInstanceInformation` aws node label. Use `AWSSSMInstanceInformation` instead. Scheduled for removal in v1.0.0.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The ARN of the instance information |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| activation_id |  | The activation ID created by AWS Systems Manager when the server or virtual machine (VM) was registered. |
| agent_version |  | The version of SSM Agent running on your Linux managed node. |
| association_status |  | The status of the association. |
| computer_name |  | The fully qualified host name of the managed node. |
| iam_role |  | The AWS Identity and Access Management (IAM) role assigned to the on-premises Systems Manager managed node. This call doesn't return the IAM role for Amazon Elastic Compute Cloud (Amazon EC2) instances. |
| instance_id | Yes | The managed node ID. |
| ip_address |  | The IP address of the managed node. |
| is_latest_version |  | Indicates whether the latest version of SSM Agent is running on your Linux managed node. This field doesn't indicate whether or not the latest version is installed on Windows managed nodes, because some older versions of Windows Server use the EC2Config service to process Systems Manager requests. |
| last_association_execution_date |  | The date the association was last run. |
| last_ping_date_time |  | The date and time when the agent last pinged the Systems Manager service. |
| last_successful_association_execution_date |  | The last date the association was successfully run. |
| name |  | The name assigned to an on-premises server, edge device, or virtual machine (VM) when it is activated as a Systems Manager managed node. The name is specified as the DefaultInstanceName property using the CreateActivation command. |
| ping_status |  | Connection status of SSM Agent. |
| platform_name |  | The name of the operating system platform running on your managed node. |
| platform_type |  | The operating system platform type. |
| platform_version |  | The version of the OS platform running on your managed node. |
| region |  | The region of the instance information. |
| registration_date |  | The date the server or VM was registered with AWS as a managed node. |
| resource_type |  | The type of instance. Instances are either EC2 instances or managed instances. |
| source_id |  | The ID of the source resource. For AWS IoT Greengrass devices, SourceId is the Thing name. |
| source_type |  | The type of the source resource. For AWS IoT Greengrass devices, SourceType is AWS::IoT::Thing. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSSSMInstanceInformation)`

- `(:AWSEC2Instance)-[:HAS_INFORMATION]->(:AWSSSMInstanceInformation)`

### AWSSSMInstancePatch

Representation of an AWS SSM [PatchComplianceData](https://docs.aws.amazon.com/systems-manager/latest/APIReference/API_PatchComplianceData.html)

> **Additional Labels**: This node also uses `SSMInstancePatch`.

> **Additional Label Definitions**:
>
> - `SSMInstancePatch`: Compatibility label for the deprecated `SSMInstancePatch` aws node label. Use `AWSSSMInstancePatch` instead. Scheduled for removal in v1.0.0.

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Composite key built as `{instance_id}-{Title}`, since SSM exposes no identifier for an instance patch |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| classification |  | The classification of the patch, such as SecurityUpdates, Updates, and CriticalUpdates. |
| cve_ids |  | The IDs of one or more Common Vulnerabilities and Exposure (CVE) issues that are resolved by the patch. |
| installed_time |  | The date/time the patch was installed on the managed node. Not all operating systems provide this level of information. |
| instance_id | Yes | The managed node ID. |
| kb_id | Yes | The operating system-specific ID of the patch. |
| region |  | The region of the instance patch. |
| severity |  | The severity of the patch such as Critical, Important, and Moderate. |
| state |  | The state of the patch on the managed node, such as INSTALLED or FAILED. |
| title | Yes | The title of the patch. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSSSMInstancePatch)`

- `(:AWSEC2Instance)-[:HAS_PATCH]->(:AWSSSMInstancePatch)`

### AWSSSMParameter

Representation of an AWS Systems Manager Parameter as returned by the [`describe_parameters` API](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ssm/client/describe_parameters.html).

> **Additional Labels**: This node also uses `SSMParameter`.

> **Additional Label Definitions**:
>
> - `SSMParameter`: A aws node participating in the shared SSMParameter graph interface.

> **Conditional Labels**:
>
> - [`Secret`](#ontology-secret) (ontology label) when `type` equals `SecureString`. A cross-provider Secret resource in Cartography's ontology.

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | The AWS parameter ARN. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| allowedpattern |  | A regular expression that defines the constraints on the parameter value. |
| arn | Yes | The Amazon Resource Name (ARN) of the parameter. |
| datatype |  | The data type of the parameter, such as text or aws:ec2:image. |
| description |  | Description of the parameter actions. |
| keyid |  | The alias or ARN of the Key Management Service (KMS) key used to encrypt the parameter. Applies to SecureString parameters only. |
| kms_key_id_short |  | The shortened KMS Key ID used to encrypt the parameter. |
| lastmodifieddate |  | Date the parameter was last changed or updated (stored as epoch time). |
| lastmodifieduser |  | Amazon Resource Name (ARN) of the AWS user who last changed the parameter. |
| name |  | The parameter name. |
| policies_json |  | A JSON string representation of the list of policies associated with the parameter. |
| region |  | The region of the parameter. |
| tier |  | The parameter tier. |
| type |  | The type of parameter. Valid parameter types include String, StringList, and SecureString. |
| value |  | The parameter value for AWS-managed public parameters fetched with `GetParametersByPath`. Private parameters discovered with `DescribeParameters` have no value. |
| version |  | The parameter version. |
| *_ont_name* | Yes | Normalized field sourced from `name`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |
| *_ont_updated_at* | Yes | Normalized field sourced from `lastmodifieddate`. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSSSMParameter)`

- `(:AWSSSMParameter)-[:ENCRYPTED_BY]->(:AWSKMSKey)`

### AWSSSOGroup

Representation of an AWS SSO Group.

> **Ontology Mapping**: This node uses the ontology label [`UserGroup`](#ontology-usergroup).

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Unique identifier for the SSO group |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| description |  | The description of the SSO group |
| display_name |  | The display name of the SSO group |
| external_id | Yes | The external ID of the SSO group |
| identity_store_id |  | The identity store ID of the SSO group |
| region |  | The AWS region |
| *_ont_description* |  | Normalized field sourced from `description`. |
| *_ont_name* | Yes | Normalized field sourced from `display_name`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSSSOGroup)`

- `(:AWSRole)-[:ALLOWED_BY]->(:AWSSSOGroup)`: MatchLink for (AWSRole)-[:ALLOWED_BY]->(AWSSSOGroup).

See schema documentation for details.
  - Properties:

    | Field | Description |
    |-------|-------------|
    | permission_set_arn | ARN of the IAM Identity Center permission set that grants this relationship. |

- `(:AWSSSOGroup)-[:HAS_PERMISSION_SET]->(:AWSPermissionSet)`

- `(:AWSSSOGroup)-[:HAS_ROLE]->(:AWSPermissionSet)`

- `(:AWSSSOUser)-[:MEMBER_OF]->(:AWSSSOGroup)`

- `(:AWSSSOUser)-[:MEMBER_OF_SSO_GROUP]->(:AWSSSOGroup)`

### AWSSSOUser

Representation of an AWS SSO User.

> **Ontology Mapping**: This node uses the ontology label [`UserAccount`](#ontology-useraccount).

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Unique identifier for the SSO user |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| external_id | Yes | The external ID of the SSO user |
| identity_store_id |  | The identity store ID of the SSO user |
| region |  | The AWS region |
| user_name |  | The username of the SSO user |
| *_ont_source* |  | Module that populated this node's ontology fields. |
| *_ont_username* | Yes | Normalized field sourced from `user_name`. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSSSOUser)`

- `(:AWSRole)-[:ALLOWED_BY]->(:AWSSSOUser)`: MatchLink for (AWSRole)-[:ALLOWED_BY]->(AWSSSOUser).

See schema documentation for details.
  - Properties:

    | Field | Description |
    |-------|-------------|
    | permission_set_arn | ARN of the IAM Identity Center permission set that grants this relationship. |

- `(:AWSSSOUser)-[:ASSUMED_ROLE_WITH_SAML]->(:AWSRole)`: MatchLink schema for ASSUMED_ROLE_WITH_SAML relationships from CloudTrail SAML events.
Creates relationships like: (AWSRole)-[:ASSUMED_ROLE_WITH_SAML]->(AWSRole)

This MatchLink handles SAML-based role assumption relationships discovered via CloudTrail
AssumeRoleWithSAML events. It creates separate relationships from regular AssumeRole events
to preserve visibility into authentication methods used.
  - Properties:

    | Field | Description |
    |-------|-------------|
    | first_seen_in_time_window | Timestamp when this relationship was first observed in the current time window. |
    | last_used | Timestamp when this relationship was last observed in use. |
    | times_used | Number of times this relationship was observed in use. |

- `(:AWSSSOUser)-[:HAS_PERMISSION_SET]->(:AWSPermissionSet)`

- `(:AWSSSOUser)-[:HAS_ROLE]->(:AWSPermissionSet)`

- `(:AWSSSOUser)-[:MEMBER_OF]->(:AWSSSOGroup)`

- `(:AWSSSOUser)-[:MEMBER_OF_SSO_GROUP]->(:AWSSSOGroup)`

- `(:EntraUser)-[:CAN_SIGN_ON_TO]->(:AWSSSOUser)`: Links an Entra user to their federated AWS Identity Center user.

- `(:User)-[:HAS_ACCOUNT]->(:AWSSSOUser)`: generated by analysis job `Ontology - AWSSSOUser HAS_ACCOUNT User linking`.

- `(:User)-[:HAS_ACCOUNT]->(:UserAccount)`

- `(:UserAccount)-[:CAN_ASSUME_IDENTITY]->(:AWSSSOUser)`

### AWSTag

Representation of an AWS [Tag](https://docs.aws.amazon.com/resourcegroupstagging/latest/APIReference/API_Tag.html). AWS Tags can be applied to many objects.

Note: This schema is for documentation purposes. The actual node creation uses
template-based queries because AWSTag has dynamic TAGGED relationships to many
different resource types (AWSEC2Instance, AWSS3Bucket, etc.). The cleanup is also
handled manually due to this dynamic nature.

The TAGGED relationship goes FROM the resource TO the AWSTag:
(resource)-[:TAGGED]->(AWSTag)

> **Ontology Mapping**: This node uses the ontology label [`Tag`](#ontology-tag).

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Unique identifier for this `AWSTag` node. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| key | Yes | Tag key. |
| value |  | Tag value. |
| *_ont_source* |  | Module that populated this node's ontology fields. |

#### Relationships

- `(:AWSAutoScalingGroup)-[:TAGGED]->(:AWSTag)`: `AWSAutoScalingGroup` is tagged with an `AWSTag` discovered by the AWS Resource Groups Tagging API.

- `(:AWSDBSubnetGroup)-[:TAGGED]->(:AWSTag)`: `AWSDBSubnetGroup` is tagged with an `AWSTag` discovered by the AWS Resource Groups Tagging API.

- `(:AWSDynamoDBTable)-[:TAGGED]->(:AWSTag)`: `AWSDynamoDBTable` is tagged with an `AWSTag` discovered by the AWS Resource Groups Tagging API.

- `(:AWSEBSVolume)-[:TAGGED]->(:AWSTag)`: `AWSEBSVolume` is tagged with an `AWSTag` discovered by the AWS Resource Groups Tagging API.

- `(:AWSEC2Instance)-[:TAGGED]->(:AWSTag)`: `AWSEC2Instance` is tagged with an `AWSTag` discovered by the AWS Resource Groups Tagging API.

- `(:AWSEC2KeyPair)-[:TAGGED]->(:AWSTag)`: `AWSEC2KeyPair` is tagged with an `AWSTag` discovered by the AWS Resource Groups Tagging API.

- `(:AWSEC2SecurityGroup)-[:TAGGED]->(:AWSTag)`: `AWSEC2SecurityGroup` is tagged with an `AWSTag` discovered by the AWS Resource Groups Tagging API.

- `(:AWSEC2Subnet)-[:TAGGED]->(:AWSTag)`: `AWSEC2Subnet` is tagged with an `AWSTag` discovered by the AWS Resource Groups Tagging API.

- `(:AWSECRRepository)-[:TAGGED]->(:AWSTag)`: `AWSECRRepository` is tagged with an `AWSTag` discovered by the AWS Resource Groups Tagging API.

- `(:AWSECSCluster)-[:TAGGED]->(:AWSTag)`: `AWSECSCluster` is tagged with an `AWSTag` discovered by the AWS Resource Groups Tagging API.

- `(:AWSECSContainer)-[:TAGGED]->(:AWSTag)`: `AWSECSContainer` is tagged with an `AWSTag` discovered by the AWS Resource Groups Tagging API.

- `(:AWSECSContainerInstance)-[:TAGGED]->(:AWSTag)`: `AWSECSContainerInstance` is tagged with an `AWSTag` discovered by the AWS Resource Groups Tagging API.

- `(:AWSECSTask)-[:TAGGED]->(:AWSTag)`: `AWSECSTask` is tagged with an `AWSTag` discovered by the AWS Resource Groups Tagging API.

- `(:AWSECSTaskDefinition)-[:TAGGED]->(:AWSTag)`: `AWSECSTaskDefinition` is tagged with an `AWSTag` discovered by the AWS Resource Groups Tagging API.

- `(:AWSEKSCluster)-[:TAGGED]->(:AWSTag)`: `AWSEKSCluster` is tagged with an `AWSTag` discovered by the AWS Resource Groups Tagging API.

- `(:AWSEMRCluster)-[:TAGGED]->(:AWSTag)`: `AWSEMRCluster` is tagged with an `AWSTag` discovered by the AWS Resource Groups Tagging API.

- `(:AWSESDomain)-[:TAGGED]->(:AWSTag)`: `AWSESDomain` is tagged with an `AWSTag` discovered by the AWS Resource Groups Tagging API.

- `(:AWSElasticIPAddress)-[:TAGGED]->(:AWSTag)`: `AWSElasticIPAddress` is tagged with an `AWSTag` discovered by the AWS Resource Groups Tagging API.

- `(:AWSElasticacheCluster)-[:TAGGED]->(:AWSTag)`: `AWSElasticacheCluster` is tagged with an `AWSTag` discovered by the AWS Resource Groups Tagging API.

- `(:AWSInternetGateway)-[:TAGGED]->(:AWSTag)`: `AWSInternetGateway` is tagged with an `AWSTag` discovered by the AWS Resource Groups Tagging API.

- `(:AWSKMSKey)-[:TAGGED]->(:AWSTag)`: `AWSKMSKey` is tagged with an `AWSTag` discovered by the AWS Resource Groups Tagging API.

- `(:AWSLambda)-[:TAGGED]->(:AWSTag)`: `AWSLambda` is tagged with an `AWSTag` discovered by the AWS Resource Groups Tagging API.

- `(:AWSLoadBalancer)-[:TAGGED]->(:AWSTag)`: `AWSLoadBalancer` is tagged with an `AWSTag` discovered by the AWS Resource Groups Tagging API.

- `(:AWSLoadBalancerV2)-[:TAGGED]->(:AWSTag)`: `AWSLoadBalancerV2` is tagged with an `AWSTag` discovered by the AWS Resource Groups Tagging API.

- `(:AWSNetworkInterface)-[:TAGGED]->(:AWSTag)`: `AWSNetworkInterface` is tagged with an `AWSTag` discovered by the AWS Resource Groups Tagging API.

- `(:AWSRDSCluster)-[:TAGGED]->(:AWSTag)`: `AWSRDSCluster` is tagged with an `AWSTag` discovered by the AWS Resource Groups Tagging API.

- `(:AWSRDSInstance)-[:TAGGED]->(:AWSTag)`: `AWSRDSInstance` is tagged with an `AWSTag` discovered by the AWS Resource Groups Tagging API.

- `(:AWSRDSSnapshot)-[:TAGGED]->(:AWSTag)`: `AWSRDSSnapshot` is tagged with an `AWSTag` discovered by the AWS Resource Groups Tagging API.

- `(:AWSRedshiftCluster)-[:TAGGED]->(:AWSTag)`: `AWSRedshiftCluster` is tagged with an `AWSTag` discovered by the AWS Resource Groups Tagging API.

- `(:AWSRole)-[:TAGGED]->(:AWSTag)`: `AWSRole` is tagged with an `AWSTag` discovered by the AWS Resource Groups Tagging API.

- `(:AWSS3Bucket)-[:TAGGED]->(:AWSTag)`: `AWSS3Bucket` is tagged with an `AWSTag` discovered by the AWS Resource Groups Tagging API.

- `(:AWSSQSQueue)-[:TAGGED]->(:AWSTag)`: `AWSSQSQueue` is tagged with an `AWSTag` discovered by the AWS Resource Groups Tagging API.

- `(:AWSSecretsManagerSecret)-[:TAGGED]->(:AWSTag)`: `AWSSecretsManagerSecret` is tagged with an `AWSTag` discovered by the AWS Resource Groups Tagging API.

- `(:AWSTransitGateway)-[:TAGGED]->(:AWSTag)`: `AWSTransitGateway` is tagged with an `AWSTag` discovered by the AWS Resource Groups Tagging API.

- `(:AWSTransitGatewayAttachment)-[:TAGGED]->(:AWSTag)`: `AWSTransitGatewayAttachment` is tagged with an `AWSTag` discovered by the AWS Resource Groups Tagging API.

- `(:AWSUser)-[:TAGGED]->(:AWSTag)`: `AWSUser` is tagged with an `AWSTag` discovered by the AWS Resource Groups Tagging API.

- `(:AWSVpc)-[:TAGGED]->(:AWSTag)`: `AWSVpc` is tagged with an `AWSTag` discovered by the AWS Resource Groups Tagging API.

### AWSTransitGateway

Representation of an [AWS Transit Gateway](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_TransitGateway.html).

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Unique identifier of the Transit Gateway |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| arn |  | AWS-unique identifier for this object (same as `id`) |
| description |  | Transit Gateway description |
| ownerid |  | Identifier of the owner linked to this `AWSTransitGateway` node. |
| region |  | AWS Region containing this `AWSTransitGateway` node. |
| state |  | Can be one of ``pending \| available \| modifying \| deleting \| deleted`` |
| tgw_id |  | Unique identifier of the Transit Gateway |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSTransitGateway)`

- `(:AWSTransitGateway)-[:SHARED_WITH]->(:AWSAccount)`

- `(:AWSTransitGateway)-[:TAGGED]->(:AWSTag)`: `AWSTransitGateway` is tagged with an `AWSTag` discovered by the AWS Resource Groups Tagging API.

- `(:AWSTransitGatewayAttachment)-[:ATTACHED_TO]->(:AWSTransitGateway)`

### AWSTransitGatewayAttachment

Representation of an [AWS Transit Gateway Attachment](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_TransitGatewayAttachment.html).

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Unique identifier of the Transit Gateway Attachment |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| region |  | AWS Region containing this `AWSTransitGatewayAttachment` node. |
| resource_type |  | Can be one of ``vpc \| vpn \| direct-connect-gateway \| tgw-peering`` |
| state |  | Can be one of ``initiating \| pendingAcceptance \| rollingBack \| pending \| available \| modifying \| deleting \| deleted \| failed \| rejected \| rejecting \| failing`` |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSTransitGatewayAttachment)`

- `(:AWSTransitGatewayAttachment)-[:ATTACHED_TO]->(:AWSTransitGateway)`

- `(:AWSTransitGatewayAttachment)-[:PART_OF_SUBNET]->(:AWSEC2Subnet)`

- `(:AWSTransitGatewayAttachment)-[:TAGGED]->(:AWSTag)`: `AWSTransitGatewayAttachment` is tagged with an `AWSTag` discovered by the AWS Resource Groups Tagging API.

- `(:AWSVpc)-[:RESOURCE]->(:AWSTransitGatewayAttachment)`

### AWSUser

Representation of an [AWSUser](https://docs.aws.amazon.com/IAM/latest/APIReference/API_User.html).  An AWS User is a type of AWS Principal.

> **Ontology Mapping**: This node uses the ontology label [`UserAccount`](#ontology-useraccount).

> **Additional Labels**: This node also uses `AWSPrincipal`.

> **Additional Label Definitions**:
>
> - `AWSPrincipal`: A aws node participating in the shared AWSPrincipal graph interface.

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Unique identifier for this `AWSUser` node. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| _ont_active |  | Property generated by analysis job: `Ontology - AWS user projection`. |
| _ont_has_mfa |  | Property generated by analysis job: `Ontology - AWS user projection`. |
| arn | Yes | Amazon Resource Name (ARN) of this `AWSUser` node. |
| createdate |  | Timestamp when the IAM user was created. |
| createdate_dt |  | Creation timestamp for the IAM user normalized as a Neo4j datetime. |
| name |  | Name of this `AWSUser` node. |
| passwordlastused |  | Timestamp when the IAM user's password was last used. |
| passwordlastused_dt |  | Last password-use timestamp normalized as a Neo4j datetime. |
| path |  | IAM path under which the IAM user is organized. |
| userid | Yes | Identifier of the user linked to this `AWSUser` node. |
| *_ont_lastactivity* | Yes | Normalized field sourced from `last_authenticated`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |
| *_ont_username* | Yes | Normalized field sourced from `name`. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSUser)`

- `(:AWSAccountAccessKey)-[:OWNED_BY]->(:AWSUser)`

- `(:AWSGuardDutyFinding)-[:AFFECTS]->(:AWSUser)`

- `(:AWSUser)-[:AWS_ACCESS_KEY]->(:AWSAccountAccessKey)`

- `(:AWSUser)-[:MAPS_TO]->(:KubernetesGroup)`: Links an AWS IAM user to the Kubernetes group it maps to.

- `(:AWSUser)-[:MAPS_TO]->(:KubernetesUser)`: Links an AWS IAM user to the Kubernetes user it maps to.

- `(:AWSUser)-[:MEMBER_AWS_GROUP]->(:AWSGroup)`

- `(:AWSUser)-[:MEMBER_OF]->(:AWSGroup)`

- `(:AWSUser)-[:MFA_DEVICE]->(:AWSMfaDevice)`

- `(:AWSUser)-[:TAGGED]->(:AWSTag)`: `AWSUser` is tagged with an `AWSTag` discovered by the AWS Resource Groups Tagging API.

- `(:User)-[:HAS_ACCOUNT]->(:UserAccount)`

### AWSVpc

Representation of an [AWS VPC](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_Vpc.html). More information on https://docs.aws.amazon.com/cli/latest/reference/ec2/describe-vpcs.html

> **Ontology Mapping**: This node uses the ontology label [`VirtualNetwork`](#ontology-virtualnetwork).

#### Properties

Ontology-generated fields are shown in *italics*.

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Unique identifier defined VPC node (vpcid) |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| dhcp_options_id |  | The ID of a set of DHCP options. |
| instance_tenancy |  | The allowed tenancy of instances launched into the VPC. |
| is_default |  | Indicates whether the VPC is the default VPC. |
| primary_cidr_block |  | The primary IPv4 CIDR block for the VPC. |
| region |  | (optional) the region of this VPC.  This field is only available on VPCs in your account.  It is not available on VPCs that are external to your account and linked via a VPC peering relationship. |
| state |  | The current state of the VPC. |
| vpcid | Yes | The VPC unique identifier |
| *_ont_cidr* | Yes | Normalized field sourced from `primary_cidr_block`. |
| *_ont_name* | Yes | Normalized field sourced from `id`. |
| *_ont_region* | Yes | Normalized field sourced from `region`. |
| *_ont_source* |  | Module that populated this node's ontology fields. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSVpc)`

- `(:AWSEC2NetworkAcl)-[:MEMBER_OF_AWS_VPC]->(:AWSVpc)`

- `(:AWSEC2RouteTable)-[:MEMBER_OF_AWS_VPC]->(:AWSVpc)`

- `(:AWSEC2Subnet)-[:MEMBER_OF_AWS_VPC]->(:AWSVpc)`

- `(:AWSInternetGateway)-[:ATTACHED_TO]->(:AWSVpc)`

- `(:AWSPeeringConnection)-[:ACCEPTER_VPC]->(:AWSVpc)`

- `(:AWSPeeringConnection)-[:REQUESTER_VPC]->(:AWSVpc)`

- `(:AWSRedshiftCluster)-[:MEMBER_OF_AWS_VPC]->(:AWSVpc)`

- `(:AWSVpc)-[:BLOCK_ASSOCIATION]->(:AWSCidrBlock)`

- `(:AWSVpc)-[:MEMBER_OF_EC2_SECURITY_GROUP]->(:AWSEC2SecurityGroup)`

- `(:AWSVpc)-[:RESOURCE]->(:AWSTransitGatewayAttachment)`

- `(:AWSVpc)-[:TAGGED]->(:AWSTag)`: `AWSVpc` is tagged with an `AWSTag` discovered by the AWS Resource Groups Tagging API.

- `(:AWSVpcEndpoint)-[:MEMBER_OF_AWS_VPC]->(:AWSVpc)`

- `(:DatabricksNetworkConfig)-[:USES_VPC]->(:AWSVpc)`: A Databricks network configuration uses an AWS VPC.

### AWSVpcEndpoint

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Unique identifier for this `AWSVpcEndpoint` node. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| creation_timestamp |  | Timestamp when the VPC endpoint was created. |
| dns_entries |  | DNS names and hosted-zone identifiers assigned to the VPC endpoint. |
| ip_address_type |  | IP address family supported by the VPC endpoint. |
| network_interface_ids |  | Identifiers of the network interface linked to this `AWSVpcEndpoint` node. |
| owner_id |  | Identifier of the owner linked to this `AWSVpcEndpoint` node. |
| policy_document |  | JSON access policy attached to the VPC endpoint. |
| private_dns_enabled |  | Whether private dns is enabled for this `AWSVpcEndpoint` node. |
| region |  | AWS Region containing this `AWSVpcEndpoint` node. |
| requester_managed |  | Whether this `AWSVpcEndpoint` node is managed by its service requester. |
| route_table_ids |  | Identifiers of the route table linked to this `AWSVpcEndpoint` node. |
| service_name |  | AWS service name exposed through the VPC endpoint. |
| service_region |  | AWS Region in which the endpoint service is available. |
| state |  | Current lifecycle state of this `AWSVpcEndpoint` node. |
| subnet_ids |  | Identifiers of the subnet linked to this `AWSVpcEndpoint` node. |
| vpc_endpoint_id | Yes | Identifier of the VPC endpoint linked to this `AWSVpcEndpoint` node. |
| vpc_endpoint_type |  | VPC endpoint type, such as Interface, Gateway, or GatewayLoadBalancer. |
| vpc_id |  | Identifier of the VPC linked to this `AWSVpcEndpoint` node. |

#### Relationships

- `(:AWSAccount)-[:RESOURCE]->(:AWSVpcEndpoint)`

- `(:AWSEC2Route)-[:ROUTES_TO_VPC_ENDPOINT]->(:AWSVpcEndpoint)`

- `(:AWSVpcEndpoint)-[:MEMBER_OF_AWS_VPC]->(:AWSVpc)`

- `(:AWSVpcEndpoint)-[:MEMBER_OF_SECURITY_GROUP]->(:AWSEC2SecurityGroup)`

- `(:AWSVpcEndpoint)-[:ROUTES_THROUGH]->(:AWSRouteTable)`

- `(:AWSVpcEndpoint)-[:USES_SUBNET]->(:AWSEC2Subnet)`

- `(:DatabricksVpcEndpoint)-[:POINTS_TO]->(:AWSVpcEndpoint)`: A registered Databricks VPC endpoint points to an AWS VPC endpoint.
