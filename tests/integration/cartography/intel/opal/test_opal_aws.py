from cartography.intel.opal.opal_aws import load_opal_resources
from tests.data.opal.opal_aws import RESOURCE_DATA
from tests.integration.util import check_nodes


def test_load_opal_resources(neo4j_session):
    # Act: Call the function to load the Opal resources
    load_opal_resources(neo4j_session, RESOURCE_DATA, 1234567890)

    # Assert: Verify that the Opal resources are correctly loaded
    assert check_nodes(neo4j_session, 'OpalResource', ['resource_id']) is not None
