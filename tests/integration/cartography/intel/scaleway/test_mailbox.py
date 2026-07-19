from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.scaleway.mailbox.domains
import cartography.intel.scaleway.mailbox.mailboxes
from tests.data.scaleway.mailbox import SCALEWAY_MAILBOX_DOMAINS
from tests.data.scaleway.mailbox import SCALEWAY_MAILBOXES
from tests.data.scaleway.mailbox import TEST_MAILBOX_DOMAIN_ID
from tests.data.scaleway.mailbox import TEST_MAILBOX_EMAIL
from tests.data.scaleway.mailbox import TEST_MAILBOX_ID
from tests.integration.cartography.intel.scaleway.test_projects import (
    _ensure_local_neo4j_has_test_projects_and_orgs,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_ORG_ID = "0681c477-fbb9-4820-b8d6-0eef10cfcd6d"
TEST_PROJECT_ID = "0681c477-fbb9-4820-b8d6-0eef10cfcd6d"


def _ensure_local_neo4j_has_test_mailbox_domains(neo4j_session):
    data = cartography.intel.scaleway.mailbox.domains.transform_domains(
        SCALEWAY_MAILBOX_DOMAINS
    )
    cartography.intel.scaleway.mailbox.domains.load_domains(
        neo4j_session, data, TEST_UPDATE_TAG
    )


@patch.object(
    cartography.intel.scaleway.mailbox.domains,
    "get",
    return_value=SCALEWAY_MAILBOX_DOMAINS,
)
def test_load_scaleway_mailbox_domains(_mock_get, neo4j_session):
    # Arrange
    client = Mock()
    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG, "ORG_ID": TEST_ORG_ID}
    _ensure_local_neo4j_has_test_projects_and_orgs(neo4j_session)

    # Act
    cartography.intel.scaleway.mailbox.domains.sync(
        neo4j_session,
        client,
        common_job_parameters,
        projects_id=[TEST_PROJECT_ID],
        update_tag=TEST_UPDATE_TAG,
    )

    # Assert Mailbox domains exist
    expected_nodes = {
        (TEST_MAILBOX_DOMAIN_ID, "example.com", "ready", 10),
    }
    assert (
        check_nodes(
            neo4j_session,
            "ScalewayMailboxDomain",
            ["id", "name", "status", "mailbox_total_count"],
        )
        == expected_nodes
    )

    # Assert Mailbox domains are linked to the project
    expected_rels = {
        (TEST_MAILBOX_DOMAIN_ID, TEST_PROJECT_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "ScalewayMailboxDomain",
            "id",
            "ScalewayProject",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )


@patch.object(
    cartography.intel.scaleway.mailbox.mailboxes,
    "get",
    return_value=(SCALEWAY_MAILBOX_DOMAINS, SCALEWAY_MAILBOXES),
)
def test_load_scaleway_mailboxes(_mock_get, neo4j_session):
    # Arrange
    client = Mock()
    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG, "ORG_ID": TEST_ORG_ID}
    _ensure_local_neo4j_has_test_projects_and_orgs(neo4j_session)
    _ensure_local_neo4j_has_test_mailbox_domains(neo4j_session)

    # Act
    cartography.intel.scaleway.mailbox.mailboxes.sync(
        neo4j_session,
        client,
        common_job_parameters,
        projects_id=[TEST_PROJECT_ID],
        update_tag=TEST_UPDATE_TAG,
    )

    # Assert Mailboxes exist
    expected_nodes = {
        (TEST_MAILBOX_ID, TEST_MAILBOX_EMAIL, "ready"),
    }
    assert (
        check_nodes(
            neo4j_session,
            "ScalewayMailbox",
            ["id", "email", "status"],
        )
        == expected_nodes
    )

    # Assert Mailboxes are linked to the project
    expected_project_rels = {
        (TEST_MAILBOX_ID, TEST_PROJECT_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "ScalewayMailbox",
            "id",
            "ScalewayProject",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_project_rels
    )

    # Assert Mailboxes are linked to the mailbox domain
    expected_domain_rels = {
        (TEST_MAILBOX_ID, TEST_MAILBOX_DOMAIN_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "ScalewayMailbox",
            "id",
            "ScalewayMailboxDomain",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_domain_rels
    )
