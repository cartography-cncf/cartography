from cartography.graph.analysis import AddRelationship
from cartography.graph.analysis import AddToSet
from cartography.graph.analysis import AnalysisJob
from cartography.graph.analysis import AnalysisStatement
from cartography.graph.analysis import SetProperty

# These jobs are unscoped: the Scaleway sync is organization-wide and single-pass, so an
# unscoped cleanup has no other project's data to remove.

_DEFAULT_FALSE_COMMENT = (
    "Store the negative verdict explicitly so exposed_internet = false is answerable."
)

# Managed databases all gate public reachability on a single is_public flag. There is no
# firewall layer to join, unlike AWS security groups or GCP authorized networks.
_PUBLIC_ENDPOINT_DATABASE_LABELS = (
    "ScalewayRdbInstance",
    "ScalewayRedisCluster",
    "ScalewayMongoDBInstance",
    "ScalewayDataWarehouseDeployment",
    "ScalewayServerlessSQLDatabase",
    "ScalewaySearchDeployment",
)

# Serverless workloads gate anonymous invocation on `privacy`: `public` means the
# auto-assigned HTTPS domain answers without a token.
_PUBLIC_PRIVACY_SERVERLESS_LABELS = (
    "ScalewayServerlessFunction",
    "ScalewayServerlessContainer",
)


def _flag_statements(
    label: str, node: str, comment: str, predicate: str
) -> tuple[AnalysisStatement, ...]:
    """Mark one label exposed on a single boolean-ish field, then default the rest to false.

    A per-label statement is required because SetProperty needs a label for the generated
    cleanup to know which nodes own the property.
    """
    return (
        AnalysisStatement(
            comment=comment,
            match=f"MATCH ({node}:{label}) WHERE {predicate}",
            effects=(
                SetProperty(node, "exposed_internet", True, label=label),
                AddToSet(node, "exposed_internet_type", "direct", label=label),
            ),
        ),
        AnalysisStatement(
            comment=_DEFAULT_FALSE_COMMENT,
            match=f"MATCH ({node}:{label}) WHERE {node}.exposed_internet IS NULL",
            effects=(SetProperty(node, "exposed_internet", False, label=label),),
        ),
    )


SCALEWAY_DATABASE_EXPOSURE = AnalysisJob(
    name="Scaleway managed database internet exposure",
    short_name="scaleway_database_exposure",
    cleanup_iterationsize=1000,
    statements=tuple(
        statement
        for label in _PUBLIC_ENDPOINT_DATABASE_LABELS
        for statement in _flag_statements(
            label,
            "db",
            # status is not filtered on: each product has its own status vocabulary, and the
            # database_instance_exposed rules key off is_public alone.
            "A public endpoint is provisioned, so the database answers from the internet.",
            "db.is_public = true",
        )
    ),
)

SCALEWAY_SERVERLESS_EXPOSURE = AnalysisJob(
    name="Scaleway serverless internet exposure",
    short_name="scaleway_serverless_exposure",
    cleanup_iterationsize=1000,
    statements=tuple(
        statement
        for label in _PUBLIC_PRIVACY_SERVERLESS_LABELS
        for statement in _flag_statements(
            label,
            "w",
            # Readiness is filtered downstream, where the ontology WORKLOAD_HAS_RUNTIME_IMAGE
            # job keeps only containers whose _ont_state is 'running' or 'ready'.
            "Anonymous callers can invoke it over its auto-assigned HTTPS domain.",
            "w.privacy = 'public'",
        )
    ),
)

SCALEWAY_LOADBALANCER_EXPOSURE = AnalysisJob(
    name="Scaleway Load Balancer internet exposure",
    short_name="scaleway_loadbalancer_exposure",
    cleanup_iterationsize=1000,
    statements=(
        AnalysisStatement(
            comment=(
                "A public IP plus a listening frontend means the load balancer forwards "
                "internet traffic. The LB API has no scheme field, so the IP is the signal; "
                "a private load balancer has ip_address IS NULL."
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
            comment=_DEFAULT_FALSE_COMMENT,
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
                "ScalewayLBBackend.pool holds IP addresses, not server ids, so the instance "
                "is resolved through its private_ip or an identifying flexible IP, within the "
                "load balancer's own project since private IPs are reusable. Going through "
                "ROUTES_TO skips backends no frontend routes to."
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
                "A public IP plus an inbound accept for 0.0.0.0/0. Both are required, as in "
                "AWS_EC2_ASSET_EXPOSURE_INSTANCE: an open group on an instance with no public "
                "address is not reachable. No port filter, since exposed_internet means "
                "reachable at all. TODO: ::/0 is not matched, only 0.0.0.0/0."
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
                "A Public Gateway PAT rule forwards a public port to a private instance. "
                "Matched by private IP within the project, so overlapping private IPs across "
                "private networks can over-match, as in the scaleway_instance_pat_exposed rule."
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
                "Follow the EXPOSE edges from SCALEWAY_LB_EXPOSE_EDGES rather than repeating "
                "its pool-to-IP join, as AWS_EC2_ASSET_EXPOSURE_INSTANCE does."
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
            # Must stay last so it only fires for instances nothing above marked.
            comment=_DEFAULT_FALSE_COMMENT,
            match="MATCH (instance:ScalewayInstance) WHERE instance.exposed_internet IS NULL",
            effects=(
                SetProperty(
                    "instance", "exposed_internet", False, label="ScalewayInstance"
                ),
            ),
        ),
    ),
)

# The load balancer verdict is written first, then the EXPOSE edges that depend on it, then
# the instance job that reads those edges for its `lb` path.
#
# These use run_typed_analysis_job rather than run_typed_analysis_and_ensure_deps because
# Scaleway has no selective intra-module sync (no scaleway_requested_syncs), so every
# resource these jobs read is always synced. Add dep-checking if that ever changes.
SCALEWAY_EXPOSURE_JOBS = (
    SCALEWAY_LOADBALANCER_EXPOSURE,
    SCALEWAY_LB_EXPOSE_EDGES,
    SCALEWAY_INSTANCE_EXPOSURE,
    SCALEWAY_DATABASE_EXPOSURE,
    SCALEWAY_SERVERLESS_EXPOSURE,
)
