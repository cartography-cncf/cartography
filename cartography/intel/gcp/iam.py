import json
import logging
import time
from datetime import datetime
from typing import Dict
from typing import List

import neo4j
from cloudconsolelink.clouds.gcp import GCPLinker
from googleapiclient.discovery import HttpError
from googleapiclient.discovery import Resource

from . import label
from cartography.intel.gcp import external_idp
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)
gcp_console_link = GCPLinker()


def set_used_state(session: neo4j.Session, project_id: str, common_job_parameters: Dict, update_tag: int) -> None:
    session.execute_write(_set_used_state_tx, project_id, common_job_parameters, update_tag)


@timeit
def get_service_accounts(iam: Resource, project_id: str) -> List[Dict]:
    service_accounts: List[Dict] = []
    try:
        req = iam.projects().serviceAccounts().list(name=f'projects/{project_id}')
        while req is not None:
            res = req.execute()
            page = res.get('accounts', [])
            service_accounts.extend(page)
            req = iam.projects().serviceAccounts().list_next(previous_request=req, previous_response=res)

        return service_accounts
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err['status'] == 'PERMISSION_DENIED':
            logger.warning(
                (
                    "Could not retrieve service accounts on project %s due to permissions issue. Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return []
        else:
            raise


@timeit
def transform_service_accounts(service_accounts: List[Dict], project_id: str) -> List[Dict]:
    for account in service_accounts:
        account['firstName'] = account['name'].split('@')[0]
        account['id'] = account['email']
        account['service_account_name'] = account['name'].split('/')[-1]
        account['consolelink'] = gcp_console_link.get_console_link(
            resource_name='service_account', project_id=project_id, service_account_unique_id=account['uniqueId'],
        )
    return service_accounts


def get_service_account_last_used_activities(policyanalyzer: Resource, project_id: str):
    activities = []
    try:
        parent = f"projects/{project_id}/locations/global/activityTypes/serviceAccountKeyLastAuthentication"
        res = policyanalyzer.projects().locations().activityTypes().activities().query(parent=parent).execute()
        activities.extend(res.get('activities', []))

    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err['status'] == 'PERMISSION_DENIED':
            logger.warning(
                (
                    "Could not retrieve service accounts last used activities on project %s due to permissions issue. Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return []
        else:
            raise
    return activities


def get_last_authenticated_time(key_id: str, activities: List[Dict]):
    for actvity in activities:
        if key_id in actvity.get("fullResourceName", ""):
            return actvity.get("activity", {}).get("lastAuthenticatedTime", "")
    return ""


@timeit
def get_service_account_keys(iam: Resource, project_id: str, service_account: Dict, activities: List[Dict]) -> List[Dict]:
    service_keys: List[Dict] = []
    try:
        res = iam.projects().serviceAccounts().keys().list(name=service_account['name']).execute()
        keys = res.get('keys', [])
        for key in keys:
            key['id'] = key['name'].split('/')[-1]
            key['service_account_key_name'] = key['name'].split('/')[-1]
            key['serviceaccount'] = service_account['name']
            key['lastAuthenticatedTime'] = get_last_authenticated_time(key.get("id"), activities)
            key['consolelink'] = gcp_console_link.get_console_link(
                resource_name='service_account_key', project_id=project_id, service_account_unique_id=service_account['uniqueId'],
            )
            key['validAfterTime'] = key.get('validAfterTime')
            key['validBeforeTime'] = key.get('validBeforeTime')

        service_keys.extend(keys)

        return service_keys
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err['status'] == 'PERMISSION_DENIED':
            logger.warning(
                (
                    "Could not retrieve Keys on project %s & account %s due to permissions issue. Code: %s, Message: %s"
                ), project_id, service_account['name'], err['code'], err['message'],
            )
            return []
        else:
            raise


@timeit
def get_predefined_roles(iam: Resource, project_id: str) -> List[Dict]:
    roles: List[Dict] = []
    try:
        req = iam.roles().list(view="FULL")
        while req is not None:
            res = req.execute()
            page = res.get('roles', [])
            roles.extend(page)
            req = iam.roles().list_next(previous_request=req, previous_response=res)

        return roles
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err['status'] == 'PERMISSION_DENIED':
            logger.warning(
                (
                    "Could not retrieve predefined roles on project %s due to permissions issue. Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return roles
        else:
            raise


@timeit
def get_organization_custom_roles(iam: Resource, crm_v1: Resource, project_id: str) -> List[Dict]:
    roles: List[Dict] = []
    try:
        req = crm_v1.projects().get(projectId=project_id)
        res_project = req.execute()
        if res_project.get('parent', {}).get('type', '') == 'organization':
            req = iam.organizations().roles().list(
                parent=f"organizations/{res_project.get('parent', {}).get('id')}", view="FULL",
            )
            while req is not None:
                res = req.execute()
                page = res.get('roles', [])
                roles.extend(page)
                req = iam.organizations().roles().list_next(previous_request=req, previous_response=res)
        return roles
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err['status'] == 'PERMISSION_DENIED':
            logger.warning(
                (
                    "Could not retrieve organization custom roles on project %s due to permissions issue. Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return roles
        else:
            raise


@timeit
def get_project_custom_roles(iam: Resource, project_id: str) -> List[Dict]:
    roles: List[Dict] = []
    try:
        req = iam.projects().roles().list(parent=f'projects/{project_id}', view="FULL")
        while req is not None:
            res = req.execute()
            page = res.get('roles', [])
            roles.extend(page)
            req = iam.projects().roles().list_next(previous_request=req, previous_response=res)

        return roles
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err['status'] == 'PERMISSION_DENIED':
            logger.warning(
                (
                    "Could not retrieve project custom role on project %s due to permissions issue. Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return roles
        else:
            raise


@timeit
def transform_roles(roles_list: List[Dict], project_id: str, type: str, common_job_parameters: Dict) -> List[Dict]:
    for role in roles_list:
        role['id'] = get_role_id(role['name'], project_id, common_job_parameters)
        role['type'] = type
        role['parent'] = ['project', 'organization']
        role['is_sso'] = True
        if role['name'].startswith('projects/'):
            role['parent'] = ['project']
            del role['is_sso']
        if role['name'].startswith('organizations/'):
            role['parent'] = ['organization']
        role['consolelink'] = gcp_console_link.get_console_link(
            resource_name='iam_role', project_id=project_id, role_id=role['name'],
        )
        if role.get("stage") == "BETA":
            role["title"] = f'{role["title"]} Beta'
    return roles_list


@timeit
def get_role_id(role_name: str, project_id: str, common_job_parameters: Dict) -> str:
    if role_name.startswith('organizations/'):
        return role_name

    elif role_name.startswith('projects/'):
        return role_name

    elif role_name.startswith('roles/'):
        return f'{common_job_parameters["GCP_ORGANIZATION_ID"]}/{role_name}'
    return ''


@timeit
def get_policy_bindings(crm_v1: Resource, crm_v2: Resource, project_id: str) -> List[Dict]:
    bindings = []

    try:
        req = crm_v1.projects().getIamPolicy(resource=project_id, body={'options': {'requestedPolicyVersion': 3}})
        res = req.execute()
        if res.get('bindings'):
            for binding in res['bindings']:
                binding['parent'] = 'project'
                binding['parent_id'] = f"projects/{project_id}"
                bindings.append(binding)

    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err['status'] == 'PERMISSION_DENIED':
            logger.warning(
                (
                    "Could not retrieve policy bindings on project %s due to permissions issue. Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return bindings
        else:
            raise

    try:
        req = crm_v1.projects().get(projectId=project_id)
        res_project = req.execute()

    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err['status'] == 'PERMISSION_DENIED':
            logger.warning(
                (
                    "Could not retrieve project details on project %s due to permissions issue. Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return bindings
        else:
            raise

    parent_type = res_project.get('parent', {}).get('type', '')
    try:
        if parent_type == 'organization':
            req = crm_v1.organizations().getIamPolicy(resource=f"organizations/{res_project.get('parent', {}).get('id', '')}")
            res = req.execute()
            if res.get('bindings'):
                for binding in res['bindings']:
                    binding['parent'] = 'organization'
                    binding['parent_id'] = f"organizations/{res_project.get('parent', {}).get('id', '')}"
                    bindings.append(binding)
        elif parent_type == 'folder':
            req = crm_v2.folders().getIamPolicy(resource=f"folders/{res_project.get('parent', {}).get('id', '')}")
            res = req.execute()
            if res.get('bindings'):
                for binding in res['bindings']:
                    binding['parent'] = 'folder'
                    binding['parent_id'] = f"folders/{res_project.get('parent', {}).get('id', '')}"
                    bindings.append(binding)

        return bindings
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err['status'] == 'PERMISSION_DENIED':
            logger.warning(
                (
                    "Could not retrieve policy bindings on project for parent %s in %s due to permissions issue. Code: %s, Message: %s"
                ), parent_type, project_id, err['code'], err['message'],
            )
            return bindings
        else:
            raise


def transform_bindings(bindings: Dict, project_id: str) -> tuple:
    users = []
    groups = []
    domains = []
    service_account = []
    entity_list = []
    public_access = False
    for binding in bindings:
        for member in binding['members']:
            if member.startswith('allUsers') or member.startswith('allAuthenticatedUsers'):
                public_access = True
            else:
                if member.startswith('user:'):
                    usr = member[len('user:'):]
                    users.append({
                        "id": f'projects/{project_id}/users/{usr}',
                        "email": usr,
                        "name": usr.split("@")[0],
                    })

                elif member.startswith('group:'):
                    grp = member[len('group:'):]
                    groups.append({
                        "id": f'projects/{project_id}/groups/{grp}',
                        "email": grp,
                        "name": grp.split('@')[0],
                    })

                elif member.startswith('domain:'):
                    dmn = member[len('domain:'):]
                    domains.append({
                        "id": f'projects/{project_id}/domains/{dmn}',
                        "email": dmn,
                        "name": dmn,
                    })

                elif member.startswith('serviceAccount:'):
                    sac = member[len('serviceAccount:'):]
                    service_account.append({
                        "id": f'projects/{project_id}/service_account/{sac}',
                        "email": sac,
                        "name": sac,
                    })

    entity_list.extend(users)
    entity_list.extend(groups)
    entity_list.extend(domains)
    entity_list.extend(service_account)
    # return (
    #     [dict(s) for s in {frozenset(d.items()) for d in users}],
    #     [dict(s) for s in {frozenset(d.items()) for d in groups}],
    #     [dict(s) for s in {frozenset(d.items()) for d in domains}],
    # )
    return entity_list, public_access


@timeit
def get_apikeys_keys(apikey: Resource, project_id: str) -> List[Resource]:
    api_keys = []
    try:
        req = apikey.projects().locations().keys().list(parent=f"projects/{project_id}/locations/global")
        while req is not None:
            res = req.execute()
            if 'keys' in res:
                api_keys.extend(res['keys'])
            req = apikey.projects().locations().keys().list_next(previous_request=req, previous_response=res)

        return api_keys
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err['status'] == 'PERMISSION_DENIED':
            logger.warning(
                (
                    "Could not retrieve api keys on project %s due to permissions issue. Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return []
        else:
            raise


@timeit
def transform_api_keys(apikeys: List, project_id: str) -> List[Dict]:
    list_keys = []

    for key in apikeys:
        key['consolelink'] = gcp_console_link.get_console_link(project_id=project_id, api_key_id=key['uid'], resource_name='api_key')
        key['id'] = key['name']
        list_keys.append(key)

    return list_keys


@timeit
def load_api_keys(
    neo4j_session: neo4j.Session, api_keys: List[Dict],
    project_id: str, gcp_update_tag: int,
) -> None:

    query = """
    UNWIND $ApiKeys as key
    MERGE (apikey:GCPAPIKey{id: key.id})
    ON CREATE SET
        apikey.firstseen = timestamp()
    SET
        apikey.lastupdated = $gcp_update_tag,
        apikey.uniqueId = key.name,
        apikey.consolelink = key.consolelink,
        apikey.region = key.region,
        apikey.updateTime = key.updateTime,
        apikey.deleteTime = key.deleteTime
    WITH apikey
    MATCH (p:GCPProject{id: $project_id})
    MERGE (p)-[r:RESOURCE]->(apikey)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag
    """
    neo4j_session.run(
        query,
        ApiKeys=api_keys,
        project_id=project_id,
        region="global",
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def cleanup_api_keys(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('gcp_api_keys_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def load_service_accounts(
    neo4j_session: neo4j.Session,
    service_accounts: List[Dict], project_id: str, gcp_update_tag: int,


) -> None:
    ingest_service_accounts = """
    UNWIND $service_accounts_list AS sa
    MERGE (u:GCPServiceAccount{id: sa.id})
    ON CREATE SET u:GCPPrincipal, u.firstseen = timestamp()
    SET u.name = sa.name, u.displayname = sa.displayName,
    u.service_account_name = sa.service_account_name,
    u.create_date = $createDate,
    u.email = sa.email,
    u.consolelink = sa.consolelink,
    u.parent = $parent,
    u.parent_id = $parentId,
    u.region = $region,
    u.disabled = sa.disabled, u.serviceaccountid = sa.uniqueId,
    u.lastupdated = $gcp_update_tag
    WITH u
    MATCH (p:GCPProject{id: $project_id})
    MERGE (p)-[r:RESOURCE]->(u)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag
    """

    neo4j_session.run(
        ingest_service_accounts,
        service_accounts_list=service_accounts,
        parent=['project'],
        parentId=[f'projects/{project_id}'],
        project_id=project_id,
        createDate=datetime.utcnow(),
        region="global",
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def cleanup_service_accounts(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('gcp_iam_service_accounts_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def load_service_account_keys(
    neo4j_session: neo4j.Session, service_account_keys: List[Dict],
    service_account: str, project_id: str, gcp_update_tag: int,
) -> None:
    ingest_service_accounts = """
    UNWIND $service_account_keys_list AS sa
    MERGE (u:GCPServiceAccountKey{id: sa.id})
    ON CREATE SET u.firstseen = timestamp()
    SET u.name=sa.name, u.serviceaccountid= $serviceaccount,
    u.region = $region,
    u.create_date = $createDate,
    u.keytype = sa.keyType, u.origin = sa.keyOrigin,
    u.consolelink = sa.consolelink,
    u.lastauthenticatedtime=sa.lastAuthenticatedTime,
    u.algorithm = sa.keyAlgorithm, u.validbeforetime = sa.validBeforeTime,

    u.validaftertime = sa.validAfterTime, u.lastupdated = $gcp_update_tag,
    u.disabled = sa.disabled
    WITH u, sa
    MATCH (:GCPProject{id: $project_id})-[:RESOURCE]->(d:GCPServiceAccount{id: $serviceaccount})
    MERGE (d)-[r:HAS_KEY]->(u)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag
    """

    neo4j_session.run(
        ingest_service_accounts,
        service_account_keys_list=service_account_keys,
        serviceaccount=service_account,
        createDate=datetime.utcnow(),
        region="global",
        project_id=project_id,
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def cleanup_service_account_keys(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('gcp_iam_service_account_keys_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def load_project_roles(neo4j_session: neo4j.Session, roles: List[Dict], project_id: str, gcp_update_tag: int) -> None:
    ingest_roles = """
    UNWIND $roles_list AS d
    MERGE (u:GCPRole{id: d.id})
    ON CREATE SET u.firstseen = timestamp()
    SET u.name = d.name,
    u.title = d.title,
    u.region = $region,
    u.create_date = $createDate,
    u.is_sso = d.is_sso,
    u.description = d.description,
    u.deleted = d.deleted,
    u.consolelink = d.consolelink,
    u.type = d.type,
    u.parent = d.parent,
    u.permissions = d.includedPermissions,
    u.roleid = d.id,
    u.lastupdated = $gcp_update_tag
    WITH u
    MATCH (p:GCPProject{id: $project_id})
    MERGE (p)-[r:RESOURCE]->(u)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag
    """

    neo4j_session.run(
        ingest_roles,
        roles_list=roles,
        region="global",
        createDate=datetime.utcnow(),
        project_id=project_id,
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def load_sso_roles(neo4j_session: neo4j.Session, roles: List[Dict], org_id: str, gcp_update_tag: int) -> None:
    ingest_roles = """
    UNWIND $roles_list AS d
    MERGE (u:GCPRole{id: d.id})
    ON CREATE SET u.firstseen = timestamp()
    SET u.name = d.name,
    u.title = d.title,
    u.region = $region,
    u.create_date = $createDate,
    u.description = d.description,
    u.is_sso = d.is_sso,
    u.deleted = d.deleted,
    u.consolelink = d.consolelink,
    u.type = d.type,
    u.parent = d.parent,
    u.permissions = d.includedPermissions,
    u.roleid = d.id,
    u.lastupdated = $gcp_update_tag
    WITH u
    MATCH (o:GCPOrganization{id: $org_id})
    MERGE (o)-[r:RESOURCE]->(u)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag
    """

    neo4j_session.run(
        ingest_roles,
        roles_list=roles,
        region="global",
        createDate=datetime.utcnow(),
        org_id=org_id,
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def cleanup_roles(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('gcp_iam_roles_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def load_bindings(neo4j_session: neo4j.Session, bindings: List[Dict], project_id: str, organization_id: str, gcp_update_tag: int, common_job_parameters: Dict) -> None:
    for binding in bindings:
        role_id = get_role_id(binding['role'], project_id, common_job_parameters)

        for member in binding['members']:
            if member.startswith('user:'):
                usr = member[len('user:'):]
                user = {
                    'id': usr,
                    "email": usr,
                    "name": usr.split("@")[0],
                    "parent": binding['parent'],
                    "parent_id": binding['parent_id'],
                    "consolelink": gcp_console_link.get_console_link(project_id=project_id, resource_name='iam_user'),

                }
                if role_id.startswith("projects/"):
                    attach_project_role_to_user(
                        neo4j_session, role_id, user,
                        project_id, organization_id, gcp_update_tag,
                    )
                else:
                    attach_sso_role_to_user(
                        neo4j_session, role_id, user,
                        project_id, organization_id, gcp_update_tag,
                    )

            elif member.startswith('serviceAccount:'):
                serviceAccount = {
                    'id': member[len('serviceAccount:'):],
                    "parent": binding['parent'],
                    "parent_id": binding['parent_id'],
                }
                if role_id.startswith("projects/"):
                    attach_project_role_to_service_account(
                        neo4j_session,
                        role_id, serviceAccount,
                        project_id,
                        gcp_update_tag,
                    )
                else:
                    attach_sso_role_to_service_account(
                        neo4j_session,
                        role_id, serviceAccount,
                        project_id,
                        organization_id,
                        gcp_update_tag,
                    )

            elif member.startswith('group:'):
                grp = member[len('group:'):]
                group = {
                    "id": grp,
                    "email": grp,
                    "name": grp.split('@')[0],
                    "parent": binding['parent'],
                    "parent_id": binding['parent_id'],
                    "consolelink": gcp_console_link.get_console_link(project_id=project_id, resource_name='iam_group'),
                }
                if role_id.startswith("projects/"):
                    attach_project_role_to_group(
                        neo4j_session, role_id,
                        group,
                        project_id,
                        organization_id,
                        gcp_update_tag,
                    )
                else:
                    attach_sso_role_to_group(
                        neo4j_session, role_id,
                        group,
                        project_id,
                        organization_id,
                        gcp_update_tag,
                    )

            elif member.startswith('domain:'):
                dmn = member[len('domain:'):]
                domain = {
                    "id": dmn,
                    "email": dmn,
                    "name": dmn,
                    "parent": binding['parent'],
                    "parent_id": binding['parent_id'],
                    "consolelink": gcp_console_link.get_console_link(project_id=project_id, resource_name='iam_domain'),
                }
                if role_id.startswith("projects/"):
                    attach_project_role_to_domain(
                        neo4j_session, role_id,
                        domain,
                        project_id,
                        gcp_update_tag,
                    )
                else:
                    attach_sso_role_to_domain(
                        neo4j_session, role_id,
                        domain,
                        project_id,
                        organization_id,
                        gcp_update_tag,
                    )

            elif member.startswith('deleted:'):
                member = member[len('deleted:'):]
                if member.startswith('user:'):
                    usr = member[len('user:'):]
                    user = {
                        'id': usr,
                        "email": usr,
                        "name": usr.split("@")[0],
                        "is_deleted": True,
                        "parent": binding['parent'],
                        "parent_id": binding['parent_id'],

                    }
                    if role_id.startswith("projects/"):
                        attach_project_role_to_user(
                            neo4j_session,
                            role_id,
                            user,
                            project_id,
                            organization_id,
                            gcp_update_tag,
                        )
                    else:
                        attach_sso_role_to_user(
                            neo4j_session,
                            role_id,
                            user,
                            project_id,
                            organization_id,
                            gcp_update_tag,
                        )

                elif member.startswith('serviceAccount:'):
                    serviceAccount = {

                        'id': member[len('serviceAccount:'):],
                        'is_deleted': True,
                        "parent": binding['parent'],
                        "parent_id": binding['parent_id'],

                    }
                    if role_id.startswith("projects/"):
                        attach_project_role_to_service_account(
                            neo4j_session,
                            role_id, serviceAccount,
                            project_id,
                            gcp_update_tag,
                        )
                    else:
                        attach_sso_role_to_service_account(
                            neo4j_session,
                            role_id, serviceAccount,
                            project_id,
                            organization_id,
                            gcp_update_tag,
                        )

                elif member.startswith('group:'):
                    grp = member[len('group:'):]
                    group = {
                        "id": grp,
                        "email": grp,
                        "name": grp.split('@')[0],
                        "is_deleted": True,
                        "parent": binding['parent'],
                        "parent_id": binding['parent_id'],
                    }
                    if role_id.startswith("projects/"):
                        attach_project_role_to_group(
                            neo4j_session, role_id,
                            group,
                            project_id,
                            organization_id,
                            gcp_update_tag,
                        )
                    else:
                        attach_sso_role_to_group(
                            neo4j_session, role_id,
                            group,
                            project_id,
                            organization_id,
                            gcp_update_tag,
                        )

                elif member.startswith('domain:'):
                    dmn = member[len('domain:'):]
                    domain = {
                        "id": dmn,
                        "email": dmn,
                        "name": dmn,
                        "is_deleted": True,
                        "parent": binding['parent'],
                        "parent_id": binding['parent_id'],
                    }
                    if role_id.startswith("projects/"):
                        attach_project_role_to_domain(
                            neo4j_session, role_id,
                            domain,
                            project_id,
                            gcp_update_tag,
                        )
                    else:
                        attach_sso_role_to_domain(
                            neo4j_session, role_id,
                            domain,
                            project_id,
                            organization_id,
                            gcp_update_tag,
                        )


@timeit
def cleanup_policy_binding(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('gcp_iam_policy_binding_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def attach_project_role_to_user(
    neo4j_session: neo4j.Session, role_id: str, user: Dict,
    project_id: str, organization_id: str, gcp_update_tag: int,
) -> None:
    ingest_script = """
    MERGE (user:GCPUser{id: $UserId})
    ON CREATE SET
    user:GCPPrincipal,
    user.firstseen = timestamp()
    SET
    user.email = $UserEmail,
    user.name = $UserName,
    user.create_date = $createDate,
    user.lastupdated = $gcp_update_tag,
    user.isDeleted = $isDeleted,
    user.consolelink = $ConsoleLink
    WITH user
    MATCH (:GCPProject{id: $project_id})-[:RESOURCE]->(role:GCPRole{id: $RoleId})
    MERGE (user)-[r:ASSUME_ROLE]->(role)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag
    WITH user,role
    MATCH (p:GCPOrganization{id: $organization_id})
    MERGE (p)-[pr:RESOURCE]->(user)
    ON CREATE SET
    pr.firstseen = timestamp()
    SET pr.lastupdated = $gcp_update_tag
    """

    neo4j_session.run(
        ingest_script,
        RoleId=role_id,
        UserId=user['id'],
        UserEmail=user['email'],
        UserName=user['name'],
        ConsoleLink=user.get('consolelink'),
        createDate=datetime.utcnow(),
        Parent=user['parent'],
        ParentId=user['parent_id'],
        isDeleted=user.get('is_deleted', False),
        project_id=project_id,
        organization_id=organization_id,
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def attach_sso_role_to_user(
    neo4j_session: neo4j.Session, role_id: str, user: Dict,
    project_id: str, organization_id: str, gcp_update_tag: int,
) -> None:
    ingest_script = """
    MERGE (user:GCPUser{id: $UserId})
    ON CREATE SET
    user:GCPPrincipal,
    user.firstseen = timestamp()
    SET
    user.email = $UserEmail,
    user.name = $UserName,
    user.create_date = $createDate,
    user.lastupdated = $gcp_update_tag,
    user.isDeleted = $isDeleted,
    user.consolelink = $ConsoleLink
    WITH user
    MATCH (:GCPOrganization{id: $organization_id})-[:RESOURCE]->(role:GCPRole{id: $RoleId})
    MATCH (:GCPOrganization{id: $organization_id})-[:OWNER]->(project:GCPProject{id: $project_id})
    MERGE (user)-[r1:ASSUME_ROLE{project_id:$project_id}]->(role)-[r2:HAS_ACCESS_TO{email:$UserId}]->(project)
    ON CREATE SET r1.firstseen = timestamp(),
    r2.firstseen = timestamp()
    SET r1.lastupdated = $gcp_update_tag,
    r2.lastupdated = $gcp_update_tag
    WITH user,role
    MATCH (p:GCPOrganization{id: $organization_id})
    MERGE (p)-[pr:RESOURCE]->(user)
    ON CREATE SET
    pr.firstseen = timestamp()
    SET pr.lastupdated = $gcp_update_tag
    """

    neo4j_session.run(
        ingest_script,
        RoleId=role_id,
        UserId=user['id'],
        UserEmail=user['email'],
        UserName=user['name'],
        ConsoleLink=user.get('consolelink'),
        createDate=datetime.utcnow(),
        Parent=user['parent'],
        ParentId=user['parent_id'],
        isDeleted=user.get('is_deleted', False),
        project_id=project_id,
        organization_id=organization_id,
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def attach_project_role_to_service_account(
    neo4j_session: neo4j.Session, role_id: str,
    serviceAccount: Dict, project_id: str, gcp_update_tag: int,
) -> None:
    ingest_script = """
    MATCH (sa:GCPServiceAccount{id: $saId})
    SET
    sa.isDeleted = $isDeleted
    WITH sa
    MATCH (:GCPProject{id: $project_id})-[:RESOURCE]->(role:GCPRole{id: $RoleId})
    MERGE (sa)-[r:ASSUME_ROLE]->(role)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag
    """

    neo4j_session.run(
        ingest_script,
        RoleId=role_id,
        isDeleted=serviceAccount.get('is_deleted', False),
        Parent=serviceAccount['parent'],
        ParentId=serviceAccount['parent_id'],
        saId=serviceAccount['id'],
        project_id=project_id,
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def attach_sso_role_to_service_account(
    neo4j_session: neo4j.Session, role_id: str,
    serviceAccount: Dict, project_id: str, organization_id: str, gcp_update_tag: int,
) -> None:
    ingest_script = """
    MATCH (sa:GCPServiceAccount{id: $saId})
    SET
    sa.isDeleted = $isDeleted
    WITH sa
    MATCH (:GCPOrganization{id: $organization_id})-[:RESOURCE]->(role:GCPRole{id: $RoleId})
    MATCH (:GCPOrganization{id: $organization_id})-[:OWNER]->(project:GCPProject{id: $project_id})
    MERGE (sa)-[r1:ASSUME_ROLE{project_id:$project_id}]->(role)-[r2:HAS_ACCESS_TO{email:$saId}]->(project)
    ON CREATE SET r1.firstseen = timestamp(),
    r2.firstseen = timestamp()
    SET r1.lastupdated = $gcp_update_tag,
    r2.lastupdated = $gcp_update_tag
    """

    neo4j_session.run(
        ingest_script,
        RoleId=role_id,
        isDeleted=serviceAccount.get('is_deleted', False),
        Parent=serviceAccount['parent'],
        ParentId=serviceAccount['parent_id'],
        saId=serviceAccount['id'],
        project_id=project_id,
        organization_id=organization_id,
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def attach_project_role_to_group(
    neo4j_session: neo4j.Session, role_id: str, group: Dict,
    project_id: str, organization_id: str, gcp_update_tag: int,
) -> None:
    ingest_script = """
    MERGE (group:GCPGroup{id: $GroupId})
    ON CREATE SET
    group:GCPPrincipal,
    group.firstseen = timestamp()
    SET
    group.email = $GroupEmail,
    group.name = $GroupName,
    group.create_date = $createDate,
    group.consolelink = $ConsoleLink,
    group.lastupdated = $gcp_update_tag,
    group.isDeleted = $isDeleted
    WITH group
    MATCH (:GCPProject{id: $project_id})-[:RESOURCE]->(role:GCPRole{id: $RoleId})
    MERGE (group)-[r:ASSUME_ROLE]->(role)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag
    WITH group,role
    MATCH (p:GCPOrganization{id: $organization_id})
    MERGE (p)-[pr:RESOURCE]->(group)
    ON CREATE SET
    pr.firstseen = timestamp()
    SET pr.lastupdated = $gcp_update_tag
    """

    neo4j_session.run(
        ingest_script,
        RoleId=role_id,
        GroupId=group['id'],
        GroupName=group['name'],
        createDate=datetime.utcnow(),
        GroupEmail=group['email'],
        ConsoleLink=group['consolelink'],
        Parent=group['parent'],
        ParentId=group['parent_id'],
        isDeleted=group.get('is_deleted', False),
        project_id=project_id,
        organization_id=organization_id,
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def attach_sso_role_to_group(
    neo4j_session: neo4j.Session, role_id: str, group: Dict,
    project_id: str, organization_id: str, gcp_update_tag: int,
) -> None:
    ingest_script = """
    MERGE (group:GCPGroup{id: $GroupId})
    ON CREATE SET
    group:GCPPrincipal,
    group.firstseen = timestamp()
    SET
    group.email = $GroupEmail,
    group.name = $GroupName,
    group.create_date = $createDate,
    group.consolelink = $ConsoleLink,
    group.lastupdated = $gcp_update_tag,
    group.isDeleted = $isDeleted
    WITH group
    MATCH (:GCPOrganization{id: $organization_id})-[:RESOURCE]->(role:GCPRole{id: $RoleId})
    MATCH (:GCPOrganization{id: $organization_id})-[:OWNER]->(project:GCPProject{id: $project_id})
    MERGE (group)-[r1:ASSUME_ROLE{project_id:$project_id}]->(role)-[r2:HAS_ACCESS_TO{email:$GroupId}]->(project)
    ON CREATE SET r1.firstseen = timestamp(),
    r2.firstseen = timestamp()
    SET r1.lastupdated = $gcp_update_tag,
    r2.lastupdated = $gcp_update_tag
    WITH group,role
    MATCH (p:GCPOrganization{id: $organization_id})
    MERGE (p)-[pr:RESOURCE]->(group)
    ON CREATE SET
    pr.firstseen = timestamp()
    SET pr.lastupdated = $gcp_update_tag
    """

    neo4j_session.run(
        ingest_script,
        RoleId=role_id,
        GroupId=group['id'],
        GroupName=group['name'],
        createDate=datetime.utcnow(),
        GroupEmail=group['email'],
        ConsoleLink=group['consolelink'],
        Parent=group['parent'],
        ParentId=group['parent_id'],
        isDeleted=group.get('is_deleted', False),
        project_id=project_id,
        organization_id=organization_id,
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def attach_project_role_to_domain(
    neo4j_session: neo4j.Session, role_id: str, domain: Dict,
    project_id: str, gcp_update_tag: int,
) -> None:
    ingest_script = """
    MERGE (domain:GCPDomain{id: $DomainId})
    ON CREATE SET
    domain:GCPPrincipal,
    domain.firstseen = timestamp()
    SET
    domain.email = $DomainEmail,
    domain.name = $DomainName,
    domain.create_date = $createDate,
    domain.consolelink = $ConsoleLink,
    domain.lastupdated = $gcp_update_tag,
    domain.isDeleted = $isDeleted
    WITH domain
    MATCH (:GCPProject{id: $project_id})-[:RESOURCE]->(role:GCPRole{id: $RoleId})
    MERGE (domain)-[r:ASSUME_ROLE]->(role)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag
    WITH domain,role
    MATCH (p:GCPProject{id: $project_id})
    MERGE (p)-[pr:RESOURCE]->(domain)
    ON CREATE SET
    pr.firstseen = timestamp()
    SET pr.lastupdated = $gcp_update_tag
    """

    neo4j_session.run(
        ingest_script,
        RoleId=role_id,
        DomainId=domain['id'],
        Parent=domain['parent'],
        createDate=datetime.utcnow(),
        ParentId=domain['parent_id'],
        DomainEmail=domain['email'],
        ConsoleLink=domain['consolelink'],
        DomainName=domain['name'],
        isDeleted=domain.get('is_deleted', False),
        project_id=project_id,
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def attach_sso_role_to_domain(
    neo4j_session: neo4j.Session, role_id: str, domain: Dict,
    project_id: str, organization_id: str, gcp_update_tag: int,
) -> None:
    ingest_script = """
    MERGE (domain:GCPDomain{id: $DomainId})
    ON CREATE SET
    domain:GCPPrincipal,
    domain.firstseen = timestamp()
    SET
    domain.email = $DomainEmail,
    domain.name = $DomainName,
    domain.create_date = $createDate,
    domain.consolelink = $ConsoleLink,
    domain.lastupdated = $gcp_update_tag,
    domain.isDeleted = $isDeleted
    WITH domain
    MATCH (:GCPOrganization{id: $organization_id})-[:RESOURCE]->(role:GCPRole{id: $RoleId})
    MATCH (:GCPOrganization{id: $organization_id})-[:OWNER]->(project:GCPProject{id: $project_id})
    MERGE (domain)-[r1:ASSUME_ROLE{project_id:$project_id}]->(role)-[r2:HAS_ACCESS_TO{email:$DomainId}]->(project)
    ON CREATE SET r1.firstseen = timestamp(),
    r2.firstseen = timestamp()
    SET r1.lastupdated = $gcp_update_tag,
    r2.lastupdated = $gcp_update_tag
    WITH domain,role
    MATCH (p:GCPProject{id: $project_id})
    MERGE (p)-[pr:RESOURCE]->(domain)
    ON CREATE SET
    pr.firstseen = timestamp()
    SET pr.lastupdated = $gcp_update_tag
    """

    neo4j_session.run(
        ingest_script,
        RoleId=role_id,
        DomainId=domain['id'],
        Parent=domain['parent'],
        createDate=datetime.utcnow(),
        ParentId=domain['parent_id'],
        DomainEmail=domain['email'],
        ConsoleLink=domain['consolelink'],
        DomainName=domain['name'],
        isDeleted=domain.get('is_deleted', False),
        project_id=project_id,
        organization_id=organization_id,
        gcp_update_tag=gcp_update_tag,
    )


def _set_used_state_tx(
    tx: neo4j.Transaction, project_id: str, common_job_parameters: Dict, update_tag: int,
) -> None:
    ingest_role_used = """
    MATCH (:CloudanixWorkspace{id: $WORKSPACE_ID})-[:OWNER]->
    (:GCPProject{id: $GCP_PROJECT_ID})-[:RESOURCE]->(n:GCPRole)
    WHERE (n)<-[:ASSUME_ROLE]-() AND n.lastupdated = $update_tag
    SET n.isUsed = $isUsed
    """

    tx.run(
        ingest_role_used,
        WORKSPACE_ID=common_job_parameters['WORKSPACE_ID'],
        update_tag=update_tag,
        GCP_PROJECT_ID=project_id,
        isUsed=True,
    )

    ingest_entity_used = """
    MATCH (:CloudanixWorkspace{id: $WORKSPACE_ID})-[:OWNER]->
    (:GCPProject{id: $GCP_PROJECT_ID})-[:RESOURCE]->(n:GCPPrincipal)
    WHERE ()<-[:ASSUME_ROLE]-(n) AND n.lastupdated = $update_tag
    SET n.isUsed = $isUsed
    """

    tx.run(
        ingest_entity_used,
        WORKSPACE_ID=common_job_parameters['WORKSPACE_ID'],
        update_tag=update_tag,
        GCP_PROJECT_ID=project_id,
        isUsed=True,
    )

    ingest_entity_unused = """
    MATCH (:CloudanixWorkspace{id: $WORKSPACE_ID})-[:OWNER]->
    (:GCPProject{id: $GCP_PROJECT_ID})-[:RESOURCE]->(n:GCPPrincipal)
    WHERE n.isUsed IS NULL AND n.lastupdated = $update_tag
    SET n.isUsed = $isUsed
    """

    tx.run(
        ingest_entity_unused,
        WORKSPACE_ID=common_job_parameters['WORKSPACE_ID'],
        update_tag=update_tag,
        GCP_PROJECT_ID=project_id,
        isUsed=False,
    )


@timeit
def sync(
    neo4j_session: neo4j.Session, iam: Resource, policyanalyzer: Resource, crm_v1: Resource, crm_v2: Resource, apikey: Resource,
    project_id: str, gcp_update_tag: int, common_job_parameters: Dict,
) -> None:
    tic = time.perf_counter()

    logger.info("Syncing IAM for project '%s', at %s.", project_id, tic)

    if common_job_parameters.get("EXTERNAL_IDP"):
        external_idp.sync(neo4j_session, common_job_parameters.get("EXTERNAL_IDP"), project_id, gcp_update_tag, common_job_parameters)

    organization_id = common_job_parameters['GCP_ORGANIZATION_ID']

    service_accounts_list = get_service_accounts(iam, project_id)
    service_accounts_list = transform_service_accounts(service_accounts_list, project_id)
    activities = get_service_account_last_used_activities(policyanalyzer, project_id)
    load_service_accounts(neo4j_session, service_accounts_list, project_id, gcp_update_tag)

    for service_account in service_accounts_list:
        service_account_keys = get_service_account_keys(iam, project_id, service_account, activities)
        load_service_account_keys(neo4j_session, service_account_keys, service_account['id'], project_id, gcp_update_tag)

    cleanup_service_accounts(neo4j_session, common_job_parameters)
    label.sync_labels(
        neo4j_session, service_accounts_list, gcp_update_tag,
        common_job_parameters, 'service accounts', 'GCPServiceAccount',
    )

    predefined_roles_list = get_predefined_roles(iam, project_id)
    project_custom_roles_list = get_project_custom_roles(iam, project_id)
    organization_custom_roles_list = get_organization_custom_roles(iam, crm_v1, project_id)

    predefined_roles_list = transform_roles(predefined_roles_list, project_id, 'predefined', common_job_parameters)
    project_custom_roles_list = transform_roles(project_custom_roles_list, project_id, 'custom', common_job_parameters)
    organization_custom_roles_list = transform_roles(organization_custom_roles_list, project_id, 'custom', common_job_parameters)

    load_project_roles(neo4j_session, project_custom_roles_list, project_id, gcp_update_tag)
    load_sso_roles(neo4j_session, predefined_roles_list, common_job_parameters["GCP_ORGANIZATION_ID"], gcp_update_tag)
    load_sso_roles(neo4j_session, organization_custom_roles_list, common_job_parameters["GCP_ORGANIZATION_ID"], gcp_update_tag)

    cleanup_roles(neo4j_session, common_job_parameters)
    label.sync_labels(neo4j_session, project_custom_roles_list, gcp_update_tag, common_job_parameters, 'roles', 'GCPRole')

    keys = get_apikeys_keys(apikey, project_id)
    api_keys = transform_api_keys(keys, project_id)
    load_api_keys(neo4j_session, api_keys, project_id, gcp_update_tag)
    cleanup_api_keys(neo4j_session, common_job_parameters)

    bindings = get_policy_bindings(crm_v1, crm_v2, project_id)
    # users_from_bindings, groups_from_bindings, domains_from_bindings = transform_bindings(bindings, project_id)
    load_bindings(neo4j_session, bindings, project_id, organization_id, gcp_update_tag, common_job_parameters)
    # set_used_state(neo4j_session, project_id, common_job_parameters, gcp_update_tag)

    cleanup_policy_binding(neo4j_session, common_job_parameters)

    toc = time.perf_counter()
    logger.info(f"Time to process IAM: {toc - tic:0.4f} seconds")
