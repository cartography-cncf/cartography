from unittest.mock import patch

import neo4j

import cartography.intel.aws.iam
import tests.data.aws.iam.server_certificates
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "123456789012"
TEST_UPDATE_TAG = 123456789


@patch("cartography.intel.aws.iam.get_server_certificates")
def test_sync_server_certificates(mock_get_server_certificates, neo4j_session):

    neo4j_session.run("MERGE (a:AWSAccount {id: $Account})", Account=TEST_ACCOUNT_ID)
    mock_get_server_certificates.return_value = (
        tests.data.aws.iam.server_certificates.LIST_SERVER_CERTIFICATES_RESPONSE[
            "ServerCertificateMetadataList"
        ]
    )

    cartography.intel.aws.iam.sync_server_certificates(
        neo4j_session,
        "dummy_session",
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"AWS_ID": TEST_ACCOUNT_ID},
    )

    assert check_nodes(
        neo4j_session,
        "AWSServerCertificate",
        ["id", "server_certificate_name", "expiration"],
    ) == {("ASCATEST", "test-cert", neo4j.time.DateTime(2024, 1, 1, 0, 0, 0, 0))}

    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "AWSServerCertificate",
        "server_certificate_id",
        "RESOURCE",
    ) == {(TEST_ACCOUNT_ID, "ASCATEST")}
