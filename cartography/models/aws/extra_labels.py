from dataclasses import dataclass

from cartography.models.core.nodes import ExtraNodeLabel


@dataclass(frozen=True)
class AWSIpRuleLabel(ExtraNodeLabel):
    """A aws node participating in the shared AWSIpRule graph interface."""

    label: str = "AWSIpRule"


@dataclass(frozen=True)
class AWSIpv4CidrBlockLabel(ExtraNodeLabel):
    """A aws node participating in the shared AWSIpv4CidrBlock graph interface."""

    label: str = "AWSIpv4CidrBlock"


@dataclass(frozen=True)
class AWSIpv6CidrBlockLabel(ExtraNodeLabel):
    """A aws node participating in the shared AWSIpv6CidrBlock graph interface."""

    label: str = "AWSIpv6CidrBlock"


@dataclass(frozen=True)
class AWSPolicyLabel(ExtraNodeLabel):
    """A aws node participating in the shared AWSPolicy graph interface."""

    label: str = "AWSPolicy"


@dataclass(frozen=True)
class AWSPrincipalLabel(ExtraNodeLabel):
    """A aws node participating in the shared AWSPrincipal graph interface."""

    label: str = "AWSPrincipal"


@dataclass(frozen=True)
class EndpointLabel(ExtraNodeLabel):
    """A aws node participating in the shared Endpoint graph interface."""

    label: str = "Endpoint"


@dataclass(frozen=True)
class IpLabel(ExtraNodeLabel):
    """A aws node participating in the shared Ip graph interface."""

    label: str = "Ip"


@dataclass(frozen=True)
class KeyPairLabel(ExtraNodeLabel):
    """A aws node participating in the shared KeyPair graph interface."""

    label: str = "KeyPair"


@dataclass(frozen=True)
class MfaDeviceLabel(ExtraNodeLabel):
    """A aws node participating in the shared MfaDevice graph interface."""

    label: str = "MfaDevice"


@dataclass(frozen=True)
class SSMParameterLabel(ExtraNodeLabel):
    """A aws node participating in the shared SSMParameter graph interface."""

    label: str = "SSMParameter"


@dataclass(frozen=True)
class LoadBalancerV2Label(ExtraNodeLabel):
    """A aws node participating in the shared LoadBalancerV2 graph interface."""

    label: str = "LoadBalancerV2"


@dataclass(frozen=True)
class LegacyACMCertificateLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `ACMCertificate` aws node label."""

    label: str = "ACMCertificate"


@dataclass(frozen=True)
class LegacyAPIGatewayClientCertificateLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `APIGatewayClientCertificate` aws node label."""

    label: str = "APIGatewayClientCertificate"


@dataclass(frozen=True)
class LegacyAPIGatewayDeploymentLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `APIGatewayDeployment` aws node label."""

    label: str = "APIGatewayDeployment"


@dataclass(frozen=True)
class LegacyAPIGatewayIntegrationLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `APIGatewayIntegration` aws node label."""

    label: str = "APIGatewayIntegration"


@dataclass(frozen=True)
class LegacyAPIGatewayMethodLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `APIGatewayMethod` aws node label."""

    label: str = "APIGatewayMethod"


@dataclass(frozen=True)
class LegacyAPIGatewayResourceLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `APIGatewayResource` aws node label."""

    label: str = "APIGatewayResource"


@dataclass(frozen=True)
class LegacyAPIGatewayRestAPILabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `APIGatewayRestAPI` aws node label."""

    label: str = "APIGatewayRestAPI"


@dataclass(frozen=True)
class LegacyAPIGatewayStageLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `APIGatewayStage` aws node label."""

    label: str = "APIGatewayStage"


@dataclass(frozen=True)
class LegacyAPIGatewayV2APILabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `APIGatewayV2API` aws node label."""

    label: str = "APIGatewayV2API"


@dataclass(frozen=True)
class LegacyAccountAccessKeyLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `AccountAccessKey` aws node label."""

    label: str = "AccountAccessKey"


@dataclass(frozen=True)
class LegacyAutoScalingGroupLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `AutoScalingGroup` aws node label."""

    label: str = "AutoScalingGroup"


@dataclass(frozen=True)
class LegacyCloudFormationStackLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `CloudFormationStack` aws node label."""

    label: str = "CloudFormationStack"


@dataclass(frozen=True)
class LegacyCloudFrontDistributionLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `CloudFrontDistribution` aws node label."""

    label: str = "CloudFrontDistribution"


@dataclass(frozen=True)
class LegacyCloudTrailTrailLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `CloudTrailTrail` aws node label."""

    label: str = "CloudTrailTrail"


