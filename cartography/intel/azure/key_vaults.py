import logging
from typing import Dict
from typing import List

import neo4j
from azure.core.exceptions import HttpResponseError
from azure.keyvault.certificates import CertificateClient
from azure.mgmt.keyvault import KeyVaultManagementClient
from cloudconsolelink.clouds.azure import AzureLinker

from .util.credentials import Credentials
from cartography.util import get_azure_resource_group_name
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)
azure_console_link = AzureLinker()


def load_key_vaults(session: neo4j.Session, subscription_id: str, data_list: List[Dict], update_tag: int) -> None:
    session.execute_write(_load_key_vaults_tx, subscription_id, data_list, update_tag)


def load_key_vaults_keys(session: neo4j.Session, subscription_id: str, data_list: List[Dict], update_tag: int) -> None:
    session.execute_write(_load_key_vaults_keys_tx, subscription_id, data_list, update_tag)


def load_key_vaults_secrets(session: neo4j.Session, subscription_id: str, data_list: List[Dict], update_tag: int) -> None:
    session.execute_write(_load_key_vault_secrets_tx, subscription_id, data_list, update_tag)


def load_key_vaults_certificates(session: neo4j.Session, subscription_id: str, data_list: List[Dict], update_tag: int) -> None:
    session.execute_write(_load_key_vault_certificates_tx, subscription_id, data_list, update_tag)


@timeit
def get_key_vault_certificates_client(credentials: Credentials, vault_url: str) -> CertificateClient:
    client = CertificateClient(vault_url, credentials)
    return client


@timeit
def get_key_vaults_client(credentials: Credentials, subscription_id: str) -> KeyVaultManagementClient:
    client = KeyVaultManagementClient(credentials, subscription_id)
    return client


@timeit
def get_key_vaults_list(client: KeyVaultManagementClient) -> List[Dict]:
    try:
        key_vaults_list = list(map(lambda x: x.as_dict(), client.vaults.list_by_subscription()))
        return key_vaults_list
    except HttpResponseError as e:
        logger.warning(f"Error while retrieving key vaults - {e}")
        return []


def update_access_policies(vault: Dict, common_job_parameters: Dict, client: KeyVaultManagementClient):
    List_Certificate_Permissions = False
    for policy in vault.get('properties', {}).get('access_policies', []):
        if policy.get('object_id') == common_job_parameters['Object_ID'] and 'List' in policy.get('permissions', {}).get('certificates') or 'list' in policy.get('permissions', {}).get('certificates'):
            List_Certificate_Permissions = True
            break
    if not List_Certificate_Permissions:
        parameters = {
            "properties": {
                "access_policies": [
                    {
                        "tenant_id": common_job_parameters['AZURE_TENANT_ID'],
                        "object_id": common_job_parameters['Object_ID'],
                        "permissions": {
                            "keys": [
                                "List",
                                "Get",
                            ],
                            "secrets": [
                                "List",
                                "Get",
                            ],
                            "certificates": [
                                "List",
                                "Get",
                            ],
                        },
                    },
                ],
            },
        }
        client.vaults.update_access_policy(resource_group_name=vault['resource_group'], vault_name=vault['name'], operation_kind='add', parameters=parameters)


@timeit
def transform_key_vaults(key_vaults: List[Dict], regions: List, common_job_parameters: Dict) -> List[Dict]:
    key_vaults_data = []
    for vault in key_vaults:
        vault['created_on'] = vault.get('systemData', {}).get('createdAt')
        vault['updated_on'] = vault.get('systemData', {}).get('lastModifiedAt')
        vault['resource_group'] = get_azure_resource_group_name(vault.get('id'))
        vault['consolelink'] = azure_console_link.get_console_link(
            id=vault['id'], primary_ad_domain_name=common_job_parameters['Azure_Primary_AD_Domain_Name'],
        )
        if regions is None:
            key_vaults_data.append(vault)
        else:
            if vault.get('location') in regions or vault.get('location') == 'global':
                key_vaults_data.append(vault)
    return key_vaults_data


def _load_key_vaults_tx(
    tx: neo4j.Transaction, subscription_id: str, key_vaults_list: List[Dict], update_tag: int,
) -> None:
    ingest_vault = """
    UNWIND $key_vaults_list AS vault
    MERGE (k:AzureKeyVault{id: vault.id})
    ON CREATE SET k.firstseen = timestamp(),
    k.type = vault.type,
    k.location = vault.location,
    k.region = vault.location,
    k.uri = vault.properties.vault_uri,
    k.network_acl_default_action = vault.properties.network_acls.default_action,
    k.consolelink = vault.consolelink,
    k.resourcegroup = vault.resource_group
    SET k.lastupdated = $update_tag,
    k.name = vault.name
    WITH k
    MATCH (owner:AzureSubscription{id: $SUBSCRIPTION_ID})
    MERGE (owner)-[r:RESOURCE]->(k)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """

    tx.run(
        ingest_vault,
        key_vaults_list=key_vaults_list,
        SUBSCRIPTION_ID=subscription_id,
        update_tag=update_tag,
    )
    for key_vault in key_vaults_list:
        resource_group = get_azure_resource_group_name(key_vault.get('id'))
        _attach_resource_group_key_vaults(tx, key_vault['id'], resource_group, update_tag)


