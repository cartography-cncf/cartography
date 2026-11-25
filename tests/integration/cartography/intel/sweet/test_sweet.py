import pytest

import cartography.intel.sweet
from cartography.client.core.tx import load
from cartography.config import Config
from cartography.intel.aws.organizations import load_aws_account_nodes_from_config
from cartography.models.aws.ecr.image import ECRImageSchema
from cartography.models.aws.route53.dnsrecord import AWSDNSRecordSchema
from tests.data.sweet import ACCOUNT_ID
from tests.data.sweet import API_KEY
from tests.data.sweet import API_SECRET
from tests.data.sweet import ATTACK_CHAIN_DOMAIN
from tests.data.sweet import ATTACK_CHAIN_ID
from tests.data.sweet import ATTACK_CHAINS
from tests.data.sweet import AWS_ACCOUNTS
from tests.data.sweet import AWS_ORGANIZATIONS
from tests.data.sweet import CVE_ID
from tests.data.sweet import CVE_VULNERABILITY_ID
from tests.data.sweet import GHSA_ID
from tests.data.sweet import GHSA_VULNERABILITY_ID
from tests.data.sweet import IMAGE_DIGEST
from tests.data.sweet import ORG_MANAGEMENT_ACCOUNT_ID
from tests.data.sweet import TENANT_ID
from tests.data.sweet import VULNERABILITIES
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
OTHER_TENANT_ID = "other-example-tenant"
DNS_RECORD_ID = f"Z1+{ATTACK_CHAIN_DOMAIN}+A"


def _delete_test_data(neo4j_session) -> None:
    neo4j_session.run(
        """
        MATCH (n)
        WHERE n:SweetTenant
           OR n:SweetAWSAccount
           OR n:SweetAWSOrganization
           OR n:SweetVulnerability
           OR n:SweetAttackChain
           OR (n:AWSAccount AND n.id IN $account_ids)
           OR (n:AWSECRImage AND n.id = $image_id)
           OR (n:AWSDNSRecord AND n.id = $dns_record_id)
           OR (n:CVE AND n.id = $cve_id)
        DETACH DELETE n
        """,
        account_ids=[ACCOUNT_ID, ORG_MANAGEMENT_ACCOUNT_ID],
        image_id=IMAGE_DIGEST,
        dns_record_id=DNS_RECORD_ID,
        cve_id=CVE_ID,
    )
    neo4j_session.run(
        "MATCH (n:ModuleSyncMetadata) WHERE n.id IN $ids DETACH DELETE n",
        ids=[
            f"SweetTenant_{TENANT_ID}_SweetData",
            f"SweetTenant_{OTHER_TENANT_ID}_SweetData",
        ],
    )


@pytest.fixture(autouse=True)
def isolate_sweet_test_data(neo4j_session):
    _delete_test_data(neo4j_session)
    yield
    _delete_test_data(neo4j_session)


def _config(update_tag: int = TEST_UPDATE_TAG, tenant_id: str | None = TENANT_ID):
    return Config(
        neo4j_uri="bolt://localhost:7687",
        update_tag=update_tag,
        sweet_api_key=API_KEY,
        sweet_api_secret=API_SECRET,
        sweet_tenant_id=tenant_id,
    )


def _patch_sweet_api(
    mocker,
    vulnerabilities=VULNERABILITIES,
    attack_chains=ATTACK_CHAINS,
):
    mocker.patch("cartography.intel.sweet.api.authenticate")
    mocker.patch(
        "cartography.intel.sweet.aws.get_accounts",
        return_value=AWS_ACCOUNTS,
    )
    mocker.patch(
        "cartography.intel.sweet.aws.get_organizations",
        return_value=AWS_ORGANIZATIONS,
    )
    mocker.patch(
        "cartography.intel.sweet.vulnerabilities.get",
        return_value=[vulnerabilities],
    )
    mocker.patch(
        "cartography.intel.sweet.attack_chains.get",
        return_value=[attack_chains],
    )


def _seed_aws_accounts(neo4j_session) -> None:
    load_aws_account_nodes_from_config(
        neo4j_session,
        [
            {"id": ACCOUNT_ID, "name": "workload", "foreign": None},
            {"id": ORG_MANAGEMENT_ACCOUNT_ID, "name": "management", "foreign": None},
        ],
        TEST_UPDATE_TAG,
    )


def _seed_cve(neo4j_session) -> None:
    neo4j_session.run(
        "MERGE (c:CVE {id: $id}) SET c.lastupdated = $update_tag",
        id=CVE_ID,
        update_tag=TEST_UPDATE_TAG,
    )


