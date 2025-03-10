import logging
from typing import Dict
from typing import List

import neo4j
from googleapiclient.discovery import Resource
from googleapiclient.errors import HttpError

from cartography.util import run_cleanup_job
from cartography.util import timeit


logger = logging.getLogger(__name__)


GOOGLE_API_NUM_RETRIES = 5


@timeit
def get_all_groups(admin: Resource) -> List[Dict]:
    """
    Return list of Google Groups in your organization
    Returns empty list if we are unable to enumerate the groups for any reasons

    googleapiclient.discovery.build('admin', 'directory_v1', credentials=credentials, cache_discovery=False)

    :param admin: google's apiclient discovery resource object.  From googleapiclient.discovery.build
    See https://googleapis.github.io/google-api-python-client/docs/epy/googleapiclient.discovery-module.html#build.
    :return: List of Google groups in domain
    """
    request = admin.groups().list(customer='my_customer', maxResults=20, orderBy='email')
    response_objects = []
    while request is not None:
        try:
            resp = request.execute(num_retries=GOOGLE_API_NUM_RETRIES)
            response_objects.append(resp)
            request = admin.groups().list_next(request, resp)
        except HttpError as e:
            if e.resp.status == 403 and "Request had insufficient authentication scopes" in str(e):
                logger.error(
                    "Missing required GSuite scopes. If using the gcloud CLI, ",
                    "run: gcloud auth application-default login --scopes="
                    '"https://www.googleapis.com/auth/admin.directory.user.readonly,'
                    'https://www.googleapis.com/auth/admin.directory.group.readonly,'
                    'https://www.googleapis.com/auth/admin.directory.group.member.readonly,'
                    'https://www.googleapis.com/auth/cloud-platform"',
                )
            raise
    return response_objects


@timeit
def transform_groups(response_objects: List[Dict]) -> List[Dict]:
    """  Strips list of API response objects to return list of group objects only

    :param response_objects:
    :return: list of dictionary objects as defined in /docs/root/modules/gsuite/schema.md
    """
    groups: List[Dict] = []
    for response_object in response_objects:
        for group in response_object['groups']:
            groups.append(group)
    return groups


@timeit
def transform_users(response_objects: List[Dict]) -> List[Dict]:
    """  Strips list of API response objects to return list of group objects only
    :param response_objects:
    :return: list of dictionary objects as defined in /docs/root/modules/gsuite/schema.md
    """
    users: List[Dict] = []
    for response_object in response_objects:
        for user in response_object['users']:
            users.append(user)
    return users


@timeit
def get_all_groups_for_email(admin: Resource, email: str) -> List[Dict]:
    """ Fetch all groups of which the given group is a member

    Arguments:
        email: A string representing the email address for the group

    Returns a list of Group models
    Throws GoogleException
    """
    request = admin.groups().list(userKey=email, maxResults=500)
    groups: List[Dict] = []
    while request is not None:
        resp = request.execute(num_retries=GOOGLE_API_NUM_RETRIES)
        groups = groups + resp.get('groups', [])
        request = admin.groups().list_next(request, resp)
    return groups


@timeit
def get_members_for_group(admin: Resource, group_email: str) -> List[Dict]:
    """ Get all members for a google group

    :param group_email: A string representing the email address for the group

    :return: List of dictionaries representing Users or Groups.
    """
    request = admin.members().list(
        groupKey=group_email,
        maxResults=500,
    )
    members: List[Dict] = []
    while request is not None:
        resp = request.execute(num_retries=GOOGLE_API_NUM_RETRIES)
        members = members + resp.get('members', [])
        request = admin.members().list_next(request, resp)

    return members


@timeit
def get_all_users(admin: Resource) -> List[Dict]:
    """
    Return list of Google Users in your organization
    Returns empty list if we are unable to enumerate the groups for any reasons
    https://developers.google.com/admin-sdk/directory/v1/guides/manage-users

    :param admin: apiclient discovery resource object
    see
    :return: List of Google users in domain
    see https://developers.google.com/admin-sdk/directory/v1/guides/manage-users#get_all_domain_users
    """
    request = admin.users().list(customer='my_customer', maxResults=500, orderBy='email')
    response_objects = []
    while request is not None:
        resp = request.execute(num_retries=GOOGLE_API_NUM_RETRIES)
        response_objects.append(resp)
        request = admin.users().list_next(request, resp)
    return response_objects


