import argparse
import base64
import json
import logging
import os
from typing import List
from typing import Union

from dynaconf import Dynaconf

from cartography.config import Config

logger = logging.getLogger(__name__)


settings = Dynaconf(
    includes=["settings.toml"],
    load_dotenv=True,
    merge_enabled=True,
    envvar_prefix="CARTOGRAPHY",
)


def check_module_settings(
    module_name: str, required_settings: List[str], multi_tenant: bool = False
) -> bool:
    """
    Check if the required settings for a module are set in the configuration.

    Args:
        module_name (str): The name of the module.
        required_settings (List[str]): A list of required settings for the module.
        multi_tenant (bool): If True, check for each configured tenant.

    Returns:
        bool: True if all required settings are present, False otherwise.
    """
    module_settings = settings.get(module_name.upper(), None)
    if module_settings is None:
        logger.info(
            "%s import is not configured - skipping this module. See docs to configure.",
            module_name,
        )
        return False

    if multi_tenant:
        missing_settings = []
        for tenant_name, tenant_settings in module_settings.items():
            missing_settings.extend(
                [
                    f"{tenant_name}.{setting}"
                    for setting in required_settings
                    if not tenant_settings.get(setting)
                ],
            )
    else:
        missing_settings = [
            setting for setting in required_settings if not module_settings.get(setting)
        ]

    if len(missing_settings) > 0:
        logger.warning(
            "%s import is not configured - skipping this module. Missing settings: %s",
            module_name,
            ", ".join(missing_settings),
        )
        return False
    return True


def deprecated_config(argument_name: str, env_name: str):
    """Helper to deprecate a config argument in favor of an environment variable"""
    msg = (
        f"The '{argument_name}' parameter is deprecated"
        f" use '{env_name}' varenv instead (or define it in settings.toml)"
    )
    logger.warning(msg)


