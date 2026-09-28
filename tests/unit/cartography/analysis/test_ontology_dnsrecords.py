from cartography.analysis.ontology.analysis import DNS_RECORD_LINKING_JOBS
from cartography.graph.analysisbuilder import to_graph_job
from cartography.models.aws.route53.dnsrecord import AWSDNSRecordSchema

MATCH_GUARD = "NOT dns:AWSDNSRecord"
CLEANUP_GUARD = "NOT source:AWSDNSRecord"


def _route53_owned_targets() -> set[str]:
    """
    The target labels route53 itself writes DNS_POINTS_TO edges to, read from the schema so
    this cannot drift when a relationship is added to or removed from the route53 loader.
    """
    return {
        rel.target_node_label
        for rel in AWSDNSRecordSchema().other_relationships.rels
        if rel.rel_label == "DNS_POINTS_TO"
    }


def test_ontology_dns_merges_leave_route53_owned_edges_untouched():
    """
    Route53 owns some DNS_POINTS_TO edges and stamps them with the AWS run's update tag. For
    those targets the ontology jobs must neither delete the edge nor refresh its lastupdated,
    so AWSDNSRecord has to be excluded from the MERGE's match and not only from the cleanup's
    WHERE. A cleanup-only guard would leave a separate ontology run silently re-stamping a
    provider-owned edge with its own tag.
    """
    owned = _route53_owned_targets()
    checked = set()

    for job in DNS_RECORD_LINKING_JOBS:
        for statement in job.statements:
            owned_targets = {
                effect.target_label for effect in statement.effects
            } & owned
            if not owned_targets:
                continue
            # A statement matching only GCPRecordSet can never reach an AWSDNSRecord.
            if "(dns:GCPRecordSet)" in statement.match:
                continue
            checked |= owned_targets
            assert MATCH_GUARD in statement.match, (
                f"{job.short_name} merges DNS_POINTS_TO to {sorted(owned_targets)}, which "
                f"route53 owns, without excluding AWSDNSRecord from its match, so it "
                f"re-stamps route53-owned edges with the ontology run's update tag."
            )

    assert checked, "no ontology DNS job targets a route53-owned label; test is vacuous"


def test_ontology_dns_cleanups_guard_route53_owned_edges():
    """The companion guard: the cleanup must not delete what route53 owns either."""
    owned = _route53_owned_targets()
    checked = set()

    for job in DNS_RECORD_LINKING_JOBS:
        for statement in to_graph_job(job).statements:
            if "DELETE r" not in statement.query:
                continue
            # A cleanup scoped to GCPRecordSet sources can never reach an AWSDNSRecord. No job
            # emits one today, since the GCP statements declare the same guarded DNSRecord
            # effect as the generic ones and dedupe into a single delete, but such a cleanup
            # would be safe if one came back.
            if "(source:GCPRecordSet)" in statement.query:
                continue
            for target in owned:
                if f"(target:{target})" not in statement.query:
                    continue
                checked.add(target)
                assert CLEANUP_GUARD in statement.query, (
                    f"{job.short_name} deletes DNS_POINTS_TO to {target} from a source that "
                    f"can be an AWSDNSRecord without the {CLEANUP_GUARD!r} guard, so it "
                    f"removes route53-owned edges whenever the update tags differ."
                )

    assert (
        checked
    ), "no ontology DNS cleanup targets a route53-owned label; test is vacuous"
