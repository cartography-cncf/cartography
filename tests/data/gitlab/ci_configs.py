"""Test data for the GitLab CI config parser and intel module."""

TEST_GITLAB_URL = "https://gitlab.example.com"
TEST_PROJECT_ID = 123

# Minimal pipeline with mixed includes (string, project pinned, project unpinned, remote, template)
PIPELINE_WITH_MIXED_INCLUDES = """
include:
  - '/templates/local-template.yml'
  - project: my-org/shared-ci
    ref: a5ac7e51b41094c92402da3b24376905380afc29
    file: /templates/build.yml
  - project: my-org/shared-ci
    ref: main
    file: /templates/deploy.yml
  - remote: 'https://example.com/ci/templates/test.yml'
  - template: Auto-DevOps.gitlab-ci.yml

stages:
  - build
  - test
  - deploy

variables:
  DEBUG: "false"

default:
  image: python:3.13

build:
  stage: build
  script:
    - echo "Building $CI_PROJECT_NAME with $DATABASE_URL"
    - echo "Token is $DEPLOY_TOKEN"

manual_deploy:
  stage: deploy
  when: manual
  script:
    - ./deploy.sh

mr_only:
  stage: test
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
  script:
    - ./test.sh
"""

# Pipeline triggered only on schedules
PIPELINE_SCHEDULED = """
workflow:
  rules:
    - if: $CI_PIPELINE_SOURCE == "schedule"

stages:
  - cron

nightly:
  stage: cron
  script:
    - ./nightly.sh
"""

# Pipeline that includes a list of local files in a single entry
PIPELINE_LOCAL_LIST = """
include:
  local:
    - '/templates/a.yml'
    - '/templates/b.yml'

build:
  script:
    - echo build
"""

# Empty / non-dict YAML
PIPELINE_EMPTY = ""
PIPELINE_NOT_A_DICT = "- just\n- a\n- list"
PIPELINE_BAD_YAML = "include: [\nnot valid yaml"

# Pipeline with no includes and a top-level image
PIPELINE_NO_INCLUDES = """
image: alpine:3.20

stages:
  - build

build:
  script:
    - echo build
"""

# Sample merged_yaml from /api/v4/projects/:id/ci/lint
LINT_RESPONSE = {
    "valid": True,
    "merged_yaml": PIPELINE_WITH_MIXED_INCLUDES,
    "errors": [],
}

LINT_RESPONSE_INVALID = {
    "valid": False,
    "merged_yaml": PIPELINE_WITH_MIXED_INCLUDES,
    "errors": ["some error"],
}