def _attach_resource_group_key_vaults(tx: neo4j.Transaction, key_vault_id: str, resource_group: str, update_tag: int) -> None:
    ingest_vault = """
    MATCH (k:AzureKeyVault{id: $key_vault_id})
    WITH k
    MATCH (rg:AzureResourceGroup{name: $resource_group})
    MERGE (k)-[r:RESOURCE_GROUP]->(rg)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """
    tx.run(
        ingest_vault,
        key_vault_id=key_vault_id,
        resource_group=resource_group,
        update_tag=update_tag,
    )


@timeit
def get_key_vault_keys_list(client: KeyVaultManagementClient, vault: Dict) -> List[Dict]:

    try:
        keys_list = list(map(lambda x: x.as_dict(), client.keys.list(resource_group_name=vault['resource_group'], vault_name=vault['name'])))
        return keys_list
    except HttpResponseError as e:
        logger.warning(f"Error while retrieving key vaults keys - {e}")
        return []


@timeit
def transform_key_vaults_keys(keys: List[Dict], vault_id: str, common_job_parameters):
    keys_data = []
    for key in keys:
        key['consolelink'] = azure_console_link.get_console_link(
            id=key['key_uri'], primary_ad_domain_name=common_job_parameters['Azure_Primary_AD_Domain_Name'],
        )
        key['vault_id'] = vault_id
        keys_data.append(key)
    return keys_data


def _load_key_vaults_keys_tx(
    tx: neo4j.Transaction, subscription_id: str, key_vault_keys: List[Dict], update_tag: int,
) -> None:

    ingest_keys = """
    UNWIND $KEYS as key
    MERGE (k:AzureKeyVaultKey{id: key.id})
    ON CREATE SET k.firstseen = timestamp(),
    k.name = key.name,
    k.type = key.type,
    k.location = key.location,
    k.region = key.location,
    k.key_uri = key.key_uri,
    k.enabled = key.attributes.enabled,
    k.expires = key.attributes.expires,
    k.created = key.attributes.created,
    k.updated = key.attributes.updated,
    k.exportable = key.attributes.exportable,
    k.consolelink = key.consolelink,
    k.managed = key.managed
    SET k.lastupdated = $update_tag
    WITH k, key
    MATCH (keyvault:AzureKeyVault{id: key.vault_id})
    MERGE (keyvault)-[r:HAS_KEY]->(k)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """

    tx.run(
        ingest_keys,
        KEYS=key_vault_keys,
        SUBSCRIPTION_ID=subscription_id,
        update_tag=update_tag,
    )


@timeit
def get_key_vault_secrets(client: KeyVaultManagementClient, vault: Dict) -> List[Dict]:

    try:
        secrets_list = list(map(lambda x: x.as_dict(), client.secrets.list(resource_group_name=vault['resource_group'], vault_name=vault['name'])))
        return secrets_list
    except HttpResponseError as e:
        logger.warning(f"Error while retrieving secrets list  - {e}")
        return []


@timeit
def transform_key_vault_secrets(secrets: List[Dict], vault_id: str, common_job_parameters):
    secrets_data = []
    for secret in secrets:
        secret['consolelink'] = azure_console_link.get_console_link(
            id=secret['properties']['secret_uri'], primary_ad_domain_name=common_job_parameters['Azure_Primary_AD_Domain_Name'],
        )
        secret['vault_id'] = vault_id
        secrets_data.append(secret)
    return secrets_data


@timeit
def _load_key_vault_secrets_tx(
    tx: neo4j.Transaction, subscription_id: str, key_vault_secrets: List[Dict], update_tag: int,
) -> None:

    ingest_secrets = """
    UNWIND $SECRETS as sec
    MERGE (s:AzureKeyVaultSecret{id: sec.id})
    ON CREATE SET s.firstseen = timestamp(),
    s.name = sec.name,
    s.type = sec.type,
    s.location = sec.location,
    s.region = sec.location,
    s.secret_uri = sec.properties.secret_uri,
    s.enabled = sec.properties.attributes.enabled,
    s.secret_uri_with_version = sec.properties.secret_uri_with_version,
    s.created = sec.properties.attributes.created,
    s.updated = sec.properties.attributes.updated,
    s.consolelink = sec.consolelink,
    s.contentType = sec.content_type,
    s.managed = s.managed
    SET s.lasupdated = $update_tag
    WITH s, sec
    MATCH (keyvault:AzureKeyVault{id: sec.vault_id})
    MERGE (keyvault)-[r:HAS_SECRET]->(s)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """

    tx.run(
        ingest_secrets,
        SECRETS=key_vault_secrets,
        SUBSCRIPTION_ID=subscription_id,
        update_tag=update_tag,
    )


