CREATE INDEX ON :APIGatewayClientCertificate(id);
CREATE INDEX ON :APIGatewayRestAPI(id);
CREATE INDEX ON :APIGatewayResource(id);
CREATE INDEX ON :APIGatewayStage(id);
CREATE INDEX ON :AWSAccount(id);
CREATE INDEX ON :AWSCidrBlock(id);
CREATE INDEX ON :AWSDNSRecord(id);
CREATE INDEX ON :AWSDNSZone(name);
CREATE INDEX ON :AWSDNSZone(zoneid);
CREATE INDEX ON :AWSGroup(arn);
CREATE INDEX ON :AWSIpv4CidrBlock(id);
CREATE INDEX ON :AWSIpv6CidrBlock(id);
CREATE INDEX ON :AWSLambda(id);
CREATE INDEX ON :AWSPolicy(id);
CREATE INDEX ON :AWSPolicy(name);
CREATE INDEX ON :AWSPolicyStatement(id);
CREATE INDEX ON :AWSPrincipal(arn);
CREATE INDEX ON :AWSRole(arn);
CREATE INDEX ON :AWSTag(id);
CREATE INDEX ON :AWSTransitGateway(arn);
CREATE INDEX ON :AWSTransitGateway(id);
CREATE INDEX ON :AWSTransitGatewayAttachment(id);
CREATE INDEX ON :AWSUser(arn);
CREATE INDEX ON :AWSUser(name);
CREATE INDEX ON :AWSVpc(id);
CREATE INDEX ON :AccountAccessKey(accesskeyid);
CREATE INDEX ON :AutoScalingGroup(arn);
CREATE INDEX ON :ChromeExtension(id);
CREATE INDEX ON :Dependency(id);
CREATE INDEX ON :DBGroup(name);
CREATE INDEX ON :DNSRecord(id);
CREATE INDEX ON :DNSZone(name);
CREATE INDEX ON :DynamoDBGlobalSecondaryIndex(id);
CREATE INDEX ON :DynamoDBTable(arn);
CREATE INDEX ON :DynamoDBTable(id);
CREATE INDEX ON :EC2Instance(id);
CREATE INDEX ON :EC2Instance(instanceid);
CREATE INDEX ON :EC2Instance(publicdnsname);
CREATE INDEX ON :EC2KeyPair(id);
CREATE INDEX ON :EC2PrivateIp(id);
CREATE INDEX ON :EC2Reservation(reservationid);
CREATE INDEX ON :EC2SecurityGroup(groupid);
CREATE INDEX ON :EC2SecurityGroup(id);
CREATE INDEX ON :EC2Subnet(id);
CREATE INDEX ON :EC2Subnet(subnetid);
CREATE INDEX ON :ECRImage(id);
CREATE INDEX ON :ECRRepository(id);
CREATE INDEX ON :ECRRepository(name);
CREATE INDEX ON :ECRRepository(uri);
CREATE INDEX ON :ECRRepositoryImage(id);
CREATE INDEX ON :ECRRepositoryImage(tag);
CREATE INDEX ON :ECRScanFinding(id);
CREATE INDEX ON :EKSCluster(id);
CREATE INDEX ON :ELBListener(id);
CREATE INDEX ON :ELBV2Listener(id);
CREATE INDEX ON :Endpoint(id);
CREATE INDEX ON :ESDomain(arn);
CREATE INDEX ON :ESDomain(id);
CREATE INDEX ON :ESDomain(name);
CREATE INDEX ON :GCPDNSZone(id);
CREATE INDEX ON :GCPRecordSet(id);
CREATE INDEX ON :GCPFolder(id);
CREATE INDEX ON :GCPForwardingRule(id);
CREATE INDEX ON :GCPInstance(id);
CREATE INDEX ON :GCPNetworkInterface(id);
CREATE INDEX ON :GCPNetworkTag(id);
CREATE INDEX ON :GCPNicAccessConfig(id);
CREATE INDEX ON :GCPNicAccessConfig(id);
CREATE INDEX ON :GCPOrganization(id);
CREATE INDEX ON :GCPProject(id);
CREATE INDEX ON :GCPProject(projectnumber);
CREATE INDEX ON :GCPBucket(id);
CREATE INDEX ON :GCPBucketLabel(key);
CREATE INDEX ON :GCPSubnet(id);
CREATE INDEX ON :GCPVpc(id);
CREATE INDEX ON :GitHubOrganization(id);
CREATE INDEX ON :GitHubRepository(id);
CREATE INDEX ON :GitHubUser(id);
CREATE INDEX ON :GKECluster(id);
CREATE INDEX ON :GSuiteGroup(email);
CREATE INDEX ON :GSuiteGroup(id);
CREATE INDEX ON :GSuiteUser(email);
CREATE INDEX ON :GSuiteUser(id);
CREATE INDEX ON :Ip(id);
CREATE INDEX ON :Ip(ip);
CREATE INDEX ON :IpPermissionInbound(ruleid);
CREATE INDEX ON :IpPermissionsEgress(ruleid);
CREATE INDEX ON :IpRange(id);
CREATE INDEX ON :IpRule(ruleid);
CREATE INDEX ON :JamfComputerGroup(id);
CREATE INDEX ON :KMSKey(id);
CREATE INDEX ON :KMSAlias(id);
CREATE INDEX ON :KMSGrant(id);
CREATE INDEX ON :LoadBalancer(dnsname);
CREATE INDEX ON :LoadBalancer(id);
CREATE INDEX ON :LoadBalancerV2(dnsname);
CREATE INDEX ON :LoadBalancerV2(id);
CREATE INDEX ON :NetworkInterface(id);
CREATE INDEX ON :NameServer(id);
CREATE INDEX ON :OktaOrganization(id);
CREATE INDEX ON :OktaUser(id);
CREATE INDEX ON :OktaUser(email);
CREATE INDEX ON :OktaGroup(id);
CREATE INDEX ON :OktaGroup(name);
CREATE INDEX ON :OktaApplication(id);
CREATE INDEX ON :OktaUserFactor(id);
CREATE INDEX ON :OktaTrustedOrigin(id);
CREATE INDEX ON :OktaAdministrationRole(id);
CREATE INDEX ON :Package(id);
CREATE INDEX ON :Package(name);
CREATE INDEX ON :ProgrammingLanguage(id);
CREATE INDEX ON :PublicIpAddress(ip);
CREATE INDEX ON :PythonLibrary(id);
CREATE INDEX ON :RedshiftCluster(id);
CREATE INDEX ON :RedshiftCluster(arn);
CREATE INDEX ON :RDSInstance(db_instance_identifier);
CREATE INDEX ON :RDSInstance(id);
CREATE INDEX ON :RDSInstance(arn);
CREATE INDEX ON :ReplyUri(id);
CREATE INDEX ON :Risk(id);
CREATE INDEX ON :S3Acl(id);
CREATE INDEX ON :S3Bucket(id);
CREATE INDEX ON :S3Bucket(name);
CREATE INDEX ON :S3Bucket(arn);
CREATE INDEX ON :User(arn);
CREATE INDEX ON :AzureTenant(id);
CREATE INDEX ON :AzurePrincipal(email);
CREATE INDEX ON :AzureSubscription(id);
CREATE INDEX ON :VirtualMachine(id);
CREATE INDEX ON :AzureDataDisk(id);
CREATE INDEX ON :AzureDisk(id);
CREATE INDEX ON :AzureSnapshot(id);
