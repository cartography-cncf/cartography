from cartography.graph.analysis import AddRelationship
from cartography.graph.analysis import AddToSet
from cartography.graph.analysis import AnalysisJob
from cartography.graph.analysis import AnalysisStatement
from cartography.graph.analysis import Param
from cartography.graph.analysis import ScopeById
from cartography.graph.analysis import SetProperty
from cartography.graph.analysis import Var

AWS_EC2_IAM_INSTANCE_PROFILE = AnalysisJob(
    name="EC2 Instances assume IAM roles",
    short_name="aws_ec2_iaminstanceprofile",
    scope=ScopeById("AWSAccount", "AWS_ID", scope_on="i"),
    statements=(
        AnalysisStatement(
            match="MATCH (i:AWSEC2Instance)-[:INSTANCE_PROFILE]->(p:AWSInstanceProfile)-[:ASSOCIATED_WITH]->(r:AWSRole)",
            effects=(
                AddRelationship(
                    "i",
                    "STS_ASSUMEROLE_ALLOW",
                    "r",
                    rel_alias="s",
                    source_label="AWSEC2Instance",
                    target_label="AWSRole",
                ),
            ),
        ),
    ),
)
AWS_LAMBDA_ECR = AnalysisJob(
    name="Lambda functions with ECR images",
    short_name="aws_lambda_ecr",
    statements=(
        AnalysisStatement(
            match="""
            MATCH (lmbda:AWSLambda)
            MATCH (e:AWSECRImage)
            WHERE e.digest = 'sha256:' + lmbda.codesha256
            """,
            effects=(
                AddRelationship(
                    "lmbda",
                    "HAS",
                    "e",
                    source_label="AWSLambda",
                    target_label="AWSECRImage",
                ),
            ),
        ),
    ),
)
AWS_LB_CONTAINER_EXPOSURE = AnalysisJob(
    name="AWS LoadBalancer to ECS Container direct relationship",
    short_name="aws_lb_container_exposure",
    scope=ScopeById("AWSAccount", "AWS_ID", scope_on="lb"),
    statements=(
        AnalysisStatement(
            match="MATCH (lb:AWSLoadBalancerV2 {scheme: 'internet-facing'})-[:EXPOSE]->(ip:AWSEC2PrivateIp)<-[:PRIVATE_IP_ADDRESS]-(ni:AWSNetworkInterface)<-[:NETWORK_INTERFACE]-(task:AWSECSTask)-[:HAS_CONTAINER]->(c:AWSECSContainer) WHERE ip.public_ip IS NULL",
            effects=(
                AddRelationship(
                    "lb",
                    "EXPOSE",
                    "c",
                    properties={"exposure_type": "via_lb_only"},
                    source_label="AWSLoadBalancerV2",
                    target_label="AWSECSContainer",
                ),
            ),
        ),
    ),
)
AWS_LB_NACL_DIRECT = AnalysisJob(
    name="AWS LoadBalancer to NACL direct relationship",
    short_name="aws_lb_nacl_direct",
    scope=ScopeById("AWSAccount", "AWS_ID", scope_on="lb"),
    statements=(
        AnalysisStatement(
            match="MATCH (lb:AWSLoadBalancerV2)-[:SUBNET]->(subnet:AWSEC2Subnet)<-[:PART_OF_SUBNET]-(nacl:AWSEC2NetworkAcl)",
            effects=(
                AddRelationship(
                    "nacl",
                    "PROTECTS",
                    "lb",
                    source_label="AWSEC2NetworkAcl",
                    target_label="AWSLoadBalancerV2",
                    scoped_to="target",
                ),
            ),
        ),
    ),
)
AWS_EC2_ASSET_EXPOSURE_LOAD_BALANCER_V2 = AnalysisJob(
    name="AWS LoadBalancerV2 internet exposure",
    short_name="aws_ec2_asset_exposure_load_balancer_v2",
    cleanup_iterationsize=1000,
    statements=(
        AnalysisStatement(
            match="""
            MATCH (elbv2:AWSLoadBalancerV2{scheme: 'internet-facing', type: 'network'})-[:ELBV2_LISTENER]->(:AWSELBV2Listener)
            WITH DISTINCT elbv2
            """,
            effects=(
                SetProperty(
                    "elbv2", "exposed_internet", True, label="AWSLoadBalancerV2"
                ),
                SetProperty(
                    "elbv2", "exposed_internet_type", None, label="AWSLoadBalancerV2"
                ),
            ),
        ),
        AnalysisStatement(
            match="""
            MATCH (cidr:AWSIpRange{range:'0.0.0.0/0'})-[:MEMBER_OF_IP_RULE]->(perm:AWSIpPermissionInbound)-[:MEMBER_OF_EC2_SECURITY_GROUP]->(sg:AWSEC2SecurityGroup)<-[:MEMBER_OF_EC2_SECURITY_GROUP]-(elbv2:AWSLoadBalancerV2{scheme: 'internet-facing'})-[:ELBV2_LISTENER]->(listener:AWSELBV2Listener)
            WHERE perm.protocol = '-1' OR (listener.port>=perm.fromport AND listener.port<=perm.toport)
            """,
            effects=(
                SetProperty(
                    "elbv2", "exposed_internet", True, label="AWSLoadBalancerV2"
                ),
                SetProperty(
                    "elbv2", "exposed_internet_type", None, label="AWSLoadBalancerV2"
                ),
            ),
        ),
    ),
)
AWS_EC2_ASSET_EXPOSURE_LOAD_BALANCER = AnalysisJob(
    name="AWS LoadBalancer internet exposure",
    short_name="aws_ec2_asset_exposure_load_balancer",
    cleanup_iterationsize=1000,
    statements=(
        AnalysisStatement(
            match="""
            MATCH (cidr:AWSIpRange{range:'0.0.0.0/0'})-[:MEMBER_OF_IP_RULE]->(perm:AWSIpPermissionInbound)-[:MEMBER_OF_EC2_SECURITY_GROUP]->(sg:AWSEC2SecurityGroup)<-[:SOURCE_SECURITY_GROUP]-(elb:AWSLoadBalancer{scheme: 'internet-facing'})-[:ELB_LISTENER]->(listener:AWSELBListener)
            WHERE perm.protocol = '-1' OR (listener.port>=perm.fromport AND listener.port<=perm.toport)
            """,
            effects=(
                SetProperty("elb", "exposed_internet", True, label="AWSLoadBalancer"),
                SetProperty(
                    "elb", "exposed_internet_type", None, label="AWSLoadBalancer"
                ),
            ),
        ),
    ),
)
AWS_EC2_ASSET_EXPOSURE_INSTANCE = AnalysisJob(
    name="AWS EC2 instance internet exposure",
    short_name="aws_ec2_asset_exposure_instance",
    cleanup_iterationsize=1000,
    statements=(
        AnalysisStatement(
            match="""
            MATCH (:AWSIpRange{id: '0.0.0.0/0'})-[:MEMBER_OF_IP_RULE]->(:AWSIpPermissionInbound)-[:MEMBER_OF_EC2_SECURITY_GROUP]->(:AWSEC2SecurityGroup)<-[:MEMBER_OF_EC2_SECURITY_GROUP|NETWORK_INTERFACE*..2]-(instance:AWSEC2Instance)
            WHERE instance.publicipaddress IS NOT NULL
            """,
            effects=(
                SetProperty(
                    "instance", "exposed_internet", True, label="AWSEC2Instance"
                ),
                AddToSet(
                    "instance",
                    "exposed_internet_type",
                    "direct",
                    label="AWSEC2Instance",
                ),
            ),
        ),
        AnalysisStatement(
            match="MATCH (:AWSLoadBalancer{exposed_internet: true})-[:EXPOSE]->(e:AWSEC2Instance)",
            effects=(
                SetProperty("e", "exposed_internet", True, label="AWSEC2Instance"),
                AddToSet("e", "exposed_internet_type", "elb", label="AWSEC2Instance"),
            ),
        ),
        AnalysisStatement(
            match="MATCH (:AWSLoadBalancerV2{exposed_internet: true})-[:EXPOSE]->(e:AWSEC2Instance)",
            effects=(
                SetProperty("e", "exposed_internet", True, label="AWSEC2Instance"),
                AddToSet("e", "exposed_internet_type", "elbv2", label="AWSEC2Instance"),
            ),
        ),
    ),
)
AWS_EC2_ASSET_EXPOSURE_AUTO_SCALING_GROUP = AnalysisJob(
    name="AWS Auto Scaling group internet exposure",
    short_name="aws_ec2_asset_exposure_auto_scaling_group",
    cleanup_iterationsize=1000,
    statements=(
        AnalysisStatement(
            match="""
            MATCH (instance:AWSEC2Instance{exposed_internet: true})-[:MEMBER_AUTO_SCALE_GROUP]->(asg:AWSAutoScalingGroup)
            UNWIND instance.exposed_internet_type as type
            WITH DISTINCT type, asg
            """,
            effects=(
                SetProperty(
                    "asg", "exposed_internet", True, label="AWSAutoScalingGroup"
                ),
                AddToSet(
                    "asg",
                    "exposed_internet_type",
                    Var("type"),
                    label="AWSAutoScalingGroup",
                ),
            ),
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
    statements=(
        AnalysisStatement(
            match="MATCH (k:AWSEC2KeyPair) WHERE size(k.keyfingerprint) = 47",
            effects=(SetProperty("k", "user_uploaded", True, label="AWSEC2KeyPair"),),
        ),
        AnalysisStatement(
            match="MATCH (k1:AWSEC2KeyPair) MATCH (k2:AWSEC2KeyPair) WHERE id(k1) < id(k2) AND k1.keyfingerprint = k2.keyfingerprint",
            effects=(
                SetProperty(
                    "k1", "duplicate_keyfingerprint", True, label="AWSEC2KeyPair"
                ),
                SetProperty(
                    "k2", "duplicate_keyfingerprint", True, label="AWSEC2KeyPair"
                ),
            ),
        ),
    ),
)
AWS_EC2_KEYPAIR_MATCHING_FINGERPRINT = AnalysisJob(
    name="Analysis jobs for EC2 Key Pairs matching fingerprints",
    short_name="aws_ec2_keypair_analysis_matching_fingerprint",
    statements=(
        AnalysisStatement(
            match="MATCH (k1:AWSEC2KeyPair) MATCH (k2:AWSEC2KeyPair) WHERE id(k1) < id(k2) AND k1.keyfingerprint = k2.keyfingerprint",
            effects=(
                AddRelationship(
                    "k1",
                    "MATCHING_FINGERPRINT",
                    "k2",
                    undirected=True,
                    source_label="AWSEC2KeyPair",
                    target_label="AWSEC2KeyPair",
                    firstseen=Param("UPDATE_TAG"),
                ),
            ),
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
    statements=(
        AnalysisStatement(
            match="MATCH (cluster:AWSEKSCluster) WHERE cluster.endpoint_public_access = true",
            effects=(
                SetProperty("cluster", "exposed_internet", True, label="AWSEKSCluster"),
            ),
        ),
    ),
)
AWS_FOREIGN_ACCOUNTS = AnalysisJob(
    name="AWS - Foreign account analysis",
    short_name="aws_foreign_accounts",
    statements=(
        AnalysisStatement(
            match="MATCH (foreign:AWSAccount) where foreign.inscope IS NULL",
            effects=(SetProperty("foreign", "foreign", True, label="AWSAccount"),),
        ),
    ),
)
AWS_ECS_ASSET_EXPOSURE = AnalysisJob(
    name="AWS ECS internet exposure (deprecated: use ontology LoadBalancer-[:EXPOSE]->Container)",
    short_name="aws_ecs_asset_exposure",
    cleanup_iterationsize=1000,
    statements=(
        AnalysisStatement(
            match="""
            MATCH (lb:AWSLoadBalancerV2 {exposed_internet: true})-[:EXPOSE]->(ip:AWSEC2PrivateIp)<-[:PRIVATE_IP_ADDRESS]-(ni:AWSNetworkInterface)<-[:NETWORK_INTERFACE]-(task:AWSECSTask)-[:HAS_CONTAINER]->(container:AWSECSContainer)
            WITH DISTINCT container
            """,
            effects=(
                SetProperty(
                    "container", "exposed_internet", True, label="AWSECSContainer"
                ),
                AddToSet(
                    "container",
                    "exposed_internet_type",
                    "elbv2",
                    label="AWSECSContainer",
                ),
            ),
        ),
    ),
)