@timeit
def load_gsuite_groups(neo4j_session: neo4j.Session, groups: List[Dict], gsuite_update_tag: int) -> None:
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
    logger.info(f'Ingesting {len(groups)} gsuite groups')
    neo4j_session.run(ingestion_qry, GroupData=groups, UpdateTag=gsuite_update_tag)


@timeit
def load_gsuite_users(neo4j_session: neo4j.Session, users: List[Dict], gsuite_update_tag: int) -> None:
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
    logger.info(f'Ingesting {len(users)} gsuite users')
    neo4j_session.run(ingestion_qry, UserData=users, UpdateTag=gsuite_update_tag)


@timeit
def load_gsuite_members(neo4j_session: neo4j.Session, group: Dict, members: List[Dict], gsuite_update_tag: int) -> None:
    ingestion_qry = """
        UNWIND $MemberData as member
        MATCH (user:GSuiteUser {id: member.id}),(group:GSuiteGroup {id: $GroupID })
        MERGE (user)-[r:MEMBER_GSUITE_GROUP]->(group)
        ON CREATE SET
        r.firstseen = $UpdateTag
        SET
        r.lastupdated = $UpdateTag
    """
    neo4j_session.run(
        ingestion_qry,
        MemberData=members,
        GroupID=group.get("id"),
        UpdateTag=gsuite_update_tag,
    )
    membership_qry = """
        UNWIND $MemberData as member
        MATCH(group_1: GSuiteGroup{id: member.id}), (group_2:GSuiteGroup {id: $GroupID})
        MERGE (group_1)-[r:MEMBER_GSUITE_GROUP]->(group_2)
        ON CREATE SET
        r.firstseen = $UpdateTag
        SET
        r.lastupdated = $UpdateTag
    """
    neo4j_session.run(membership_qry, MemberData=members, GroupID=group.get("id"), UpdateTag=gsuite_update_tag)


@timeit
def cleanup_gsuite_users(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job(
        'gsuite_ingest_users_cleanup.json',
        neo4j_session,
        common_job_parameters,
    )


@timeit
def cleanup_gsuite_groups(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job(
        'gsuite_ingest_groups_cleanup.json',
        neo4j_session,
        common_job_parameters,
    )


@timeit
def sync_gsuite_users(
    neo4j_session: neo4j.Session, admin: Resource, gsuite_update_tag: int, common_job_parameters: Dict,
) -> None:
    """
    GET GSuite user objects using the google admin api resource, load the data into Neo4j and clean up stale nodes.

    :param session: The Neo4j session
    :param admin: Google admin resource object created by `googleapiclient.discovery.build()`.
    See https://googleapis.github.io/google-api-python-client/docs/epy/googleapiclient.discovery-module.html#build.
    :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with
    :param common_job_parameters: Parameters to carry to the Neo4j jobs
    :return: Nothing
    """
    logger.debug('Syncing GSuite Users')
    resp_objs = get_all_users(admin)
    users = transform_users(resp_objs)
    load_gsuite_users(neo4j_session, users, gsuite_update_tag)
    cleanup_gsuite_users(neo4j_session, common_job_parameters)


@timeit
def sync_gsuite_groups(
    neo4j_session: neo4j.Session, admin: Resource, gsuite_update_tag: int, common_job_parameters: Dict,
) -> None:
    """
    GET GSuite group objects using the google admin api resource, load the data into Neo4j and clean up stale nodes.

    :param neo4j_session: The Neo4j session
    :param admin: Google admin resource object created by `googleapiclient.discovery.build()`.
    See https://googleapis.github.io/google-api-python-client/docs/epy/googleapiclient.discovery-module.html#build.
    :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with
    :param common_job_parameters: Parameters to carry to the Neo4j jobs
    :return: Nothing
    """
    logger.debug('Syncing GSuite Groups')
    resp_objs = get_all_groups(admin)
    groups = transform_groups(resp_objs)
    load_gsuite_groups(neo4j_session, groups, gsuite_update_tag)
    cleanup_gsuite_groups(neo4j_session, common_job_parameters)
    sync_gsuite_members(groups, neo4j_session, admin, gsuite_update_tag)


@timeit
def sync_gsuite_members(
    groups: List[Dict], neo4j_session: neo4j.Session, admin: Resource, gsuite_update_tag: int,
) -> None:
    for group in groups:
        members = get_members_for_group(admin, group['email'])
        load_gsuite_members(neo4j_session, group, members, gsuite_update_tag)