@dataclass(frozen=True)
class LegacyCloudWatchLogGroupLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `CloudWatchLogGroup` aws node label."""

    label: str = "CloudWatchLogGroup"


@dataclass(frozen=True)
class LegacyCloudWatchLogMetricFilterLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `CloudWatchLogMetricFilter` aws node label."""

    label: str = "CloudWatchLogMetricFilter"


@dataclass(frozen=True)
class LegacyCloudWatchMetricAlarmLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `CloudWatchMetricAlarm` aws node label."""

    label: str = "CloudWatchMetricAlarm"


@dataclass(frozen=True)
class LegacyCodeBuildProjectLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `CodeBuildProject` aws node label."""

    label: str = "CodeBuildProject"


@dataclass(frozen=True)
class LegacyCognitoIdentityPoolLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `CognitoIdentityPool` aws node label."""

    label: str = "CognitoIdentityPool"


@dataclass(frozen=True)
class LegacyCognitoUserPoolLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `CognitoUserPool` aws node label."""

    label: str = "CognitoUserPool"


@dataclass(frozen=True)
class LegacyDBSubnetGroupLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `DBSubnetGroup` aws node label."""

    label: str = "DBSubnetGroup"


@dataclass(frozen=True)
class LegacyDynamoDBArchivalSummaryLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `DynamoDBArchivalSummary` aws node label."""

    label: str = "DynamoDBArchivalSummary"


@dataclass(frozen=True)
class LegacyDynamoDBBackupLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `DynamoDBBackup` aws node label."""

    label: str = "DynamoDBBackup"


@dataclass(frozen=True)
class LegacyDynamoDBBillingModeSummaryLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `DynamoDBBillingModeSummary` aws node label."""

    label: str = "DynamoDBBillingModeSummary"


@dataclass(frozen=True)
class LegacyDynamoDBGlobalSecondaryIndexLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `DynamoDBGlobalSecondaryIndex` aws node label."""

    label: str = "DynamoDBGlobalSecondaryIndex"


@dataclass(frozen=True)
class LegacyDynamoDBRestoreSummaryLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `DynamoDBRestoreSummary` aws node label."""

    label: str = "DynamoDBRestoreSummary"


@dataclass(frozen=True)
class LegacyDynamoDBSSEDescriptionLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `DynamoDBSSEDescription` aws node label."""

    label: str = "DynamoDBSSEDescription"


@dataclass(frozen=True)
class LegacyDynamoDBStreamLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `DynamoDBStream` aws node label."""

    label: str = "DynamoDBStream"


@dataclass(frozen=True)
class LegacyDynamoDBTableLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `DynamoDBTable` aws node label."""

    label: str = "DynamoDBTable"


@dataclass(frozen=True)
class LegacyEBSSnapshotLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `EBSSnapshot` aws node label."""

    label: str = "EBSSnapshot"


@dataclass(frozen=True)
class LegacyEBSVolumeLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `EBSVolume` aws node label."""

    label: str = "EBSVolume"


@dataclass(frozen=True)
class LegacyEC2ImageLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `EC2Image` aws node label."""

    label: str = "EC2Image"


@dataclass(frozen=True)
class LegacyEC2InstanceLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `EC2Instance` aws node label."""

    label: str = "EC2Instance"


@dataclass(frozen=True)
class LegacyEC2Ipv6AddressLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `EC2Ipv6Address` aws node label."""

    label: str = "EC2Ipv6Address"


@dataclass(frozen=True)
class LegacyEC2KeyPairLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `EC2KeyPair` aws node label."""

    label: str = "EC2KeyPair"


@dataclass(frozen=True)
class LegacyEC2NetworkAclLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `EC2NetworkAcl` aws node label."""

    label: str = "EC2NetworkAcl"


@dataclass(frozen=True)
class LegacyEC2NetworkAclRuleLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `EC2NetworkAclRule` aws node label."""

    label: str = "EC2NetworkAclRule"


@dataclass(frozen=True)
class LegacyEC2PrivateIpLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `EC2PrivateIp` aws node label."""

    label: str = "EC2PrivateIp"


@dataclass(frozen=True)
class LegacyEC2ReservationLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `EC2Reservation` aws node label."""

    label: str = "EC2Reservation"


@dataclass(frozen=True)
class LegacyEC2ReservedInstanceLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `EC2ReservedInstance` aws node label."""

    label: str = "EC2ReservedInstance"


