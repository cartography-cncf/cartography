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
    :type selected_modules: str
    :param selected_modules: Comma-separated list of cartography top-level modules to sync. Optional.
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
    :type kandji_base_uri: string
    :param kandji_base_uri: Kandji data provider base URI, e.g. https://company.api.kandji.io. Optional.
    :type kandji_tenant_id: string
    :param kandji_tenant_id: Kandji tenant id. e.g. company Optional.
    :type kandji_token: string
    :param kandji_token: Token used to authenticate to the Kandji data provider. Optional.
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
    :type lastpass_cid: str
    :param lastpass_cid: Lastpass account ID. Optional.
    :type lastpass_provhash: str
    :param lastpass_provhash: Lastpass API KEY. Optional.
    :type bigfix_username: str
    :param bigfix_username: The username to authenticate to BigFix. Optional.
    :type bigfix_password: str
    :param bigfix_password: The password to authenticate to BigFix. Optional.
    :type bigfix_root_url: str
    :param bigfix_root_url: The API URL to use for BigFix, e.g. "https://example.com:52311". Optional.
    :type duo_api_key: str
    :param duo_api_key: The Duo api key. Optional.
    :type duo_api_key: str
    :param duo_api_key: The Duo api secret. Optional.
    :type duo_api_hostname: str
    :param duo_api_hostname: The Duo api hostname, e.g. "api-abc123.duosecurity.com". Optional.
    :param semgrep_app_token: The Semgrep api token. Optional.
    :type semgrep_app_token: str
    :param semgrep_dependency_ecosystems: Comma-separated list of Semgrep dependency ecosystems to fetch. Optional.
    :type semgrep_dependency_ecosystems: str
    :type snipeit_base_uri: string
    :param snipeit_base_uri: SnipeIT data provider base URI. Optional.
    :type snipeit_token: string
    :param snipeit_token: Token used to authenticate to the SnipeIT data provider. Optional.
    :type snipeit_tenant_id: string
    :param snipeit_tenant_id: Token used to authenticate to the SnipeIT data provider. Optional.
    """

    def __init__(
        self,
        neo4j_uri,
        neo4j_user=None,
        neo4j_password=None,
        neo4j_max_connection_lifetime=None,
        neo4j_database=None,
        selected_modules=None,
        update_tag=None,
        aws_sync_all_profiles=False,
        aws_best_effort_mode=False,
        azure_sync_all_subscriptions=False,
        azure_sp_auth=None,
        azure_tenant_id=None,
        azure_client_id=None,
        azure_client_secret=None,
        aws_requested_syncs=None,
        analysis_job_directory=None,
        oci_sync_all_profiles=None,
        okta_org_id=None,
        okta_api_key=None,
        okta_saml_role_regex=None,
        github_config=None,
        digitalocean_token=None,
        permission_relationships_file=None,
        jamf_base_uri=None,
        jamf_user=None,
        jamf_password=None,
        kandji_base_uri=None,
        kandji_tenant_id=None,
        kandji_token=None,
        k8s_kubeconfig=None,
        statsd_enabled=False,
        statsd_prefix=None,
        statsd_host=None,
        statsd_port=None,
        pagerduty_api_key=None,
        pagerduty_request_timeout=None,
        nist_cve_url=None,
        cve_enabled=False,
        cve_api_key: str | None = None,
        crowdstrike_client_id=None,
        crowdstrike_client_secret=None,
        crowdstrike_api_url=None,
        gsuite_auth_method=None,
        gsuite_config=None,
        lastpass_cid=None,
        lastpass_provhash=None,
        bigfix_username=None,
        bigfix_password=None,
        bigfix_root_url=None,
        duo_api_key=None,
        duo_api_secret=None,
        duo_api_hostname=None,
        semgrep_app_token=None,
        semgrep_dependency_ecosystems=None,
        snipeit_base_uri=None,
        snipeit_token=None,
        snipeit_tenant_id=None,
    ):
        self.neo4j_uri = neo4j_uri
        self.neo4j_user = neo4j_user
        self.neo4j_password = neo4j_password
        self.neo4j_max_connection_lifetime = neo4j_max_connection_lifetime
        self.neo4j_database = neo4j_database
        self.selected_modules = selected_modules
        self.update_tag = update_tag
        self.aws_sync_all_profiles = aws_sync_all_profiles
        self.aws_best_effort_mode = aws_best_effort_mode
        self.azure_sync_all_subscriptions = azure_sync_all_subscriptions
        self.azure_sp_auth = azure_sp_auth
        self.azure_tenant_id = azure_tenant_id
        self.azure_client_id = azure_client_id
        self.azure_client_secret = azure_client_secret
        self.aws_requested_syncs = aws_requested_syncs
        self.analysis_job_directory = analysis_job_directory
        self.oci_sync_all_profiles = oci_sync_all_profiles
        self.okta_org_id = okta_org_id
        self.okta_api_key = okta_api_key
        self.okta_saml_role_regex = okta_saml_role_regex
        self.github_config = github_config
        self.digitalocean_token = digitalocean_token
        self.permission_relationships_file = permission_relationships_file
        self.jamf_base_uri = jamf_base_uri
        self.jamf_user = jamf_user
        self.jamf_password = jamf_password
        self.kandji_base_uri = kandji_base_uri
        self.kandji_tenant_id = kandji_tenant_id
        self.kandji_token = kandji_token
        self.k8s_kubeconfig = k8s_kubeconfig
        self.statsd_enabled = statsd_enabled
        self.statsd_prefix = statsd_prefix
        self.statsd_host = statsd_host
        self.statsd_port = statsd_port
        self.pagerduty_api_key = pagerduty_api_key
        self.pagerduty_request_timeout = pagerduty_request_timeout
        self.nist_cve_url = nist_cve_url
        self.cve_enabled = cve_enabled
        self.cve_api_key: str | None = cve_api_key
        self.crowdstrike_client_id = crowdstrike_client_id
        self.crowdstrike_client_secret = crowdstrike_client_secret
        self.crowdstrike_api_url = crowdstrike_api_url
        self.gsuite_auth_method = gsuite_auth_method
        self.gsuite_config = gsuite_config
        self.lastpass_cid = lastpass_cid
        self.lastpass_provhash = lastpass_provhash
        self.bigfix_username = bigfix_username
        self.bigfix_password = bigfix_password
        self.bigfix_root_url = bigfix_root_url
        self.duo_api_key = duo_api_key
        self.duo_api_secret = duo_api_secret
        self.duo_api_hostname = duo_api_hostname
        self.semgrep_app_token = semgrep_app_token
        self.semgrep_dependency_ecosystems = semgrep_dependency_ecosystems
        self.snipeit_base_uri = snipeit_base_uri
        self.snipeit_token = snipeit_token
        self.snipeit_tenant_id = snipeit_tenant_id
