import json
import os


class AppContext:
    def __init__(
        self,
        region=None,
        log_level=None,
        app_env=None,
        config_key_id=None,
        inventorysyncaws_config=None,
        cartography_config=None,
        awscomplianceanalystpython_config=None,
        cloudresourcemanager_config=None,

        logger=None,
        aws_account_id=None,

        authorization_key=None,
        authorization_value=None,
        assume_role_access_key_key_id=None,
        assume_role_access_key_cipher=None,
        assume_role_access_secret_key_id=None,
        assume_role_access_secret_cipher=None,
        sns_offline_url=None,

        audit_sns_request_topic=None,
        audit_sns_response_topic=None,
        aws_iam_compliance_request_topic=None,
        aws_iam_compliance_response_topic=None,
        aws_iam_compliance_min_days_for_rotation=None,
        aws_iam_compliance_min_days_for_update=None,
        aws_iam_compliance_min_days_for_use=None,
        aws_sg_audit_request_topic=None,
        aws_sg_audit_response_topic=None,
        aws_s3_public_check_request_topic=None,
        aws_s3_public_check_response_topic=None,
        aws_ec2_monitoring_request_topic=None,
        aws_ec2_monitoring_response_topic=None,
        aws_ec2_monitoring_outdated_instance_types=None,
        aws_rds_monitoring_request_topic=None,
        aws_rds_monitoring_response_topic=None,
        aws_lambda_monitoring_request_topic=None,
        aws_lambda_monitoring_response_topic=None,
        aws_es_monitoring_request_topic=None,
        aws_es_monitoring_response_topic=None,
        aws_kms_monitoring_request_topic=None,
        aws_kms_monitoring_response_topic=None,
        aws_elb_monitoring_request_topic=None,
        aws_elb_monitoring_response_topic=None,
        aws_ses_monitoring_request_topic=None,
        aws_ses_monitoring_response_topic=None,
        aws_dynamodb_monitoring_request_topic=None,
        aws_dynamodb_monitoring_response_topic=None,
        aws_sns_monitoring_request_topic=None,
        aws_sns_monitoring_response_topic=None,
        aws_kubernetes_monitoring_request_topic=None,
        aws_kubernetes_monitoring_response_topic=None,
        aws_kubernetes_monitoring_latest_versions=None,

        aws_apigateway_monitoring_request_topic=None,
        aws_apigateway_monitoring_response_topic=None,
        aws_cloudfront_monitoring_request_topic=None,
        aws_cloudfront_monitoring_response_topic=None,
        aws_cloudtrail_monitoring_request_topic=None,
        aws_cloudtrail_monitoring_response_topic=None,
        aws_redshift_monitoring_request_topic=None,
        aws_redshift_monitoring_response_topic=None,
        aws_redshift_monitoring_idleconnection_limit_per_day=None,
        aws_redshift_monitoring_idle_readiops_limit_per_day=None,
        aws_redshift_monitoring_idle_writeiops_limit_per_day=None,
        aws_redshift_monitoring_maximum_diskspace_usage_limit=None,
        aws_redshift_monitoring_underutilized_average_cpu_usage_limit=None,
        aws_redshift_monitoring_underutilized_readiops_limit_per_day=None,
        aws_redshift_monitoring_underutilized_writeiops_limit_per_day=None,
        aws_cloudformation_monitoring_request_topic=None,
        aws_cloudformation_monitoring_response_topic=None,
        aws_sqs_monitoring_request_topic=None,
        aws_sqs_monitoring_response_topic=None,
        aws_cloudwatch_monitoring_request_topic=None,
        aws_cloudwatch_monitoring_response_topic=None,
        aws_route53_monitoring_request_topic=None,
        aws_route53_monitoring_response_topic=None,

        neo4j_uri=None,
        neo4j_user=None,
        neo4j_pwd=None,
        neo4j_connection_lifetime=None,
        aws_inventory_sync_request_topic=None,
        aws_inventory_sync_response_topic=None,
        aws_iam_deepdive_request_topic=None,
        aws_iam_deepdive_response_topic=None,
        aws_inventory_views_request_topic=None,
        aws_inventory_views_response_topic=None,

        aws_remediation_request_topic=None,
        aws_remediation_response_topic=None,
        aws_remediation_sourceip=None,
        aws_remediation_ports=None,
        aws_remediation_rotation_threshold=None,
        aws_remediation_retention_period=None,
        aws_remediation_kms_master_key_id=None,
        aws_remediation_kms_datakey_reuse_period_seconds=None,
        aws_cost_anomaly_request_topic=None,
        aws_cost_anomaly_response_topic=None,
        aws_cost_anomaly_granularity=None,
        aws_cost_anomaly_cost_usage_table=None,
        aws_cost_anomaly_secondary_index=None,
        aws_cost_anomaly_total_days_to_prefill=None,
        aws_cost_anomaly_services=None,
        aws_cost_saving_request_topic=None,
        aws_cost_saving_response_topic=None,
        aws_cartography_queue_url=None,
    ):
        self.region = region
        self.log_level = log_level
        self.app_env = app_env
        self.config_key_id = config_key_id
        self.inventorysyncaws_config = inventorysyncaws_config
        self.cartography_config = cartography_config
        self.awscomplianceanalystpython_config = awscomplianceanalystpython_config
        self.cloudresourcemanager_config = cloudresourcemanager_config

        self.logger = logger
        self.aws_account_id = aws_account_id

        self.authorization_key = authorization_key
        self.authorization_value = authorization_value
        self.assume_role_access_key_key_id = assume_role_access_key_key_id
        self.assume_role_access_key_cipher = assume_role_access_key_cipher
        self.assume_role_access_secret_key_id = assume_role_access_secret_key_id
        self.assume_role_access_secret_cipher = assume_role_access_secret_cipher
        self.sns_offline_url = sns_offline_url

        self.audit_sns_request_topic = audit_sns_request_topic
        self.audit_sns_response_topic = audit_sns_response_topic
        self.aws_iam_compliance_request_topic = aws_iam_compliance_request_topic
        self.aws_iam_compliance_response_topic = aws_iam_compliance_response_topic
        self.aws_iam_compliance_min_days_for_rotation = aws_iam_compliance_min_days_for_rotation
        self.aws_iam_compliance_min_days_for_update = aws_iam_compliance_min_days_for_update
        self.aws_iam_compliance_min_days_for_use = aws_iam_compliance_min_days_for_use
        self.aws_sg_audit_request_topic = aws_sg_audit_request_topic
        self.aws_sg_audit_response_topic = aws_sg_audit_response_topic
        self.aws_s3_public_check_request_topic = aws_s3_public_check_request_topic
        self.aws_s3_public_check_response_topic = aws_s3_public_check_response_topic
        self.aws_ec2_monitoring_request_topic = aws_ec2_monitoring_request_topic
        self.aws_ec2_monitoring_response_topic = aws_ec2_monitoring_response_topic
        self.aws_ec2_monitoring_outdated_instance_types = aws_ec2_monitoring_outdated_instance_types
        self.aws_rds_monitoring_request_topic = aws_rds_monitoring_request_topic
        self.aws_rds_monitoring_response_topic = aws_rds_monitoring_response_topic
        self.aws_lambda_monitoring_request_topic = aws_lambda_monitoring_request_topic
        self.aws_lambda_monitoring_response_topic = aws_lambda_monitoring_response_topic
        self.aws_es_monitoring_request_topic = aws_es_monitoring_request_topic
        self.aws_es_monitoring_response_topic = aws_es_monitoring_response_topic
        self.aws_kms_monitoring_request_topic = aws_kms_monitoring_request_topic
        self.aws_kms_monitoring_response_topic = aws_kms_monitoring_response_topic
        self.aws_elb_monitoring_request_topic = aws_elb_monitoring_request_topic
        self.aws_elb_monitoring_response_topic = aws_elb_monitoring_response_topic
        self.aws_ses_monitoring_request_topic = aws_ses_monitoring_request_topic
        self.aws_ses_monitoring_response_topic = aws_ses_monitoring_response_topic
        self.aws_dynamodb_monitoring_request_topic = aws_dynamodb_monitoring_request_topic
        self.aws_dynamodb_monitoring_response_topic = aws_dynamodb_monitoring_response_topic
        self.aws_sns_monitoring_request_topic = aws_sns_monitoring_request_topic
        self.aws_sns_monitoring_response_topic = aws_sns_monitoring_response_topic
        self.aws_kubernetes_monitoring_request_topic = aws_kubernetes_monitoring_request_topic
        self.aws_kubernetes_monitoring_response_topic = aws_kubernetes_monitoring_response_topic
        self.aws_kubernetes_monitoring_latest_versions = aws_kubernetes_monitoring_latest_versions

        self.aws_apigateway_monitoring_request_topic = aws_apigateway_monitoring_request_topic
        self.aws_apigateway_monitoring_response_topic = aws_apigateway_monitoring_response_topic
        self.aws_cloudfront_monitoring_request_topic = aws_cloudfront_monitoring_request_topic
        self.aws_cloudfront_monitoring_response_topic = aws_cloudfront_monitoring_response_topic
        self.aws_cloudtrail_monitoring_request_topic = aws_cloudtrail_monitoring_request_topic
        self.aws_cloudtrail_monitoring_response_topic = aws_cloudtrail_monitoring_response_topic
        self.aws_redshift_monitoring_request_topic = aws_redshift_monitoring_request_topic
        self.aws_redshift_monitoring_response_topic = aws_redshift_monitoring_response_topic
        self.aws_redshift_monitoring_idleconnection_limit_per_day = aws_redshift_monitoring_idleconnection_limit_per_day
        self.aws_redshift_monitoring_idle_readiops_limit_per_day = aws_redshift_monitoring_idle_readiops_limit_per_day
        self.aws_redshift_monitoring_idle_writeiops_limit_per_day = aws_redshift_monitoring_idle_writeiops_limit_per_day
        self.aws_redshift_monitoring_maximum_diskspace_usage_limit = aws_redshift_monitoring_maximum_diskspace_usage_limit
        self.aws_redshift_monitoring_underutilized_average_cpu_usage_limit = aws_redshift_monitoring_underutilized_average_cpu_usage_limit
        self.aws_redshift_monitoring_underutilized_readiops_limit_per_day = aws_redshift_monitoring_underutilized_readiops_limit_per_day
        self.aws_redshift_monitoring_underutilized_writeiops_limit_per_day = aws_redshift_monitoring_underutilized_writeiops_limit_per_day
        self.aws_cloudformation_monitoring_request_topic = aws_cloudformation_monitoring_request_topic
        self.aws_cloudformation_monitoring_response_topic = aws_cloudformation_monitoring_response_topic
        self.aws_sqs_monitoring_request_topic = aws_sqs_monitoring_request_topic
        self.aws_sqs_monitoring_response_topic = aws_sqs_monitoring_response_topic
        self.aws_cloudwatch_monitoring_request_topic = aws_cloudwatch_monitoring_request_topic
        self.aws_cloudwatch_monitoring_response_topic = aws_cloudwatch_monitoring_response_topic
        self.aws_route53_monitoring_request_topic = aws_route53_monitoring_request_topic
        self.aws_route53_monitoring_response_topic = aws_route53_monitoring_response_topic

        self.neo4j_uri = neo4j_uri
        self.neo4j_user = neo4j_user
        self.neo4j_pwd = neo4j_pwd
        self.neo4j_connection_lifetime = neo4j_connection_lifetime
        self.aws_inventory_sync_request_topic = aws_inventory_sync_request_topic
        self.aws_inventory_sync_response_topic = aws_inventory_sync_response_topic
        self.aws_iam_deepdive_request_topic = aws_iam_deepdive_request_topic
        self.aws_iam_deepdive_response_topic = aws_iam_deepdive_response_topic
        self.aws_inventory_views_request_topic = aws_inventory_views_request_topic
        self.aws_inventory_views_response_topic = aws_inventory_views_response_topic

        self.aws_remediation_request_topic = aws_remediation_request_topic
        self.aws_remediation_response_topic = aws_remediation_response_topic
        self.aws_remediation_sourceip = aws_remediation_sourceip
        self.aws_remediation_ports = aws_remediation_ports
        self.aws_remediation_rotation_threshold = aws_remediation_rotation_threshold
        self.aws_remediation_retention_period = aws_remediation_retention_period
        self.aws_remediation_kms_master_key_id = aws_remediation_kms_master_key_id
        self.aws_remediation_kms_datakey_reuse_period_seconds = aws_remediation_kms_datakey_reuse_period_seconds
        self.aws_cost_anomaly_request_topic = aws_cost_anomaly_request_topic
        self.aws_cost_anomaly_response_topic = aws_cost_anomaly_response_topic
        self.aws_cost_anomaly_granularity = aws_cost_anomaly_granularity
        self.aws_cost_anomaly_cost_usage_table = aws_cost_anomaly_cost_usage_table
        self.aws_cost_anomaly_secondary_index = aws_cost_anomaly_secondary_index
        self.aws_cost_anomaly_total_days_to_prefill = aws_cost_anomaly_total_days_to_prefill
        self.aws_cost_anomaly_services = aws_cost_anomaly_services
        self.aws_cost_saving_request_topic = aws_cost_saving_request_topic
        self.aws_cost_saving_response_topic = aws_cost_saving_response_topic

        self.aws_cartography_queue_url = aws_cartography_queue_url

    def parse(self, config):
        config = json.loads(config)
        self.sns_offline_url = self.get_value(config, ['common', 'sns', 'offlineURL'])

        self.aws_cartography_queue_url = self.get_value(config, ["common", "cartography", "aws", "queueUrl", "us"])
        if os.environ.get("CDX_DC") == "IN":
            self.aws_cartography_queue_url = self.get_value(config, ["common", "cartography", "aws", "queueUrl", "in"])
        elif os.environ.get("CDX_DC") == "MC1":
            self.aws_cartography_queue_url = self.get_value(config, ["common", "cartography", "aws", "queueUrl", "mc1"])
        if os.environ.get("CDX_CLOUD_TYPE") == "AZURE":
            self.aws_cartography_queue_url = self.get_value(config, ["common", "cartography", "azure", "queueUrl", "us"])

        if config.get('audit'):
            cfg = config['audit']
            self.audit_sns_request_topic = self.get_sns_topic(self.get_value(cfg, ['sns', 'reqTopic']))
            self.audit_sns_response_topic = self.get_sns_topic(self.get_value(cfg, ['sns', 'resTopic']))
            self.aws_iam_compliance_request_topic = self.get_sns_topic(self.get_value(cfg, ['iamcompliance', 'reqTopic']), self.audit_sns_request_topic)
            self.aws_iam_compliance_response_topic = self.get_sns_topic(self.get_value(cfg, ['iamcompliance', 'resTopic']), self.audit_sns_response_topic)
            self.aws_iam_compliance_min_days_for_rotation = self.get_value(cfg, ['iamcompliance', 'minDaysForRotation'])
            self.aws_iam_compliance_min_days_for_update = self.get_value(cfg, ['iamcompliance', 'minDaysForUpdate'])
            self.aws_iam_compliance_min_days_for_use = self.get_value(cfg, ['iamcompliance', 'minDaysForUse'])
            self.aws_sg_audit_request_topic = self.get_sns_topic(self.get_value(cfg, ['sgaudit', 'reqTopic']), self.audit_sns_request_topic)
            self.aws_sg_audit_response_topic = self.get_sns_topic(self.get_value(cfg, ['sgaudit', 'resTopic']), self.audit_sns_response_topic)
            self.aws_s3_public_check_request_topic = self.get_sns_topic(self.get_value(cfg, ['s3publiccheck', 'reqTopic']), self.audit_sns_request_topic)
            self.aws_s3_public_check_response_topic = self.get_sns_topic(self.get_value(cfg, ['s3publiccheck', 'resTopic']), self.audit_sns_response_topic)
            self.aws_ec2_monitoring_request_topic = self.get_sns_topic(self.get_value(cfg, ['ec2monitoring', 'reqTopic']), self.audit_sns_request_topic)
            self.aws_ec2_monitoring_response_topic = self.get_sns_topic(self.get_value(cfg, ['ec2monitoring', 'resTopic']), self.audit_sns_response_topic)
            self.aws_ec2_monitoring_outdated_instance_types = self.get_value(cfg, ['ec2monitoring', 'outdatedInstanceTypes'])
            self.aws_rds_monitoring_request_topic = self.get_sns_topic(self.get_value(cfg, ['rdsmonitoring', 'reqTopic']), self.audit_sns_request_topic)
            self.aws_rds_monitoring_response_topic = self.get_sns_topic(self.get_value(cfg, ['rdsmonitoring', 'resTopic']), self.audit_sns_response_topic)
            self.aws_lambda_monitoring_request_topic = self.get_sns_topic(self.get_value(cfg, ['lambdamonitoring', 'reqTopic']), self.audit_sns_request_topic)
            self.aws_lambda_monitoring_response_topic = self.get_sns_topic(self.get_value(cfg, ['lambdamonitoring', 'resTopic']), self.audit_sns_response_topic)
            self.aws_es_monitoring_request_topic = self.get_sns_topic(self.get_value(cfg, ['esmonitoring', 'reqTopic']), self.audit_sns_request_topic)
            self.aws_es_monitoring_response_topic = self.get_sns_topic(self.get_value(cfg, ['esmonitoring', 'resTopic']), self.audit_sns_response_topic)
            self.aws_kms_monitoring_request_topic = self.get_sns_topic(self.get_value(cfg, ['kmsmonitoring', 'reqTopic']), self.audit_sns_request_topic)
            self.aws_kms_monitoring_response_topic = self.get_sns_topic(self.get_value(cfg, ['kmsmonitoring', 'resTopic']), self.audit_sns_response_topic)
            self.aws_elb_monitoring_request_topic = self.get_sns_topic(self.get_value(cfg, ['elbmonitoring', 'reqTopic']), self.audit_sns_request_topic)
            self.aws_elb_monitoring_response_topic = self.get_sns_topic(self.get_value(cfg, ['elbmonitoring', 'resTopic']), self.audit_sns_response_topic)
            self.aws_ses_monitoring_request_topic = self.get_sns_topic(self.get_value(cfg, ['sesmonitoring', 'reqTopic']), self.audit_sns_request_topic)
            self.aws_ses_monitoring_response_topic = self.get_sns_topic(self.get_value(cfg, ['sesmonitoring', 'resTopic']), self.audit_sns_response_topic)
            self.aws_dynamodb_monitoring_request_topic = self.get_sns_topic(self.get_value(cfg, ['dynamodbmonitoring', 'reqTopic']), self.audit_sns_request_topic)
            self.aws_dynamodb_monitoring_response_topic = self.get_sns_topic(self.get_value(cfg, ['dynamodbmonitoring', 'resTopic']), self.audit_sns_response_topic)
            self.aws_sns_monitoring_request_topic = self.get_sns_topic(self.get_value(cfg, ['snsmonitoring', 'reqTopic']), self.audit_sns_request_topic)
            self.aws_sns_monitoring_response_topic = self.get_sns_topic(self.get_value(cfg, ['snsmonitoring', 'resTopic']), self.audit_sns_response_topic)
            self.aws_kubernetes_monitoring_request_topic = self.get_sns_topic(self.get_value(cfg, ['kubernetesmonitoring', 'reqTopic']), self.audit_sns_request_topic)
            self.aws_kubernetes_monitoring_response_topic = self.get_sns_topic(self.get_value(cfg, ['kubernetesmonitoring', 'resTopic']), self.audit_sns_response_topic)
            self.aws_kubernetes_monitoring_latest_versions = self.get_value(cfg, ['kubernetesmonitoring', 'latestVersions'])
            self.aws_apigateway_monitoring_request_topic = self.get_sns_topic(self.get_value(cfg, ['apigatewaymonitoring', 'reqTopic']), self.audit_sns_request_topic)
            self.aws_apigateway_monitoring_response_topic = self.get_sns_topic(self.get_value(cfg, ['apigatewaymonitoring', 'resTopic']), self.audit_sns_response_topic)
            self.aws_cloudfront_monitoring_request_topic = self.get_sns_topic(self.get_value(cfg, ['cloudfrontmonitoring', 'reqTopic']), self.audit_sns_request_topic)
            self.aws_cloudfront_monitoring_response_topic = self.get_sns_topic(self.get_value(cfg, ['cloudfrontmonitoring', 'resTopic']), self.audit_sns_response_topic)
            self.aws_cloudtrail_monitoring_request_topic = self.get_sns_topic(self.get_value(cfg, ['cloudtrailmonitoring', 'reqTopic']), self.audit_sns_request_topic)
            self.aws_cloudtrail_monitoring_response_topic = self.get_sns_topic(self.get_value(cfg, ['cloudtrailmonitoring', 'resTopic']), self.audit_sns_response_topic)
            self.aws_redshift_monitoring_request_topic = self.get_sns_topic(self.get_value(cfg, ['redshiftmonitoring', 'reqTopic']), self.audit_sns_request_topic)
            self.aws_redshift_monitoring_response_topic = self.get_sns_topic(self.get_value(cfg, ['redshiftmonitoring', 'resTopic']), self.audit_sns_response_topic)
            self.aws_redshift_monitoring_idleconnection_limit_per_day = self.get_value(cfg, ['redshiftmonitoring', 'idleConnectionLimitPerDay'])
            self.aws_redshift_monitoring_idle_readiops_limit_per_day = self.get_value(cfg, ['redshiftmonitoring', 'idleReadIOPSLimitPerDay'])
            self.aws_redshift_monitoring_idle_writeiops_limit_per_day = self.get_value(cfg, ['redshiftmonitoring', 'idleWriteIOPSLimitPerDay'])
            self.aws_redshift_monitoring_maximum_diskspace_usage_limit = self.get_value(cfg, ['redshiftmonitoring', 'maximumDiskSpaceUsageLimit'])
            self.aws_redshift_monitoring_underutilized_average_cpu_usage_limit = self.get_value(cfg, ['redshiftmonitoring', 'underutilizedAverageCPUUsageLimit'])
            self.aws_redshift_monitoring_underutilized_readiops_limit_per_day = self.get_value(cfg, ['redshiftmonitoring', 'underutilizedReadIOPSLimitPerDay'])
            self.aws_redshift_monitoring_underutilized_writeiops_limit_per_day = self.get_value(cfg, ['redshiftmonitoring', 'underutilizedWriteIOPSLimitPerDay'])
            self.aws_cloudformation_monitoring_request_topic = self.get_sns_topic(self.get_value(cfg, ['cloudformationmonitoring', 'reqTopic']), self.audit_sns_request_topic)
            self.aws_cloudformation_monitoring_response_topic = self.get_sns_topic(self.get_value(cfg, ['cloudformationmonitoring', 'resTopic']), self.audit_sns_response_topic)
            self.aws_sqs_monitoring_request_topic = self.get_sns_topic(self.get_value(cfg, ['sqsmonitoring', 'reqTopic']), self.audit_sns_request_topic)
            self.aws_sqs_monitoring_response_topic = self.get_sns_topic(self.get_value(cfg, ['sqsmonitoring', 'resTopic']), self.audit_sns_response_topic)
            self.aws_cloudwatch_monitoring_request_topic = self.get_sns_topic(self.get_value(cfg, ['cloudwatchmonitoring', 'reqTopic']), self.audit_sns_request_topic)
            self.aws_cloudwatch_monitoring_response_topic = self.get_sns_topic(self.get_value(cfg, ['cloudwatchmonitoring', 'resTopic']), self.audit_sns_response_topic)
            self.aws_route53_monitoring_request_topic = self.get_sns_topic(self.get_value(cfg, ['route53monitoring', 'reqTopic']), self.audit_sns_request_topic)
            self.aws_route53_monitoring_response_topic = self.get_sns_topic(self.get_value(cfg, ['route53monitoring', 'resTopic']), self.audit_sns_response_topic)

        if config.get('inventory'):
            cfg = config['inventory']
            self.neo4j_uri = self.get_value(cfg, ['neo4j', 'uri'])
            self.neo4j_user = self.get_value(cfg, ['neo4j', 'user'])
            self.neo4j_pwd = self.get_value(cfg, ['neo4j', 'pwd'])
            self.neo4j_connection_lifetime = self.get_value(cfg, ['neo4j', 'connection_lifetime'])
            self.aws_inventory_sync_request_topic = self.get_sns_topic(self.get_value(cfg, ['awsinventorysync', 'reqTopic']), self.audit_sns_request_topic)
            self.aws_inventory_sync_response_topic = self.get_sns_topic(self.get_value(cfg, ['awsinventorysync', 'resTopic']), self.audit_sns_response_topic)
            self.aws_iam_deepdive_request_topic = self.get_sns_topic(self.get_value(cfg, ['awsiamdeepdive', 'reqTopic']), self.audit_sns_request_topic)
            self.aws_iam_deepdive_response_topic = self.get_sns_topic(self.get_value(cfg, ['awsiamdeepdive', 'resTopic']), self.audit_sns_response_topic)
            self.aws_inventory_views_request_topic = self.get_sns_topic(self.get_value(cfg, ['awsinventoryviews', 'reqTopic']), self.audit_sns_request_topic)
            self.aws_inventory_views_response_topic = self.get_sns_topic(self.get_value(cfg, ['awsinventoryviews', 'resTopic']), self.audit_sns_response_topic)

        if config.get('monitoring'):
            cfg = config['monitoring']
            self.aws_remediation_request_topic = self.get_sns_topic(self.get_value(cfg, ['awsremediation', 'reqTopic']), self.audit_sns_request_topic)
            self.aws_remediation_response_topic = self.get_sns_topic(self.get_value(cfg, ['awsremediation', 'resTopic']), self.audit_sns_response_topic)
            self.aws_remediation_sourceip = self.get_value(cfg, ['awsremediation', 'sourceIp'])
            self.aws_remediation_ports = self.get_value(cfg, ['awsremediation', 'ports'])
            self.aws_remediation_rotation_threshold = self.get_value(cfg, ['awsremediation', 'rotationThreshold'])
            self.aws_remediation_retention_period = self.get_value(cfg, ['awsremediation', 'retentionPeriod'])
            self.aws_remediation_kms_master_key_id = self.get_value(cfg, ['awsremediation', 'kmsMasterKeyId'])
            self.aws_remediation_kms_datakey_reuse_period_seconds = self.get_value(cfg, ['awsremediation', 'kmsDataKeyReusePeriodSeconds'])
            self.aws_cost_anomaly_request_topic = self.get_sns_topic(self.get_value(cfg, ['awscostanomaly', 'reqTopic']), self.audit_sns_request_topic)
            self.aws_cost_anomaly_response_topic = self.get_sns_topic(self.get_value(cfg, ['awscostanomaly', 'resTopic']), self.audit_sns_response_topic)
            self.aws_cost_anomaly_granularity = self.get_value(cfg, ['awscostanomaly', 'granularity'])
            self.aws_cost_anomaly_cost_usage_table = self.get_value(cfg, ['awscostanomaly', 'costAndUsageTable'])
            self.aws_cost_anomaly_secondary_index = self.get_value(cfg, ['awscostanomaly', 'secondaryIndex'])
            self.aws_cost_anomaly_total_days_to_prefill = self.get_value(cfg, ['awscostanomaly', 'totalDaysToPrefill'])
            self.aws_cost_anomaly_services = self.get_value(cfg, ['awscostanomaly', 'services'])
            self.aws_cost_saving_request_topic = self.get_sns_topic(self.get_value(cfg, ['awscostsaving', 'reqTopic']), self.audit_sns_request_topic)
            self.aws_cost_saving_response_topic = self.get_sns_topic(self.get_value(cfg, ['awscostsaving', 'resTopic']), self.audit_sns_response_topic)

    def get_sns_topic(self, topic, def_val=None):
        if not topic or len(topic) == 0:
            return def_val

        return f'arn:aws:sns:{self.region}:{self.aws_account_id}:{topic}'

    def get_value(self, cfg, keys):
        if cfg.get(keys[0]):
            return self.get_value(cfg[keys[0]], keys[1:]) if len(keys) > 1 else cfg.get(keys[0])

        return None
