CREATE INDEX ON :AWSConfigurationRecorder(id);
CREATE INDEX ON :AWSConfigurationRecorder(lastupdated);
CREATE INDEX ON :AWSConfigDeliveryChannel(id);
CREATE INDEX ON :AWSConfigDeliveryChannel(lastupdated);
CREATE INDEX ON :AWSConfigRule(id);
CREATE INDEX ON :AWSConfigRule(lastupdated);
CREATE INDEX ON :APIGatewayClientCertificate(id);
CREATE INDEX ON :APIGatewayClientCertificate(lastupdated);
CREATE INDEX ON :APIGatewayRestAPI(id);
CREATE INDEX ON :APIGatewayRestAPI(lastupdated);
CREATE INDEX ON :APIGatewayResource(id);
CREATE INDEX ON :APIGatewayResource(lastupdated);
CREATE INDEX ON :APIGatewayStage(id);
CREATE INDEX ON :APIGatewayStage(lastupdated);
CREATE INDEX ON :AWSAccount(id);
CREATE INDEX ON :AWSAccount(lastupdated);
CREATE INDEX ON :AWSCidrBlock(id);
CREATE INDEX ON :AWSCidrBlock(lastupdated);
CREATE INDEX ON :AWSDNSRecord(id);
CREATE INDEX ON :AWSDNSRecord(lastupdated);
CREATE INDEX ON :AWSDNSZone(name);
CREATE INDEX ON :AWSDNSZone(zoneid);
CREATE INDEX ON :AWSDNSZone(lastupdated);
CREATE INDEX ON :AWSGroup(arn);
CREATE INDEX ON :AWSGroup(lastupdated);
CREATE INDEX ON :AWSInspectorFinding(id);
CREATE INDEX ON :AWSInspectorPackage(id);
CREATE INDEX ON :AWSInternetGateway(id);
CREATE INDEX ON :AWSInternetGateway(lastupdated);
CREATE INDEX ON :AWSIpv4CidrBlock(id);
CREATE INDEX ON :AWSIpv4CidrBlock(lastupdated);
CREATE INDEX ON :AWSIpv6CidrBlock(id);
CREATE INDEX ON :AWSIpv6CidrBlock(lastupdated);
CREATE INDEX ON :AWSLambda(id);
CREATE INDEX ON :AWSLambda(lastupdated);
CREATE INDEX ON :AWSLambdaEventSourceMapping(id);
CREATE INDEX ON :AWSLambdaEventSourceMapping(lastupdated);
CREATE INDEX ON :AWSLambdaFunctionAlias(id);
CREATE INDEX ON :AWSLambdaFunctionAlias(lastupdated);
CREATE INDEX ON :AWSLambdaLayer(id);
CREATE INDEX ON :AWSLambdaLayer(lastupdated);
CREATE INDEX ON :AWSPeeringConnection(id);
CREATE INDEX ON :AWSPeeringConnection(lastupdated);
CREATE INDEX ON :AWSPolicy(id);
CREATE INDEX ON :AWSPolicy(name);
CREATE INDEX ON :AWSPolicy(lastupdated);
CREATE INDEX ON :AWSPolicyStatement(id);
CREATE INDEX ON :AWSPolicyStatement(lastupdated);
CREATE INDEX ON :AWSPrincipal(arn);
CREATE INDEX ON :AWSPrincipal(lastupdated);
CREATE INDEX ON :AWSRole(arn);
CREATE INDEX ON :AWSRole(lastupdated);
CREATE INDEX ON :AWSTag(id);
CREATE INDEX ON :AWSTag(key);
CREATE INDEX ON :AWSTag(lastupdated);
CREATE INDEX ON :AWSTransitGateway(arn);
CREATE INDEX ON :AWSTransitGateway(id);
CREATE INDEX ON :AWSTransitGateway(lastupdated);
CREATE INDEX ON :AWSTransitGatewayAttachment(id);
CREATE INDEX ON :AWSTransitGatewayAttachment(lastupdated);
CREATE INDEX ON :AWSUser(arn);
CREATE INDEX ON :AWSUser(name);
CREATE INDEX ON :AWSUser(lastupdated);
CREATE INDEX ON :AWSVpc(id);
CREATE INDEX ON :AWSVpc(lastupdated);
CREATE INDEX ON :AccountAccessKey(accesskeyid);
CREATE INDEX ON :AccountAccessKey(lastupdated);
CREATE INDEX ON :AutoScalingGroup(arn);
CREATE INDEX ON :AutoScalingGroup(lastupdated);
CREATE INDEX ON :ChromeExtension(id);
CREATE INDEX ON :ChromeExtension(lastupdated);
CREATE INDEX ON :CrowdstrikeHost(id);
CREATE INDEX ON :CrowdstrikeHost(instance_id);
CREATE INDEX ON :CrowdstrikeHost(lastupdated);
CREATE INDEX ON :CVE(id);
CREATE INDEX ON :CVE(lastupdated);
CREATE INDEX ON :Dependency(id);
CREATE INDEX ON :Dependency(lastupdated);
CREATE INDEX ON :DBGroup(name);
CREATE INDEX ON :DBGroup(lastupdated);
CREATE INDEX ON :DNSRecord(id);
CREATE INDEX ON :DNSRecord(lastupdated);
CREATE INDEX ON :DNSZone(name);
CREATE INDEX ON :DNSZone(lastupdated);
CREATE INDEX ON :DOAccount(id);
CREATE INDEX ON :DOAccount(lastupdated);
CREATE INDEX ON :DODroplet(id);
CREATE INDEX ON :DODroplet(lastupdated);
CREATE INDEX ON :DOProject(id);
CREATE INDEX ON :DOProject(lastupdated);
CREATE INDEX ON :DynamoDBGlobalSecondaryIndex(id);
CREATE INDEX ON :DynamoDBGlobalSecondaryIndex(lastupdated);
CREATE INDEX ON :DynamoDBTable(arn);
CREATE INDEX ON :DynamoDBTable(id);
CREATE INDEX ON :DynamoDBTable(lastupdated);
CREATE INDEX ON :EBSSnapshot(id);
CREATE INDEX ON :EBSSnapshot(lastupdated);
CREATE INDEX ON :EBSVolume(id);
CREATE INDEX ON :EBSVolume(lastupdated);
CREATE INDEX ON :EC2Image(id);
CREATE INDEX ON :EC2Image(lastupdated);
CREATE INDEX ON :EC2Instance(id);
CREATE INDEX ON :EC2Instance(instanceid);
CREATE INDEX ON :EC2Instance(publicdnsname);
CREATE INDEX ON :EC2Instance(lastupdated);
CREATE INDEX ON :EC2KeyPair(id);
CREATE INDEX ON :EC2KeyPair(keyfingerprint);
CREATE INDEX ON :EC2KeyPair(lastupdated);
CREATE INDEX ON :EC2PrivateIp(id);
CREATE INDEX ON :EC2PrivateIp(lastupdated);
CREATE INDEX ON :EC2Reservation(reservationid);
CREATE INDEX ON :EC2Reservation(lastupdated);
CREATE INDEX ON :EC2ReservedInstance(id);
CREATE INDEX ON :EC2ReservedInstance(lastupdated);
CREATE INDEX ON :EC2SecurityGroup(groupid);
CREATE INDEX ON :EC2SecurityGroup(id);
CREATE INDEX ON :EC2SecurityGroup(lastupdated);
CREATE INDEX ON :EC2Subnet(id);
CREATE INDEX ON :EC2Subnet(subnetid);
CREATE INDEX ON :EC2Subnet(lastupdated);
CREATE INDEX ON :ECRImage(id);
CREATE INDEX ON :ECRImage(digest);
CREATE INDEX ON :ECRImage(lastupdated);
CREATE INDEX ON :ECRRepository(id);
CREATE INDEX ON :ECRRepository(name);
CREATE INDEX ON :ECRRepository(uri);
CREATE INDEX ON :ECRRepository(lastupdated);
CREATE INDEX ON :ECRRepositoryImage(id);
CREATE INDEX ON :ECRRepositoryImage(uri);
CREATE INDEX ON :ECRRepositoryImage(tag);
CREATE INDEX ON :ECRRepositoryImage(lastupdated);
CREATE INDEX ON :ECRScanFinding(id);
CREATE INDEX ON :ECRScanFinding(lastupdated);
CREATE INDEX ON :ECSCluster(id);
CREATE INDEX ON :ECSCluster(lastupdated);
CREATE INDEX ON :ECSContainerInstance(id);
CREATE INDEX ON :ECSContainerInstance(lastupdated);
CREATE INDEX ON :ECSService(id);
CREATE INDEX ON :ECSService(lastupdated);
CREATE INDEX ON :ECSTaskDefinition(id);
CREATE INDEX ON :ECSTaskDefinition(lastupdated);
CREATE INDEX ON :ECSTask(id);
CREATE INDEX ON :ECSTask(lastupdated);
CREATE INDEX ON :ECSContainerDefinition(id);
CREATE INDEX ON :ECSContainerDefinition(lastupdated);
CREATE INDEX ON :ECSContainer(id);
CREATE INDEX ON :ECSContainer(lastupdated);
CREATE INDEX ON :EKSCluster(id);
CREATE INDEX ON :EKSCluster(lastupdated);
CREATE INDEX ON :ElasticacheCluster(id);
CREATE INDEX ON :ElasticacheCluster(arn);
CREATE INDEX ON :ElasticacheCluster(lastupdated);
CREATE INDEX ON :ElasticIPAddress(id);
CREATE INDEX ON :ElasticIPAddress(lastupdated);
CREATE INDEX ON :ELBListener(id);
CREATE INDEX ON :ELBListener(lastupdated);
CREATE INDEX ON :ELBV2Listener(id);
CREATE INDEX ON :ELBV2Listener(lastupdated);
CREATE INDEX ON :EMRCluster(id);
CREATE INDEX ON :EMRCluster(arn);
CREATE INDEX ON :EMRCluster(lastupdated);
CREATE INDEX ON :Endpoint(id);
CREATE INDEX ON :Endpoint(lastupdated);
CREATE INDEX ON :ESDomain(arn);
CREATE INDEX ON :ESDomain(id);
CREATE INDEX ON :ESDomain(name);
CREATE INDEX ON :ESDomain(lastupdated);
CREATE INDEX ON :GCPDNSZone(id);
CREATE INDEX ON :GCPDNSZone(lastupdated);
CREATE INDEX ON :GCPRecordSet(id);
CREATE INDEX ON :GCPRecordSet(lastupdated);
CREATE INDEX ON :GCPFolder(id);
CREATE INDEX ON :GCPFolder(lastupdated);
CREATE INDEX ON :GCPForwardingRule(id);
CREATE INDEX ON :GCPForwardingRule(lastupdated);
CREATE INDEX ON :GCPInstance(id);
CREATE INDEX ON :GCPInstance(lastupdated);
CREATE INDEX ON :GCPNetworkInterface(id);
CREATE INDEX ON :GCPNetworkInterface(lastupdated);
CREATE INDEX ON :GCPNetworkTag(id);
CREATE INDEX ON :GCPNetworkTag(lastupdated);
CREATE INDEX ON :GCPNicAccessConfig(id);
CREATE INDEX ON :GCPNicAccessConfig(lastupdated);
CREATE INDEX ON :GCPOrganization(id);
CREATE INDEX ON :GCPOrganization(lastupdated);
CREATE INDEX ON :GCPProject(id);
CREATE INDEX ON :GCPProject(projectnumber);
CREATE INDEX ON :GCPProject(lastupdated);
CREATE INDEX ON :GCPBucket(id);
CREATE INDEX ON :GCPBucket(lastupdated);
CREATE INDEX ON :GCPBucketLabel(key);
CREATE INDEX ON :GCPBucketLabel(lastupdated);
CREATE INDEX ON :GCPSubnet(id);
CREATE INDEX ON :GCPSubnet(lastupdated);
CREATE INDEX ON :GCPVpc(id);
CREATE INDEX ON :GCPVpc(lastupdated);
CREATE INDEX ON :GitHubOrganization(id);
CREATE INDEX ON :GitHubOrganization(lastupdated);
CREATE INDEX ON :GitHubRepository(id);
CREATE INDEX ON :GitHubRepository(lastupdated);
CREATE INDEX ON :GitHubUser(id);
CREATE INDEX ON :GitHubUser(lastupdated);
CREATE INDEX ON :GKECluster(id);
CREATE INDEX ON :GKECluster(lastupdated);
CREATE INDEX ON :GSuiteGroup(email);
CREATE INDEX ON :GSuiteGroup(id);
CREATE INDEX ON :GSuiteGroup(lastupdated);
CREATE INDEX ON :GSuiteUser(email);
CREATE INDEX ON :GSuiteUser(id);
CREATE INDEX ON :GSuiteUser(lastupdated);
CREATE INDEX ON :Ip(id);
CREATE INDEX ON :Ip(ip);
CREATE INDEX ON :Ip(lastupdated);
CREATE INDEX ON :IpPermissionInbound(ruleid);
CREATE INDEX ON :IpPermissionInbound(lastupdated);
CREATE INDEX ON :IpPermissionsEgress(ruleid);
CREATE INDEX ON :IpPermissionsEgress(lastupdated);
CREATE INDEX ON :IpRange(id);
CREATE INDEX ON :IpRange(lastupdated);
CREATE INDEX ON :IpRule(ruleid);
CREATE INDEX ON :IpRule(lastupdated);
CREATE INDEX ON :JamfComputerGroup(id);
CREATE INDEX ON :JamfComputerGroup(lastupdated);
CREATE INDEX ON :KMSKey(id);
CREATE INDEX ON :KMSKey(arn);
CREATE INDEX ON :KMSKey(lastupdated);
CREATE INDEX ON :KMSAlias(id);
CREATE INDEX ON :KMSAlias(lastupdated);
CREATE INDEX ON :KMSGrant(id);
CREATE INDEX ON :KMSGrant(lastupdated);
CREATE INDEX ON :LaunchConfiguration(id);
CREATE INDEX ON :LaunchConfiguration(name);
CREATE INDEX ON :LaunchConfiguration(lastupdated);
CREATE INDEX ON :LaunchTemplate(id);
CREATE INDEX ON :LaunchTemplate(name);
CREATE INDEX ON :LaunchTemplate(lastupdated);
CREATE INDEX ON :LaunchTemplateVersion(id);
CREATE INDEX ON :LaunchTemplateVersion(name);
CREATE INDEX ON :LaunchTemplateVersion(lastupdated);
CREATE INDEX ON :LoadBalancer(dnsname);
CREATE INDEX ON :LoadBalancer(id);
CREATE INDEX ON :LoadBalancer(lastupdated);
CREATE INDEX ON :LoadBalancerV2(dnsname);
CREATE INDEX ON :LoadBalancerV2(id);
CREATE INDEX ON :LoadBalancerV2(lastupdated);
CREATE INDEX ON :NetworkInterface(id);
CREATE INDEX ON :NetworkInterface(lastupdated);
CREATE INDEX ON :NameServer(id);
CREATE INDEX ON :NameServer(lastupdated);
CREATE INDEX ON :OktaOrganization(id);
CREATE INDEX ON :OktaOrganization(lastupdated);
CREATE INDEX ON :OktaUser(id);
CREATE INDEX ON :OktaUser(email);
CREATE INDEX ON :OktaUser(lastupdated);
CREATE INDEX ON :OktaGroup(id);
CREATE INDEX ON :OktaGroup(name);
CREATE INDEX ON :OktaGroup(lastupdated);
CREATE INDEX ON :OktaApplication(id);
CREATE INDEX ON :OktaApplication(lastupdated);
CREATE INDEX ON :OktaUserFactor(id);
CREATE INDEX ON :OktaUserFactor(lastupdated);
CREATE INDEX ON :OktaTrustedOrigin(id);
CREATE INDEX ON :OktaTrustedOrigin(lastupdated);
CREATE INDEX ON :OktaAdministrationRole(id);
CREATE INDEX ON :OktaAdministrationRole(lastupdated);
CREATE INDEX ON :OCICompartment(ocid);
CREATE INDEX ON :OCICompartment(name);
CREATE INDEX ON :OCICompartment(lastupdated);
CREATE INDEX ON :OCIGroup(ocid);
CREATE INDEX ON :OCIGroup(lastupdated);
CREATE INDEX ON :OCIPolicy(ocid);
CREATE INDEX ON :OCIPolicy(lastupdated);
CREATE INDEX ON :OCIRegion(key);
CREATE INDEX ON :OCIRegion(name);
CREATE INDEX ON :OCIRegion(lastupdated);
CREATE INDEX ON :OCITenancy(ocid);
CREATE INDEX ON :OCITenancy(lastupdated);
CREATE INDEX ON :OCIUser(ocid);
CREATE INDEX ON :OCIUser(name);
CREATE INDEX ON :OCIUser(lastupdated);
CREATE INDEX ON :Package(id);
CREATE INDEX ON :Package(name);
CREATE INDEX ON :Package(lastupdated);
CREATE INDEX ON :PagerDutyEscalationPolicy(id);
CREATE INDEX ON :PagerDutyEscalationPolicy(name);
CREATE INDEX ON :PagerDutyEscalationPolicy(lastupdated);
CREATE INDEX ON :PagerDutyEscalationPolicyRule(id);
CREATE INDEX ON :PagerDutyEscalationPolicyRule(lastupdated);
CREATE INDEX ON :PagerDutyIntegration(id);
CREATE INDEX ON :PagerDutyIntegration(lastupdated);
CREATE INDEX ON :PagerDutySchedule(id);
CREATE INDEX ON :PagerDutySchedule(name);
CREATE INDEX ON :PagerDutySchedule(lastupdated);
CREATE INDEX ON :PagerDutyScheduleLayer(id);
CREATE INDEX ON :PagerDutyScheduleLayer(lastupdated);
CREATE INDEX ON :PagerDutyService(id);
CREATE INDEX ON :PagerDutyService(name);
CREATE INDEX ON :PagerDutyService(lastupdated);
CREATE INDEX ON :PagerDutyTeam(id);
CREATE INDEX ON :PagerDutyTeam(name);
CREATE INDEX ON :PagerDutyTeam(lastupdated);
CREATE INDEX ON :PagerDutyUser(id);
CREATE INDEX ON :PagerDutyUser(name);
CREATE INDEX ON :PagerDutyUser(lastupdated);
CREATE INDEX ON :PagerDutyVendor(id);
CREATE INDEX ON :PagerDutyVendor(name);
CREATE INDEX ON :PagerDutyVendor(lastupdated);
CREATE INDEX ON :ProgrammingLanguage(id);
CREATE INDEX ON :ProgrammingLanguage(lastupdated);
CREATE INDEX ON :PublicIpAddress(ip);
CREATE INDEX ON :PublicIpAddress(lastupdated);
CREATE INDEX ON :PythonLibrary(id);
CREATE INDEX ON :PythonLibrary(lastupdated);
CREATE INDEX ON :RedshiftCluster(id);
CREATE INDEX ON :RedshiftCluster(arn);
CREATE INDEX ON :RedshiftCluster(lastupdated);
CREATE INDEX ON :RDSCluster(db_cluster_identifier);
CREATE INDEX ON :RDSCluster(id);
CREATE INDEX ON :RDSCluster(arn);
CREATE INDEX ON :RDSCluster(lastupdated);
CREATE INDEX ON :RDSInstance(db_instance_identifier);
CREATE INDEX ON :RDSInstance(id);
CREATE INDEX ON :RDSInstance(arn);
CREATE INDEX ON :RDSInstance(lastupdated);
CREATE INDEX ON :ReplyUri(id);
CREATE INDEX ON :ReplyUri(lastupdated);
CREATE INDEX ON :Risk(id);
CREATE INDEX ON :Risk(lastupdated);
CREATE INDEX ON :S3Acl(id);
CREATE INDEX ON :S3Acl(lastupdated);
CREATE INDEX ON :S3Bucket(id);
CREATE INDEX ON :S3Bucket(name);
CREATE INDEX ON :S3Bucket(arn);
CREATE INDEX ON :S3Bucket(lastupdated);
CREATE INDEX ON :SecretsManagerSecret(id);
CREATE INDEX ON :SecretsManagerSecret(lastupdated);
CREATE INDEX ON :SecurityHub(id);
CREATE INDEX ON :SecurityHub(lastupdated);
CREATE INDEX ON :SpotlightVulnerability(id);
CREATE INDEX ON :SpotlightVulnerability(cve_id);
CREATE INDEX ON :SpotlightVulnerability(host_info_local_ip);
CREATE INDEX ON :SpotlightVulnerability(lastupdated);
CREATE INDEX ON :SQSQueue(id);
CREATE INDEX ON :SQSQueue(lastupdated);
CREATE INDEX ON :SSMInstanceInformation(id);
CREATE INDEX ON :SSMInstanceInformation(lastupdated);
CREATE INDEX ON :SSMInstancePatch(id);
CREATE INDEX ON :SSMInstancePatch(lastupdated);
CREATE INDEX ON :User(arn);
CREATE INDEX ON :User(lastupdated);
CREATE INDEX ON :AzureTenant(id);
CREATE INDEX ON :AzureTenant(lastupdated);
CREATE INDEX ON :AzurePrincipal(email);
CREATE INDEX ON :AzurePrincipal(lastupdated);
CREATE INDEX ON :AzureSubscription(id);
CREATE INDEX ON :AzureSubscription(lastupdated);
CREATE INDEX ON :AzureCosmosDBAccount(id);
CREATE INDEX ON :AzureCosmosDBAccount(lastupdated);
CREATE INDEX ON :AzureCosmosDBLocation(id);
CREATE INDEX ON :AzureCosmosDBLocation(lastupdated);
CREATE INDEX ON :AzureCosmosDBCorsPolicy(id);
CREATE INDEX ON :AzureCosmosDBCorsPolicy(lastupdated);
CREATE INDEX ON :AzureCosmosDBAccountFailoverPolicy(id);
CREATE INDEX ON :AzureCosmosDBAccountFailoverPolicy(lastupdated);
CREATE INDEX ON :AzureCDBPrivateEndpointConnection(id);
CREATE INDEX ON :AzureCDBPrivateEndpointConnection(lastupdated);
CREATE INDEX ON :AzureCosmosDBVirtualNetworkRule(id);
CREATE INDEX ON :AzureCosmosDBVirtualNetworkRule(lastupdated);
CREATE INDEX ON :AzureCosmosDBSqlDatabase(id);
CREATE INDEX ON :AzureCosmosDBSqlDatabase(lastupdated);
CREATE INDEX ON :AzureCosmosDBCassandraKeyspace(id);
CREATE INDEX ON :AzureCosmosDBCassandraKeyspace(lastupdated);
CREATE INDEX ON :AzureCosmosDBMongoDBDatabase(id);
CREATE INDEX ON :AzureCosmosDBMongoDBDatabase(lastupdated);
CREATE INDEX ON :AzureCosmosDBTableResource(id);
CREATE INDEX ON :AzureCosmosDBTableResource(lastupdated);
CREATE INDEX ON :AzureCosmosDBSqlContainer(id);
CREATE INDEX ON :AzureCosmosDBSqlContainer(lastupdated);
CREATE INDEX ON :AzureCosmosDBCassandraTable(id);
CREATE INDEX ON :AzureCosmosDBCassandraTable(lastupdated);
CREATE INDEX ON :AzureCosmosDBMongoDBCollection(id);
CREATE INDEX ON :AzureCosmosDBMongoDBCollection(lastupdated);
CREATE INDEX ON :AzureStorageAccount(id);
CREATE INDEX ON :AzureStorageAccount(lastupdated);
CREATE INDEX ON :AzureStorageQueueService(id);
CREATE INDEX ON :AzureStorageQueueService(lastupdated);
CREATE INDEX ON :AzureStorageTableService(id);
CREATE INDEX ON :AzureStorageTableService(lastupdated);
CREATE INDEX ON :AzureStorageFileService(id);
CREATE INDEX ON :AzureStorageFileService(lastupdated);
CREATE INDEX ON :AzureStorageBlobService(id);
CREATE INDEX ON :AzureStorageBlobService(lastupdated);
CREATE INDEX ON :AzureStorageQueue(id);
CREATE INDEX ON :AzureStorageQueue(lastupdated);
CREATE INDEX ON :AzureStorageTable(id);
CREATE INDEX ON :AzureStorageTable(lastupdated);
CREATE INDEX ON :AzureStorageFileShare(id);
CREATE INDEX ON :AzureStorageFileShare(lastupdated);
CREATE INDEX ON :AzureStorageBlobContainer(id);
CREATE INDEX ON :AzureStorageBlobContainer(lastupdated);
CREATE INDEX ON :AzureSQLServer(id);
CREATE INDEX ON :AzureSQLServer(lastupdated);
CREATE INDEX ON :AzureServerDNSAlias(id);
CREATE INDEX ON :AzureServerDNSAlias(lastupdated);
CREATE INDEX ON :AzureServerADAdministrator(id);
CREATE INDEX ON :AzureServerADAdministrator(lastupdated);
CREATE INDEX ON :AzureRecoverableDatabase(id);
CREATE INDEX ON :AzureRecoverableDatabase(lastupdated);
CREATE INDEX ON :AzureRestorableDroppedDatabase(id);
CREATE INDEX ON :AzureRestorableDroppedDatabase(lastupdated);
CREATE INDEX ON :AzureFailoverGroup(id);
CREATE INDEX ON :AzureFailoverGroup(lastupdated);
CREATE INDEX ON :AzureElasticPool(id);
CREATE INDEX ON :AzureElasticPool(lastupdated);
CREATE INDEX ON :AzureSQLDatabase(id);
CREATE INDEX ON :AzureSQLDatabase(lastupdated);
CREATE INDEX ON :AzureReplicationLink(id);
CREATE INDEX ON :AzureReplicationLink(lastupdated);
CREATE INDEX ON :AzureDatabaseThreatDetectionPolicy(id);
CREATE INDEX ON :AzureDatabaseThreatDetectionPolicy(lastupdated);
CREATE INDEX ON :AzureRestorePoint(id);
CREATE INDEX ON :AzureRestorePoint(lastupdated);
CREATE INDEX ON :AzureTransparentDataEncryption(id);
CREATE INDEX ON :AzureTransparentDataEncryption(lastupdated);
CREATE INDEX ON :AzureVirtualMachine(id);
CREATE INDEX ON :AzureVirtualMachine(lastupdated);
CREATE INDEX ON :AzureDataDisk(id);
CREATE INDEX ON :AzureDataDisk(lastupdated);
CREATE INDEX ON :AzureDisk(id);
CREATE INDEX ON :AzureDisk(lastupdated);
CREATE INDEX ON :AzureSnapshot(id);
CREATE INDEX ON :AzureSnapshot(lastupdated);
CREATE INDEX ON :KubernetesCluster(id);
CREATE INDEX ON :KubernetesCluster(name);
CREATE INDEX ON :KubernetesCluster(lastupdated);
CREATE INDEX ON :KubernetesNamespace(id);
CREATE INDEX ON :KubernetesNamespace(name);
CREATE INDEX ON :KubernetesNamespace(lastupdated);
CREATE INDEX ON :KubernetesPod(id);
CREATE INDEX ON :KubernetesPod(name);
CREATE INDEX ON :KubernetesPod(lastupdated);
CREATE INDEX ON :KubernetesContainer(id);
CREATE INDEX ON :KubernetesContainer(name);
CREATE INDEX ON :KubernetesContainer(image);
CREATE INDEX ON :KubernetesContainer(lastupdated);
CREATE INDEX ON :KubernetesService(id);
CREATE INDEX ON :KubernetesService(name);
CREATE INDEX ON :KubernetesService(lastupdated);
