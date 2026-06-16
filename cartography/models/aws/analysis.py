from cartography.graph.analysis import AnalysisJob
from cartography.graph.analysis import AnalysisScope
from cartography.graph.analysis import AnalysisStatement
from cartography.graph.analysis import PropertyEffect
from cartography.graph.analysis import RelationshipEffect

AWS_SCOPE = AnalysisScope("AWSAccount", "AWS_ID")

AWS_EC2_IAM_INSTANCE_PROFILE = AnalysisJob(
    name="EC2 Instances assume IAM roles",
    short_name="aws_ec2_iaminstanceprofile",
    scope=AWS_SCOPE,
    effect=RelationshipEffect("EC2Instance", "STS_ASSUMEROLE_ALLOW", "AWSRole"),
    statements=(
        AnalysisStatement(
            "MATCH (aa:AWSAccount{id: $AWS_ID})-[:RESOURCE]->(i:EC2Instance)-[:INSTANCE_PROFILE]->(p:AWSInstanceProfile)-[:ASSOCIATED_WITH]->(r:AWSRole)\n"
            "MERGE (i)-[s:STS_ASSUMEROLE_ALLOW]->(r)\n"
            "ON CREATE SET s.firstseen = timestamp()\n"
            "SET s.lastupdated = $UPDATE_TAG",
        ),
    ),
)

AWS_LAMBDA_ECR = AnalysisJob(
    name="Lambda functions with ECR images",
    short_name="aws_lambda_ecr",
    effect=RelationshipEffect("AWSLambda", "HAS", "ECRImage"),
    statements=(
        AnalysisStatement(
            "MATCH (l:AWSLambda) \n"
            " WITH COLLECT(l) as lmbda_list \n"
            " UNWIND lmbda_list as lmbda \n"
            " MATCH (e:ECRImage) \n"
            " WHERE e.digest = 'sha256:' + lmbda.codesha256 \n"
            " MERGE (lmbda)-[r:HAS]->(e) \n"
            " SET r.lastupdated = $UPDATE_TAG",
        ),
    ),
)

AWS_LB_CONTAINER_EXPOSURE = AnalysisJob(
    name="AWS LoadBalancer to ECS Container direct relationship",
    short_name="aws_lb_container_exposure",
    scope=AWS_SCOPE,
    effect=RelationshipEffect(
        "AWSLoadBalancerV2",
        "EXPOSE",
        "ECSContainer",
        properties=("exposure_type",),
    ),
    statements=(
        AnalysisStatement(
            "MATCH (aa:AWSAccount{id: $AWS_ID})-[:RESOURCE]->(lb:AWSLoadBalancerV2 {scheme: 'internet-facing'})-[:EXPOSE]->(ip:EC2PrivateIp)<-[:PRIVATE_IP_ADDRESS]-(ni:NetworkInterface)<-[:NETWORK_INTERFACE]-(task:ECSTask)-[:HAS_CONTAINER]->(c:ECSContainer) "
            "WHERE ip.public_ip IS NULL MERGE (lb)-[r:EXPOSE]->(c) SET r.lastupdated = $UPDATE_TAG, r.exposure_type = 'via_lb_only'",
        ),
    ),
)

AWS_LB_NACL_DIRECT = AnalysisJob(
    name="AWS LoadBalancer to NACL direct relationship",
    short_name="aws_lb_nacl_direct",
    scope=AWS_SCOPE,
    effect=RelationshipEffect(
        "EC2NetworkAcl",
        "PROTECTS",
        "AWSLoadBalancerV2",
        scoped_to="target",
    ),
    statements=(
        AnalysisStatement(
            "MATCH (aa:AWSAccount{id: $AWS_ID})-[:RESOURCE]->(lb:AWSLoadBalancerV2)-[:SUBNET]->(subnet:EC2Subnet)<-[:PART_OF_SUBNET]-(nacl:EC2NetworkAcl) "
            "MERGE (nacl)-[r:PROTECTS]->(lb) SET r.lastupdated = $UPDATE_TAG",
        ),
    ),
)

