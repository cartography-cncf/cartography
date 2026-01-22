# Copyright (c) 2020, Oracle and/or its affiliates.
from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.oci.iam as iam
from tests.data.oci.iam import LIST_COMPARTMENTS
from tests.data.oci.iam import LIST_GROUP_MEMBERSHIPS
from tests.data.oci.iam import LIST_GROUPS
from tests.data.oci.iam import LIST_POLICIES
from tests.data.oci.iam import LIST_USERS
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_TENANCY_ID = (
    "ocid1.tenancy.oc1..nqilyrb1l5t6gnmlcjgeim8q47vccnklev8k2ud9skn78eapu116oyv9wcr0"
)
TEST_REGION = "us-phoenix-1"
TEST_UPDATE_TAG = 123456789


def _create_test_tenancy(neo4j_session):
    """Create a test OCITenancy node for relationship testing."""
    neo4j_session.run(
        """
        MERGE (t:OCITenancy{ocid: $tenancy_id})
        SET t.lastupdated = $update_tag, t.name = 'test-tenancy'
        """,
        tenancy_id=TEST_TENANCY_ID,
        update_tag=TEST_UPDATE_TAG,
    )


@patch.object(iam, "get_user_list_data", return_value=LIST_USERS)
def test_sync_users(mock_get_users, neo4j_session):
    """
    Ensure that OCI users are synced correctly with their nodes and relationships.
    """
    # Arrange
    _create_test_tenancy(neo4j_session)
    mock_iam_client = MagicMock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "OCI_TENANCY_ID": TEST_TENANCY_ID,
    }

    # Act
    iam.sync_users(
        neo4j_session,
        mock_iam_client,
        TEST_TENANCY_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert - OCIUser nodes exist
    assert check_nodes(neo4j_session, "OCIUser", ["ocid", "name"]) == {
        (
            "ocid1.user.oc1..m5oaceraqeiq47zqstzy6ickbbfkw7vg4srozp4sskn78eapu116oyv9wcr0",
            "example-user-0",
        ),
        (
            "ocid1.user.oc1..srozp4sskn78eapu116oyv9wcr06ickbbfkw7vg4m5oaceraqeiq47zqstzy",
            "example-user-1",
        ),
    }

    # Assert - Relationships (OCITenancy)-[RESOURCE]->(OCIUser)
    assert check_rels(
        neo4j_session,
        "OCITenancy",
        "ocid",
        "OCIUser",
        "ocid",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (
            TEST_TENANCY_ID,
            "ocid1.user.oc1..m5oaceraqeiq47zqstzy6ickbbfkw7vg4srozp4sskn78eapu116oyv9wcr0",
        ),
        (
            TEST_TENANCY_ID,
            "ocid1.user.oc1..srozp4sskn78eapu116oyv9wcr06ickbbfkw7vg4m5oaceraqeiq47zqstzy",
        ),
    }


@patch.object(iam, "get_group_list_data", return_value=LIST_GROUPS)
def test_sync_groups(mock_get_groups, neo4j_session):
    """
    Ensure that OCI groups are synced correctly with their nodes and relationships.
    """
    # Arrange
    _create_test_tenancy(neo4j_session)
    mock_iam_client = MagicMock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "OCI_TENANCY_ID": TEST_TENANCY_ID,
    }

    # Act
    iam.sync_groups(
        neo4j_session,
        mock_iam_client,
        TEST_TENANCY_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert - OCIGroup nodes exist
    assert check_nodes(neo4j_session, "OCIGroup", ["ocid", "name"]) == {
        (
            "ocid1.group.oc1..wa03xlg35zi0tb33qyrjteen36zrkauzhjz8pi0yzt4d2b78uo745h5ze6at",
            "example-group-0",
        ),
        (
            "ocid1.group.oc1..bkan5que3j9ixlsf0xn56xrj7xnjgez0bhfqll68zt4d2b78uo745h5ze6at",
            "example-group-1",
        ),
    }

    # Assert - Relationships (OCITenancy)-[RESOURCE]->(OCIGroup)
    assert check_rels(
        neo4j_session,
        "OCITenancy",
        "ocid",
        "OCIGroup",
        "ocid",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (
            TEST_TENANCY_ID,
            "ocid1.group.oc1..wa03xlg35zi0tb33qyrjteen36zrkauzhjz8pi0yzt4d2b78uo745h5ze6at",
        ),
        (
            TEST_TENANCY_ID,
            "ocid1.group.oc1..bkan5que3j9ixlsf0xn56xrj7xnjgez0bhfqll68zt4d2b78uo745h5ze6at",
        ),
    }


@patch.object(iam, "get_group_list_data", return_value=LIST_GROUPS)
@patch.object(iam, "get_user_list_data", return_value=LIST_USERS)
@patch.object(iam, "get_group_membership_data", return_value=LIST_GROUP_MEMBERSHIPS)
def test_sync_group_memberships(
    mock_get_memberships, mock_get_users, mock_get_groups, neo4j_session
):
    """
    Ensure that OCI group memberships create correct user-group relationships.
    """
    # Arrange
    _create_test_tenancy(neo4j_session)
    mock_iam_client = MagicMock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "OCI_TENANCY_ID": TEST_TENANCY_ID,
    }

    # First sync users and groups
    iam.sync_users(
        neo4j_session,
        mock_iam_client,
        TEST_TENANCY_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )
    iam.sync_groups(
        neo4j_session,
        mock_iam_client,
        TEST_TENANCY_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Act - Sync group memberships
    iam.sync_group_memberships(
        neo4j_session,
        mock_iam_client,
        TEST_TENANCY_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert - Relationships (OCIUser)-[MEMBER_OCID_GROUP]->(OCIGroup)
    assert check_rels(
        neo4j_session,
        "OCIUser",
        "ocid",
        "OCIGroup",
        "ocid",
        "MEMBER_OCID_GROUP",
        rel_direction_right=True,
    ) == {
        (
            "ocid1.user.oc1..m5oaceraqeiq47zqstzy6ickbbfkw7vg4srozp4sskn78eapu116oyv9wcr0",
            "ocid1.group.oc1..wa03xlg35zi0tb33qyrjteen36zrkauzhjz8pi0yzt4d2b78uo745h5ze6at",
        ),
        (
            "ocid1.user.oc1..srozp4sskn78eapu116oyv9wcr06ickbbfkw7vg4m5oaceraqeiq47zqstzy",
            "ocid1.group.oc1..wa03xlg35zi0tb33qyrjteen36zrkauzhjz8pi0yzt4d2b78uo745h5ze6at",
        ),
    }


def test_load_compartments(neo4j_session):
    """
    Ensure that OCI compartments are loaded correctly.
    """
    # Arrange
    _create_test_tenancy(neo4j_session)

    # Act
    iam.load_compartments(
        neo4j_session,
        LIST_COMPARTMENTS["Compartments"],
        TEST_TENANCY_ID,
        TEST_UPDATE_TAG,
    )

    # Assert - OCICompartment nodes exist
    assert check_nodes(neo4j_session, "OCICompartment", ["ocid", "name"]) == {
        (
            "ocid1.compartment.oc1..cin4w1x06m84tnb54h038960q9i41vutzd5lmibackk8r1vaelmgf11rwazz",
            "example-compartment-0",
        ),
        (
            "ocid1.compartment.oc1..54h038960q9i41vutzd5lmibac4tnbkkcin4w1x06m88r1vaelmgf11rwazz",
            "example-compartment-1",
        ),
    }

    # Assert - Relationships (OCITenancy)-[OCI_COMPARTMENT]->(OCICompartment)
    assert check_rels(
        neo4j_session,
        "OCITenancy",
        "ocid",
        "OCICompartment",
        "ocid",
        "OCI_COMPARTMENT",
        rel_direction_right=True,
    ) == {
        (
            TEST_TENANCY_ID,
            "ocid1.compartment.oc1..cin4w1x06m84tnb54h038960q9i41vutzd5lmibackk8r1vaelmgf11rwazz",
        ),
        (
            TEST_TENANCY_ID,
            "ocid1.compartment.oc1..54h038960q9i41vutzd5lmibac4tnbkkcin4w1x06m88r1vaelmgf11rwazz",
        ),
    }


def test_load_policies(neo4j_session):
    """
    Ensure that OCI policies are loaded correctly.
    """
    # Arrange
    _create_test_tenancy(neo4j_session)

    # Act
    iam.load_policies(
        neo4j_session,
        LIST_POLICIES["Policies"],
        TEST_TENANCY_ID,
        TEST_UPDATE_TAG,
    )

    # Assert - OCIPolicy nodes exist
    assert check_nodes(neo4j_session, "OCIPolicy", ["ocid", "name"]) == {
        (
            "ocid1.policy.oc1..aecin4w1x06m8lm4tvutzd5lmibackk8r1vgnb54h038960q9i41f11rwazz",
            "example-policy-0",
        ),
        (
            "ocid1.policy.oc1..4tvutzd5lmibackk8r1vaecin4w1x06m8lmgnb54h038960q9i41f11rwazz",
            "example-policy-1",
        ),
    }

    # Assert - Relationships (OCITenancy)-[OCI_POLICY]->(OCIPolicy)
    assert check_rels(
        neo4j_session,
        "OCITenancy",
        "ocid",
        "OCIPolicy",
        "ocid",
        "OCI_POLICY",
        rel_direction_right=True,
    ) == {
        (
            TEST_TENANCY_ID,
            "ocid1.policy.oc1..aecin4w1x06m8lm4tvutzd5lmibackk8r1vgnb54h038960q9i41f11rwazz",
        ),
        (
            TEST_TENANCY_ID,
            "ocid1.policy.oc1..4tvutzd5lmibackk8r1vaecin4w1x06m8lmgnb54h038960q9i41f11rwazz",
        ),
    }
