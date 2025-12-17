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
    :type aws_regions: str
    :param aws_regions: Comma-separated list of AWS regions to sync. Optional.
    :type aws_best_effort_mode: bool
    :param aws_best_effort_mode: If True, AWS sync will not raise any exceptions, just log. If False (default),
        exceptions will be raised.
    :type aws_cloudtrail_management_events_lookback_hours: int
    :param aws_cloudtrail_management_events_lookback_hours: Number of hours back to retrieve CloudTrail management events from. Optional.
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
    :type azure_subscription_id: str | None
    :param azure_subscription_id: The Azure Subscription ID to sync.
    :type entra_tenant_id: str
    :param entra_tenant_id: Tenant Id for connecting in a Service Principal Authentication approach. Optional.
    :type entra_client_id: str
    :param entra_client_id: Client Id for connecting in a Service Principal Authentication approach. Optional.
    :type entra_client_secret: str
    :param entra_client_secret: Client Secret for connecting in a Service Principal Authentication approach. Optional.
    :type aws_requested_syncs: str
    :param aws_requested_syncs: Comma-separated list of AWS resources to sync. Optional.
    :type aws_guardduty_severity_threshold: str
    :param aws_guardduty_severity_threshold: GuardDuty severity threshold filter. Only findings at or above this
        severity level will be synced. Valid values: LOW, MEDIUM, HIGH, CRITICAL. Optional.
    :type experimental_aws_inspector_batch: int
    :param experimental_aws_inspector_batch: EXPERIMENTAL: Batch size for AWS Inspector findings sync. Controls how
        many findings are fetched, processed and cleaned up at a time. Default is 1000. Optional.
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
    :type github_commit_lookback_days: int
    :param github_commit_lookback_days: Number of days to look back for GitHub commit tracking. Optional.
    :type digitalocean_token: str
    :param digitalocean_token: DigitalOcean access token. Optional.
    :type permission_relationships_file: str
    :param permission_relationships_file: File path for the resource permission relationships file. Optional.
    :type azure_permission_relationships_file: str
    :param azure_permission_relationships_file: File path for the Azure permission relationships file. Optional.
    :type gcp_permission_relationships_file: str
    :param gcp_permission_relationships_file: File path for the GCP resource permission relationships file. Optional.
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
    :type: managed_kubernetes: str
    :param managed_kubernetes: Type of managed Kubernetes service (e.g., "eks"). Optional.
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
    :type googleworkspace_auth_method: str
    :param googleworkspace_auth_method: Auth method (delegated, oauth, default) used for Google Workspace. Optional.
    :type googleworkspace_config: str
    :param googleworkspace_config: Base64 encoded config object or config file path for Google Workspace. Optional.
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
    :type tailscale_token: str
    :param tailscale_token: Tailscale API token. Optional.
    :type tailscale_org: str
    :param tailscale_org: Tailscale organization name. Optional.
    :type tailscale_base_url: str
    :param tailscale_base_url: Tailscale API base URL. Optional.
    :type cloudflare_token: string
    :param cloudflare_token: Cloudflare API key. Optional.
    :type openai_apikey: string
    :param openai_apikey: OpenAI API key. Optional.
    :type openai_org_id: string
    :param openai_org_id: OpenAI organization id. Optional.
    :type anthropic_apikey: string
    :param anthropic_apikey: Anthropic API key. Optional.
    :type airbyte_client_id: str
    :param airbyte_client_id: Airbyte client ID for API authentication. Optional.
    :type airbyte_client_secret: str
    :param airbyte_client_secret: Airbyte client secret for API authentication. Optional.
    :type airbyte_api_url: str
    :param airbyte_api_url: Airbyte API base URL, e.g. https://api.airbyte.com/v1. Optional.
    :type trivy_s3_bucket: str
    :param trivy_s3_bucket: The S3 bucket name containing Trivy scan results. Optional.
    :type trivy_s3_prefix: str
    :param trivy_s3_prefix: The S3 prefix path containing Trivy scan results. Optional.
    :type ontology_users_source: str
    :param ontology_users_source: Comma-separated list of sources of truth for user data in the ontology. Optional.
    :type ontology_devices_source: str
    :param ontology_devices_source: Comma-separated list of sources of truth for client computers data in the ontology.
        Optional.
    :type trivy_results_dir: str
    :param trivy_results_dir: Local directory containing Trivy scan results. Optional.
    :type scaleway_access_key: str
    :param scaleway_access_key: Scaleway access key. Optional.
    :type scaleway_secret_key: str
    :param scaleway_secret_key: Scaleway secret key. Optional.
    :type scaleway_org: str
    :param scaleway_org: Scaleway organization id. Optional.
    :type sentinelone_api_url: string
    :param sentinelone_api_url: SentinelOne API URL. Optional.
    :type sentinelone_api_token: string
    :param sentinelone_api_token: SentinelOne API token for authentication. Optional.
    :type sentinelone_account_ids: list[str]
    :param sentinelone_account_ids: List of SentinelOne account IDs to sync. Optional.
    :type spacelift_api_endpoint: string
    :param spacelift_api_endpoint: Spacelift GraphQL API endpoint. Optional.
    :type spacelift_api_token: string
    :param spacelift_api_token: Spacelift API token for authentication. Optional (can use API key instead).
    :type spacelift_api_key_id: string
    :param spacelift_api_key_id: Spacelift API key ID for token exchange authentication. Optional (alternative to token).
    :type spacelift_api_key_secret: string
    :param spacelift_api_key_secret: Spacelift API key secret for token exchange authentication. Optional (alternative to token).
    :type spacelift_ec2_ownership_s3_bucket: string
    :param spacelift_ec2_ownership_s3_bucket: S3 bucket name containing EC2 ownership data from Athena. Optional.
    :type spacelift_ec2_ownership_s3_prefix: string
    :param spacelift_ec2_ownership_s3_prefix: S3 prefix for EC2 ownership data from Athena. All JSON files under this prefix will be processed. Optional.
    :type keycloak_client_id: str
    :param keycloak_client_id: Keycloak client ID for API authentication. Optional.
    :type keycloak_client_secret: str
    :param keycloak_client_secret: Keycloak client secret for API authentication. Optional.
    :type keycloak_realm: str
    :param keycloak_realm: Keycloak realm for authentication (all realms will be synced). Optional.
    :type keycloak_url: str
    :param keycloak_url: Keycloak base URL, e.g. https://keycloak.example.com. Optional.
    :type slack_token: str
    :param slack_token: Slack API token. Optional.
    :type slack_teams: list[str]
    :param slack_teams: List of Slack team IDs to sync. Optional.
    :type slack_channels_memberships: bool
    :param slack_channels_memberships: If True, sync Slack channel membership data. Optional.
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
        aws_regions=None,
        aws_best_effort_mode=False,
        aws_cloudtrail_management_events_lookback_hours=None,
        experimental_aws_inspector_batch=1000,
        azure_sync_all_subscriptions=False,
        azure_sp_auth=None,
        azure_tenant_id=None,
        azure_client_id=None,
        azure_client_secret=None,
        azure_subscription_id: str | None = None,
        entra_tenant_id=None,
        entra_client_id=None,
        entra_client_secret=None,
        aws_requested_syncs=None,
        aws_guardduty_severity_threshold=None,
        analysis_job_directory=None,
        oci_sync_all_profiles=None,
        okta_org_id=None,
        okta_api_key=None,
        okta_saml_role_regex=None,
        github_config=None,
        github_commit_lookback_days=30,
        digitalocean_token=None,
        permission_relationships_file=None,
        azure_permission_relationships_file=None,
        gcp_permission_relationships_file=None,
        jamf_base_uri=None,
        jamf_user=None,
        jamf_password=None,
        kandji_base_uri=None,
        kandji_tenant_id=None,
        kandji_token=None,
        k8s_kubeconfig=None,
        managed_kubernetes=None,
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
        googleworkspace_auth_method=None,
        googleworkspace_config=None,
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
        tailscale_token=None,
        tailscale_org=None,
        tailscale_base_url=None,
        cloudflare_token=None,
        openai_apikey=None,
        openai_org_id=None,
        anthropic_apikey=None,
        airbyte_client_id=None,
        airbyte_client_secret=None,
        airbyte_api_url=None,
        trivy_s3_bucket=None,
        trivy_s3_prefix=None,
        ontology_users_source=None,
        ontology_devices_source=None,
        trivy_results_dir=None,
        scaleway_access_key=None,
        scaleway_secret_key=None,
        scaleway_org=None,
        sentinelone_api_url=None,
        sentinelone_api_token=None,
        sentinelone_account_ids=None,
        spacelift_api_endpoint=None,
        spacelift_api_token=None,
        spacelift_api_key_id=None,
        spacelift_api_key_secret=None,
        spacelift_ec2_ownership_s3_bucket=None,
        spacelift_ec2_ownership_s3_prefix=None,
        keycloak_client_id=None,
        keycloak_client_secret=None,
        keycloak_realm=None,
        keycloak_url=None,
        slack_token=None,
        slack_teams=None,
        slack_channels_memberships=False,
    ):
        self.neo4j_uri = neo4j_uri
        self.neo4j_user = neo4j_user
        self.neo4j_password = neo4j_password
        self.neo4j_max_connection_lifetime = neo4j_max_connection_lifetime
        self.neo4j_database = neo4j_database
        self.selected_modules = selected_modules
        self.update_tag = update_tag
        self.aws_sync_all_profiles = aws_sync_all_profiles
        self.aws_regions = aws_regions
        self.aws_best_effort_mode = aws_best_effort_mode
        self.aws_cloudtrail_management_events_lookback_hours = (
            aws_cloudtrail_management_events_lookback_hours
        )
        self.experimental_aws_inspector_batch = experimental_aws_inspector_batch
        self.azure_sync_all_subscriptions = azure_sync_all_subscriptions
        self.azure_sp_auth = azure_sp_auth
        self.azure_tenant_id = azure_tenant_id
        self.azure_client_id = azure_client_id
        self.azure_client_secret = azure_client_secret
        self.azure_subscription_id = azure_subscription_id
        self.entra_tenant_id = entra_tenant_id
        self.entra_client_id = entra_client_id
        self.entra_client_secret = entra_client_secret
        self.aws_requested_syncs = aws_requested_syncs
        self.aws_guardduty_severity_threshold = aws_guardduty_severity_threshold
        self.analysis_job_directory = analysis_job_directory
        self.oci_sync_all_profiles = oci_sync_all_profiles
        self.okta_org_id = okta_org_id
        self.okta_api_key = okta_api_key
        self.okta_saml_role_regex = okta_saml_role_regex
        self.github_config = github_config
        self.github_commit_lookback_days = github_commit_lookback_days
        self.digitalocean_token = digitalocean_token
        self.permission_relationships_file = permission_relationships_file
        self.azure_permission_relationships_file = azure_permission_relationships_file
        self.gcp_permission_relationships_file = gcp_permission_relationships_file
        self.jamf_base_uri = jamf_base_uri
        self.jamf_user = jamf_user
        self.jamf_password = jamf_password
        self.kandji_base_uri = kandji_base_uri
        self.kandji_tenant_id = kandji_tenant_id
        self.kandji_token = kandji_token
        self.k8s_kubeconfig = k8s_kubeconfig
        self.managed_kubernetes = managed_kubernetes
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
        self.googleworkspace_auth_method = googleworkspace_auth_method
        self.googleworkspace_config = googleworkspace_config
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
        self.tailscale_token = tailscale_token
        self.tailscale_org = tailscale_org
        self.tailscale_base_url = tailscale_base_url
        self.cloudflare_token = cloudflare_token
        self.openai_apikey = openai_apikey
        self.openai_org_id = openai_org_id
        self.anthropic_apikey = anthropic_apikey
        self.airbyte_client_id = airbyte_client_id
        self.airbyte_client_secret = airbyte_client_secret
        self.airbyte_api_url = airbyte_api_url
        self.trivy_s3_bucket = trivy_s3_bucket
        self.trivy_s3_prefix = trivy_s3_prefix
        self.ontology_users_source = ontology_users_source
        self.ontology_devices_source = ontology_devices_source
        self.trivy_results_dir = trivy_results_dir
        self.scaleway_access_key = scaleway_access_key
        self.scaleway_secret_key = scaleway_secret_key
        self.scaleway_org = scaleway_org
        self.sentinelone_api_url = sentinelone_api_url
        self.sentinelone_api_token = sentinelone_api_token
        self.sentinelone_account_ids = sentinelone_account_ids
        self.spacelift_api_endpoint = spacelift_api_endpoint
        self.spacelift_api_token = spacelift_api_token
        self.spacelift_api_key_id = spacelift_api_key_id
        self.spacelift_api_key_secret = spacelift_api_key_secret
        self.spacelift_ec2_ownership_s3_bucket = spacelift_ec2_ownership_s3_bucket
        self.spacelift_ec2_ownership_s3_prefix = spacelift_ec2_ownership_s3_prefix
        self.keycloak_client_id = keycloak_client_id
        self.keycloak_client_secret = keycloak_client_secret
        self.keycloak_realm = keycloak_realm
        self.keycloak_url = keycloak_url
        self.slack_token = slack_token
        self.slack_teams = slack_teams
        self.slack_channels_memberships = slack_channels_memberships