AWS_EC2_ASSET_EXPOSURE_LOAD_BALANCER_V2 = AnalysisJob(
    name="AWS LoadBalancerV2 internet exposure",
    short_name="aws_ec2_asset_exposure_load_balancer_v2",
    effect=PropertyEffect(
        "AWSLoadBalancerV2",
        ("exposed_internet", "exposed_internet_type"),
    ),
    cleanup_iterationsize=1000,
    statements=(
        AnalysisStatement(
            "MATCH (elbv2:AWSLoadBalancerV2{scheme: 'internet-facing', type: 'network'})-->(:ELBV2Listener)\n"
            "WITH DISTINCT elbv2\n"
            "SET elbv2.exposed_internet = true",
        ),
        AnalysisStatement(
            "MATCH (cidr:AWSIpRange{range:'0.0.0.0/0'})-->(perm:AWSIpPermissionInbound)-->(sg:EC2SecurityGroup)<-[:MEMBER_OF_EC2_SECURITY_GROUP]-(elbv2:AWSLoadBalancerV2{scheme: 'internet-facing'})-->(listener:ELBV2Listener)\n"
            "WHERE perm.protocol = '-1' OR (listener.port>=perm.fromport AND listener.port<=perm.toport)\n"
            "SET elbv2.exposed_internet = true",
        ),
    ),
)

AWS_EC2_ASSET_EXPOSURE_LOAD_BALANCER = AnalysisJob(
    name="AWS LoadBalancer internet exposure",
    short_name="aws_ec2_asset_exposure_load_balancer",
    effect=PropertyEffect(
        "AWSLoadBalancer",
        ("exposed_internet", "exposed_internet_type"),
    ),
    cleanup_iterationsize=1000,
    statements=(
        AnalysisStatement(
            "MATCH (cidr:AWSIpRange{range:'0.0.0.0/0'})-->(perm:AWSIpPermissionInbound)-->(sg:EC2SecurityGroup)<-[:SOURCE_SECURITY_GROUP]-(elb:AWSLoadBalancer{scheme: 'internet-facing'})-->(listener:ELBListener)\n"
            "WHERE perm.protocol = '-1' OR (listener.port>=perm.fromport AND listener.port<=perm.toport)\n"
            "SET elb.exposed_internet = true",
        ),
    ),
)

AWS_EC2_ASSET_EXPOSURE_INSTANCE = AnalysisJob(
    name="AWS EC2 instance internet exposure",
    short_name="aws_ec2_asset_exposure_instance",
    effect=PropertyEffect(
        "EC2Instance",
        ("exposed_internet", "exposed_internet_type"),
    ),
    cleanup_iterationsize=1000,
    statements=(
        AnalysisStatement(
            "MATCH (:AWSIpRange{id: '0.0.0.0/0'})-[:MEMBER_OF_IP_RULE]->(:AWSIpPermissionInbound)-[:MEMBER_OF_EC2_SECURITY_GROUP]->(group:EC2SecurityGroup)<-[:MEMBER_OF_EC2_SECURITY_GROUP|NETWORK_INTERFACE*..2]-(instance:EC2Instance) "
            "WITH instance WHERE (instance.publicipaddress IS NOT NULL) AND (instance.exposed_internet_type IS NULL OR NOT 'direct' IN instance.exposed_internet_type) "
            "SET instance.exposed_internet = true, instance.exposed_internet_type = CASE WHEN instance.exposed_internet_type IS NULL THEN ['direct'] WHEN NOT 'direct' IN instance.exposed_internet_type THEN instance.exposed_internet_type + ['direct'] ELSE instance.exposed_internet_type END;",
        ),
        AnalysisStatement(
            "MATCH (elb:AWSLoadBalancer{exposed_internet: true})-[:EXPOSE]->(e:EC2Instance)\n"
            "WITH e\n"
            "WHERE (e.exposed_internet_type IS NULL) OR (NOT 'elb' IN e.exposed_internet_type)\n"
            "SET e.exposed_internet = true, e.exposed_internet_type = coalesce(e.exposed_internet_type, []) + 'elb'",
        ),
        AnalysisStatement(
            "MATCH (elbv2:AWSLoadBalancerV2{exposed_internet: true})-[:EXPOSE]->(e:EC2Instance)\n"
            "WITH e\n"
            "WHERE (e.exposed_internet_type IS NULL) OR (NOT 'elbv2' IN e.exposed_internet_type)\n"
            "SET e.exposed_internet = true, e.exposed_internet_type = coalesce(e.exposed_internet_type, []) + 'elbv2'",
        ),
    ),
)

AWS_EC2_ASSET_EXPOSURE_AUTO_SCALING_GROUP = AnalysisJob(
    name="AWS AutoScalingGroup internet exposure",
    short_name="aws_ec2_asset_exposure_auto_scaling_group",
    effect=PropertyEffect(
        "AutoScalingGroup",
        ("exposed_internet", "exposed_internet_type"),
    ),
    cleanup_iterationsize=1000,
    statements=(
        AnalysisStatement(
            "MATCH (instance:EC2Instance{exposed_internet: true})-[:MEMBER_AUTO_SCALE_GROUP]->(asg:AutoScalingGroup)\n"
            "WITH distinct instance.exposed_internet_type as types, asg\n"
            "UNWIND types as type\n"
            "WITH type, asg\n"
            "WHERE asg.exposed_internet_type IS NULL OR (NOT type IN asg.exposed_internet_type)\n"
            "SET asg.exposed_internet = true, asg.exposed_internet_type = coalesce(asg.exposed_internet_type, []) + type;",
        ),
    ),
)

