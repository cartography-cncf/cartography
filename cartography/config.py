class Config:
    """
    A common interface for cartography configuration.

    All fields defined on this class must be present on a configuration object. Fields documented as required must
    contain valid values. Fields documented as optional may contain None, in which case cartography will choose a
    sensible default value for that piece of configuration.

    :type neo4j_uri: string
    :param neo4j_uri: URI for a Neo4j graph database service. Required.
    :type neo4j_user: string
    :param neo4j_user: User name for a Neo4j graph database service. Optional.
    :type neo4j_password: string
    :param neo4j_password: Password for a Neo4j graph database service. Optional.
    :type neo4j_max_connection_lifetime: int
    :param neo4j_max_connection_lifetime: Time in seconds for Neo4j driver to consider a TCP connection alive.
        See https://neo4j.com/docs/driver-manual/1.7/client-applications/. Optional.
    :type neo4j_database: string
    :param neo4j_database: The name of the database in Neo4j to connect to. If not specified, uses your Neo4j database
    settings to infer which database is set to default.
    See https://neo4j.com/docs/api/python-driver/4.4/api.html#database. Optional.
    :type update_tag: int
    :param update_tag: Update tag for a cartography sync run. Optional.
    :type aws_sync_all_profiles: bool
    :param aws_sync_all_profiles: If True, AWS sync will run for all non-default profiles in the AWS_CONFIG_FILE. If
        False (default), AWS sync will run using the default credentials only. Optional.
    :type aws_best_effort_mode: bool
    :param aws_best_effort_mode: If True, AWS sync will not raise any exceptions, just log. If False (default),
        exceptions will be raised.
    :type azure_sync_all_subscriptions: bool
    :param azure_sync_all_subscriptions: If True, Azure sync will run for all profiles in azureProfile.json. If
        False (default), Azure sync will run using current user session via CLI credentials. Optional.
    :type azure_sp_auth: bool
    :param azure_sp_auth: If True, Azure sync will run using Service Principal Authentication. If
        False (default), Azure sync will run using current user session via CLI credentials. Optional.
    :type azure_tenant_id: str
    :param azure_tenant_id: Tenant Id for connecting in a Service Principal Authentication approach. Optional.
    :type azure_client_id: str
    :param azure_client_id: Client Id for connecting in a Service Principal Authentication approach. Optional.
    :type azure_client_secret: str
    :param azure_client_secret: Client Secret for connecting in a Service Principal Authentication approach. Optional.
    :type aws_requested_syncs: str
    :param aws_requested_syncs: Comma-separated list of AWS resources to sync. Optional.
    :type crxcavator_api_base_uri: str
    :param crxcavator_api_base_uri: URI for CRXcavator API. Optional.
    :type crxcavator_api_key: str
    :param crxcavator_api_key: Auth key for CRXcavator API. Optional.
    :type analysis_job_directory: str
    :param analysis_job_directory: Path to a directory tree containing analysis jobs to run. Optional.
    :type oci_sync_all_profiles: bool
    :param oci_sync_all_profiles: whether OCI will sync non-default profiles in OCI_CONFIG_FILE. Optional.
    :type okta_org_id: str
    :param okta_org_id: Okta organization id. Optional.
    :type okta_api_key: str
    :param okta_api_key: Okta API key. Optional.
    :type okta_saml_role_regex: str
    :param okta_saml_role_regex: The regex used to map okta groups to AWS roles. Optional.
    :type github_config: str
    :param github_config: Base64 encoded config object for GitHub ingestion. Optional.
    :type azure_devops_config: str
    :param azure_devops_config: Base64 encoded config object for Azure DevOps ingestion. Optional.
    :type digitalocean_token: str
    :param digitalocean_token: DigitalOcean access token. Optional.
    :type permission_relationships_file: str
    :param permission_relationships_file: File path for the resource permission relationships file. Optional.
    :type jamf_base_uri: string
    :param jamf_base_uri: Jamf data provider base URI, e.g. https://example.com/JSSResource. Optional.
    :type jamf_user: string
    :param jamf_user: User name used to authenticate to the Jamf data provider. Optional.
    :type jamf_password: string
    :param jamf_password: Password used to authenticate to the Jamf data provider. Optional.
    :type statsd_enabled: bool
    :param statsd_enabled: Whether to collect statsd metrics such as sync execution times. Optional.
    :type statsd_host: str
    :param statsd_host: If statsd_enabled is True, send metrics to this host. Optional.
    :type: statsd_port: int
    :param statsd_port: If statsd_enabled is True, send metrics to this port on statsd_host. Optional.
    :type: k8s_kubeconfig: str
    :param k8s_kubeconfig: Path to kubeconfig file for kubernetes cluster(s). Optional
    :type: pagerduty_api_key: str
    :param pagerduty_api_key: API authentication key for pagerduty. Optional.
    :type: pagerduty_request_timeout: int
    :param pagerduty_request_timeout: Seconds to timeout for pagerduty session requests. Optional
    :type: nist_cve_url: str
    :param nist_cve_url: NIST CVE data provider base URI, e.g. https://nvd.nist.gov/feeds/json/cve/1.1. Optional.
    :type: gsuite_auth_method: str
    :param gsuite_auth_method: Auth method (delegated, oauth) used for Google Workspace. Optional.
    :type gsuite_config: str
    :param gsuite_config: Base64 encoded config object or config file path for Google Workspace. Optional.
    """

    def __init__(
        self,
        neo4j_uri,
        neo4j_user=None,
        neo4j_password=None,
        neo4j_max_connection_lifetime=None,
        neo4j_database=None,
        update_tag=None,
        aws_sync_all_profiles=False,
        aws_best_effort_mode=False,
        azure_sync_all_subscriptions=False,
        azure_sp_auth=None,
        azure_tenant_id=None,
        azure_client_id=None,
        azure_client_secret=None,
        azure_redirect_uri=None,
        azure_subscription_id=None,
        azure_refresh_token=None,
        azure_graph_scope=None,
        azure_default_graph_scope=None,
        azure_vault_scope=None,
        azure_azure_scope=None,
        aws_requested_syncs=None,
        azure_requested_syncs=None,
        gcp_requested_syncs=None,
        analysis_job_directory=None,
        crxcavator_api_base_uri=None,
        crxcavator_api_key=None,
        oci_sync_all_profiles=None,
        okta_org_id=None,
        okta_api_key=None,
        okta_saml_role_regex=None,
        github_config=None,
        azure_devops_config=None,
        digitalocean_token=None,
        permission_relationships_file=None,
        jamf_base_uri=None,
        jamf_user=None,
        jamf_password=None,
        k8s_kubeconfig=None,
        statsd_enabled=False,
        statsd_prefix=None,
        statsd_host=None,
        statsd_port=None,
        credentials=None,
        params=None,
        pagerduty_api_key=None,
        pagerduty_request_timeout=None,
        nist_cve_url=None,
        cve_enabled=False,
        crowdstrike_client_id=None,
        crowdstrike_client_secret=None,
        crowdstrike_api_url=None,
        gsuite_auth_method=None,
        gsuite_config=None,
        refresh_entitlements=False,
        identity_store_region=None,
        bitbucket_access_token=None,
        gitlab_access_token=None,
        gitlab_hosted_domain=None,
        aws_internal_accounts=None,
        partial=None,
        manual_run=None,
        dc=None,
    ):
        self.neo4j_uri = neo4j_uri
        self.neo4j_user = neo4j_user
        self.neo4j_password = neo4j_password
        self.neo4j_max_connection_lifetime = neo4j_max_connection_lifetime
        self.neo4j_database = neo4j_database
        self.update_tag = update_tag
        self.aws_sync_all_profiles = aws_sync_all_profiles
        self.aws_best_effort_mode = aws_best_effort_mode
        self.azure_sync_all_subscriptions = azure_sync_all_subscriptions
        self.azure_sp_auth = azure_sp_auth
        self.azure_tenant_id = azure_tenant_id
        self.azure_client_id = azure_client_id
        self.azure_client_secret = azure_client_secret
        self.azure_redirect_uri = azure_redirect_uri
        self.azure_subscription_id = azure_subscription_id
        self.azure_refresh_token = azure_refresh_token
        self.azure_graph_scope = azure_graph_scope
        self.azure_default_graph_scope = azure_default_graph_scope
        self.azure_vault_scope = azure_vault_scope
        self.azure_azure_scope = azure_azure_scope
        self.aws_requested_syncs = aws_requested_syncs
        self.azure_requested_syncs = azure_requested_syncs
        self.gcp_requested_syncs = gcp_requested_syncs
        self.analysis_job_directory = analysis_job_directory
        self.crxcavator_api_base_uri = crxcavator_api_base_uri
        self.crxcavator_api_key = crxcavator_api_key
        self.oci_sync_all_profiles = oci_sync_all_profiles
        self.okta_org_id = okta_org_id
        self.okta_api_key = okta_api_key
        self.okta_saml_role_regex = okta_saml_role_regex
        self.github_config = github_config
        self.azure_devops_config = azure_devops_config
        self.bitbucket_access_token = bitbucket_access_token
        self.gitlab_access_token = gitlab_access_token
        self.gitlab_hosted_domain = gitlab_hosted_domain
        self.digitalocean_token = digitalocean_token
        self.permission_relationships_file = permission_relationships_file
        self.jamf_base_uri = jamf_base_uri
        self.jamf_user = jamf_user
        self.jamf_password = jamf_password
        self.k8s_kubeconfig = k8s_kubeconfig
        self.statsd_enabled = statsd_enabled
        self.statsd_prefix = statsd_prefix
        self.statsd_host = statsd_host
        self.statsd_port = statsd_port
        self.credentials = credentials
        self.params = params
        self.pagerduty_api_key = pagerduty_api_key
        self.pagerduty_request_timeout = pagerduty_request_timeout
        self.nist_cve_url = nist_cve_url
        self.cve_enabled = cve_enabled
        self.crowdstrike_client_id = crowdstrike_client_id
        self.crowdstrike_client_secret = crowdstrike_client_secret
        self.crowdstrike_api_url = crowdstrike_api_url
        self.gsuite_auth_method = gsuite_auth_method
        self.gsuite_config = gsuite_config
        self.refresh_entitlements = refresh_entitlements
        self.identity_store_region = identity_store_region
        self.aws_internal_accounts = aws_internal_accounts
        self.partial = partial
        self.manual_run = manual_run
        self.dc = dc
