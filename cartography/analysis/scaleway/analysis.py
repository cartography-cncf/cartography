from cartography.graph.analysis import AddRelationship
from cartography.graph.analysis import AddToSet
from cartography.graph.analysis import AnalysisJob
from cartography.graph.analysis import AnalysisStatement
from cartography.graph.analysis import SetProperty

# Scaleway exposure jobs are deliberately unscoped. Unlike AWS, GCP and Azure, the
# Scaleway sync is organization-wide and single-pass: every project is refreshed in
# one run of start_scaleway_ingestion, so there is no other project's data for an
# unscoped cleanup to wrongly remove. The jobs therefore run once at the end of
# ingestion, which is also where Azure runs its own unscoped property jobs.

# Every Scaleway managed-database product carries a single
# is_public flag meaning "a public endpoint is provisioned". There is no separate
# firewall layer to join, unlike AWS security groups or GCP authorized networks, so
# that flag is the whole reachability signal. The products differ only by label, hence
# the generated statements: a per-label statement is required because SetProperty needs
# a label for the generated cleanup to know which nodes own the property.
_PUBLIC_ENDPOINT_DATABASE_LABELS = (
    "ScalewayRdbInstance",
    "ScalewayRedisCluster",
    "ScalewayMongoDBInstance",
    "ScalewayDataWarehouseDeployment",
    "ScalewayServerlessSQLDatabase",
    "ScalewaySearchDeployment",
)


def _public_endpoint_statements(label: str) -> tuple[AnalysisStatement, ...]:
    """Mark one managed-database label exposed on is_public, then default the rest to false."""
    return (
        AnalysisStatement(
            comment=(
                f"A {label} is reachable from the internet when Scaleway has provisioned a "
                "public endpoint for it. status is deliberately not filtered on: the "
                "database products each use their own status vocabulary, and the existing "
                "database_instance_exposed rules key off is_public alone, so adding a "
                "filter here would make the property and the rules disagree."
            ),
            match=f"MATCH (db:{label}) WHERE db.is_public = true",
            effects=(
                SetProperty("db", "exposed_internet", True, label=label),
                AddToSet("db", "exposed_internet_type", "direct", label=label),
            ),
        ),
        AnalysisStatement(
            comment=(
                "Record the negative verdict explicitly so that exposed_internet = false is "
                "answerable and not confused with 'never evaluated', as GCP and Azure do."
            ),
            match=f"MATCH (db:{label}) WHERE db.exposed_internet IS NULL",
            effects=(SetProperty("db", "exposed_internet", False, label=label),),
        ),
    )


SCALEWAY_DATABASE_EXPOSURE = AnalysisJob(
    name="Scaleway managed database internet exposure",
    short_name="scaleway_database_exposure",
    cleanup_iterationsize=1000,
    statements=tuple(
        statement
        for label in _PUBLIC_ENDPOINT_DATABASE_LABELS
        for statement in _public_endpoint_statements(label)
    ),
)

SCALEWAY_LOADBALANCER_EXPOSURE = AnalysisJob(
    name="Scaleway Load Balancer internet exposure",
    short_name="scaleway_loadbalancer_exposure",
    cleanup_iterationsize=1000,
    statements=(
        AnalysisStatement(
            comment=(
                "A Load Balancer is internet-facing when it holds at least one public IP "
                "and has at least one frontend listening. transform_loadbalancers derives "
                "ip_address from the API's ip list, so a private, private-network-only Load "
                "Balancer has ip_address IS NULL and is correctly skipped. Requiring a "
                "frontend mirrors the AWS network load balancer rule, which demands "
                "scheme = internet-facing plus listener presence: a public address with "
                "nothing listening on it forwards no traffic. The Scaleway LB API exposes no "
                "scheme field, which is why the public IP is the signal instead."
            ),
            match="""
            MATCH (lb:ScalewayLoadBalancer)-[:HAS]->(:ScalewayLBFrontend)
            WHERE lb.ip_address IS NOT NULL
            WITH DISTINCT lb
            """,
            effects=(
                SetProperty(
                    "lb", "exposed_internet", True, label="ScalewayLoadBalancer"
                ),
                AddToSet(
                    "lb",
                    "exposed_internet_type",
                    "direct",
                    label="ScalewayLoadBalancer",
                ),
            ),
        ),
        AnalysisStatement(
            comment=(
                "Record the negative verdict explicitly so that exposed_internet = false is "
                "answerable and not confused with 'never evaluated', as GCP and Azure do."
            ),
            match="MATCH (lb:ScalewayLoadBalancer) WHERE lb.exposed_internet IS NULL",
            effects=(
                SetProperty(
                    "lb", "exposed_internet", False, label="ScalewayLoadBalancer"
                ),
            ),
        ),
    ),
)

