CONTRIBUTING to CloudScope-GCP
Author: Sapna Mohanta

This file explains how to contribute this GCP ingestion module to CNCF Cartography.
It provides a PR-style guide, recommended branch names, commit message format, and tests to include.

1. Fork the cartography repository and create a branch:
   git clone https://github.com/your-username/cartography.git
   cd cartography
   git checkout -b sapna/gcp-integration-<short-description>

2. Add module files under cartography/intel/gcp/ (follow the structure in this repo):
   - gcp_resources.py
   - schema.yaml
   - tests/

3. Write unit tests for the module to run in CI (mock GCP responses).

4. Commit messages:
   Use concise messages, e.g.:
     feat(gcp): add compute and storage ingestion module
     test(gcp): add unit tests for resource parsing

5. Submit a pull request with a descriptive title and link to this repository for reviewers to replicate the work locally.

6. In PR description include:
   - Description of resources covered
   - Example Cypher queries
   - Any limitations and follow-ups

Thank you.