def _seed_ecr_image(neo4j_session) -> None:
    load(
        neo4j_session,
        ECRImageSchema(),
        [
            {
                "imageDigest": IMAGE_DIGEST,
                "digest": IMAGE_DIGEST,
                "type": "image",
            },
        ],
        lastupdated=TEST_UPDATE_TAG,
        Region="us-east-1",
        AWS_ID=ACCOUNT_ID,
    )


def _seed_dns_record(neo4j_session) -> None:
    load(
        neo4j_session,
        AWSDNSRecordSchema(),
        [
            {
                "id": DNS_RECORD_ID,
                "name": ATTACK_CHAIN_DOMAIN,
                "name_normalized": ATTACK_CHAIN_DOMAIN,
                "type": "A",
                "value": "203.0.113.10",
                "zoneid": "Z1",
            },
        ],
        lastupdated=TEST_UPDATE_TAG,
        AWS_ID=ACCOUNT_ID,
    )


def test_sync_links_aws_connections_to_monitored_accounts(neo4j_session, mocker):
    # Arrange
    _seed_aws_accounts(neo4j_session)
    _patch_sweet_api(mocker)

    # Act
    cartography.intel.sweet.start_sweet_ingestion(neo4j_session, _config())

    # Assert
    assert check_nodes(neo4j_session, "SweetTenant", ["id"]) == {(TENANT_ID,)}
    assert check_nodes(
        neo4j_session,
        "SweetAWSAccount",
        ["id", "account_id", "role_arn", "enabled"],
    ) == {
        (
            f"{TENANT_ID}:{ACCOUNT_ID}",
            ACCOUNT_ID,
            f"arn:aws:iam::{ACCOUNT_ID}:role/SweetSecurityRole",
            True,
        ),
    }
    assert check_nodes(
        neo4j_session,
        "SweetAWSOrganization",
        ["id", "management_account_id"],
    ) == {
        (f"{TENANT_ID}:{ORG_MANAGEMENT_ACCOUNT_ID}", ORG_MANAGEMENT_ACCOUNT_ID),
    }
    assert check_rels(
        neo4j_session,
        "SweetAWSAccount",
        "account_id",
        "AWSAccount",
        "id",
        "MONITORS",
    ) == {(ACCOUNT_ID, ACCOUNT_ID)}
    assert check_rels(
        neo4j_session,
        "SweetAWSOrganization",
        "management_account_id",
        "AWSAccount",
        "id",
        "MONITORS",
    ) == {(ORG_MANAGEMENT_ACCOUNT_ID, ORG_MANAGEMENT_ACCOUNT_ID)}
    assert check_rels(
        neo4j_session,
        "SweetTenant",
        "id",
        "SweetAWSAccount",
        "account_id",
        "RESOURCE",
    ) == {(TENANT_ID, ACCOUNT_ID)}


def test_sync_keeps_one_connection_per_tenant_for_a_shared_account(
    neo4j_session,
    mocker,
):
    # Arrange
    _seed_aws_accounts(neo4j_session)
    _patch_sweet_api(mocker)

    # Act
    cartography.intel.sweet.start_sweet_ingestion(neo4j_session, _config())
    cartography.intel.sweet.start_sweet_ingestion(
        neo4j_session,
        _config(tenant_id=OTHER_TENANT_ID),
    )

    # Assert
    assert check_rels(
        neo4j_session,
        "SweetTenant",
        "id",
        "SweetAWSAccount",
        "id",
        "RESOURCE",
    ) == {
        (TENANT_ID, f"{TENANT_ID}:{ACCOUNT_ID}"),
        (OTHER_TENANT_ID, f"{OTHER_TENANT_ID}:{ACCOUNT_ID}"),
    }
    assert check_rels(
        neo4j_session,
        "SweetAWSAccount",
        "id",
        "AWSAccount",
        "id",
        "MONITORS",
    ) == {
        (f"{TENANT_ID}:{ACCOUNT_ID}", ACCOUNT_ID),
        (f"{OTHER_TENANT_ID}:{ACCOUNT_ID}", ACCOUNT_ID),
    }


def test_sync_does_not_store_aws_external_id(neo4j_session, mocker):
    # Arrange
    _patch_sweet_api(mocker)

    # Act
    cartography.intel.sweet.start_sweet_ingestion(neo4j_session, _config())

    # Assert
    result = neo4j_session.run(
        """
        MATCH (n)
        WHERE n:SweetAWSAccount OR n:SweetAWSOrganization
        RETURN
            count(n) AS connections,
            sum(
                CASE WHEN any(key IN keys(n) WHERE toLower(key) CONTAINS 'external')
                THEN 1 ELSE 0 END
            ) AS connections_with_external_id
        """,
    ).single()
    assert result["connections"] == 2
    assert result["connections_with_external_id"] == 0