@dataclass(frozen=True)
class LegacyEC2RouteLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `EC2Route` aws node label."""

    label: str = "EC2Route"


@dataclass(frozen=True)
class LegacyEC2RouteTableLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `EC2RouteTable` aws node label."""

    label: str = "EC2RouteTable"


@dataclass(frozen=True)
class LegacyEC2RouteTableAssociationLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `EC2RouteTableAssociation` aws node label."""

    label: str = "EC2RouteTableAssociation"


@dataclass(frozen=True)
class LegacyEC2SecurityGroupLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `EC2SecurityGroup` aws node label."""

    label: str = "EC2SecurityGroup"


@dataclass(frozen=True)
class LegacyEC2SubnetLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `EC2Subnet` aws node label."""

    label: str = "EC2Subnet"


@dataclass(frozen=True)
class LegacyECRImageLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `ECRImage` aws node label."""

    label: str = "ECRImage"


@dataclass(frozen=True)
class LegacyECRImageLayerLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `ECRImageLayer` aws node label."""

    label: str = "ECRImageLayer"


@dataclass(frozen=True)
class LegacyECRPullThroughCacheRuleLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `ECRPullThroughCacheRule` aws node label."""

    label: str = "ECRPullThroughCacheRule"


@dataclass(frozen=True)
class LegacyECRRepositoryLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `ECRRepository` aws node label."""

    label: str = "ECRRepository"


@dataclass(frozen=True)
class LegacyECRRepositoryImageLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `ECRRepositoryImage` aws node label."""

    label: str = "ECRRepositoryImage"


@dataclass(frozen=True)
class LegacyECSClusterLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `ECSCluster` aws node label."""

    label: str = "ECSCluster"


@dataclass(frozen=True)
class LegacyECSContainerLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `ECSContainer` aws node label."""

    label: str = "ECSContainer"


@dataclass(frozen=True)
class LegacyECSContainerDefinitionLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `ECSContainerDefinition` aws node label."""

    label: str = "ECSContainerDefinition"


@dataclass(frozen=True)
class LegacyECSContainerInstanceLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `ECSContainerInstance` aws node label."""

    label: str = "ECSContainerInstance"


@dataclass(frozen=True)
class LegacyECSServiceLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `ECSService` aws node label."""

    label: str = "ECSService"


@dataclass(frozen=True)
class LegacyECSTaskLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `ECSTask` aws node label."""

    label: str = "ECSTask"


@dataclass(frozen=True)
class LegacyECSTaskDefinitionLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `ECSTaskDefinition` aws node label."""

    label: str = "ECSTaskDefinition"


@dataclass(frozen=True)
class LegacyEKSClusterLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `EKSCluster` aws node label."""

    label: str = "EKSCluster"


@dataclass(frozen=True)
class LegacyELBListenerLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `ELBListener` aws node label."""

    label: str = "ELBListener"


@dataclass(frozen=True)
class LegacyELBV2ListenerLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `ELBV2Listener` aws node label."""

    label: str = "ELBV2Listener"


@dataclass(frozen=True)
class LegacyELBV2TargetGroupLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `ELBV2TargetGroup` aws node label."""

    label: str = "ELBV2TargetGroup"


@dataclass(frozen=True)
class LegacyEMRClusterLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `EMRCluster` aws node label."""

    label: str = "EMRCluster"


@dataclass(frozen=True)
class LegacyESDomainLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `ESDomain` aws node label."""

    label: str = "ESDomain"


@dataclass(frozen=True)
class LegacyEfsAccessPointLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `EfsAccessPoint` aws node label."""

    label: str = "EfsAccessPoint"


@dataclass(frozen=True)
class LegacyEfsFileSystemLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `EfsFileSystem` aws node label."""

    label: str = "EfsFileSystem"


@dataclass(frozen=True)
class LegacyEfsMountTargetLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `EfsMountTarget` aws node label."""

    label: str = "EfsMountTarget"


@dataclass(frozen=True)
class LegacyElasticIPAddressLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `ElasticIPAddress` aws node label."""

    label: str = "ElasticIPAddress"


@dataclass(frozen=True)
class LegacyElasticacheClusterLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `ElasticacheCluster` aws node label."""

    label: str = "ElasticacheCluster"


@dataclass(frozen=True)
class LegacyElasticacheTopicLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `ElasticacheTopic` aws node label."""

    label: str = "ElasticacheTopic"


@dataclass(frozen=True)
class LegacyEventBridgeRuleLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `EventBridgeRule` aws node label."""

    label: str = "EventBridgeRule"


@dataclass(frozen=True)
class LegacyEventBridgeTargetLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `EventBridgeTarget` aws node label."""

    label: str = "EventBridgeTarget"


@dataclass(frozen=True)
class LegacyGlueConnectionLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `GlueConnection` aws node label."""

    label: str = "GlueConnection"


