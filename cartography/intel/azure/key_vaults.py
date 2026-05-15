import logging
from typing import Any

import neo4j
from azure.core.exceptions import ResourceNotFoundError
from azure.keyvault.certificates import CertificateClient
from azure.keyvault.keys import KeyClient
from azure.keyvault.secrets import SecretClient
from azure.mgmt.keyvault import KeyVaultManagementClient

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.azure.key_vault import AzureKeyVaultSchema
from cartography.models.azure.key_vault_certificate import (
    AzureKeyVaultCertificateSchema,
)
from cartography.models.azure.key_vault_key import AzureKeyVaultKeySchema
from cartography.models.azure.key_vault_secret import AzureKeyVaultSecretSchema
from cartography.util import timeit

from .util.credentials import Credentials

logger = logging.getLogger(__name__)


@timeit
def get_key_vaults(credentials: Credentials, subscription_id: str) -> list[dict]:
    client = KeyVaultManagementClient(credentials.credential, subscription_id)
    return [vault.as_dict() for vault in client.vaults.list_by_subscription()]


@timeit
def get_secrets(credentials: Credentials, vault_uri: str) -> list[dict]:
    client = SecretClient(vault_url=vault_uri, credential=credentials.credential)
    secrets = []
    for secret_props in client.list_properties_of_secrets():
        secrets.append(
            {
                "id": secret_props.id,
                "name": secret_props.name,
                "enabled": secret_props.enabled,
                "created_on": secret_props.created_on,
                "updated_on": secret_props.updated_on,
            }
        )
    return secrets


@timeit
def get_keys(credentials: Credentials, vault_uri: str) -> list[dict]:
    client = KeyClient(vault_url=vault_uri, credential=credentials.credential)
    keys = []
    for key_props in client.list_properties_of_keys():
        keys.append(
            {
                "id": key_props.id,
                "name": key_props.name,
                "enabled": key_props.enabled,
                "created_on": key_props.created_on,
                "updated_on": key_props.updated_on,
            }
        )
    return keys


@timeit
def get_certificates(credentials: Credentials, vault_uri: str) -> list[dict]:
    client = CertificateClient(vault_url=vault_uri, credential=credentials.credential)
    certs = []
    for cert_props in client.list_properties_of_certificates():
        certs.append(
            {
                "id": cert_props.id,
                "name": cert_props.name,
                "enabled": cert_props.enabled,
                "created_on": cert_props.created_on,
                "updated_on": cert_props.updated_on,
                "x5t": (
                    cert_props.x509_thumbprint.hex()
                    if cert_props.x509_thumbprint
                    else None
                ),
            }
        )
    return certs


def transform_key_vaults(key_vaults_response: list[dict]) -> list[dict]:
    transformed_vaults: list[dict[str, Any]] = []
    for vault in key_vaults_response:
        transformed_vault = {
            "id": vault.get("id"),
            "name": vault.get("name"),
            "location": vault.get("location"),
            "tenant_id": vault.get("properties", {}).get("tenant_id"),
            "sku_name": vault.get("properties", {}).get("sku", {}).get("name"),
            "vault_uri": vault.get("properties", {}).get("vault_uri"),
        }
        transformed_vaults.append(transformed_vault)
    return transformed_vaults


def transform_secrets(secrets_response: list[dict]) -> list[dict]:
    transformed_secrets: list[dict[str, Any]] = []
    for secret in secrets_response:
        transformed_secret = {
            "id": secret.get("id"),
            "name": secret.get("name"),
            "enabled": secret.get("enabled"),
            "created_on": secret.get("created_on"),
            "updated_on": secret.get("updated_on"),
        }
        transformed_secrets.append(transformed_secret)
    return transformed_secrets


def transform_keys(keys_response: list[dict]) -> list[dict]:
    transformed_keys: list[dict[str, Any]] = []
    for key in keys_response:
        transformed_key = {
            "id": key.get("id"),
            "name": key.get("name"),
            "enabled": key.get("enabled"),
            "created_on": key.get("created_on"),
            "updated_on": key.get("updated_on"),
        }
        transformed_keys.append(transformed_key)
    return transformed_keys


def transform_certificates(certificates_response: list[dict]) -> list[dict]:
    transformed_certs: list[dict[str, Any]] = []
    for cert in certificates_response:
        transformed_cert = {
            "id": cert.get("id"),
            "name": cert.get("name"),
            "enabled": cert.get("enabled"),
            "created_on": cert.get("created_on"),
            "updated_on": cert.get("updated_on"),
            "x5t": cert.get("x5t"),
        }
        transformed_certs.append(transformed_cert)
    return transformed_certs


@timeit
def load_key_vaults(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    subscription_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AzureKeyVaultSchema(),
        data,
        lastupdated=update_tag,
        AZURE_SUBSCRIPTION_ID=subscription_id,
    )


@timeit
def load_secrets(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    subscription_id: str,
    vault_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AzureKeyVaultSecretSchema(),
        data,
        lastupdated=update_tag,
        AZURE_SUBSCRIPTION_ID=subscription_id,
        VAULT_ID=vault_id,
    )


