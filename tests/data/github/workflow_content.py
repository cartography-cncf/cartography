"""
Test data for GitHub Workflow content parsing.
"""

# Sample CI workflow with various features
WORKFLOW_CI_CONTENT = """
name: CI

on:
  push:
    branches: [main, master]
  pull_request:
    branches: [main]

permissions:
  contents: read
  pull-requests: write

env:
  NODE_VERSION: "18"

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}

      - name: Install dependencies
        run: npm ci
        env:
          NPM_TOKEN: ${{ secrets.NPM_TOKEN }}

      - name: Run tests
        run: npm test
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
          API_KEY: ${{ secrets.API_KEY }}

  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
      - run: npm run lint
"""

# Workflow with pinned SHA actions
WORKFLOW_PINNED_ACTIONS = """
name: Secure Build

on: push

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@a5ac7e51b41094c92402da3b24376905380afc29
      - uses: actions/setup-python@0a5c61591373683505ea898e09a3ea4f39ef2b9c
        with:
          python-version: "3.11"
      - run: pip install -r requirements.txt
"""

# Workflow with reusable workflow calls
WORKFLOW_REUSABLE = """
name: Deploy

on:
  workflow_dispatch:

jobs:
  call-build:
    uses: ./.github/workflows/build.yml
    with:
      environment: production
    secrets: inherit

  call-external:
    uses: octo-org/example-repo/.github/workflows/reusable.yml@main
    secrets:
      deploy_key: ${{ secrets.DEPLOY_KEY }}
"""

# Workflow with all permission types
WORKFLOW_FULL_PERMISSIONS = """
name: Full Permissions

on: push

permissions:
  actions: write
  contents: write
  packages: write
  pull-requests: write
  issues: write
  deployments: write
  statuses: write
  checks: write
  id-token: write
  security-events: write

jobs:
  example:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
"""

# Workflow with Docker action
WORKFLOW_DOCKER_ACTION = """
name: Docker Build

on: push

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: docker://alpine:3.18
        with:
          args: echo "Hello from Alpine"
      - uses: docker://ghcr.io/owner/image:latest
"""

# Workflow with local action
WORKFLOW_LOCAL_ACTION = """
name: Local Action

on: push

jobs:
  custom:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: ./.github/actions/my-custom-action
        with:
          input: value
"""

# Malformed workflow (for testing error handling)
WORKFLOW_MALFORMED = """
name: Bad Workflow
on: push
jobs:
  - this is not valid yaml structure
  build:
    runs-on: invalid
"""

# Empty workflow
WORKFLOW_EMPTY = ""

# Workflow with secrets in various locations
WORKFLOW_SECRETS_EVERYWHERE = """
name: Secrets Test

on: push

env:
  GLOBAL_SECRET: ${{ secrets.GLOBAL_SECRET }}

jobs:
  job1:
    runs-on: ubuntu-latest
    env:
      JOB_SECRET: ${{ secrets.JOB_SECRET }}
    steps:
      - uses: actions/checkout@v4
      - name: Step with secrets
        run: |
          echo "Using ${{ secrets.STEP_SECRET }}"
          curl -H "Authorization: ${{ secrets.AUTH_TOKEN }}" https://api.example.com
        env:
          STEP_ENV_SECRET: ${{ secrets.STEP_ENV_SECRET }}
      - uses: some-action@v1
        with:
          token: ${{ secrets.WITH_SECRET }}

  job2:
    runs-on: ubuntu-latest
    steps:
      - run: echo "${{ secrets.ANOTHER_SECRET }}"
"""

# Workflow with global read-all permissions
WORKFLOW_READ_ALL_PERMISSIONS = """
name: Read All
on: push
permissions: read-all
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
"""