@dataclass(frozen=True)
class LegacyGlueJobLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `GlueJob` aws node label."""

    label: str = "GlueJob"


@dataclass(frozen=True)
class LegacyGuardDutyDetectorLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `GuardDutyDetector` aws node label."""

    label: str = "GuardDutyDetector"


@dataclass(frozen=True)
class LegacyGuardDutyFindingLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `GuardDutyFinding` aws node label."""

    label: str = "GuardDutyFinding"


@dataclass(frozen=True)
class LegacyKMSAliasLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `KMSAlias` aws node label."""

    label: str = "KMSAlias"


@dataclass(frozen=True)
class LegacyKMSGrantLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `KMSGrant` aws node label."""

    label: str = "KMSGrant"


@dataclass(frozen=True)
class LegacyKMSKeyLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `KMSKey` aws node label."""

    label: str = "KMSKey"


@dataclass(frozen=True)
class LegacyLaunchConfigurationLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `LaunchConfiguration` aws node label."""

    label: str = "LaunchConfiguration"


@dataclass(frozen=True)
class LegacyLaunchTemplateLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `LaunchTemplate` aws node label."""

    label: str = "LaunchTemplate"


@dataclass(frozen=True)
class LegacyLaunchTemplateVersionLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `LaunchTemplateVersion` aws node label."""

    label: str = "LaunchTemplateVersion"


@dataclass(frozen=True)
class LegacyNameServerLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `NameServer` aws node label."""

    label: str = "NameServer"


@dataclass(frozen=True)
class LegacyPublicSSMParameterLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `PublicSSMParameter` aws node label."""

    label: str = "PublicSSMParameter"


@dataclass(frozen=True)
class LegacyRDSClusterLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `RDSCluster` aws node label."""

    label: str = "RDSCluster"


@dataclass(frozen=True)
class LegacyRDSEventSubscriptionLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `RDSEventSubscription` aws node label."""

    label: str = "RDSEventSubscription"


@dataclass(frozen=True)
class LegacyRDSInstanceLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `RDSInstance` aws node label."""

    label: str = "RDSInstance"


@dataclass(frozen=True)
class LegacyRDSSnapshotLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `RDSSnapshot` aws node label."""

    label: str = "RDSSnapshot"


@dataclass(frozen=True)
class LegacyRedshiftClusterLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `RedshiftCluster` aws node label."""

    label: str = "RedshiftCluster"


@dataclass(frozen=True)
class LegacyS3AccountPublicAccessBlockLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `S3AccountPublicAccessBlock` aws node label."""

    label: str = "S3AccountPublicAccessBlock"


@dataclass(frozen=True)
class LegacyS3AclLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `S3Acl` aws node label."""

    label: str = "S3Acl"


@dataclass(frozen=True)
class LegacyS3BucketLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `S3Bucket` aws node label."""

    label: str = "S3Bucket"


@dataclass(frozen=True)
class LegacyS3PolicyStatementLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `S3PolicyStatement` aws node label."""

    label: str = "S3PolicyStatement"


@dataclass(frozen=True)
class LegacySESEmailIdentityLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `SESEmailIdentity` aws node label."""

    label: str = "SESEmailIdentity"


@dataclass(frozen=True)
class LegacySNSTopicLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `SNSTopic` aws node label."""

    label: str = "SNSTopic"


@dataclass(frozen=True)
class LegacySNSTopicSubscriptionLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `SNSTopicSubscription` aws node label."""

    label: str = "SNSTopicSubscription"


@dataclass(frozen=True)
class LegacySQSQueueLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `SQSQueue` aws node label."""

    label: str = "SQSQueue"


@dataclass(frozen=True)
class LegacySSMInstanceInformationLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `SSMInstanceInformation` aws node label."""

    label: str = "SSMInstanceInformation"


@dataclass(frozen=True)
class LegacySSMInstancePatchLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `SSMInstancePatch` aws node label."""

    label: str = "SSMInstancePatch"


@dataclass(frozen=True)
class LegacySecretsManagerSecretLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `SecretsManagerSecret` aws node label."""

    label: str = "SecretsManagerSecret"


@dataclass(frozen=True)
class LegacySecretsManagerSecretVersionLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `SecretsManagerSecretVersion` aws node label."""

    label: str = "SecretsManagerSecretVersion"


@dataclass(frozen=True)
class LegacySecurityHubLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `SecurityHub` aws node label."""

    label: str = "SecurityHub"