SCALEWAY_LB_EXPOSE_EDGES = AnalysisJob(
    name="Scaleway Load Balancer EXPOSE relationships",
    short_name="scaleway_lb_expose_edges",
    statements=(
        AnalysisStatement(
            comment=(
                "Materialize the internet-facing frontend to backend asset edge for Scaleway "
                "Load Balancers. EXPOSE runs from the load balancer to the instance it puts "
                "at risk, the direction fixed by ONTOLOGY_REL_CONSTRAINTS for "
                "LoadBalancer -> ComputeInstance. Only load balancers already marked "
                "exposed_internet occur here, so the edge always means 'reachable from the "
                "internet through this frontend'. ScalewayLBBackend.pool holds plain IP "
                "addresses rather than server ids, so the instance is resolved by matching "
                "the pool against its private_ip and against the address of any flexible IP "
                "identifying it. The match is confined to the load balancer's own project "
                "because private IPs are reusable across projects. Traversing "
                "frontend -[:ROUTES_TO]-> backend rather than the load balancer's direct HAS "
                "edge keeps out backends that no frontend routes to and which therefore "
                "receive no traffic."
            ),
            match="""
            MATCH (lb:ScalewayLoadBalancer {exposed_internet: true})-[:HAS]->(:ScalewayLBFrontend)-[:ROUTES_TO]->(backend:ScalewayLBBackend)
            MATCH (lb)<-[:RESOURCE]-(:ScalewayProject)-[:RESOURCE]->(instance:ScalewayInstance)
            WHERE backend.pool IS NOT NULL
              AND (
                (instance.private_ip IS NOT NULL AND instance.private_ip IN backend.pool)
                OR EXISTS {
                  MATCH (fip:ScalewayFlexibleIp)-[:IDENTIFIES]->(instance)
                  WHERE fip.address IN backend.pool
                }
              )
            WITH DISTINCT lb, instance
            """,
            effects=(
                AddRelationship(
                    "lb",
                    "EXPOSE",
                    "instance",
                    properties={"exposure_type": "lb"},
                    source_label="ScalewayLoadBalancer",
                    target_label="ScalewayInstance",
                ),
            ),
        ),
    ),
)

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
                "An Instance with no public entry point of its own is still reachable when an "
                "internet-facing Load Balancer forwards to it. This follows the EXPOSE edge "
                "materialized by SCALEWAY_LB_EXPOSE_EDGES rather than repeating that job's "
                "pool-to-IP join, the same way AWS_EC2_ASSET_EXPOSURE_INSTANCE reads "
                "(:AWSLoadBalancer {exposed_internet: true})-[:EXPOSE]->(instance). This is "
                "why SCALEWAY_EXPOSURE_JOBS runs the load balancer jobs before this one."
            ),
            match="MATCH (:ScalewayLoadBalancer {exposed_internet: true})-[:EXPOSE]->(instance:ScalewayInstance)",
            effects=(
                SetProperty(
                    "instance", "exposed_internet", True, label="ScalewayInstance"
                ),
                AddToSet(
                    "instance",
                    "exposed_internet_type",
                    "lb",
                    label="ScalewayInstance",
                ),
            ),
        ),
        AnalysisStatement(
            comment=(
                "Record the negative verdict explicitly so that exposed_internet = false is "
                "answerable and not confused with 'never evaluated', as GCP and Azure do. "
                "This must stay the last statement of the job so it only fires for instances "
                "no earlier statement marked."
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

# Order matters. The load balancer verdict is written first, then the EXPOSE edges that
# depend on it, then the instance job which reads those edges to pick up its `lb` path.
# The database job is independent of that chain.
SCALEWAY_EXPOSURE_JOBS = (
    SCALEWAY_LOADBALANCER_EXPOSURE,
    SCALEWAY_LB_EXPOSE_EDGES,
    SCALEWAY_INSTANCE_EXPOSURE,
    SCALEWAY_DATABASE_EXPOSURE,
)
