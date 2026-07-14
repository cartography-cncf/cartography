# Analysis-job examples

## GCP module - scoped + global jobs

```python
# cartography/intel/gcp/__init__.py

def start_gcp_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    # ... sync all orgs, folders, projects, and resources ...

    run_typed_analysis_job(GCP_COMPUTE_INSTANCE_VPC_ANALYSIS, neo4j_session, common_job_parameters)
    run_typed_analysis_job(GCP_GKE_ASSET_EXPOSURE, neo4j_session, common_job_parameters)
    run_typed_analysis_job(GCP_GKE_BASIC_AUTH, neo4j_session, common_job_parameters)


def _sync_one_project(...) -> None:
    # ... sync project resources ...

    run_typed_analysis_job(
        GCP_COMPUTE_FORWARDING_RULE_EXPOSURE,
        neo4j_session,
        common_job_parameters,
    )
    run_typed_analysis_job(
        GCP_COMPUTE_FIREWALL_INGRESS,
        neo4j_session,
        common_job_parameters,
    )
    run_typed_analysis_job(
        GCP_COMPUTE_INSTANCE_EXPOSURE,
        neo4j_session,
        common_job_parameters,
    )
    run_typed_analysis_job(
        GCP_COMPUTE_CLOUDRUN_EXPOSURE,
        neo4j_session,
        common_job_parameters,
    )
```

## AWS module - scoped + global with deps

```python
# cartography/intel/aws/__init__.py

def _sync_one_account(...) -> None:
    # ... sync resources ...

    run_typed_analysis_job(AWS_EC2_IAM_INSTANCE_PROFILE, neo4j_session, common_job_parameters)
    run_typed_analysis_job(AWS_LAMBDA_ECR, neo4j_session, common_job_parameters)


def _perform_aws_analysis(requested_syncs, neo4j_session, common_job_parameters) -> None:
    run_typed_analysis_and_ensure_deps(
        AWS_EC2_ASSET_EXPOSURE_JOBS,
        {"ec2:instance", "ec2:security_group", "ec2:load_balancer", "ec2:load_balancer_v2"},
        set(requested_syncs),
        common_job_parameters,
        neo4j_session,
    )

    run_typed_analysis_and_ensure_deps(
        AWS_EKS_ASSET_EXPOSURE,
        {"eks"},
        set(requested_syncs),
        common_job_parameters,
        neo4j_session,
    )
```

## Semgrep module - scoped within findings sync

```python
# cartography/intel/semgrep/findings.py

def sync_findings(...) -> None:
    # ... load findings ...

    run_typed_analysis_job(SEMGREP_SCA_RISK_ANALYSIS, neo4j_session, common_job_parameters)

    cleanup(neo4j_session, common_job_parameters)
```

## Audit table

Modules with proper analysis-job integration as of the migration:

| Module    | Analysis jobs                                                                                                                                                                                       | Location                                       |
| --------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------- |
| AWS       | `AWS_EC2_ASSET_EXPOSURE_JOBS`, `AWS_EC2_KEYPAIR_ANALYSIS_JOBS`, `AWS_EKS_ASSET_EXPOSURE`, `AWS_FOREIGN_ACCOUNTS`, `AWS_ECS_ASSET_EXPOSURE`                                                          | Global (in `_perform_aws_analysis`)            |
| AWS       | `AWS_EC2_IAM_INSTANCE_PROFILE`, `AWS_LAMBDA_ECR`                                                                                                                                                     | Scoped (per-account in `_sync_one_account`)    |
| AWS S3    | `AWS_S3ACL_ANALYSIS`                                                                                                                                                                                 | Scoped (in `s3.py`)                            |
| GCP       | `GCP_COMPUTE_EXPOSURE_JOBS`                                                                                                                                                                         | Scoped (per-project in `_sync_one_project`)    |
| GCP       | `GCP_GKE_ASSET_EXPOSURE`, `GCP_GKE_BASIC_AUTH`, `GCP_COMPUTE_INSTANCE_VPC_ANALYSIS`                                                                                                                  | Global (end of `start_gcp_ingestion`)          |
| GSuite    | `GSUITE_HUMAN_LINK`                                                                                                                                                                                  | Global (end of `start_gsuite_ingestion`)       |
| Keycloak  | `cartography.intel.keycloak.inheritance` (Python)                                                                                                                                                    | Global (end of `start_keycloak_ingestion`)     |
| Semgrep   | `SEMGREP_SCA_RISK_ANALYSIS`                                                                                                                                                                         | Scoped (in `findings.py`)                      |

`AWS_ECS_ASSET_EXPOSURE` is marked deprecated in favour of the ontology `LoadBalancer-[:EXPOSE]->Container` pattern but is still called for backward compatibility.
