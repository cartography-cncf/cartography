from unittest import mock
from unittest.mock import patch

from googleapiclient.errors import HttpError

from cartography.intel.gsuite import api


def test_get_all_users():
    client = mock.MagicMock()
    raw_request_1 = mock.MagicMock()
    raw_request_2 = mock.MagicMock()

    user1 = {"primaryEmail": "employee1@test.lyft.com"}
    user2 = {"primaryEmail": "employee2@test.lyft.com"}
    user3 = {"primaryEmail": "employee3@test.lyft.com"}

    client.users().list.return_value = raw_request_1
    client.users().list_next.side_effect = [raw_request_2, None]

    raw_request_1.execute.return_value = {"users": [user1, user2]}
    raw_request_2.execute.return_value = {"users": [user3]}

    result = api.get_all_users(client)
    emails = [
        user["primaryEmail"]
        for response_object in result
        for user in response_object["users"]
    ]

    expected = [
        "employee1@test.lyft.com",
        "employee2@test.lyft.com",
        "employee3@test.lyft.com",
    ]
    assert sorted(emails) == sorted(expected)


def test_get_all_groups():
    client = mock.MagicMock()
    raw_request_1 = mock.MagicMock()
    raw_request_2 = mock.MagicMock()

    group1 = {"email": "group1@test.lyft.com"}
    group2 = {"email": "group2@test.lyft.com"}
    group3 = {"email": "group3@test.lyft.com"}

    client.groups().list.return_value = raw_request_1
    client.groups().list_next.side_effect = [raw_request_2, None]

    raw_request_1.execute.return_value = {"groups": [group1, group2]}
    raw_request_2.execute.return_value = {"groups": [group3]}

    result = api.get_all_groups(client)
    emails = [
        group["email"]
        for response_object in result
        for group in response_object["groups"]
    ]

    expected = [
        "group1@test.lyft.com",
        "group2@test.lyft.com",
        "group3@test.lyft.com",
    ]
    assert sorted(emails) == sorted(expected)


@patch("cartography.intel.gsuite.api.cleanup_gsuite_users")
@patch("cartography.intel.gsuite.api.load_gsuite_users")
@patch(
    "cartography.intel.gsuite.api.get_all_users",
    return_value=[
        {
            "users": [
                {"primaryEmail": "group1@test.lyft.com"},
                {"primaryEmail": "group2@test.lyft.com"},
            ],
        },
        {
            "users": [
                {"primaryEmail": "group3@test.lyft.com"},
                {"primaryEmail": "group4@test.lyft.com"},
            ],
        },
    ],
)
def test_sync_gsuite_users(get_all_users, load_gsuite_users, cleanup_gsuite_users):
    client = mock.MagicMock()
    gsuite_update_tag = 1
    session = mock.MagicMock()
    common_job_param = {
        "UPDATE_TAG": gsuite_update_tag,
    }
    api.sync_gsuite_users(session, client, gsuite_update_tag, common_job_param)
    users = api.transform_users(get_all_users())
    load_gsuite_users.assert_called_with(
        session,
        users,
        gsuite_update_tag,
    )
    cleanup_gsuite_users.assert_called_once()


@patch("cartography.intel.gsuite.api.sync_gsuite_owners")
@patch("cartography.intel.gsuite.api.sync_gsuite_members")
@patch("cartography.intel.gsuite.api.cleanup_gsuite_groups")
@patch("cartography.intel.gsuite.api.load_gsuite_groups")
@patch(
    "cartography.intel.gsuite.api.get_all_groups",
    return_value=[
        {
            "groups": [
                {"email": "group1@test.lyft.com"},
                {"email": "group2@test.lyft.com"},
            ],
        },
        {
            "groups": [
                {"email": "group3@test.lyft.com"},
                {"email": "group4@test.lyft.com"},
            ],
        },
    ],
)
def test_sync_gsuite_groups(
    all_groups,
    load_gsuite_groups,
    cleanup_gsuite_groups,
    sync_gsuite_members,
    sync_gsuite_owners,
):
    admin_client = mock.MagicMock()
    session = mock.MagicMock()
    gsuite_update_tag = 1
    common_job_param = {
        "UPDATE_TAG": gsuite_update_tag,
    }
    api.sync_gsuite_groups(session, admin_client, gsuite_update_tag, common_job_param)
    groups = api.transform_groups(all_groups())
    load_gsuite_groups.assert_called_with(session, groups, gsuite_update_tag)
    cleanup_gsuite_groups.assert_called_once()
    sync_gsuite_members.assert_called_with(
        groups,
        session,
        admin_client,
        gsuite_update_tag,
    )
    sync_gsuite_owners.assert_called_with(
        groups,
        session,
        admin_client,
        gsuite_update_tag,
    )


