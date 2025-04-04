import unittest
import os
import requests
from neo4j import GraphDatabase

# Test Msft365BasicFunctionality
#   Attempts to authenticate with Microsoft Graph API
#   Verifies that the authentication succeeds (status code 200)
#   Confirms that an access token is returned
#   Stores the token for potential use in other tests

class TestMsft365BasicFunctionality(unittest.TestCase):
    def setUp(self):
        # Get credentials from environment variables
        self.tenant_id = os.environ.get('Msft365_TENANT_ID')
        self.client_id = os.environ.get('Msft365_CLIENT_ID')
        self.client_secret = os.environ.get('Msft365_CLIENT_SECRET')
        
        # Neo4j connection parameters - use container name instead of localhost
        self.neo4j_uri = os.environ.get('NEO4J_URI', 'bolt://neo4j:7687')
        self.neo4j_user = os.environ.get('NEO4J_USER', 'neo4j')
        self.neo4j_password = os.environ.get('NEO4J_PASSWORD', 'password')
        
        # Skip test if credentials are not available
        if not all([self.tenant_id, self.client_id, self.client_secret]):
            self.skipTest("Msft365 credentials not available")
        
        # Print credential info for debugging (mask sensitive parts)
        print(f"Testing with tenant ID: {self.tenant_id[:4]}...{self.tenant_id[-4:]}")
        print(f"Client ID: {self.client_id[:4]}...{self.client_id[-4:]}")
        print(f"Secret length: {len(self.client_secret)} chars")
    
    def test_can_authenticate_with_graph_api(self):
        """Test that we can authenticate with Microsoft Graph API."""
        url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
        payload = {
            "client_id": self.client_id,
            "scope": "https://graph.microsoft.com/.default",
            "client_secret": self.client_secret,
            "grant_type": "client_credentials",
        }
        
        response = requests.post(url, data=payload)
        print(f"Auth response status: {response.status_code}")
        if response.status_code != 200:
            print(f"Auth error: {response.text}")
        
        self.assertEqual(response.status_code, 200, msg=f"Authentication failed: {response.text}")
        self.assertIn("access_token", response.json())
        
        # Store token for other tests
        self.access_token = response.json().get("access_token")

        

        return self.access_token

    #Test that we can fetch users from Microsoft Graph API.
    def test_can_fetch_users(self):
        # First authenticate to get token
        access_token = self.test_can_authenticate_with_graph_api()
        
        # Set up request headers to authenticate and format API requests to the Microsoft Graph API
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # Make request to users endpoint
        url = "https://graph.microsoft.com/v1.0/users?$top=5"
        response = requests.get(url, headers=headers)
        
        # Print response info for debugging
        print(f"Users response status: {response.status_code}")
        if response.status_code != 200:
            print(f"Error fetching users: {response.text}")
        
        # Assert response is successful
        self.assertEqual(response.status_code, 200)
        
        # Get users from response
        users = response.json().get("value", [])
        
        # Assert users were returned
        self.assertIsInstance(users, list)
        print(f"Retrieved {len(users)} users")
        
        # Print some user details
        for user in users[:3]:  # Show first 3 users
            print(f"  - {user.get('displayName')} ({user.get('userPrincipalName')})")
        
        return users
   
    # Test that we can fetch organizational units from Microsoft Graph API
    def test_can_fetch_organizational_units(self):
        
        # First authenticate to get token
        access_token = self.test_can_authenticate_with_graph_api()
        
        # Set up request headers
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # Make request to administrative units endpoint
        url = "https://graph.microsoft.com/v1.0/directory/administrativeUnits"
        response = requests.get(url, headers=headers)
        
        # Print response info for debugging
        print(f"Administrative units response status: {response.status_code}")
        
        # This API might return 403 if you don't have permissions or 404 if not available in your tenant
        if response.status_code == 403:
            print("Access denied to administrative units. This requires specific permissions.")
            self.skipTest("No access to administrative units")
        elif response.status_code == 404:
            print("Administrative units endpoint not found. This may not be available in your tenant.")
            self.skipTest("Administrative units not available")
        elif response.status_code != 200:
            print(f"Error fetching administrative units: {response.text}")
        
        # Assert response is successful
        self.assertEqual(response.status_code, 200)
        
        # Get organizational units from response
        org_units = response.json().get("value", [])
        
        # Assert organizational units were returned
        self.assertIsInstance(org_units, list)
        print(f"Retrieved {len(org_units)} organizational units")
        
        # Print some organizational unit details
        for ou in org_units[:3]:  # Show first 3 OUs
            print(f"  - {ou.get('displayName')} ({ou.get('description', 'No description')})")
        
        return org_units
    
    def test_can_fetch_groups(self):
        # First authenticate to get token
        access_token = self.test_can_authenticate_with_graph_api()
        
        # Set up request headers
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # Make request to groups endpoint
        url = "https://graph.microsoft.com/v1.0/groups?$top=5"
        response = requests.get(url, headers=headers)
        
        # Print response info for debugging
        print(f"Groups response status: {response.status_code}")
        if response.status_code != 200:
            print(f"Error fetching groups: {response.text}")
        
        # Assert response is successful
        self.assertEqual(response.status_code, 200)
        
        # Get groups from response
        groups = response.json().get("value", [])
        
        # Assert groups were returned
        self.assertIsInstance(groups, list)
        print(f"Retrieved {len(groups)} groups")
        
        # Print some group details
        for group in groups[:3]:  # Show first 3 groups
            print(f" - {group.get('displayName')} ({group.get('id')})")
        
        return groups


    #Test that we can fetch members of a group.
    def test_can_fetch_group_members(self):
    
        # First fetch groups to get a group ID
        groups = self.test_can_fetch_groups()
        
        # Skip test if no groups were found
        if not groups:
            self.skipTest("No groups available to test membership")
        
        # Get the first group's ID
        group_id = groups[0].get("id")
        group_name = groups[0].get("displayName")
        
        # Get access token
        access_token = self.test_can_authenticate_with_graph_api()
        
        # Set up request headers
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # Make request to group members endpoint
        url = f"https://graph.microsoft.com/v1.0/groups/{group_id}/members"
        response = requests.get(url, headers=headers)
        
        # Print response info for debugging
        print(f"Group members response status: {response.status_code}")
        if response.status_code != 200:
            print(f"Error fetching group members: {response.text}")
        
        # Assert response is successful
        self.assertEqual(response.status_code, 200)
        
        # Get members from response
        members = response.json().get("value", [])
        
        # Assert members were returned (might be empty if group has no members)
        self.assertIsInstance(members, list)
        print(f"Retrieved {len(members)} members for group '{group_name}'")
        
        # Print some member details
        for member in members[:3]:  # Show first 3 members
            print(f"  - {member.get('displayName')}")
        
        return members

    # Test that we can fetch devices from Microsoft Graph API
    def test_can_fetch_devices(self):
    
        # First authenticate to get token
        access_token = self.test_can_authenticate_with_graph_api()
        
        # Set up request headers
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        # Make request to devices endpoint
        url = "https://graph.microsoft.com/v1.0/devices?$top=5"
        response = requests.get(url, headers=headers)

        # Print response info for debugging
        print(f"Devices response status: {response.status_code}")
        if response.status_code == 403:
            print("Access denied to devices. Requires Device.Read.All permission")
            self.skipTest("No device read permissions")
        elif response.status_code != 200:
            print(f"Error fetching devices: {response.text}")

        self.assertEqual(response.status_code, 200)
        
        # Get devices from response
        devices = response.json().get("value", [])
        self.assertIsInstance(devices, list)
        print(f"Retrieved {len(devices)} devices")

        # Print device details
        for device in devices[:3]:  # Show first 3 devices
            print(f" - {device.get('displayName')} ({device.get('operatingSystem')})")
        return devices

        