AWS_EC2_ASSET_EXPOSURE_JOBS = (
    AWS_EC2_ASSET_EXPOSURE_LOAD_BALANCER_V2,
    AWS_EC2_ASSET_EXPOSURE_LOAD_BALANCER,
    AWS_EC2_ASSET_EXPOSURE_INSTANCE,
    AWS_EC2_ASSET_EXPOSURE_AUTO_SCALING_GROUP,
)

AWS_EC2_KEYPAIR_PROPERTIES = AnalysisJob(
    name="Analysis jobs for EC2 Key Pairs properties",
    short_name="aws_ec2_keypair_analysis_properties",
    effect=PropertyEffect("EC2KeyPair", ("user_uploaded", "duplicate_keyfingerprint")),
    statements=(
        AnalysisStatement(
            "MATCH (k:EC2KeyPair) WHERE size(k.keyfingerprint) = 47 SET k.user_uploaded = True",
        ),
        AnalysisStatement(
            "MATCH (k1:EC2KeyPair) MATCH (k2:EC2KeyPair) WHERE id(k1) < id(k2) AND k1.keyfingerprint = k2.keyfingerprint "
            "SET k1.duplicate_keyfingerprint = True, k2.duplicate_keyfingerprint = True RETURN COUNT(*) as TotalCompleted",
        ),
    ),
)

AWS_EC2_KEYPAIR_MATCHING_FINGERPRINT = AnalysisJob(
    name="Analysis jobs for EC2 Key Pairs matching fingerprints",
    short_name="aws_ec2_keypair_analysis_matching_fingerprint",
    effect=RelationshipEffect("EC2KeyPair", "MATCHING_FINGERPRINT", "EC2KeyPair"),
    statements=(
        AnalysisStatement(
            "MATCH (k1:EC2KeyPair) MATCH (k2:EC2KeyPair) WHERE id(k1) < id(k2) AND k1.keyfingerprint = k2.keyfingerprint "
            "MERGE (k1)-[r:MATCHING_FINGERPRINT]-(k2) ON CREATE SET r.firstseen = $UPDATE_TAG SET r.lastupdated = $UPDATE_TAG RETURN COUNT(*) as TotalCompleted",
        ),
    ),
)

AWS_EC2_KEYPAIR_ANALYSIS_JOBS = (
    AWS_EC2_KEYPAIR_PROPERTIES,
    AWS_EC2_KEYPAIR_MATCHING_FINGERPRINT,
)

AWS_EKS_ASSET_EXPOSURE = AnalysisJob(
    name="AWS EKS internet exposure",
    short_name="aws_eks_asset_exposure",
    effect=PropertyEffect("EKSCluster", ("exposed_internet",)),
    statements=(
        AnalysisStatement(
            "MATCH (cluster:EKSCluster) WHERE cluster.endpoint_public_access = true SET cluster.exposed_internet = true",
        ),
    ),
)

AWS_FOREIGN_ACCOUNTS = AnalysisJob(
    name="AWS - Foreign account analysis",
    short_name="aws_foreign_accounts",
    effect=PropertyEffect("AWSAccount", ("foreign",)),
    statements=(
        AnalysisStatement(
            "MATCH (foreign:AWSAccount) where foreign.inscope IS NULL SET foreign.foreign = true",
        ),
    ),
)

AWS_ECS_ASSET_EXPOSURE = AnalysisJob(
    name="AWS ECS internet exposure (deprecated: use ontology LoadBalancer-[:EXPOSE]->Container)",
    short_name="aws_ecs_asset_exposure",
    effect=PropertyEffect(
        "ECSContainer",
        ("exposed_internet", "exposed_internet_type"),
    ),
    cleanup_iterationsize=1000,
    statements=(
        AnalysisStatement(
            "MATCH (lb:AWSLoadBalancerV2 {exposed_internet: true})-[:EXPOSE]->(ip:EC2PrivateIp)<-[:PRIVATE_IP_ADDRESS]-(ni:NetworkInterface)<-[:NETWORK_INTERFACE]-(task:ECSTask)-[:HAS_CONTAINER]->(container:ECSContainer) "
            "WITH DISTINCT container WHERE (container.exposed_internet_type IS NULL) OR (NOT 'elbv2' IN container.exposed_internet_type) "
            "SET container.exposed_internet = true, container.exposed_internet_type = coalesce(container.exposed_internet_type, []) + 'elbv2'",
        ),
    ),
)
