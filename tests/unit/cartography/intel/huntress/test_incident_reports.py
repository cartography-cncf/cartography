from cartography.intel.huntress.incident_reports import transform
from tests.data.huntress.incident_reports import INCIDENT_REPORTS


def test_transform_summarizes_the_inlined_remediations() -> None:
    reports = {report["id"]: report for report in transform(INCIDENT_REPORTS)}

    assert reports[4001]["remediation_count"] == 2
    assert reports[4001]["remediation_types"] == ["containment", "manual"]
    assert reports[4002]["remediation_count"] == 0
    assert reports[4002]["remediation_types"] == []


def test_transform_handles_a_report_without_remediations() -> None:
    reports = {report["id"]: report for report in transform(INCIDENT_REPORTS)}

    assert reports[4003]["remediation_count"] is None
    assert reports[4003]["remediation_types"] == []


def test_transform_keeps_the_indicator_types_but_drops_the_counts_map() -> None:
    """Neo4j cannot store a map as a node property, so only the type list survives."""
    reports = {report["id"]: report for report in transform(INCIDENT_REPORTS)}

    assert reports[4001]["indicator_types"] == ["footholds", "process_detections"]
    assert "indicator_counts" not in reports[4001]


def test_transform_keeps_the_agent_link_optional() -> None:
    reports = {report["id"]: report for report in transform(INCIDENT_REPORTS)}

    assert reports[4001]["agent_id"] == 3001
    # An identity incident is raised against a tenant, not an endpoint.
    assert reports[4003]["agent_id"] is None
