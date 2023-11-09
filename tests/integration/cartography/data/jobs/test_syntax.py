import sys

import pytest

import cartography.util
if sys.version_info >= (3, 7):
    from importlib.resources import contents
else:
    from importlib_resources import contents


def test_analysis_jobs_cypher_syntax(neo4j_session):
    parameters = {
        'AWS_ID': 'my_aws_account_id',
        'OCI_TENANCY_ID': 'my_oci_tenant_id',
        'UPDATE_TAG': 'my_update_tag',
        'OKTA_ORG_ID': 'my_okta_org_id',
        'DEPLOYMENT_ID': 'my_deployment_id',
    }

    for job_name in contents('cartography.data.jobs.analysis'):
        if not job_name.endswith('.json'):
            continue
        try:
            cartography.util.run_analysis_job(job_name, neo4j_session, parameters)
        except Exception as e:
            pytest.fail(f"run_analysis_job failed for analysis job '{job_name}' with exception: {e}")

    for job_name in contents('cartography.data.jobs.scoped_analysis'):
        if not job_name.endswith('.json'):
            continue
        try:
            cartography.util.run_scoped_analysis_job(job_name, neo4j_session, parameters)
        except Exception as e:
            pytest.fail(f"run_analysis_job failed for analysis job '{job_name}' with exception: {e}")


def test_cleanup_jobs_cypher_syntax(neo4j_session):
    parameters = {
        'AWS_ID': None,
        'OCI_TENANCY_ID': None,
        'UPDATE_TAG': None,
        'OKTA_ORG_ID': None,
        'DO_ACCOUNT_ID': None,
        'AZURE_SUBSCRIPTION_ID': None,
    }

    for job_name in contents('cartography.data.jobs.cleanup'):
        if not job_name.endswith('.json'):
            continue
        try:
            cartography.util.run_cleanup_job(job_name, neo4j_session, parameters)
        except Exception as e:
            pytest.fail(f"run_cleanup_job failed for cleanup job '{job_name}' with exception: {e}")
