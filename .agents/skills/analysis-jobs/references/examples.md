# Analysis-job examples

## GCP module — global jobs at end of ingestion

```python
# cartography/intel/gcp/__init__.py

def start_gcp_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    # ... sync all orgs, folders, projects, and resources ...

    run_analysis_job("gcp_compute_asset_inet_exposure.json", neo4j_session, common_job_parameters)
    run_analysis_job("gcp_gke_asset_exposure.json",          neo4j_session, common_job_parameters)
    run_analysis_job("gcp_gke_basic_auth.json",              neo4j_session, common_job_parameters)
    run_analysis_job("gcp_compute_instance_vpc_analysis.json", neo4j_session, common_job_parameters)
```

## AWS module — scoped + global with deps

```python
# cartography/intel/aws/__init__.py

def _sync_one_account(...) -> None:
    # ... sync resources ...

    # scoped per-account
    run_scoped_analysis_job("aws_ec2_iaminstanceprofile.json", neo4j_session, common_job_parameters)

    # cross-account, but called per account loop
    run_analysis_job("aws_lambda_ecr.json", neo4j_session, common_job_parameters)


def _perform_aws_analysis(requested_syncs, neo4j_session, common_job_parameters) -> None:
    run_analysis_and_ensure_deps(
        "aws_ec2_asset_exposure.json",
        {"ec2:instance", "ec2:security_group", "ec2:load_balancer", "ec2:load_balancer_v2"},
        set(requested_syncs),
        common_job_parameters,
        neo4j_session,
    )

    run_analysis_and_ensure_deps(
        "aws_eks_asset_exposure.json",
        {"eks"},
        set(requested_syncs),
        common_job_parameters,
        neo4j_session,
    )
```

## Semgrep module — scoped within findings sync

```python
# cartography/intel/semgrep/findings.py

def sync_findings(...) -> None:
    # ... load findings ...

    run_scoped_analysis_job("semgrep_sca_risk_analysis.json", neo4j_session, common_job_parameters)

    cleanup(neo4j_session, common_job_parameters)
```

## Audit table

Modules with proper analysis-job integration as of the migration:

| Module    | Analysis jobs                                                                                                                                                                                       | Location                                       |
| --------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------- |
| AWS       | `aws_ec2_asset_exposure.json`, `aws_ec2_keypair_analysis.json`, `aws_eks_asset_exposure.json`, `aws_foreign_accounts.json`, `aws_ecs_asset_exposure.json`                                            | Global (in `_perform_aws_analysis`)            |
| AWS       | `aws_ec2_iaminstanceprofile.json`, `aws_lambda_ecr.json`                                                                                                                                            | Scoped (per-account in `_sync_one_account`)    |
| AWS S3    | `aws_s3acl_analysis.json`                                                                                                                                                                            | Scoped (in `s3.py`)                            |
| GCP       | `gcp_compute_asset_inet_exposure.json`, `gcp_gke_asset_exposure.json`, `gcp_gke_basic_auth.json`, `gcp_compute_instance_vpc_analysis.json`                                                          | Global (end of `start_gcp_ingestion`)          |
| GSuite    | `gsuite_human_link.json`                                                                                                                                                                             | Global (end of `start_gsuite_ingestion`)       |
| Keycloak  | `cartography.intel.keycloak.inheritance` (Python)                                                                                                                                                    | Global (end of `start_keycloak_ingestion`)     |
| Semgrep   | `semgrep_sca_risk_analysis.json`                                                                                                                                                                    | Scoped (in `findings.py`)                      |

`aws_ecs_asset_exposure.json` is marked deprecated in favour of the ontology `LoadBalancer-[:EXPOSE]->Container` pattern but is still called for backward compatibility.
