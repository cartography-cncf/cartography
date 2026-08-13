"""Scaleway internet exposure, for the paths that span several node types.

Only instances need analysis: their exposure depends on security-group rules, Public Gateway
PAT rules and load balancer backends, which are three separate syncs. Every other Scaleway
resource decides its own exposure from one API response, so it sets exposed_internet in
transform() instead: see the load balancers, databases, serverless, object storage, container
registry, Kapsule and bare metal intel modules.

These jobs are unscoped: the Scaleway sync is organization-wide and single-pass, so an
unscoped cleanup has no other project's data to remove. They also use
run_typed_analysis_job rather than run_typed_analysis_and_ensure_deps, because Scaleway has
no selective intra-module sync like aws_requested_syncs or gcp_requested_syncs, so every
resource they read is always present. Add dep-checking if that ever changes.
"""

from cartography.graph.analysis import AddRelationship
from cartography.graph.analysis import AddToSet
from cartography.graph.analysis import AnalysisJob
from cartography.graph.analysis import AnalysisStatement
from cartography.graph.analysis import SetProperty

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
              AND NOT coalesce(instance.state, 'running') IN ['stopped', 'stopped_in_place']
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
                "A Security Group whose inbound_default_policy is 'accept' lets through any "
                "inbound traffic no rule matched, so a public-IP instance in such a group is "
                "reachable even with no explicit 0.0.0.0/0 rule. Without this the instance "
                "falls through to the final pass and is persisted as not exposed, which is "
                "the one direction this verdict must not get wrong. Ordering between an "
                "accept default and an explicit drop is not modelled, so this errs towards "
                "reporting exposure."
            ),
            match="""
            MATCH (instance:ScalewayInstance)-[:MEMBER_OF_SCALEWAY_SECURITY_GROUP]->(sg:ScalewaySecurityGroup)
            WHERE size(coalesce(instance.public_ips, [])) > 0
              AND NOT coalesce(instance.state, 'running') IN ['stopped', 'stopped_in_place']
              AND sg.inbound_default_policy = 'accept'
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
            match="""
            MATCH (:ScalewayLoadBalancer {exposed_internet: true})-[:EXPOSE]->(instance:ScalewayInstance)
            WHERE NOT coalesce(instance.state, 'running') IN ['stopped', 'stopped_in_place']
            """,
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
            match="MATCH (instance:ScalewayInstance) WHERE instance.exposed_internet IS NULL",
            effects=(
                SetProperty(
                    "instance", "exposed_internet", False, label="ScalewayInstance"
                ),
            ),
        ),
    ),
)

# The EXPOSE edges come first, since the instance job reads them for its `lb` path. The
# load balancer's own exposed_internet is already set by its transform, so nothing here has
# to produce it.
SCALEWAY_EXPOSURE_JOBS = (
    SCALEWAY_LB_EXPOSE_EDGES,
    SCALEWAY_INSTANCE_EXPOSURE,
)
