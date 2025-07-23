import cartography.intel.gcp.dns
import tests.data.gcp.dns


def test_load_dns_zones(mocker):
    mock_session = mocker.Mock()
    zones = tests.data.gcp.dns.DNS_ZONES
    project_id = "project-x"
    update_tag = 42
    cartography.intel.gcp.dns.load_dns_zones(mock_session, zones, project_id, update_tag)
    mock_session.run.assert_called_once()
    query = mock_session.run.call_args[0][0]
    params = mock_session.run.call_args[1]
    assert "UNWIND $records as record" in query
    assert "MERGE(zone:GCPDNSZone{id:record.id})" in query
    assert params["records"] == zones


def test_load_rrs(mocker):
   
    mock_session = mocker.Mock()
    rrs = tests.data.gcp.dns.DNS_RRS
    project_id = "project-x"
    update_tag = 42
    cartography.intel.gcp.dns.load_rrs(mock_session, rrs, project_id, update_tag)
    mock_session.run.assert_called_once()
    query = mock_session.run.call_args[0][0]
    params = mock_session.run.call_args[1]
    assert "UNWIND $records as record" in query
    assert "MERGE(rrs:GCPRecordSet{id:record.name})" in query
    assert params["records"] == rrs


def test_load_dns_zones_single_zone(mocker):
  
    mock_session = mocker.Mock()
    single_zone = [tests.data.gcp.dns.DNS_ZONES[0]]
    project_id = "project-x"
    update_tag = 42
    cartography.intel.gcp.dns.load_dns_zones(mock_session, single_zone, project_id, update_tag)
    mock_session.run.assert_called_once()
    query = mock_session.run.call_args[0][0]
    assert "UNWIND $records as record" in query
    assert "MERGE(zone:GCPDNSZone{id:record.id})" in query


def test_load_rrs_single_record(mocker):
    mock_session = mocker.Mock()
    single_rr = [tests.data.gcp.dns.DNS_RRS[0]]
    project_id = "project-x"
    update_tag = 42
    cartography.intel.gcp.dns.load_rrs(mock_session, single_rr, project_id, update_tag)
    mock_session.run.assert_called_once()
    query = mock_session.run.call_args[0][0]
    assert "UNWIND $records as record" in query
    assert "MERGE(rrs:GCPRecordSet{id:record.name})" in query
