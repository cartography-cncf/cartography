import argparse
import getpass
import logging
import os
import sys
from typing import Optional

import cartography.config
import cartography.sync
import cartography.util
from cartography.intel.aws.util.common import parse_and_validate_aws_requested_syncs
from cartography.intel.semgrep.dependencies import parse_and_validate_semgrep_ecosystems


logger = logging.getLogger(__name__)


class CLI:
    """
    :type sync: cartography.sync.Sync
    :param sync: A sync task for the command line program to execute.
    :type prog: string
    :param prog: The name of the command line program. This will be displayed in usage and help output.
    """

    def __init__(self, sync: Optional[cartography.sync.Sync] = None, prog: Optional[str] = None):
        self.sync = sync if sync else cartography.sync.build_default_sync()
        self.prog = prog
        self.parser = self._build_parser()

    def _build_parser(self):
        """
        :rtype: argparse.ArgumentParser
        :return: A cartography argument parser. Calling parse_args on the argument parser will return an object which
            implements the cartography.config.Config interface.
        """
        parser = argparse.ArgumentParser(
            prog=self.prog,
            description=(
                "cartography consolidates infrastructure assets and the relationships between them in an intuitive "
                "graph view. This application can be used to pull configuration data from multiple sources, load it "
                "in to Neo4j, and run arbitrary enrichment and analysis on that data. Please make sure you have Neo4j "
                "running and have configured AWS credentials with the SecurityAudit IAM policy before getting started. "
                "Running cartography with no parameters will execute a simple sync against a Neo4j instance running "
                "locally. It will use your default AWS credentials and will not execute and post-sync analysis jobs. "
                "Please see the per-parameter documentation below for information on how to connect to different Neo4j "
                "instances, use auth when communicating with Neo4j, sync data from multiple AWS accounts, and execute "
                "arbitrary analysis jobs after the conclusion of the sync."
            ),
            epilog='For more documentation please visit: https://github.com/lyft/cartography',
        )
        parser.add_argument(
            '-v',
            '--verbose',
            action='store_true',
            help='Enable verbose logging for cartography.',
        )
        parser.add_argument(
            '-q',
            '--quiet',
            action='store_true',
            help='Restrict cartography logging to warnings and errors only.',
        )
        parser.add_argument(
            '--neo4j-uri',
            type=str,
            default='bolt://localhost:7687',
            help=(
                'A valid Neo4j URI to sync against. See '
                'https://neo4j.com/docs/api/python-driver/current/driver.html#uri for complete documentation on the '
                'structure of a Neo4j URI.'
            ),
        )
        parser.add_argument(
            '--neo4j-user',
            type=str,
            default=None,
            help='A username with which to authenticate to Neo4j.',
        )
        parser.add_argument(
            '--neo4j-password-env-var',
            type=str,
            default=None,
            help='The name of an environment variable containing a password with which to authenticate to Neo4j.',
        )
        parser.add_argument(
            '--neo4j-password-prompt',
            action='store_true',
            help=(
                'Present an interactive prompt for a password with which to authenticate to Neo4j. This parameter '
                'supersedes other methods of supplying a Neo4j password.'
            ),
        )
        parser.add_argument(
            '--neo4j-max-connection-lifetime',
            type=int,
            default=3600,
            help=(
                'Time in seconds for the Neo4j driver to consider a TCP connection alive. cartography default = 3600, '
                'which is the same as the Neo4j driver default. See '
                'https://neo4j.com/docs/driver-manual/1.7/client-applications/#driver-config-connection-pool-management'
                '.'
            ),
        )
        parser.add_argument(
            '--neo4j-database',
            type=str,
            default=None,
            help=(
                'The name of the database in Neo4j to connect to. If not specified, uses the config settings of your '
                'Neo4j database itself to infer which database is set to default. '
                'See https://neo4j.com/docs/api/python-driver/4.4/api.html#database.'
            ),
        )
        parser.add_argument(
            '--selected-modules',
            type=str,
            default=None,
            help=(
                'Comma-separated list of cartography top-level modules to sync. Example 1: "aws,gcp" to run AWS and GCP'
                'modules. See the full list available in source code at cartography.sync. '
                'If not specified, cartography by default will run all modules available and log warnings when it '
                'does not find credentials configured for them. '
                # TODO remove this mention about the create-indexes module when everything is using auto-indexes.
                'We recommend that you always specify the `create-indexes` module first in this list. '
                'If you specify the `analysis` module, we recommend that you include it as the LAST item of this list, '
                '(because it does not make sense to perform analysis on an empty/out-of-date graph).'
            ),
        )
        # TODO add the below parameters to a 'sync' subparser
        parser.add_argument(
            '--update-tag',
            type=int,
            default=None,
            help=(
                'A unique tag to apply to all Neo4j nodes and relationships created or updated during the sync run. '
                'This tag is used by cleanup jobs to identify nodes and relationships that are stale and need to be '
                'removed from the graph. By default, cartography will use a UNIX timestamp as the update tag.'
            ),
        )
        parser.add_argument(
            '--aws-sync-all-profiles',
            action='store_true',
            help=(
                'Enable AWS sync for all discovered named profiles. When this parameter is supplied cartography will '
                'discover all configured AWS named profiles (see '
                'https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-profiles.html) and run the AWS sync '
                'job for each profile not named "default". If this parameter is not supplied, cartography will use the '
                'default AWS credentials available in your environment to run the AWS sync once. When using this '
                'parameter it is suggested that you create an AWS config file containing a named profile for each AWS '
                'account you want to sync and use the AWS_CONFIG_FILE environment variable to point to that config '
                'file (see https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-envvars.html). cartography '
                'respects the AWS CLI/SDK environment variables and does not override them.'
            ),
        )
        parser.add_argument(
            '--aws-best-effort-mode',
            action='store_true',
            help=(
                'Enable AWS sync best effort mode when syncing AWS accounts. This will allow cartography to continue '
                'syncing other accounts and delay raising an exception until the very end.'
            ),
        )
        parser.add_argument(
            '--oci-sync-all-profiles',
            action='store_true',
            help=(
                'Enable OCI sync for all discovered named profiles. When this parameter is supplied cartography will '
                'discover all configured OCI named profiles (see '
                'https://docs.oracle.com/en-us/iaas/Content/API/Concepts/sdkconfig.htm) and run the OCI sync '
                'job for each profile not named "DEFAULT". If this parameter is not supplied, cartography will use the '
                'default OCI credentials available in your environment to run the OCI sync once.'
            ),
        )
        parser.add_argument(
            '--azure-sync-all-subscriptions',
            action='store_true',
            help=(
                'Enable Azure sync for all discovered subscriptions. When this parameter is supplied cartography will '
                'discover all configured Azure subscriptions.'
            ),
        )
        parser.add_argument(
            '--azure-sp-auth',
            action='store_true',
            help=(
                'Use Service Principal authentication for Azure sync.'
            ),
        )
        parser.add_argument(
            '--azure-tenant-id',
            type=str,
            default=None,
            help=(
                'Azure Tenant Id for Service Principal Authentication.'
            ),
        )
        parser.add_argument(
            '--azure-client-id',
            type=str,
            default=None,
            help=(
                'Azure Client Id for Service Principal Authentication.'
            ),
        )
        parser.add_argument(
            '--azure-client-secret-env-var',
            type=str,
            default=None,
            help=(
                'The name of environment variable containing Azure Client Secret for Service Principal Authentication.'
            ),
        )
        parser.add_argument(
            '--aws-requested-syncs',
            type=str,
            default=None,
            help=(
                'Comma-separated list of AWS resources to sync. Example 1: "ecr,s3,ec2:instance" for ECR, S3, and all '
                'EC2 instance resources. See the full list available in source code at cartography.intel.aws.resources.'
                ' If not specified, cartography by default will run all AWS sync modules available.'
            ),
        )
        parser.add_argument(
            '--analysis-job-directory',
            type=str,
            default=None,
            help=(
                'A path to a directory containing analysis jobs to run at the conclusion of the sync. cartography will '
                'discover all JSON files in the given directory (and its subdirectories) and pass them to the GraphJob '
                'API to execute against the graph. This allows you to apply data transformation and augmentation at '
                'the end of a sync run without writing code. cartography does not guarantee the order in which the '
                'jobs are executed.'
            ),
        )
        parser.add_argument(
            '--okta-org-id',
            type=str,
            default=None,
            help=(
                'Okta organizational id to sync. Required if you are using the Okta intel module. Ignored otherwise.'
            ),
        )
        parser.add_argument(
            '--okta-api-key-env-var',
            type=str,
            default=None,
            help=(
                'The name of an environment variable containing a key with which to auth to the Okta API.'
                'Required if you are using the Okta intel module. Ignored otherwise.'
            ),
        )
        parser.add_argument(
            '--okta-saml-role-regex',
            type=str,
            default=r"^aws\#\S+\#(?{{role}}[\w\-]+)\#(?{{accountid}}\d+)$",
            help=(
                'The regex used to map Okta groups to AWS roles when using okta as a SAML provider.'
                'The regex is the one entered in Step 5: Enabling Group Based Role Mapping in Okta'
                'https://saml-doc.okta.com/SAML_Docs/How-to-Configure-SAML-2.0-for-Amazon-Web-Service#c-step5'
                'The regex must contain the {{role}} and {{accountid}} tags'
            ),
        )
        parser.add_argument(
            '--github-config-env-var',
            type=str,
            default=None,
            help=(
                'The name of an environment variable containing a Base64 encoded GitHub config object.'
                'Required if you are using the GitHub intel module. Ignored otherwise.'
            ),
        )
        parser.add_argument(
            '--digitalocean-token-env-var',
            type=str,
            default=None,
            help=(
                'The name of an environment variable containing a DigitalOcean access token.'
                'Required if you are using the DigitalOcean intel module. Ignored otherwise.'
            ),
        )
        parser.add_argument(
            '--permission-relationships-file',
            type=str,
            default="cartography/data/permission_relationships.yaml",
            help=(
                'The path to the permission relationships mapping file.'
                'If omitted the default permission relationships will be created'
            ),
        )
        parser.add_argument(
            '--jamf-base-uri',
            type=str,
            default=None,
            help=(
                'Your Jamf base URI, e.g. https://hostname.com/JSSResource.'
                'Required if you are using the Jamf intel module. Ignored otherwise.'
            ),
        )
        parser.add_argument(
            '--jamf-user',
            type=str,
            default=None,
            help='A username with which to authenticate to Jamf.',
        )
        parser.add_argument(
            '--jamf-password-env-var',
            type=str,
            default=None,
            help='The name of an environment variable containing a password with which to authenticate to Jamf.',
        )
        parser.add_argument(
            '--kandji-base-uri',
            type=str,
            default=None,
            help=(
                'Your Kandji base URI, e.g. https://company.api.kandji.io.'
                'Required if you are using the Kandji intel module. Ignored otherwise.'
            ),
        )
        parser.add_argument(
            '--kandji-tenant-id',
            type=str,
            default=None,
            help=(
                'Your Kandji tenant id e.g. company.'
                'Required using the Kandji intel module. Ignored otherwise.'
            ),
        )
        parser.add_argument(
            '--kandji-token-env-var',
            type=str,
            default=None,
            help='The name of an environment variable containing token with which to authenticate to Kandji.',
        )
        parser.add_argument(
            '--k8s-kubeconfig',
            default=None,
            type=str,
            help=(
                'The path to kubeconfig file specifying context to access K8s cluster(s).'
            ),
        )
        parser.add_argument(
            '--nist-cve-url',
            type=str,
            default='https://services.nvd.nist.gov/rest/json/cves/2.0/',
            help=(
                'The base url for the NIST CVE data. Default = https://services.nvd.nist.gov/rest/json/cves/2.0/'
            ),
        )
        parser.add_argument(
            '--cve-enabled',
            action='store_true',
            help=(
                'If set, CVE data will be synced from NIST.'
            ),
        )
        parser.add_argument(
            '--cve-api-key-env-var',
            type=str,
            default=None,
            help=(
                'If set, uses the provided NIST NVD API v2.0 key.'
            ),
        )
        parser.add_argument(
            '--statsd-enabled',
            action='store_true',
            help=(
                'If set, enables sending metrics using statsd to a server of your choice.'
            ),
        )
        parser.add_argument(
            '--statsd-prefix',
            type=str,
            default='',
            help=(
                'The string to prefix statsd metrics with. Only used if --statsd-enabled is on. Default = empty string.'
            ),
        )
        parser.add_argument(
            '--statsd-host',
            type=str,
            default='127.0.0.1',
            help=(
                'The IP address of your statsd server. Only used if --statsd-enabled is on. Default = 127.0.0.1.'
            ),
        )
        parser.add_argument(
            '--statsd-port',
            type=int,
            default=8125,
            help=(
                'The port of your statsd server. Only used if --statsd-enabled is on. Default = UDP 8125.'
            ),
        )
        parser.add_argument(
            '--pagerduty-api-key-env-var',
            type=str,
            default=None,
            help=(
                'The name of environment variable containing the pagerduty API key for authentication.'
            ),
        )
        parser.add_argument(
            '--pagerduty-request-timeout',
            type=int,
            default=None,
            help=(
                'Seconds to timeout for pagerduty API sessions.'
            ),
        )
        parser.add_argument(
            '--crowdstrike-client-id-env-var',
            type=str,
            default=None,
            help=(
                'The name of environment variable containing the crowdstrike client id for authentication.'
            ),
        )
        parser.add_argument(
            '--crowdstrike-client-secret-env-var',
            type=str,
            default=None,
            help=(
                'The name of environment variable containing the crowdstrike secret key for authentication.'
            ),
        )
        parser.add_argument(
            '--crowdstrike-api-url',
            type=str,
            default=None,
            help=(
                'The crowdstrike URL, if using self-hosted. Defaults to the public crowdstrike API URL otherwise.'
            ),
        )
        parser.add_argument(
            '--gsuite-auth-method',
            type=str,
            default='delegated',
            choices=['delegated', 'oauth'],
            help=(
                'The method used by GSuite to authenticate. delegated is the legacy one.'
            ),
        )
        parser.add_argument(
            '--gsuite-tokens-env-var',
            type=str,
            default='GSUITE_GOOGLE_APPLICATION_CREDENTIALS',
            help=(
                'The name of environment variable containing secrets for GSuite authentication.'
            ),
        )
        parser.add_argument(
            '--lastpass-cid-env-var',
            type=str,
            default=None,
            help=(
                'The name of environment variable containing the Lastpass CID for authentication.'
            ),
        )
        parser.add_argument(
            '--lastpass-provhash-env-var',
            type=str,
            default=None,
            help=(
                'The name of environment variable containing the Lastpass provhash for authentication.'
            ),
        )
        parser.add_argument(
            '--bigfix-username',
            type=str,
            default=None,
            help=(
                'The BigFix username for authentication.'
            ),
        )
        parser.add_argument(
            '--bigfix-password-env-var',
            type=str,
            default=None,
            help=(
                'The name of environment variable containing the BigFix password for authentication.'
            ),
        )
        parser.add_argument(
            '--bigfix-root-url',
            type=str,
            default=None,
            help=(
                'The BigFix Root URL, a.k.a the BigFix API URL'
            ),
        )
        parser.add_argument(
            '--duo-api-key-env-var',
            type=str,
            default=None,
            help=(
                'The name of environment variable containing the Duo api key'
            ),
        )
        parser.add_argument(
            '--duo-api-secret-env-var',
            type=str,
            default=None,
            help=(
                'The name of environment variable containing the Duo api secret'
            ),
        )
        parser.add_argument(
            '--duo-api-hostname',
            type=str,
            default=None,
            help=(
                'The Duo api hostname'
            ),
        )
        parser.add_argument(
            '--semgrep-app-token-env-var',
            type=str,
            default=None,
            help=(
                'The name of environment variable containing the Semgrep app token key. '
                'Required if you are using the Semgrep intel module. Ignored otherwise.'
            ),
        )
        parser.add_argument(
            '--semgrep-dependency-ecosystems',
            type=str,
            default=None,
            help=(
                'Comma-separated list of language ecosystems for which dependencies will be retrieved from Semgrep. '
                'For example, a value of "gomod,npm" will retrieve Go and NPM dependencies. '
                'See the full list of supported ecosystems in source code at cartography.intel.semgrep.dependencies. '
                'Required if you are using the Semgrep dependencies intel module. Ignored otherwise.'
            ),
        )
        parser.add_argument(
            '--snipeit-base-uri',
            type=str,
            default=None,
            help=(
                'Your SnipeIT base URI'
                'Required if you are using the SnipeIT intel module. Ignored otherwise.'
            ),
        )
        parser.add_argument(
            '--snipeit-token-env-var',
            type=str,
            default=None,
            help='The name of an environment variable containing token with which to authenticate to SnipeIT.',
        )
        parser.add_argument(
            '--snipeit-tenant-id',
            type=str,
            default=None,
            help='An ID for the SnipeIT tenant.',
        )

        return parser

    def main(self, argv: str) -> int:
        """
        Entrypoint for the command line interface.

        :type argv: string
        :param argv: The parameters supplied to the command line program.
        """
        # TODO support parameter lookup in environment variables if not present on command line
        config: argparse.Namespace = self.parser.parse_args(argv)
        # Logging config
        if config.verbose:
            logging.getLogger('cartography').setLevel(logging.DEBUG)
        elif config.quiet:
            logging.getLogger('cartography').setLevel(logging.WARNING)
        else:
            logging.getLogger('cartography').setLevel(logging.INFO)
        logger.debug("Launching cartography with CLI configuration: %r", vars(config))
        # Neo4j config
        if config.neo4j_user:
            config.neo4j_password = None
            if config.neo4j_password_prompt:
                logger.info("Reading password for Neo4j user '%s' interactively.", config.neo4j_user)
                config.neo4j_password = getpass.getpass()
            elif config.neo4j_password_env_var:
                logger.debug(
                    "Reading password for Neo4j user '%s' from environment variable '%s'.",
                    config.neo4j_user,
                    config.neo4j_password_env_var,
                )
                config.neo4j_password = os.environ.get(config.neo4j_password_env_var)
            if not config.neo4j_password:
                logger.warning("Neo4j username was provided but a password could not be found.")
        else:
            config.neo4j_password = None

        # Selected modules
        if config.selected_modules:
            self.sync = cartography.sync.build_sync(config.selected_modules)

        # AWS config
        if config.aws_requested_syncs:
            # No need to store the returned value; we're using this for input validation.
            parse_and_validate_aws_requested_syncs(config.aws_requested_syncs)

        # Azure config
        if config.azure_sp_auth and config.azure_client_secret_env_var:
            logger.debug(
                "Reading Client Secret for Azure Service Principal Authentication from environment variable %s",
                config.azure_client_secret_env_var,
            )
            config.azure_client_secret = os.environ.get(config.azure_client_secret_env_var)
        else:
            config.azure_client_secret = None

        # Okta config
        if config.okta_org_id and config.okta_api_key_env_var:
            logger.debug(f"Reading API key for Okta from environment variable {config.okta_api_key_env_var}")
            config.okta_api_key = os.environ.get(config.okta_api_key_env_var)
        else:
            config.okta_api_key = None

        # GitHub config
        if config.github_config_env_var:
            logger.debug(f"Reading config string for GitHub from environment variable {config.github_config_env_var}")
            config.github_config = os.environ.get(config.github_config_env_var)
        else:
            config.github_config = None

        # DigitalOcean config
        if config.digitalocean_token_env_var:
            logger.debug(f"Reading token for DigitalOcean from env variable {config.digitalocean_token_env_var}")
            config.digitalocean_token = os.environ.get(config.digitalocean_token_env_var)
        else:
            config.digitalocean_token = None

        # Jamf config
        if config.jamf_base_uri:
            if config.jamf_user:
                config.jamf_password = None
                if config.jamf_password_env_var:
                    logger.debug(
                        "Reading password for Jamf user '%s' from environment variable '%s'.",
                        config.jamf_user,
                        config.jamf_password_env_var,
                    )
                    config.jamf_password = os.environ.get(config.jamf_password_env_var)
            if not config.jamf_user:
                logger.warning("A Jamf base URI was provided but a user was not.")
            if not config.jamf_password:
                logger.warning("A Jamf password could not be found.")
        else:
            config.jamf_user = None
            config.jamf_password = None

        # Kandji config
        if config.kandji_base_uri:
            if config.kandji_token_env_var:
                logger.debug(
                    "Reading Kandji API token from environment variable '%s'.",
                    config.kandji_token_env_var,
                )
                config.kandji_token = os.environ.get(config.kandji_token_env_var)
            elif os.environ.get('KANDJI_TOKEN'):
                logger.debug(
                    "Reading Kandji API token from environment variable 'KANDJI_TOKEN'.",
                )
                config.kandji_token = os.environ.get('KANDJI_TOKEN')
            else:
                logger.warning("A Kandji base URI was provided but a token was not.")
                config.kandji_token = None
        else:
            logger.warning("A Kandji base URI was not provided.")
            config.kandji_base_uri = None

        if config.statsd_enabled:
            logger.debug(
                f'statsd enabled. Sending metrics to server {config.statsd_host}:{config.statsd_port}. '
                f'Metrics have prefix "{config.statsd_prefix}".',
            )

        # Pagerduty config
        if config.pagerduty_api_key_env_var:
            logger.debug(f"Reading API key for PagerDuty from environment variable {config.pagerduty_api_key_env_var}")
            config.pagerduty_api_key = os.environ.get(config.pagerduty_api_key_env_var)
        else:
            config.pagerduty_api_key = None

        # Crowdstrike config
        if config.crowdstrike_client_id_env_var:
            logger.debug(
                f"Reading API key for Crowdstrike from environment variable {config.crowdstrike_client_id_env_var}",
            )
            config.crowdstrike_client_id = os.environ.get(config.crowdstrike_client_id_env_var)
        else:
            config.crowdstrike_client_id = None

        if config.crowdstrike_client_secret_env_var:
            logger.debug(
                f"Reading API key for Crowdstrike from environment variable {config.crowdstrike_client_secret_env_var}",
            )
            config.crowdstrike_client_secret = os.environ.get(config.crowdstrike_client_secret_env_var)
        else:
            config.crowdstrike_client_secret = None

        # GSuite config
        if config.gsuite_tokens_env_var:
            logger.debug(f"Reading config string for GSuite from environment variable {config.gsuite_tokens_env_var}")
            config.gsuite_config = os.environ.get(config.gsuite_tokens_env_var)
        else:
            config.gsuite_tokens_env_var = None

        # Lastpass config
        if config.lastpass_cid_env_var:
            logger.debug(f"Reading CID for Lastpass from environment variable {config.lastpass_cid_env_var}")
            config.lastpass_cid = os.environ.get(config.lastpass_cid_env_var)
        else:
            config.lastpass_cid = None
        if config.lastpass_provhash_env_var:
            logger.debug(f"Reading provhash for Lastpass from environment variable {config.lastpass_provhash_env_var}")
            config.lastpass_provhash = os.environ.get(config.lastpass_provhash_env_var)
        else:
            config.lastpass_provhash = None

        # BigFix config
        if config.bigfix_username and config.bigfix_password_env_var and config.bigfix_root_url:
            logger.debug(f"Reading BigFix password from environment variable {config.bigfix_password_env_var}")
            config.bigfix_password = os.environ.get(config.bigfix_password_env_var)

        # Duo config
        if config.duo_api_key_env_var and config.duo_api_secret_env_var and config.duo_api_hostname:
            logger.debug(
                f"Reading Duo api key and secret from environment variables {config.duo_api_key_env_var}"
                f", {config.duo_api_secret_env_var}",
            )
            config.duo_api_key = os.environ.get(config.duo_api_key_env_var)
            config.duo_api_secret = os.environ.get(config.duo_api_secret_env_var)
        else:
            config.duo_api_key = None
            config.duo_api_secret = None

        # Semgrep config
        if config.semgrep_app_token_env_var:
            logger.debug(f"Reading Semgrep App Token from environment variable {config.semgrep_app_token_env_var}")
            config.semgrep_app_token = os.environ.get(config.semgrep_app_token_env_var)
        else:
            config.semgrep_app_token = None
        if config.semgrep_dependency_ecosystems:
            # No need to store the returned value; we're using this for input validation.
            parse_and_validate_semgrep_ecosystems(config.semgrep_dependency_ecosystems)

        # CVE feed config
        if config.cve_api_key_env_var:
            logger.debug(f"Reading NVD CVE API key environment variable {config.cve_api_key_env_var}")
            config.cve_api_key = os.environ.get(config.cve_api_key_env_var)
        else:
            config.cve_api_key = None

        # SnipeIT config
        if config.snipeit_base_uri:
            if config.snipeit_token_env_var:
                logger.debug(
                    "Reading SnipeIT API token from environment variable '%s'.",
                    config.snipeit_token_env_var,
                )
                config.snipeit_token = os.environ.get(config.snipeit_token_env_var)
            elif os.environ.get('SNIPEIT_TOKEN'):
                logger.debug(
                    "Reading SnipeIT API token from environment variable 'SNIPEIT_TOKEN'.",
                )
                config.snipeit_token = os.environ.get('SNIPEIT_TOKEN')
            else:
                logger.warning("A SnipeIT base URI was provided but a token was not.")
                config.kandji_token = None
        else:
            logger.warning("A SnipeIT base URI was not provided.")
            config.snipeit_base_uri = None

        # Run cartography
        try:
            return cartography.sync.run_with_config(self.sync, config)
        except KeyboardInterrupt:
            return cartography.util.STATUS_KEYBOARD_INTERRUPT


def main(argv=None):
    """
    Entrypoint for the default cartography command line interface.

    This entrypoint build and executed the default cartography sync. See cartography.sync.build_default_sync.

    :rtype: int
    :return: The return code.
    """
    logging.basicConfig(level=logging.INFO)
    logging.getLogger('botocore').setLevel(logging.WARNING)
    logging.getLogger('googleapiclient').setLevel(logging.WARNING)
    logging.getLogger('neo4j').setLevel(logging.WARNING)
    argv = argv if argv is not None else sys.argv[1:]
    sys.exit(CLI(prog='cartography').main(argv))