@timeit
def get_key_vault_certificates(client: CertificateClient, vault: Dict) -> List[Dict]:
    certificates_list = []
    try:
        certificates_data = client.list_properties_of_certificates()
        for certificate in certificates_data:
            certificate_data = {}
            certificate_data['created_on'] = certificate.created_on
            certificate_data['enabled'] = certificate.enabled
            certificate_data['expires_on'] = certificate.expires_on
            certificate_data['id'] = certificate.id
            certificate_data['name'] = certificate.name
            certificate_data['not_before'] = certificate.not_before
            certificate_data['updated_on'] = certificate.updated_on
            certificate_data['version'] = certificate.version
            certificates_list.append(certificate_data)
        return certificates_list
    except KeyError as e:
        logger.warning(f"Error while retrieving certificates list - KeyError - {e}")
        return []
    except HttpResponseError as e:
        logger.warning(f"Error while retrieving certificates list - {e}")
        return []


@timeit
def transform_key_vault_certificates(certificates: List[Dict], vault_id: str, common_job_parameters):
    certificates_data = []
    for certificate in certificates:
        certificate['vault_id'] = vault_id
        certificate['consolelink'] = azure_console_link.get_console_link(
            id=certificate['id'], primary_ad_domain_name=common_job_parameters['Azure_Primary_AD_Domain_Name'],
        )
        certificates_data.append(certificate)

    return certificates_data


@timeit
def _load_key_vault_certificates_tx(
    tx: neo4j.Transaction, subscription_id: str, key_vault_certificates: List[Dict], update_tag: int,
) -> None:

    ingest_certificates = """
    UNWIND $CERTS as cert
    MERGE (c:AzureKeyVaultCertificate{id: cert.id})
    ON CREATE SET c.firstseen = timestamp(),
    c.enabled = cert.enabled,
    c.created = cert.created_on,
    c.updated = cert.updated_on,
    c.name = cert.name,
    c.not_before = cert.not_before,
    c.expires_on = cert.expires_on,
    c.version = cert.version,
    c.contentType = cert.content_type,
    c.consolelink = cert.consolelink,
    c.keyId = cert.kid,
    c.secretId = cert.sid
    SET c.lasupdated = $update_tag
    WITH c, cert
    MATCH (keyvault:AzureKeyVault{id: cert.vault_id})
    MERGE (keyvault)-[r:HAS_CERTIFICATE]->(c)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """
    tx.run(
        ingest_certificates,
        CERTS=key_vault_certificates,
        SUBSCRIPTION_ID=subscription_id,
        update_tag=update_tag,
    )


def cleanup_key_vaults(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('azure_import_key_vaults_cleanup.json', neo4j_session, common_job_parameters)


def sync_key_vaults(
    neo4j_session: neo4j.Session, credentials: Credentials, subscription_id: str, update_tag: int,
    common_job_parameters: Dict, regions: list,
) -> None:
    client = get_key_vaults_client(credentials.arm_credentials, subscription_id)
    key_vaults = get_key_vaults_list(client)
    key_vaults_list = transform_key_vaults(key_vaults, regions, common_job_parameters)

    load_key_vaults(neo4j_session, subscription_id, key_vaults_list, update_tag)
    for key_vault in key_vaults_list:
        # KEY VAULT KEYS
        keys = get_key_vault_keys_list(client, key_vault)
        keys_list = transform_key_vaults_keys(keys, key_vault.get('id', None), common_job_parameters)
        load_key_vaults_keys(neo4j_session, subscription_id, keys_list, update_tag)

        # KEY VAULT SECRETS
        secrets = get_key_vault_secrets(client, key_vault)
        secrets_list = transform_key_vault_secrets(secrets, key_vault.get('id', None), common_job_parameters)
        load_key_vaults_secrets(neo4j_session, subscription_id, secrets_list, update_tag)

        # KEY VAULT CERTIFICATES
        try:
            # To update access policies need write permissions
            # update_access_policies(key_vault, common_job_parameters, client)
            certificate_client = get_key_vault_certificates_client(credentials.vault_credentials, key_vault.get('properties', {}).get('vault_uri', None))
            certificates = get_key_vault_certificates(certificate_client, key_vault)
            certificates_list = transform_key_vault_certificates(certificates, key_vault.get('id', None), common_job_parameters)
            load_key_vaults_certificates(neo4j_session, subscription_id, certificates_list, update_tag)
        except HttpResponseError as e:
            logger.warning(f"Error while updating access policies of vault - {e}")

    cleanup_key_vaults(neo4j_session, common_job_parameters)


@timeit
def sync(
    neo4j_session: neo4j.Session, credentials: Credentials, subscription_id: str, update_tag: int,
    common_job_parameters: Dict, region: list,
) -> None:
    logger.info("Syncing key vaults for subscription '%s'.", subscription_id)

    sync_key_vaults(neo4j_session, credentials, subscription_id, update_tag, common_job_parameters, region)