@timeit
def load_keys(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    subscription_id: str,
    vault_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AzureKeyVaultKeySchema(),
        data,
        lastupdated=update_tag,
        AZURE_SUBSCRIPTION_ID=subscription_id,
        VAULT_ID=vault_id,
    )


@timeit
def load_certificates(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    subscription_id: str,
    vault_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AzureKeyVaultCertificateSchema(),
        data,
        lastupdated=update_tag,
        AZURE_SUBSCRIPTION_ID=subscription_id,
        VAULT_ID=vault_id,
    )


@timeit
def cleanup_key_vaults(
    neo4j_session: neo4j.Session, common_job_parameters: dict
) -> None:
    GraphJob.from_node_schema(AzureKeyVaultSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync_secrets(
    neo4j_session: neo4j.Session,
    credentials: Credentials,
    subscription_id: str,
    vault_id: str,
    vault_uri: str,
    update_tag: int,
    common_job_parameters: dict,
) -> None:
    raw_secrets = get_secrets(credentials, vault_uri)
    transformed_secrets = transform_secrets(raw_secrets)
    load_secrets(
        neo4j_session, transformed_secrets, subscription_id, vault_id, update_tag
    )

    secret_cleanup_params = common_job_parameters.copy()
    secret_cleanup_params["VAULT_ID"] = vault_id
    GraphJob.from_node_schema(AzureKeyVaultSecretSchema(), secret_cleanup_params).run(
        neo4j_session
    )


@timeit
def sync_keys(
    neo4j_session: neo4j.Session,
    credentials: Credentials,
    subscription_id: str,
    vault_id: str,
    vault_uri: str,
    update_tag: int,
    common_job_parameters: dict,
) -> None:
    raw_keys = get_keys(credentials, vault_uri)
    transformed_keys = transform_keys(raw_keys)
    load_keys(neo4j_session, transformed_keys, subscription_id, vault_id, update_tag)

    key_cleanup_params = common_job_parameters.copy()
    key_cleanup_params["VAULT_ID"] = vault_id
    GraphJob.from_node_schema(AzureKeyVaultKeySchema(), key_cleanup_params).run(
        neo4j_session
    )


@timeit
def sync_certificates(
    neo4j_session: neo4j.Session,
    credentials: Credentials,
    subscription_id: str,
    vault_id: str,
    vault_uri: str,
    update_tag: int,
    common_job_parameters: dict,
) -> None:
    raw_certs = get_certificates(credentials, vault_uri)
    transformed_certs = transform_certificates(raw_certs)
    load_certificates(
        neo4j_session, transformed_certs, subscription_id, vault_id, update_tag
    )

    cert_cleanup_params = common_job_parameters.copy()
    cert_cleanup_params["VAULT_ID"] = vault_id
    GraphJob.from_node_schema(
        AzureKeyVaultCertificateSchema(), cert_cleanup_params
    ).run(neo4j_session)


@timeit
def sync_vaults(
    neo4j_session: neo4j.Session,
    credentials: Credentials,
    subscription_id: str,
    update_tag: int,
    common_job_parameters: dict,
) -> list[dict]:
    raw_vaults = get_key_vaults(credentials, subscription_id)
    transformed_vaults = transform_key_vaults(raw_vaults)
    load_key_vaults(neo4j_session, transformed_vaults, subscription_id, update_tag)
    cleanup_key_vaults(neo4j_session, common_job_parameters)
    return transformed_vaults


@timeit
def sync(
    neo4j_session: neo4j.Session,
    credentials: Credentials,
    subscription_id: str,
    update_tag: int,
    common_job_parameters: dict,
) -> None:
    logger.info(f"Syncing Azure Key Vaults for subscription {subscription_id}.")

    transformed_vaults = sync_vaults(
        neo4j_session,
        credentials,
        subscription_id,
        update_tag,
        common_job_parameters,
    )

    for vault in transformed_vaults:
        vault_id = vault["id"]
        vault_uri = vault.get("vault_uri")
        if vault_uri:
            # Sync secrets, keys, and certificates for this vault
            # Per AGENTS.md: Let errors propagate to surface systemic failures
            # Only catch ResourceNotFoundError for vaults that were deleted between list and access
            try:
                sync_secrets(
                    neo4j_session,
                    credentials,
                    subscription_id,
                    vault_id,
                    vault_uri,
                    update_tag,
                    common_job_parameters,
                )
            except ResourceNotFoundError:
                logger.warning(
                    f"Vault {vault_id} not found when syncing secrets, likely deleted. Skipping."
                )
                continue

            try:
                sync_keys(
                    neo4j_session,
                    credentials,
                    subscription_id,
                    vault_id,
                    vault_uri,
                    update_tag,
                    common_job_parameters,
                )
            except ResourceNotFoundError:
                logger.warning(
                    f"Vault {vault_id} not found when syncing keys, likely deleted. Skipping."
                )
                continue

            try:
                sync_certificates(
                    neo4j_session,
                    credentials,
                    subscription_id,
                    vault_id,
                    vault_uri,
                    update_tag,
                    common_job_parameters,
                )
            except ResourceNotFoundError:
                logger.warning(
                    f"Vault {vault_id} not found when syncing certificates, likely deleted. Skipping."
                )