def test_sync_links_vulnerabilities_to_cve_and_image(neo4j_session, mocker):
    # Arrange
    _seed_aws_accounts(neo4j_session)
    _seed_cve(neo4j_session)
    _seed_ecr_image(neo4j_session)
    _patch_sweet_api(mocker)

    # Act
    cartography.intel.sweet.start_sweet_ingestion(neo4j_session, _config())

    # Assert
    assert check_nodes(
        neo4j_session,
        "SweetVulnerability",
        ["id", "vulnerability_id", "cve_id", "status", "last_loaded"],
    ) == {
        (CVE_VULNERABILITY_ID, CVE_ID, CVE_ID, "open", "2026-11-14T12:00:00Z"),
        (GHSA_VULNERABILITY_ID, GHSA_ID, None, "ignored", None),
    }
    assert check_rels(
        neo4j_session,
        "SweetVulnerability",
        "id",
        "CVE",
        "id",
        "LINKED_TO",
    ) == {(CVE_VULNERABILITY_ID, CVE_ID)}
    assert check_rels(
        neo4j_session,
        "SweetVulnerability",
        "id",
        "AWSECRImage",
        "id",
        "AFFECTS",
    ) == {(CVE_VULNERABILITY_ID, IMAGE_DIGEST)}
    assert check_rels(
        neo4j_session,
        "SweetTenant",
        "id",
        "SweetVulnerability",
        "id",
        "RESOURCE",
    ) == {
        (TENANT_ID, CVE_VULNERABILITY_ID),
        (TENANT_ID, GHSA_VULNERABILITY_ID),
    }


def test_sync_labels_only_cve_backed_vulnerabilities_as_cve(neo4j_session, mocker):
    # Arrange
    _patch_sweet_api(mocker)

    # Act
    cartography.intel.sweet.start_sweet_ingestion(neo4j_session, _config())

    # Assert
    assert check_nodes(
        neo4j_session,
        "SweetVulnerability:CVE",
        ["id", "_ont_cve_id", "_ont_base_severity", "_ont_vuln_status"],
    ) == {
        (CVE_VULNERABILITY_ID, CVE_ID, "critical", "open"),
    }


def test_sync_links_attack_chains_to_dns_records(neo4j_session, mocker):
    # Arrange
    _seed_aws_accounts(neo4j_session)
    _seed_dns_record(neo4j_session)
    _patch_sweet_api(mocker)

    # Act
    cartography.intel.sweet.start_sweet_ingestion(neo4j_session, _config())

    # Assert
    assert check_nodes(
        neo4j_session,
        "SweetAttackChain",
        ["id", "domain", "execution_name", "_ont_status", "_ont_type"],
    ) == {
        (ATTACK_CHAIN_ID, ATTACK_CHAIN_DOMAIN, None, "open", "attack_chain"),
    }
    assert check_rels(
        neo4j_session,
        "SweetAttackChain",
        "id",
        "AWSDNSRecord",
        "id",
        "AFFECTS",
    ) == {(ATTACK_CHAIN_ID, DNS_RECORD_ID)}
    result = neo4j_session.run(
        "MATCH (n:SweetAttackChain:SecurityIssue) RETURN n.id AS id, n.endpoints AS endpoints",
    ).single()
    assert result["id"] == ATTACK_CHAIN_ID
    assert result["endpoints"] == ["GET /v1/orders/{id}"]


def test_sync_removes_findings_missing_from_a_later_sync(neo4j_session, mocker):
    # Arrange
    _patch_sweet_api(mocker)
    cartography.intel.sweet.start_sweet_ingestion(neo4j_session, _config())
    _patch_sweet_api(mocker, vulnerabilities=VULNERABILITIES[:1], attack_chains=[])

    # Act
    cartography.intel.sweet.start_sweet_ingestion(
        neo4j_session,
        _config(update_tag=TEST_UPDATE_TAG + 1),
    )

    # Assert
    assert check_nodes(neo4j_session, "SweetVulnerability", ["id"]) == {
        (CVE_VULNERABILITY_ID,),
    }
    assert check_nodes(neo4j_session, "SweetAttackChain", ["id"]) == set()


def test_sync_skips_when_sweet_is_not_configured(neo4j_session, mocker):
    # Arrange
    _patch_sweet_api(mocker)
    config = Config(neo4j_uri="bolt://localhost:7687", update_tag=TEST_UPDATE_TAG)

    # Act
    cartography.intel.sweet.start_sweet_ingestion(neo4j_session, config)

    # Assert
    assert check_nodes(neo4j_session, "SweetTenant", ["id"]) == set()
    assert check_nodes(neo4j_session, "SweetVulnerability", ["id"]) == set()
