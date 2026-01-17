import neo4j
from unittest.mock import MagicMock
from cartography.intel.microsoft_defender import machines

# This test ensures your module works without needing real API keys
def test_sync_machines(neo4j_session: neo4j.Session):
    # 1. Setup Mock Data (The same data you had in the JSON)
    mock_data = [
        {
            "id": "machine-1",
            "computerDnsName": "laptop-01",
            "riskScore": "High",
            "healthStatus": "Active",
            "osPlatform": "Windows10",
            "aadDeviceId": "azure-vm-1" # Bridging ID
        },
        {
            "id": "machine-2",
            "computerDnsName": "server-01",
            "riskScore": "Low",
            "aadDeviceId": "azure-vm-99"
        }
    ]
    
    # 2. Mock the Client so we don't hit the real API
    mock_client = MagicMock()
    mock_client.get_machines.return_value = mock_data
    
    # 3. Define Test Context
    tenant_id = "test-tenant-123"
    update_tag = 123456
    common_params = {"UPDATE_TAG": update_tag, "tenant_id": tenant_id}
    
    # 4. Run Sync
    machines.sync(neo4j_session, mock_client, tenant_id, update_tag, common_params)
    
    # 5. Verify Ingestion (Did the nodes appear?)
    result = neo4j_session.run("MATCH (m:MDEDevice) RETURN count(m) as count").single()
    assert result['count'] == 2
    
    # 6. Verify Properties
    check_node = neo4j_session.run("MATCH (m:MDEDevice {id: 'machine-1'}) RETURN m.risk_score, m.name").single()
    assert check_node['m.risk_score'] == "High"
    assert check_node['m.name'] == "laptop-01"