def populate_settings_from_config(config: Union[Config, argparse.Namespace]):
    """
    Populate settings from a Config object.

    This function ensures backwards compatibility with the old settings
    system by allowing settings to be populated from a Config object.

    Args:
        config (Config): The Config object containing the settings.
    """

    # To avoid displaying deprecation warnings for every call, we store a flag
    # in the settings object to indicate that the deprecation warning has been
    # shown.
    # Even if the flag exists, we still want to run this function because in some
    # cases the settings may be updated (e.g. if the user is using a config file
    # that is not the default one).
    # This is a temporary solution until we remove the old settings system.
    if not settings.get("_internal", {}).get("deprecated_config_warning_shown", False):
        settings.update(
            {
                "_internal": {
                    "deprecated_config_warning_shown": True,
                },
            }
        )
        show_deprecation_warning = True
    else:
        show_deprecation_warning = False

    # Common
    if config.update_tag:
        if show_deprecation_warning:
            deprecated_config("update_tag", "CARTOGRAPHY_COMMON__UPDATE_TAG")
        settings.update({"common": {"update_tag": config.update_tag}})
    if config.permission_relationships_file:
        # We do not raise a deprecation warning here because there is a default value
        # for permission_relationships_file in CLI
        settings.update(
            {
                "common": {
                    "permission_relationships_file": config.permission_relationships_file
                }
            }
        )
        # DEPRECATED: Neo4j config (please use cartography.settings instead)
    # Neo4j
    if config.neo4j_user:
        if show_deprecation_warning:
            deprecated_config("neo4j_user", "CARTOGRAPHY_NEO4J__USER")
        settings.update({"neo4j": {"user": config.neo4j_user}})
    if hasattr(config, "neo4j_password"):
        if show_deprecation_warning:
            deprecated_config("neo4j_password_*", "CARTOGRAPHY_NEO4J__PASSWORD")
        settings.update({"neo4j": {"password": config.neo4j_password}})
    if config.neo4j_uri:
        # We do not raise a deprecation warning here because there is a default value for neo4j_uri
        settings.update({"neo4j": {"uri": config.neo4j_uri}})
    if config.neo4j_max_connection_lifetime:
        # We do not raise a deprecation warning here because there is a default value
        # for neo4j_max_connection_lifetime
        settings.update(
            {"neo4j": {"max_connection_lifetime": config.neo4j_max_connection_lifetime}}
        )
    if config.neo4j_database:
        if show_deprecation_warning:
            deprecated_config("neo4j_database", "CARTOGRAPHY_NEO4J__DATABASE")
        settings.update({"neo4j": {"database": config.neo4j_database}})
    # statsd
    if config.statsd_enabled:
        if show_deprecation_warning:
            deprecated_config("statsd_enabled", "CARTOGRAPHY_STATSD__ENABLED")
        settings.update({"statsd": {"enabled": config.statsd_enabled}})
    if config.statsd_prefix:
        if show_deprecation_warning:
            deprecated_config("statsd_prefix", "CARTOGRAPHY_STATSD__PREFIX")
        settings.update({"statsd": {"prefix": config.statsd_prefix}})
    if config.statsd_host:
        # We do not raise a deprecation warning here because there is a default value for statsd_host
        settings.update({"statsd": {"host": config.statsd_host}})
    if config.statsd_port:
        # We do not raise a deprecation warning here because there is a default value for statsd_port
        settings.update({"statsd": {"port": config.statsd_port}})
    # analysis
    if config.analysis_job_directory:
        if show_deprecation_warning:
            deprecated_config(
                "analysis-job-directory", "CARTOGRAPHY_ANALYSIS__JOB_DIRECTORY"
            )
        settings.update({"analysis": {"job_directory": config.analysis_job_directory}})
    # AWS
    if config.aws_requested_syncs:
        if show_deprecation_warning:
            deprecated_config("aws_requested_syncs", "CARTOGRAPHY_AWS__REQUESTED_SYNCS")
        settings.update({"aws": {"requested_syncs": config.aws_requested_syncs}})
    if config.aws_regions:
        if show_deprecation_warning:
            deprecated_config("aws_regions", "CARTOGRAPHY_AWS__REGION")
        settings.update({"aws": {"regions": config.aws_regions}})
    if config.aws_sync_all_profiles:
        if show_deprecation_warning:
            deprecated_config(
                "aws_sync_all_profiles", "CARTOGRAPHY_AWS__SYNC_ALL_PROFILES"
            )
        settings.update({"aws": {"sync_all_profiles": config.aws_sync_all_profiles}})
    if config.aws_best_effort_mode:
        if show_deprecation_warning:
            deprecated_config(
                "aws_best_effort_mode", "CARTOGRAPHY_AWS__BEST_EFFORT_MODE"
            )
        settings.update({"aws": {"best_effort_mode": config.aws_best_effort_mode}})
    # Azure
    if config.azure_sync_all_subscriptions:
        if show_deprecation_warning:
            deprecated_config(
                "azure_sync_all_subscriptions",
                "CARTOGRAPHY_AZURE__SYNC_ALL_SUBSCRIPTIONS",
            )
        settings.update(
            {"azure": {"sync_all_subscriptions": config.azure_sync_all_subscriptions}}
        )
    if config.azure_tenant_id:
        if show_deprecation_warning:
            deprecated_config("azure_tenant_id", "CARTOGRAPHY_AZURE__TENANT_ID")
        settings.update({"azure": {"tenant_id": config.azure_tenant_id}})
    if config.azure_client_id:
        if show_deprecation_warning:
            deprecated_config("azure_client_id", "CARTOGRAPHY_AZURE__CLIENT_ID")
        settings.update({"azure": {"client_id": config.azure_client_id}})
    if hasattr(config, "azure_client_secret"):
        if show_deprecation_warning:
            deprecated_config(
                "azure_client_secret_env_var", "CARTOGRAPHY_AZURE__CLIENT_SECRET"
            )
        settings.update({"azure": {"client_secret": config.azure_client_secret}})
    if config.azure_sp_auth:
        if show_deprecation_warning:
            deprecated_config("azure_sp_auth", "CARTOGRAPHY_AZURE__SP_AUTH")
        settings.update({"azure": {"sp_auth": config.azure_sp_auth}})
    # BigFix
    if config.bigfix_username:
        if show_deprecation_warning:
            deprecated_config("bigfix_username", "CARTOGRAPHY_BIGFIX__USERNAME")
        settings.update({"bigfix": {"username": config.bigfix_username}})
    if hasattr(config, "bigfix_password"):
        if show_deprecation_warning:
            deprecated_config("bigfix_password_env_var", "CARTOGRAPHY_BIGFIX__PASSWORD")
        settings.update({"bigfix": {"password": config.bigfix_password}})
    if config.bigfix_root_url:
        if show_deprecation_warning:
            deprecated_config("bigfix_root_url", "CARTOGRAPHY_BIGFIX__ROOT_URL")
        settings.update({"bigfix": {"root_url": config.bigfix_root_url}})
    # Crowdstrike
    if hasattr(config, "crowdstrike_client_id"):
        if show_deprecation_warning:
            deprecated_config(
                "crowdstrike_client_id_env_var", "CARTOGRAPHY_CROWDSTRIKE__CLIENT_ID"
            )
        settings.update({"crowdstrike": {"client_id": config.crowdstrike_client_id}})
    if hasattr(config, "crowdstrike_client_secret"):
        if show_deprecation_warning:
            deprecated_config(
                "crowdstrike_client_secret_env_var",
                "CARTOGRAPHY_CROWDSTRIKE__CLIENT_SECRET",
            )
        settings.update(
            {"crowdstrike": {"client_secret": config.crowdstrike_client_secret}}
        )
    if config.crowdstrike_api_url:
        if show_deprecation_warning:
            deprecated_config("crowdstrike_api_url", "CARTOGRAPHY_CROWDSTRIKE__API_URL")
        settings.update({"crowdstrike": {"api_url": config.crowdstrike_api_url}})
    # CVE
    if hasattr(config, "cve_api_key"):
        if show_deprecation_warning:
            deprecated_config("cve_api_key_env_var", "CARTOGRAPHY_CVE__API_KEY")
        settings.update({"cve": {"api_key": config.cve_api_key}})
    if config.cve_enabled:
        if show_deprecation_warning:
            deprecated_config("cve_enabled", "CARTOGRAPHY_CVE__ENABLED")
        settings.update({"cve": {"enabled": config.cve_enabled}})
    if config.nist_cve_url:
        # We do not raise a deprecation warning here because there is a default value for nist_cve_url
        settings.update({"cve": {"url": config.nist_cve_url}})
    # DigitaOcean
    if hasattr(config, "digitalocean_token"):
        if show_deprecation_warning:
            deprecated_config(
                "digitalocean_token_env_var", "CARTOGRAPHY_DIGITALOCEAN__TOKEN"
            )
        settings.update({"digitalocean": {"token": config.digitalocean_token}})
    # Duo
    if hasattr(config, "duo_api_key"):
        if show_deprecation_warning:
            deprecated_config("duo_api_key_env_var", "CARTOGRAPHY_DUO__API_KEY")
        settings.update({"duo": {"api_key": config.duo_api_key}})
    if hasattr(config, "duo_api_secret"):
        if show_deprecation_warning:
            deprecated_config("duo_api_secret_env_var", "CARTOGRAPHY_DUO__API_SECRET")
        settings.update({"duo": {"api_secret": config.duo_api_secret}})
    if config.duo_api_hostname:
        if show_deprecation_warning:
            deprecated_config("duo_api_hostname", "CARTOGRAPHY_DUO__API_HOSTNAME")
        settings.update({"duo": {"api_hostname": config.duo_api_hostname}})
    # GitHub
    if hasattr(config, "github_config"):
        deprecated_config("github_config_env_var", "CARTOGRAPHY_GITHUB__*")
        try:
            auth_tokens = json.loads(
                base64.b64decode(
                    config.github_config.encode(),
                ).decode(),
            )
            for idx, auth_data in enumerate(auth_tokens["organization"]):
                settings.update(
                    {
                        "github": {
                            f"org{idx + 1}": {
                                "name": auth_data["name"],
                                "token": auth_data["token"],
                                "url": auth_data["url"],
                            },
                        },
                    }
                )
        except Exception as e:
            logger.warning(
                "Impossible to parse the github_config parameter, "
                "this parameter must be a valid JSON encoded as base64",
            )
            logger.debug(e)
    # GSuite
    if config.gsuite_auth_method:
        # We do not raise a deprecation warning here because there is a default value for gsuite_auth_method
        settings.update({"gsuite": {"auth_method": config.gsuite_auth_method}})
    if config.gsuite_config:
        if show_deprecation_warning:
            deprecated_config("github_config", "CARTOGRAPHY_GSUITE__*")
        if config.gsuite_auth_method == "delegated":
            settings.update(
                {
                    "gsuite": {
                        "settings_account_file": config.gsuite_config,
                    },
                }
            )
        elif config.gsuite_auth_method == "oauth":
            try:
                auth_tokens = json.loads(
                    str(
                        base64.b64decode(config.gsuite_config).decode(),
                    ),
                )
                settings.update(
                    {
                        "gsuite": {
                            "client_id": auth_tokens.get("client_id"),
                            "client_secret": auth_tokens.get("client_secret"),
                            "refresh_token": auth_tokens.get("refresh_token"),
                            "token_uri": auth_tokens.get("token_uri"),
                        },
                    }
                )
            except Exception as e:
                logger.warning(
                    "Impossible to parse the gsuite_config parameter, "
                    "this parameter must be a valid JSON encoded as base64 "
                    "when using 'oauth' as auth method.",
                )
                logger.debug(e)
    if os.environ.get("GSUITE_DELEGATED_ADMIN") is not None:
        if show_deprecation_warning:
            deprecated_config(
                "GSUITE_DELEGATED_ADMIN", "CARTOGRAPHY_GSUITE__DELEGATED_ADMIN"
            )
        settings.update(
            {"gsuite": {"delegated_admin": os.environ.get("GSUITE_DELEGATED_ADMIN")}}
        )
    # Jamf
    if config.jamf_base_uri:
        if show_deprecation_warning:
            deprecated_config("jamf_base_uri", "CARTOGRAPHY_JAMF__BASE_URL")
        settings.update({"jamf": {"base_url": config.jamf_base_uri}})
    if config.jamf_user:
        if show_deprecation_warning:
            deprecated_config("jamf_user", "CARTOGRAPHY_JAMF__USER")
        settings.update({"jamf": {"user": config.jamf_user}})
    if hasattr(config, "jamf_password"):
        if show_deprecation_warning:
            deprecated_config("jamf_password_env_var", "CARTOGRAPHY_JAMF__PASSWORD")
        settings.update({"jamf": {"password": config.jamf_password}})
    # K8S
    if config.k8s_kubeconfig:
        if show_deprecation_warning:
            deprecated_config("k8s_kubeconfig", "CARTOGRAPHY_K8S__KUBECONFIG")
        settings.update({"k8s": {"kubeconfig": config.k8s_kubeconfig}})
    # Kandji
    if config.kandji_base_uri:
        if show_deprecation_warning:
            deprecated_config("kandji_base_uri", "CARTOGRAPHY_KANDJI__BASE_URL")
        settings.update({"kandji": {"base_url": config.kandji_base_uri}})
    if config.kandji_tenant_id:
        if show_deprecation_warning:
            deprecated_config("kandji_tenant_id", "CARTOGRAPHY_KANDJI__TENANT_ID")
        settings.update({"kandji": {"tenant_id": config.kandji_tenant_id}})
    if hasattr(config, "kandji_token"):
        if show_deprecation_warning:
            deprecated_config("kandji_token_env_var", "CARTOGRAPHY_KANDJI__TOKEN")
        settings.update({"kandji": {"token": config.kandji_token}})
    # LastPass
    if hasattr(config, "lastpass_cid"):
        if show_deprecation_warning:
            deprecated_config("lastpass_cid_env_var", "CARTOGRAPHY_LASTPASS__CID")
        settings.update({"lastpass": {"cid": config.lastpass_cid}})
    if hasattr(config, "lastpass_provhash"):
        if show_deprecation_warning:
            deprecated_config(
                "lastpass_provhash_env_var", "CARTOGRAPHY_LASTPASS__PROVHASH"
            )
        settings.update({"lastpass": {"provhash": config.lastpass_provhash}})
    # OCI
    if config.oci_sync_all_profiles:
        if show_deprecation_warning:
            deprecated_config(
                "oci_sync_all_profiles", "CARTOGRAPHY_OCI__SYNC_ALL_PROFILES"
            )
        settings.update({"oci": {"sync_all_profiles": config.oci_sync_all_profiles}})
    # Okta
    if config.okta_org_id:
        if show_deprecation_warning:
            deprecated_config("okta_org_id", "CARTOGRAPHY_OKTA__ORG_ID")
        settings.update({"okta": {"org_id": config.okta_org_id}})
    if hasattr(config, "okta_api_key"):
        if show_deprecation_warning:
            deprecated_config("okta_api_key_env_var", "CARTOGRAPHY_OKTA__API_KEY")
        settings.update({"okta": {"api_key": config.okta_api_key}})
    if config.okta_saml_role_regex:
        # We do not raise a deprecation warning here because there is a default value for okta_saml_role_regex
        settings.update({"okta": {"saml_role_regex": config.okta_saml_role_regex}})
    # PagerDuty
    if hasattr(config, "pagerduty_api_key"):
        if show_deprecation_warning:
            deprecated_config(
                "pagerduty_api_key_env_var", "CARTOGRAPHY_PAGERDUTY__API_KEY"
            )
        settings.update({"pagerduty": {"api_key": config.pagerduty_api_key}})
    if config.pagerduty_request_timeout:
        if show_deprecation_warning:
            deprecated_config(
                "pagerduty_request_timeout", "CARTOGRAPHY_COMMON__HTTP_TIMEOUT"
            )
        if config.pagerduty_request_timeout > settings.common.http_timeout:
            logger.warning(
                "(LEGACY) PagerDuty request timeout (%d) is greater than the default HTTP timeout (%d).",
                config.pagerduty_request_timeout,
                settings.common.http_timeout,
            )
            settings.update(
                {"common": {"http_timeout": config.pagerduty_request_timeout}}
            )
    # Semgrep
    if hasattr(config, "semgrep_app_token"):
        if show_deprecation_warning:
            deprecated_config("semgrep_app_token_env_var", "CARTOGRAPHY_SEMGREP__TOKEN")
        settings.update({"semgrep": {"token": config.semgrep_app_token}})
    if config.semgrep_dependency_ecosystems:
        if show_deprecation_warning:
            deprecated_config(
                "semgrep_dependency_ecosystems",
                "CARTOGRAPHY_SEMGREP__DEPENDENCY_ECOSYSTEMS",
            )
        settings.update(
            {"semgrep": {"dependency_ecosystems": config.semgrep_dependency_ecosystems}}
        )
    # SnipeIT
    if config.snipeit_base_uri:
        if show_deprecation_warning:
            deprecated_config("snipeit_base_uri", "CARTOGRAPHY_SNIPEIT__BASE_URL")
        settings.update({"snipeit": {"base_url": config.snipeit_base_uri}})
    if config.snipeit_tenant_id:
        if show_deprecation_warning:
            deprecated_config("snipeit_tenant_id", "CARTOGRAPHY_SNIPEIT__TENANT_ID")
        settings.update({"snipeit": {"tenant_id": config.snipeit_tenant_id}})
    if hasattr(config, "snipeit_token"):
        if show_deprecation_warning:
            deprecated_config("snipeit_token_env_var", "CARTOGRAPHY_SNIPEIT__TOKEN")
        settings.update({"snipeit": {"token": config.snipeit_token}})
    # Entra
    if config.entra_client_id:
        if show_deprecation_warning:
            deprecated_config("entra_client_id", "CARTOGRAPHY_ENTRA__CLIENT_ID")
        settings.update({"entra": {"client_id": config.entra_client_id}})
    if config.entra_client_secret:
        if show_deprecation_warning:
            deprecated_config(
                "entra_client_secret_env_var", "CARTOGRAPHY_ENTRA__CLIENT_SECRET"
            )
        settings.update({"entra", {"client_secret": str(config.entra_client_secret)}})
    if config.entra_tenant_id:
        if show_deprecation_warning:
            deprecated_config("entra_tenant_id", "CARTOGRAPHY_ENTRA__TENANT_ID")
        settings.update({"entra": {"tenant_id": config.entra_tenant_id}})
