"""
AWS EC2 instance configuration and launch-template hygiene


Each rule is a single-property check over data the AWS sync already collects.
All are EXPERIMENTAL until validated against a live graph.

"""

from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule


class AwsEc2InstanceDetailedMonitoringOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    instance_id: str | None = None
    state: str | None = None
    monitoring_state: str | None = None


_aws_ec2_instance_detailed_monitoring_fact = Fact(
    id="aws_ec2_instance_detailed_monitoring_fact",
    name="EC2 detailed monitoring off",
    description="Running instances whose monitoring state is not 'enabled'.",
    cypher_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(i:AWSEC2Instance)
        WHERE i.state = 'running'
          AND (i.monitoringstate IS NULL OR i.monitoringstate <> 'enabled')
        RETURN a.id AS account_id, a.name AS account,
               i.instanceid AS instance_id, i.state AS state,
               i.monitoringstate AS monitoring_state

    """,
    cypher_visual_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(i:AWSEC2Instance)
        WHERE i.state = 'running'
          AND (i.monitoringstate IS NULL OR i.monitoringstate <> 'enabled')
        RETURN a.id AS account_id, a.name AS account,
               i.instanceid AS instance_id, i.state AS state,
               i.monitoringstate AS monitoring_state

    """,
    cypher_count_query="""
    MATCH (i:AWSEC2Instance) WHERE i.state = 'running' RETURN COUNT(i) AS count
    """,
    asset_label="AWSEC2Instance",
    asset_id_field="instance_id",
    identity_fields=("account_id", "account", "instance_id"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_ec2_instance_detailed_monitoring = Rule(
    id="aws_ec2_instance_detailed_monitoring",
    name="EC2 Detailed Monitoring Disabled",
    description="Running EC2 instance (state='running') without detailed monitoring (monitoringstate <> 'enabled' or null). Detailed monitoring provides 1-minute metric granularity for faster incident detection.",
    output_model=AwsEc2InstanceDetailedMonitoringOutput,
    facts=(_aws_ec2_instance_detailed_monitoring_fact,),
    tags=("ec2", "observability", "cspm", "low"),
    version="0.1.0",
)


class AwsEc2InstanceInternalPortsExposedOutput(Finding):
    instance_id: str | None = None
    port: str | None = None
    service: str | None = None
    security_group: str | None = None
    public_ip: str | None = None
    account_id: str | None = None
    account: str | None = None


_aws_ec2_instance_internal_ports_exposed_fact = Fact(
    id="aws_ec2_instance_internal_ports_exposed_fact",
    name="EC2 instances with internal ports open to the internet",
    description="EC2 instances whose security group allows inbound TCP (or all-protocol) traffic from 0.0.0.0/0 or ::/0 on a port from the shared INTERNAL_PORTS list. Terminated and shutting-down instances are excluded. The public IP is returned for severity refinement.",
    cypher_query="""
    MATCH (a:AWSAccount)-[:RESOURCE]->(ec2:AWSEC2Instance)-[:MEMBER_OF_EC2_SECURITY_GROUP]->(sg:AWSEC2SecurityGroup)<-[:MEMBER_OF_EC2_SECURITY_GROUP]-(rule:AWSIpPermissionInbound)
    MATCH (rule)<-[:MEMBER_OF_IP_RULE]-(ip:AWSIpRange)
    WHERE ip.range IN ['0.0.0.0/0', '::/0']
      AND coalesce(rule.protocol, '') IN ['tcp', '-1', 'all']
      AND NOT coalesce(ec2.state, 'running') IN ['terminated', 'shutting-down']
    UNWIND [{port: 20, service: 'FTP'}, {port: 21, service: 'FTP'}, {port: 23, service: 'Telnet'}, {port: 88, service: 'Kerberos'}, {port: 139, service: 'CIFS/SMB'}, {port: 161, service: 'SNMP'}, {port: 162, service: 'SNMP'}, {port: 389, service: 'LDAP'}, {port: 445, service: 'CIFS/SMB'}, {port: 464, service: 'Kerberos'}, {port: 636, service: 'LDAP'}, {port: 749, service: 'Kerberos'}, {port: 750, service: 'Kerberos'}, {port: 873, service: 'rsync'}, {port: 1433, service: 'SQL Server'}, {port: 1434, service: 'SQL Server'}, {port: 1521, service: 'Oracle'}, {port: 2049, service: 'NFS'}, {port: 2181, service: 'ZooKeeper'}, {port: 2375, service: 'Docker API'}, {port: 2376, service: 'Docker API'}, {port: 2379, service: 'etcd'}, {port: 2380, service: 'etcd'}, {port: 2483, service: 'Oracle'}, {port: 2484, service: 'Oracle'}, {port: 3306, service: 'MySQL'}, {port: 5432, service: 'PostgreSQL'}, {port: 5601, service: 'Kibana'}, {port: 5672, service: 'RabbitMQ'}, {port: 5900, service: 'VNC'}, {port: 6379, service: 'Redis'}, {port: 7000, service: 'Cassandra'}, {port: 7001, service: 'Cassandra'}, {port: 7199, service: 'Cassandra'}, {port: 9042, service: 'Cassandra'}, {port: 9092, service: 'Kafka'}, {port: 9160, service: 'Cassandra'}, {port: 9200, service: 'Elasticsearch'}, {port: 9300, service: 'Elasticsearch'}, {port: 11211, service: 'Memcached'}, {port: 15672, service: 'RabbitMQ management'}, {port: 27017, service: 'MongoDB'}, {port: 27018, service: 'MongoDB'}, {port: 27019, service: 'MongoDB'}, {port: 33060, service: 'MySQL X protocol'}] AS entry
    WITH a, ec2, sg, rule, entry
    WHERE rule.fromport IS NULL
       OR (
         coalesce(rule.fromport, 0) <= entry.port
         AND coalesce(rule.toport, rule.fromport, 0) >= entry.port
       )
    RETURN DISTINCT
        a.id AS account_id,
        a.name AS account,
        ec2.instanceid AS instance_id,
        entry.port AS port,
        entry.service AS service,
        sg.groupid AS security_group,
        ec2.publicipaddress AS public_ip
    ORDER BY account, instance_id, port, security_group
    """,
    cypher_visual_query="""
    MATCH p=(a:AWSAccount)-[:RESOURCE]->(ec2:AWSEC2Instance)-[:MEMBER_OF_EC2_SECURITY_GROUP]->(sg:AWSEC2SecurityGroup)<-[:MEMBER_OF_EC2_SECURITY_GROUP]-(rule:AWSIpPermissionInbound)
    MATCH p2=(rule)<-[:MEMBER_OF_IP_RULE]-(ip:AWSIpRange)
    WHERE ip.range IN ['0.0.0.0/0', '::/0']
      AND coalesce(rule.protocol, '') IN ['tcp', '-1', 'all']
      AND NOT coalesce(ec2.state, 'running') IN ['terminated', 'shutting-down']
      AND (
        rule.fromport IS NULL
        OR ANY(entry IN [{port: 20, service: 'FTP'}, {port: 21, service: 'FTP'}, {port: 23, service: 'Telnet'}, {port: 88, service: 'Kerberos'}, {port: 139, service: 'CIFS/SMB'}, {port: 161, service: 'SNMP'}, {port: 162, service: 'SNMP'}, {port: 389, service: 'LDAP'}, {port: 445, service: 'CIFS/SMB'}, {port: 464, service: 'Kerberos'}, {port: 636, service: 'LDAP'}, {port: 749, service: 'Kerberos'}, {port: 750, service: 'Kerberos'}, {port: 873, service: 'rsync'}, {port: 1433, service: 'SQL Server'}, {port: 1434, service: 'SQL Server'}, {port: 1521, service: 'Oracle'}, {port: 2049, service: 'NFS'}, {port: 2181, service: 'ZooKeeper'}, {port: 2375, service: 'Docker API'}, {port: 2376, service: 'Docker API'}, {port: 2379, service: 'etcd'}, {port: 2380, service: 'etcd'}, {port: 2483, service: 'Oracle'}, {port: 2484, service: 'Oracle'}, {port: 3306, service: 'MySQL'}, {port: 5432, service: 'PostgreSQL'}, {port: 5601, service: 'Kibana'}, {port: 5672, service: 'RabbitMQ'}, {port: 5900, service: 'VNC'}, {port: 6379, service: 'Redis'}, {port: 7000, service: 'Cassandra'}, {port: 7001, service: 'Cassandra'}, {port: 7199, service: 'Cassandra'}, {port: 9042, service: 'Cassandra'}, {port: 9092, service: 'Kafka'}, {port: 9160, service: 'Cassandra'}, {port: 9200, service: 'Elasticsearch'}, {port: 9300, service: 'Elasticsearch'}, {port: 11211, service: 'Memcached'}, {port: 15672, service: 'RabbitMQ management'}, {port: 27017, service: 'MongoDB'}, {port: 27018, service: 'MongoDB'}, {port: 27019, service: 'MongoDB'}, {port: 33060, service: 'MySQL X protocol'}]
             WHERE coalesce(rule.fromport, 0) <= entry.port
               AND coalesce(rule.toport, rule.fromport, 0) >= entry.port)
      )
    RETURN *
    """,
    cypher_count_query="""
    MATCH (ec2:AWSEC2Instance)
    WHERE NOT coalesce(ec2.state, 'running') IN ['terminated', 'shutting-down']
    RETURN COUNT(ec2) AS count
    """,
    asset_label="AWSEC2Instance",
    asset_id_field="instance_id",
    identity_fields=("instance_id", "port", "security_group"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_ec2_instance_internal_ports_exposed = Rule(
    id="aws_ec2_instance_internal_ports_exposed",
    name="EC2 Instance Internal Ports Exposed to Internet",
    description="Public EC2 instances with ports from the common internal-port list (databases, caches, directory services, cluster and admin protocols — see INTERNAL_PORTS in ec2_port_exposure.py) open to the internet via an attached security group. These services belong on private networks; world-open ingress invites brute-force, unauthenticated access and data exfiltration. Restrict the ingress CIDR to trusted ranges or move the service to a private subnet. SSH/RDP exposure is covered by the SG remote-admin rules.",
    output_model=AwsEc2InstanceInternalPortsExposedOutput,
    facts=(_aws_ec2_instance_internal_ports_exposed_fact,),
    tags=("infrastructure", "compute", "attack_surface", "cspm"),
    version="0.1.0",
)


class AwsEc2InstanceManagedBySsmOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    instance_id: str | None = None
    state: str | None = None
    launch_time_unix: str | None = None
    age_days: str | None = None
    image_id: str | None = None
    virtualization_type: str | None = None
    public_ip: str | None = None
    public_dns_name: str | None = None


_aws_ec2_instance_managed_by_ssm_fact = Fact(
    id="aws_ec2_instance_managed_by_ssm_fact",
    name="Running EC2 instances not managed by SSM",
    description="Running EC2 instances (state='running') with no (instance)-[:HAS_INFORMATION]->(AWSSSMInstanceInformation) record, i.e. not registered as an SSM managed node. Presence of an SSM InstanceInformation record matches the describe_instance_information basis (the ssm module is synced). Non-running instances are out of scope.",
    cypher_query="""
    MATCH (a:AWSAccount)-[:RESOURCE]->(ec2:AWSEC2Instance)
    WHERE ec2.state = 'running'
      AND NOT (ec2)-[:HAS_INFORMATION]->(:AWSSSMInstanceInformation)
    RETURN
        a.id AS account_id,
        a.name AS account,
        ec2.instanceid AS instance_id,
        ec2.state AS state
    ORDER BY account, instance_id
    """,
    cypher_visual_query="""
    MATCH p=(a:AWSAccount)-[:RESOURCE]->(ec2:AWSEC2Instance)
    WHERE ec2.state = 'running'
      AND NOT (ec2)-[:HAS_INFORMATION]->(:AWSSSMInstanceInformation)
    RETURN *
    """,
    cypher_count_query="""
    MATCH (ec2:AWSEC2Instance) WHERE ec2.state = 'running' RETURN COUNT(ec2) AS count
    """,
    asset_label="AWSEC2Instance",
    asset_id_field="instance_id",
    identity_fields=("account_id", "instance_id"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_ec2_instance_managed_by_ssm = Rule(
    id="aws_ec2_instance_managed_by_ssm",
    name="Running EC2 Instances Not Managed by SSM",
    description="Running EC2 instances (state='running') with no (instance)-[:HAS_INFORMATION]->(AWSSSMInstanceInformation) record, i.e. not registered as an SSM managed node. Presence of an SSM InstanceInformation record matches the describe_instance_information basis (the ssm module is synced). Non-running instances are out of scope.",
    output_model=AwsEc2InstanceManagedBySsmOutput,
    facts=(_aws_ec2_instance_managed_by_ssm_fact,),
    tags=("ec2", "security", "cspm", "medium"),
    version="0.1.0",
)


class AwsEc2InstanceMaxAgeOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    instance_id: str | None = None
    state: str | None = None
    launch_time_unix: str | None = None
    age_days: str | None = None
    image_id: str | None = None
    virtualization_type: str | None = None
    public_ip: str | None = None
    public_dns_name: str | None = None


_aws_ec2_instance_max_age_fact = Fact(
    id="aws_ec2_instance_max_age_fact",
    name="Running EC2 instances older than the maximum age",
    description="Running EC2 instances whose launchtimeunix (epoch seconds, stored as a string) is older than 180 days (configurable maximum age, default 180 days). launchtime reflects the last launch, i.e. running age for instances launched once. The computed age in days is returned.",
    cypher_query="""
    MATCH (a:AWSAccount)-[:RESOURCE]->(ec2:AWSEC2Instance)
    WHERE ec2.state = 'running'
      AND ec2.launchtimeunix IS NOT NULL
      AND toFloat(ec2.launchtimeunix) < (timestamp() / 1000.0) - (180 * 86400)
    RETURN
        a.id AS account_id,
        a.name AS account,
        ec2.instanceid AS instance_id,
        ec2.state AS state,
        ec2.launchtimeunix AS launch_time_unix,
        toInteger((timestamp() / 1000.0 - toFloat(ec2.launchtimeunix)) / 86400) AS age_days
    ORDER BY account, instance_id
    """,
    cypher_visual_query="""
    MATCH p=(a:AWSAccount)-[:RESOURCE]->(ec2:AWSEC2Instance)
    WHERE ec2.state = 'running'
      AND ec2.launchtimeunix IS NOT NULL
      AND toFloat(ec2.launchtimeunix) < (timestamp() / 1000.0) - (180 * 86400)
    RETURN *
    """,
    cypher_count_query="""
    MATCH (ec2:AWSEC2Instance) WHERE ec2.state = 'running' RETURN COUNT(ec2) AS count
    """,
    asset_label="AWSEC2Instance",
    asset_id_field="instance_id",
    identity_fields=("account_id", "instance_id"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_ec2_instance_max_age = Rule(
    id="aws_ec2_instance_max_age",
    name="Running EC2 Instances Older Than Maximum Age",
    description="Running EC2 instances whose launchtimeunix (epoch seconds, stored as a string) is older than 180 days (configurable maximum age, default 180 days). launchtime reflects the last launch, i.e. running age for instances launched once. The computed age in days is returned.",
    output_model=AwsEc2InstanceMaxAgeOutput,
    facts=(_aws_ec2_instance_max_age_fact,),
    tags=("ec2", "security", "cspm", "medium"),
    version="0.1.0",
)


class AwsEc2InstanceMultipleEnisOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    instance_id: str | None = None
    state: str | None = None
    eni_count: str | None = None


_aws_ec2_instance_multiple_enis_fact = Fact(
    id="aws_ec2_instance_multiple_enis_fact",
    name="EC2 instance ENI count > 1",
    description="Instances with more than one NETWORK_INTERFACE edge to an ENI.",
    cypher_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(i:AWSEC2Instance)
        OPTIONAL MATCH (i)-[:NETWORK_INTERFACE]->(eni:AWSNetworkInterface)
        WITH a, i, COUNT(eni) AS eni_count
        WHERE eni_count > 1
        RETURN a.id AS account_id, a.name AS account,
               i.instanceid AS instance_id, i.state AS state,
               eni_count AS eni_count

    """,
    cypher_visual_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(i:AWSEC2Instance)
        OPTIONAL MATCH (i)-[:NETWORK_INTERFACE]->(eni:AWSNetworkInterface)
        WITH a, i, COUNT(eni) AS eni_count
        WHERE eni_count > 1
        RETURN a.id AS account_id, a.name AS account,
               i.instanceid AS instance_id, i.state AS state,
               eni_count AS eni_count

    """,
    cypher_count_query="""
    MATCH (i:AWSEC2Instance) RETURN COUNT(i) AS count
    """,
    asset_label="AWSEC2Instance",
    asset_id_field="instance_id",
    identity_fields=("account_id", "account", "instance_id"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_ec2_instance_multiple_enis = Rule(
    id="aws_ec2_instance_multiple_enis",
    name="EC2 Instance With Multiple ENIs",
    description="EC2 instance with more than one attached network interface (all interface types). Multiple ENIs widen the network attack surface and complicate traffic attribution. LIMITATION: AWSNetworkInterface nodes are synced from EC2 instance descriptions, so ENIs attached by other services may be missing (possible false negatives).",
    output_model=AwsEc2InstanceMultipleEnisOutput,
    facts=(_aws_ec2_instance_multiple_enis_fact,),
    tags=("ec2", "network", "hygiene", "cspm", "low"),
    version="0.1.0",
)


class AwsEc2InstanceParavirtualOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    instance_id: str | None = None
    state: str | None = None
    launch_time_unix: str | None = None
    age_days: str | None = None
    image_id: str | None = None
    virtualization_type: str | None = None
    public_ip: str | None = None
    public_dns_name: str | None = None


_aws_ec2_instance_paravirtual_fact = Fact(
    id="aws_ec2_instance_paravirtual_fact",
    name="EC2 instances running paravirtual AMIs",
    description="EC2 instances whose AMI has virtualizationtype='paravirtual' (property join AWSEC2Image.imageid = instance.imageid, restricted to account-owned AMIs). LIMITATION: virtualizationtype is stored on AWSEC2Image, not AWSEC2Instance, and the ec2:images sync only covers account-owned AMIs — instances launched from public/marketplace AMIs cannot be evaluated (false negatives). Instance state is returned for context; the spec predicate does not filter on state.",
    cypher_query="""
    MATCH (a:AWSAccount)-[:RESOURCE]->(ec2:AWSEC2Instance)
    MATCH (a)-[:RESOURCE]->(img:AWSEC2Image)
    WHERE img.imageid = ec2.imageid
      AND img.virtualizationtype = 'paravirtual'
    RETURN
        a.id AS account_id,
        a.name AS account,
        ec2.instanceid AS instance_id,
        ec2.state AS state,
        ec2.imageid AS image_id,
        img.virtualizationtype AS virtualization_type
    ORDER BY account, instance_id
    """,
    cypher_visual_query="""
    MATCH p=(a:AWSAccount)-[:RESOURCE]->(ec2:AWSEC2Instance)
    MATCH p2=(a)-[:RESOURCE]->(img:AWSEC2Image)
    WHERE img.imageid = ec2.imageid
      AND img.virtualizationtype = 'paravirtual'
    RETURN *
    """,
    cypher_count_query="""
    MATCH (ec2:AWSEC2Instance) RETURN COUNT(ec2) AS count
    """,
    asset_label="AWSEC2Instance",
    asset_id_field="instance_id",
    identity_fields=("account_id", "instance_id", "image_id", "virtualization_type"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_ec2_instance_paravirtual = Rule(
    id="aws_ec2_instance_paravirtual",
    name="EC2 Instances Running Paravirtual AMIs",
    description="EC2 instances whose AMI has virtualizationtype='paravirtual' (property join AWSEC2Image.imageid = instance.imageid, restricted to account-owned AMIs). LIMITATION: virtualizationtype is stored on AWSEC2Image, not AWSEC2Instance, and the ec2:images sync only covers account-owned AMIs — instances launched from public/marketplace AMIs cannot be evaluated (false negatives). Instance state is returned for context; the spec predicate does not filter on state.",
    output_model=AwsEc2InstanceParavirtualOutput,
    facts=(_aws_ec2_instance_paravirtual_fact,),
    tags=("ec2", "security", "cspm", "medium"),
    version="0.1.0",
)


class AwsEc2InstanceProfileAttachedOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    instance_id: str | None = None
    state: str | None = None
    launch_time_unix: str | None = None
    age_days: str | None = None
    image_id: str | None = None
    virtualization_type: str | None = None
    public_ip: str | None = None
    public_dns_name: str | None = None


_aws_ec2_instance_profile_attached_fact = Fact(
    id="aws_ec2_instance_profile_attached_fact",
    name="Running EC2 instances without an IAM instance profile",
    description="Running EC2 instances (state='running') with no IAM instance profile: iaminstanceprofile IS NULL and no (instance)-[:INSTANCE_PROFILE]->(AWSInstanceProfile) relationship. Without an instance profile, workloads cannot obtain IAM role credentials via the instance metadata service and often fall back to hard-coded long-lived keys.",
    cypher_query="""
    MATCH (a:AWSAccount)-[:RESOURCE]->(ec2:AWSEC2Instance)
    WHERE ec2.state = 'running'
      AND ec2.iaminstanceprofile IS NULL
      AND NOT (ec2)-[:INSTANCE_PROFILE]->(:AWSInstanceProfile)
    RETURN
        a.id AS account_id,
        a.name AS account,
        ec2.instanceid AS instance_id,
        ec2.state AS state
    ORDER BY account, instance_id
    """,
    cypher_visual_query="""
    MATCH p=(a:AWSAccount)-[:RESOURCE]->(ec2:AWSEC2Instance)
    WHERE ec2.state = 'running'
      AND ec2.iaminstanceprofile IS NULL
      AND NOT (ec2)-[:INSTANCE_PROFILE]->(:AWSInstanceProfile)
    RETURN *
    """,
    cypher_count_query="""
    MATCH (ec2:AWSEC2Instance) WHERE ec2.state = 'running' RETURN COUNT(ec2) AS count
    """,
    asset_label="AWSEC2Instance",
    asset_id_field="instance_id",
    identity_fields=("account_id", "instance_id"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_ec2_instance_profile_attached = Rule(
    id="aws_ec2_instance_profile_attached",
    name="Running EC2 Instances Without an Instance Profile",
    description="Running EC2 instances (state='running') with no IAM instance profile: iaminstanceprofile IS NULL and no (instance)-[:INSTANCE_PROFILE]->(AWSInstanceProfile) relationship. Without an instance profile, workloads cannot obtain IAM role credentials via the instance metadata service and often fall back to hard-coded long-lived keys.",
    output_model=AwsEc2InstanceProfileAttachedOutput,
    facts=(_aws_ec2_instance_profile_attached_fact,),
    tags=("ec2", "security", "cspm", "medium"),
    version="0.1.0",
)


class AwsEc2InstancePublicIpOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    instance_id: str | None = None
    state: str | None = None
    launch_time_unix: str | None = None
    age_days: str | None = None
    image_id: str | None = None
    virtualization_type: str | None = None
    public_ip: str | None = None
    public_dns_name: str | None = None


_aws_ec2_instance_public_ip_fact = Fact(
    id="aws_ec2_instance_public_ip_fact",
    name="EC2 instances with a public IP address",
    description="EC2 instances with publicipaddress set (or a non-empty publicdnsname). EIPs associated via ENI only do not appear in instance.publicipaddress (an instance-field limitation). The built-in compute_instance_exposed rule only flags public instances with open sensitive ports; this rule flags any public IP. State is returned for context.",
    cypher_query="""
    MATCH (a:AWSAccount)-[:RESOURCE]->(ec2:AWSEC2Instance)
    WHERE ec2.publicipaddress IS NOT NULL
       OR (ec2.publicdnsname IS NOT NULL AND ec2.publicdnsname <> '')
    RETURN
        a.id AS account_id,
        a.name AS account,
        ec2.instanceid AS instance_id,
        ec2.state AS state,
        ec2.publicipaddress AS public_ip,
        ec2.publicdnsname AS public_dns_name
    ORDER BY account, instance_id
    """,
    cypher_visual_query="""
    MATCH p=(a:AWSAccount)-[:RESOURCE]->(ec2:AWSEC2Instance)
    WHERE ec2.publicipaddress IS NOT NULL
       OR (ec2.publicdnsname IS NOT NULL AND ec2.publicdnsname <> '')
    RETURN *
    """,
    cypher_count_query="""
    MATCH (ec2:AWSEC2Instance) RETURN COUNT(ec2) AS count
    """,
    asset_label="AWSEC2Instance",
    asset_id_field="instance_id",
    identity_fields=("account_id", "instance_id"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_ec2_instance_public_ip = Rule(
    id="aws_ec2_instance_public_ip",
    name="EC2 Instances With a Public IP",
    description="EC2 instances with publicipaddress set (or a non-empty publicdnsname). EIPs associated via ENI only do not appear in instance.publicipaddress (an instance-field limitation). The built-in compute_instance_exposed rule only flags public instances with open sensitive ports; this rule flags any public IP. State is returned for context.",
    output_model=AwsEc2InstancePublicIpOutput,
    facts=(_aws_ec2_instance_public_ip_fact,),
    tags=("ec2", "security", "cspm", "medium"),
    version="0.1.0",
)


class AwsEc2InstancePublicWithProfileOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    instance_id: str | None = None
    public_ip: str | None = None
    instance_profile: str | None = None
    state: str | None = None


_aws_ec2_instance_public_with_profile_fact = Fact(
    id="aws_ec2_instance_public_with_profile_fact",
    name="Public instance with profile",
    description="Instances with a public IP and an attached instance profile.",
    cypher_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(ec2:AWSEC2Instance)
        WHERE ec2.publicipaddress IS NOT NULL AND ec2.publicipaddress <> ''
          AND NOT coalesce(ec2.state, 'running') IN ['terminated', 'shutting-down']
        OPTIONAL MATCH (ec2)-[:INSTANCE_PROFILE]->(profile:AWSInstanceProfile)
        WITH a, ec2, profile
        WHERE ec2.iaminstanceprofile IS NOT NULL OR profile IS NOT NULL
        RETURN a.id AS account_id, a.name AS account, ec2.instanceid AS instance_id,
               ec2.publicipaddress AS public_ip,
               coalesce(profile.arn, ec2.iaminstanceprofile) AS instance_profile,
               ec2.state AS state

    """,
    cypher_visual_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(ec2:AWSEC2Instance)
        WHERE ec2.publicipaddress IS NOT NULL AND ec2.publicipaddress <> ''
          AND NOT coalesce(ec2.state, 'running') IN ['terminated', 'shutting-down']
        OPTIONAL MATCH (ec2)-[:INSTANCE_PROFILE]->(profile:AWSInstanceProfile)
        WITH a, ec2, profile
        WHERE ec2.iaminstanceprofile IS NOT NULL OR profile IS NOT NULL
        RETURN a.id AS account_id, a.name AS account, ec2.instanceid AS instance_id,
               ec2.publicipaddress AS public_ip,
               coalesce(profile.arn, ec2.iaminstanceprofile) AS instance_profile,
               ec2.state AS state

    """,
    cypher_count_query="""
    MATCH (ec2:AWSEC2Instance) RETURN COUNT(ec2) AS count
    """,
    asset_label="AWSEC2Instance",
    asset_id_field="instance_id",
    identity_fields=("account_id", "instance_id", "instance_profile"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_ec2_instance_public_with_profile = Rule(
    id="aws_ec2_instance_public_with_profile",
    name="EC2 Instance Public with Instance Profile",
    description="EC2 instance has a public IP address and an IAM instance profile attached (iaminstanceprofile property or INSTANCE_PROFILE relationship). Terminated and shutting-down instances are excluded. This is distinct from workload_identity_admin_capabilities, which requires admin/escalation IAM capabilities rather than merely any profile plus a public IP.",
    output_model=AwsEc2InstancePublicWithProfileOutput,
    facts=(_aws_ec2_instance_public_with_profile_fact,),
    tags=("security", "ec2", "iam", "attack_surface", "cspm"),
    version="0.1.0",
)


class AwsLaunchTemplateImdsv2Output(Finding):
    account_id: str | None = None
    account: str | None = None
    launch_template_id: str | None = None
    launch_template_name: str | None = None
    launch_template_ref: str | None = None
    region: str | None = None


_aws_launch_template_imdsv2_fact = Fact(
    id="aws_launch_template_imdsv2_fact",
    name="Launch template ASG fleet allows IMDSv1",
    description="ASG-used templates whose member instances have metadatahttpendpoint='enabled' and tokens not 'required'.",
    cypher_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(lt:AWSLaunchTemplate)<-[:HAS_LAUNCH_TEMPLATE]-(asg:AWSAutoScalingGroup)<-[:MEMBER_AUTO_SCALE_GROUP]-(i:AWSEC2Instance)
        WHERE i.metadatahttpendpoint = 'enabled' AND coalesce(i.metadatahttptokens, '') <> 'required'
        RETURN DISTINCT a.id AS account_id, a.name AS account, lt.id AS launch_template_id,
               lt.name AS launch_template_name, lt.launch_template_id AS launch_template_ref,
               lt.region AS region

    """,
    cypher_visual_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(lt:AWSLaunchTemplate)<-[:HAS_LAUNCH_TEMPLATE]-(asg:AWSAutoScalingGroup)<-[:MEMBER_AUTO_SCALE_GROUP]-(i:AWSEC2Instance)
        WHERE i.metadatahttpendpoint = 'enabled' AND coalesce(i.metadatahttptokens, '') <> 'required'
        RETURN DISTINCT a.id AS account_id, a.name AS account, lt.id AS launch_template_id,
               lt.name AS launch_template_name, lt.launch_template_id AS launch_template_ref,
               lt.region AS region

    """,
    cypher_count_query="""
        MATCH (lt:AWSLaunchTemplate)<-[:HAS_LAUNCH_TEMPLATE]-(asg:AWSAutoScalingGroup)<-[:MEMBER_AUTO_SCALE_GROUP]-(i:AWSEC2Instance)
        RETURN COUNT(DISTINCT lt) AS count

    """,
    asset_label="AWSLaunchTemplate",
    asset_id_field="launch_template_id",
    identity_fields=("account_id", "account", "launch_template_id"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_launch_template_imdsv2 = Rule(
    id="aws_launch_template_imdsv2",
    name="Launch Template IMDSv2 Required",
    description="Launch template is used by an Auto Scaling group whose member instances allow IMDSv1 (metadata HTTP endpoint enabled with tokens not 'required'). Covers only ASG-used templates and their current members, measuring effective fleet posture rather than each template version's declared config (version-level MetadataOptions are not synced); templates used directly via RunInstances are invisible.",
    output_model=AwsLaunchTemplateImdsv2Output,
    facts=(_aws_launch_template_imdsv2_fact,),
    tags=("security", "ec2", "imds", "cspm"),
    version="0.1.0",
)
