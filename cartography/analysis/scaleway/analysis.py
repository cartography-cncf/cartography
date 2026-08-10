from cartography.graph.analysis import AddToSet
from cartography.graph.analysis import AnalysisJob
from cartography.graph.analysis import AnalysisStatement
from cartography.graph.analysis import SetProperty

# Scaleway exposure jobs are deliberately unscoped. Unlike AWS, GCP and Azure, the
# Scaleway sync is organization-wide and single-pass: every project is refreshed in
# one run of start_scaleway_ingestion, so there is no other project's data for an
# unscoped cleanup to wrongly remove. The jobs therefore run once at the end of
# ingestion, which is also where Azure runs its own unscoped property jobs.

SCALEWAY_INSTANCE_EXPOSURE = AnalysisJob(
    name="Scaleway Instance internet exposure",
    short_name="scaleway_instance_exposure",
    cleanup_iterationsize=1000,
    statements=(
        AnalysisStatement(
            comment=(
                "An Instance is directly reachable when it has at least one public IP "
                "attached AND an attached Security Group has an explicit inbound accept "
                "rule for 0.0.0.0/0. Requiring both mirrors AWS_EC2_ASSET_EXPOSURE_INSTANCE, "
                "which likewise demands publicipaddress IS NOT NULL on top of the open "
                "security group: an open group on an instance with no public address is not "
                "internet-reachable. public_ips holds flexible-IP ids rather than addresses, "
                "so its size is the public-IP signal. No port filter is applied here because "
                "exposed_internet means reachable at all; the compute_instance_exposed rule "
                "narrows the same path down to management ports. Stopped instances are "
                "excluded as they are not a live attack surface. The Security Group's default "
                "inbound policy is not evaluated, only explicit accept rules. "
                "TODO: IPv6 is not covered. Only 0.0.0.0/0 is matched, not ::/0, because "
                "whether a ::/0 rule reaches an instance depends on IPv6 being enabled on it "
                "and that interaction is not verified against the Scaleway API yet."
            ),
            match="""
            MATCH (instance:ScalewayInstance)-[:MEMBER_OF_SCALEWAY_SECURITY_GROUP]->(:ScalewaySecurityGroup)<-[:MEMBER_OF_SCALEWAY_SECURITY_GROUP]-(rule:ScalewaySecurityGroupRule)
            WHERE size(coalesce(instance.public_ips, [])) > 0
              AND NOT coalesce(instance.state, 'running') IN ['stopped', 'stopped_in_place']
              AND rule.direction = 'inbound'
              AND rule.action = 'accept'
              AND rule.ip_range = '0.0.0.0/0'
            WITH DISTINCT instance
            """,
            effects=(
                SetProperty(
                    "instance", "exposed_internet", True, label="ScalewayInstance"
                ),
                AddToSet(
                    "instance",
                    "exposed_internet_type",
                    "direct",
                    label="ScalewayInstance",
                ),
            ),
        ),
        AnalysisStatement(
            comment=(
                "An Instance with no public IP of its own is still reachable when a Public "
                "Gateway PAT rule forwards a public port to its private IP. Matching is by "
                "private IP within the same project because instance to private-network "
                "membership is not modelled; in the rare case of private IPs overlapping "
                "across private networks in one project this can over-match. Same caveat as "
                "the scaleway_instance_pat_exposed rule, which uses this identical join."
            ),
            match="""
            MATCH (prj:ScalewayProject)-[:RESOURCE]->(:ScalewayPublicGateway)-[:HAS]->(pat:ScalewayPublicGatewayPatRule)
            MATCH (prj)-[:RESOURCE]->(instance:ScalewayInstance)
            WHERE instance.private_ip IS NOT NULL
              AND instance.private_ip = pat.private_ip
              AND NOT coalesce(instance.state, 'running') IN ['stopped', 'stopped_in_place']
            WITH DISTINCT instance
            """,
            effects=(
                SetProperty(
                    "instance", "exposed_internet", True, label="ScalewayInstance"
                ),
                AddToSet(
                    "instance",
                    "exposed_internet_type",
                    "pat",
                    label="ScalewayInstance",
                ),
            ),
        ),
        AnalysisStatement(
            comment=(
                "Record the negative verdict explicitly so that exposed_internet = false is "
                "answerable and not confused with 'never evaluated', as GCP and Azure do."
            ),
            match="MATCH (instance:ScalewayInstance) WHERE instance.exposed_internet IS NULL",
            effects=(
                SetProperty(
                    "instance", "exposed_internet", False, label="ScalewayInstance"
                ),
            ),
        ),
    ),
)

SCALEWAY_EXPOSURE_JOBS = (SCALEWAY_INSTANCE_EXPOSURE,)
