import neo4j
from unittest.mock import MagicMock
from cartography.intel.microsoft_defender import machines

# 1. Connect - Double check your password!
driver = neo4j.GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password")) 

# 2. Mock Data 
mock_data = [{
    "id": "machine-1",
    "computerDnsName": "laptop-01",
    "riskScore": "High",
    "healthStatus": "Active",
    "aadDeviceId": "azure-vm-1" 
}]

# 3. Execution
with driver.session() as session:
    print("Creating baseline Azure VM...")
    session.run("MERGE (v:AzureVirtualMachine{id: 'azure-vm-1', name: 'prod-web-app'})")
    
    print("Running MDE Ingestion...")
    # This calls your actual logic
    machines.sync(
        session, 
        MagicMock(get_machines=MagicMock(return_value=mock_data)), 
        "test-tenant", 
        123, 
        {"UPDATE_TAG": 123, "tenant_id": "test-tenant"}
    )
    
print("Sync complete! Check Neo4j now.")
driver.close()