def test_load_gsuite_groups():
    ingestion_qry = """
        UNWIND $GroupData as group
        MERGE (g:GSuiteGroup{id: group.id})
        ON CREATE SET
        g.firstseen = $UpdateTag,
        g.group_id = group.id
        SET
        g.admin_created = group.adminCreated,
        g.description = group.description,
        g.direct_members_count = group.directMembersCount,
        g.email = group.email,
        g.etag = group.etag,
        g.kind = group.kind,
        g.name = group.name,
        g:GCPPrincipal,
        g.lastupdated = $UpdateTag
    """
    groups = []
    update_tag = 1
    session = mock.MagicMock()
    api.load_gsuite_groups(session, groups, update_tag)
    session.run.assert_called_with(
        ingestion_qry,
        GroupData=groups,
        UpdateTag=update_tag,
    )


def test_load_gsuite_users():
    ingestion_qry = """
        UNWIND $UserData as user
        MERGE (u:GSuiteUser{id: user.id})
        ON CREATE SET
        u.user_id = user.id,
        u.firstseen = $UpdateTag
        SET
        u.agreed_to_terms = user.agreedToTerms,
        u.archived = user.archived,
        u.change_password_at_next_login = user.changePasswordAtNextLogin,
        u.creation_time = user.creationTime,
        u.customer_id = user.customerId,
        u.etag = user.etag,
        u.include_in_global_address_list = user.includeInGlobalAddressList,
        u.ip_whitelisted = user.ipWhitelisted,
        u.is_admin = user.isAdmin,
        u.is_delegated_admin =  user.isDelegatedAdmin,
        u.is_enforced_in_2_sv = user.isEnforcedIn2Sv,
        u.is_enrolled_in_2_sv = user.isEnrolledIn2Sv,
        u.is_mailbox_setup = user.isMailboxSetup,
        u.kind = user.kind,
        u.last_login_time = user.lastLoginTime,
        u.name = user.name.fullName,
        u.family_name = user.name.familyName,
        u.given_name = user.name.givenName,
        u.org_unit_path = user.orgUnitPath,
        u.primary_email = user.primaryEmail,
        u.email = user.primaryEmail,
        u.suspended = user.suspended,
        u.thumbnail_photo_etag = user.thumbnailPhotoEtag,
        u.thumbnail_photo_url = user.thumbnailPhotoUrl,
        u:GCPPrincipal,
        u.lastupdated = $UpdateTag
    """
    users = []
    update_tag = 1
    session = mock.MagicMock()
    api.load_gsuite_users(session, users, update_tag)
    session.run.assert_called_with(
        ingestion_qry,
        UserData=users,
        UpdateTag=update_tag,
    )


def test_transform_groups():
    param = [
        {
            "groups": [
                {"email": "group1@test.lyft.com"},
                {"email": "group2@test.lyft.com"},
            ],
        },
        {
            "groups": [
                {"email": "group3@test.lyft.com"},
                {"email": "group4@test.lyft.com"},
            ],
        },
    ]
    expected = [
        {"email": "group1@test.lyft.com"},
        {"email": "group2@test.lyft.com"},
        {"email": "group3@test.lyft.com"},
        {"email": "group4@test.lyft.com"},
    ]
    result = api.transform_groups(param)
    assert result == expected


def test_transform_users():
    param = [
        {
            "users": [
                {"primaryEmail": "group1@test.lyft.com"},
                {"primaryEmail": "group2@test.lyft.com"},
            ],
        },
        {
            "users": [
                {"primaryEmail": "group3@test.lyft.com"},
                {"primaryEmail": "group4@test.lyft.com"},
            ],
        },
    ]
    expected = [
        {"primaryEmail": "group1@test.lyft.com"},
        {"primaryEmail": "group2@test.lyft.com"},
        {"primaryEmail": "group3@test.lyft.com"},
        {"primaryEmail": "group4@test.lyft.com"},
    ]
    result = api.transform_users(param)
    assert result == expected


def test_get_owners_for_group():
    client = mock.MagicMock()
    raw_request = mock.MagicMock()

    owner1 = {"id": "user1@test.lyft.com", "email": "user1@test.lyft.com"}
    owner2 = {"id": "group1@test.lyft.com", "email": "group1@test.lyft.com"}

    client.groups().get.return_value = raw_request
    raw_request.execute.return_value = {"owners": [owner1, owner2]}

    result = api.get_owners_for_group(client, "testgroup@test.lyft.com")
    assert result == [owner1, owner2]


def test_get_owners_for_group_permission_denied():
    client = mock.MagicMock()
    raw_request = mock.MagicMock()

    client.groups().get.return_value = raw_request
    raw_request.execute.side_effect = HttpError(
        resp=mock.MagicMock(status=403),
        content=b"Permission denied"
    )

    result = api.get_owners_for_group(client, "testgroup@test.lyft.com")
    assert result == []


def test_load_gsuite_owners():
    session = mock.MagicMock()
    group = {"id": "group1@test.lyft.com"}
    owners = [
        {"id": "user1@test.lyft.com"},
        {"id": "group2@test.lyft.com"}
    ]
    update_tag = 1

    api.load_gsuite_owners(session, group, owners, update_tag)

    # Verify that both user and group owner queries were executed
    assert session.run.call_count == 2
    
    # Check the first call (user owners)
    first_call = session.run.call_args_list[0]
    assert "OwnerData" in first_call[1]
    assert "GroupID" in first_call[1]
    assert first_call[1]["GroupID"] == "group1@test.lyft.com"
    
    # Check the second call (group owners)
    second_call = session.run.call_args_list[1]
    assert "OwnerData" in second_call[1]
    assert "GroupID" in second_call[1]
    assert second_call[1]["GroupID"] == "group1@test.lyft.com"


def test_sync_gsuite_owners():
    groups = [
        {"email": "group1@test.lyft.com", "id": "group1@test.lyft.com"},
        {"email": "group2@test.lyft.com", "id": "group2@test.lyft.com"}
    ]
    session = mock.MagicMock()
    admin_client = mock.MagicMock()
    update_tag = 1

    # Mock the get_owners_for_group function
    with patch("cartography.intel.gsuite.api.get_owners_for_group") as mock_get_owners:
        with patch("cartography.intel.gsuite.api.load_gsuite_owners") as mock_load_owners:
            mock_get_owners.side_effect = [
                [{"id": "user1@test.lyft.com"}],  # owners for group1
                [{"id": "group3@test.lyft.com"}]  # owners for group2
            ]
            
            api.sync_gsuite_owners(groups, session, admin_client, update_tag)
            
            # Verify get_owners_for_group was called for each group
            assert mock_get_owners.call_count == 2
            mock_get_owners.assert_any_call(admin_client, "group1@test.lyft.com")
            mock_get_owners.assert_any_call(admin_client, "group2@test.lyft.com")
            
            # Verify load_gsuite_owners was called for each group
            assert mock_load_owners.call_count == 2
            mock_load_owners.assert_any_call(session, groups[0], [{"id": "user1@test.lyft.com"}], update_tag)
            mock_load_owners.assert_any_call(session, groups[1], [{"id": "group3@test.lyft.com"}], update_tag)
