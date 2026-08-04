"""
GraphQL documents for the Railway public API.

Railway's rate limit is per hour (100 requests on the Free plan, 1000 on Hobby, 10000 on
Pro), so this module deliberately favours a few deeply nested documents over many flat ones.
See docs/root/modules/railway/config.md for the resulting request budget.

Every Relay connection is capped at `first: $first` per request, so the nested bundle can
come back truncated. Each nested connection therefore has a matching flat follow-up document
below, built from the same field selection, which
cartography.intel.railway.projects.drain_project_bundle uses to fetch the remainder. The
selections are shared as Python constants rather than duplicated, so a field added to the
bundle cannot silently go missing from the follow-up.
"""

# Identifies the token holder and the workspaces it can reach. `projects` cannot be queried
# without a workspaceId, so this is the entry point for an account-scoped token.
ME_QUERY = """
query Me {
  me {
    id
    name
    email
    workspaces {
      id
      name
    }
  }
}
"""

WORKSPACE_QUERY = """
query Workspace($workspaceId: String!) {
  workspace(workspaceId: $workspaceId) {
    id
    name
    createdAt
    preferredRegion
    projectCount
    has2FAEnforcement
    hasSAML
    plan
    members {
      id
      name
      email
      role
      twoFactorAuthEnabled
    }
  }
}
"""

PROJECTS_QUERY = """
query Projects($workspaceId: String!, $first: Int!, $after: String) {
  projects(workspaceId: $workspaceId, first: $first, after: $after) {
    edges {
      node {
        id
        name
        description
        isPublic
        isTempProject
        prDeploys
        createdAt
        updatedAt
        deletedAt
        workspaceId
        subscriptionType
        members {
          id
          email
          name
          role
        }
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
"""

# --- Shared field selections -------------------------------------------------------------

_PAGE_INFO = """
    pageInfo {
      hasNextPage
      endCursor
    }
"""

_SERVICE_INSTANCE_FIELDS = """
    id
    serviceId
    serviceName
    environmentId
    createdAt
    updatedAt
    source {
      image
      repo
    }
    builder
    buildCommand
    startCommand
    rootDirectory
    dockerfilePath
    region
    numReplicas
    sleepApplication
    cronSchedule
    healthcheckPath
    restartPolicyType
    restartPolicyMaxRetries
    ipv6EgressEnabled
    latestDeployment {
      id
      status
    }
    domains {
      serviceDomains {
        id
        domain
        suffix
        targetPort
        syncStatus
        createdAt
      }
      customDomains {
        id
        domain
        targetPort
        isRailwayDomain
        syncStatus
        status {
          verified
          certificateStatus
          verificationDnsHost
        }
      }
    }
"""

_DEPLOYMENT_FIELDS = """
    id
    status
    statusUpdatedAt
    createdAt
    projectId
    environmentId
    serviceId
    url
    staticUrl
    canRedeploy
"""

_VOLUME_INSTANCE_FIELDS = """
    id
    volumeId
    environmentId
    serviceId
    mountPath
    region
    sizeMB
    currentSizeMB
    state
    createdAt
"""

# SECURITY: only the variable name and its sealed flag are requested. Railway can return
# variable values, but Cartography must never ingest secret material. Do not add `value`.
_VARIABLE_FIELDS = """
    id
    name
    isSealed
    serviceId
    environmentId
    createdAt
"""

_DEPLOYMENT_TRIGGER_FIELDS = """
    id
    provider
    repository
    branch
    serviceId
    environmentId
"""

_SERVICE_FIELDS = """
    id
    name
    icon
    projectId
    createdAt
    updatedAt
    templateId
    isRestricted
"""

_VOLUME_FIELDS = """
    id
    name
    projectId
    createdAt
"""

# The child connections of an Environment, in the exact shape the transforms expect.
_ENVIRONMENT_CHILDREN = f"""
    serviceInstances(first: $first) {{
      edges {{ node {{ {_SERVICE_INSTANCE_FIELDS} }} }}
      {_PAGE_INFO}
    }}
    deployments(first: $deploymentFirst) {{
      edges {{ node {{ {_DEPLOYMENT_FIELDS} }} }}
      {_PAGE_INFO}
    }}
    volumeInstances(first: $first) {{
      edges {{ node {{ {_VOLUME_INSTANCE_FIELDS} }} }}
      {_PAGE_INFO}
    }}
    variables(first: $first) {{
      edges {{ node {{ {_VARIABLE_FIELDS} }} }}
      {_PAGE_INFO}
    }}
    deploymentTriggers(first: $first) {{
      edges {{ node {{ {_DEPLOYMENT_TRIGGER_FIELDS} }} }}
      {_PAGE_INFO}
    }}
"""

_ENVIRONMENT_FIELDS = f"""
    id
    name
    projectId
    createdAt
    isEphemeral
    {_ENVIRONMENT_CHILDREN}
"""

# --- Documents ---------------------------------------------------------------------------

# Everything hanging off a single project, in one request.
PROJECT_BUNDLE_QUERY = f"""
query ProjectBundle($projectId: String!, $first: Int!, $deploymentFirst: Int!) {{
  project(id: $projectId) {{
    id
    environments(first: $first) {{
      edges {{ node {{ {_ENVIRONMENT_FIELDS} }} }}
      {_PAGE_INFO}
    }}
    services(first: $first) {{
      edges {{ node {{ {_SERVICE_FIELDS} }} }}
      {_PAGE_INFO}
    }}
    volumes(first: $first) {{
      edges {{ node {{ {_VOLUME_FIELDS} }} }}
      {_PAGE_INFO}
    }}
  }}
}}
"""

# Follow-up documents, used only when the bundle came back truncated. Each one returns the
# same node shape as its counterpart inside the bundle.
PROJECT_ENVIRONMENTS_QUERY = f"""
query ProjectEnvironments($projectId: String!, $first: Int!, $deploymentFirst: Int!, $after: String) {{
  project(id: $projectId) {{
    environments(first: $first, after: $after) {{
      edges {{ node {{ {_ENVIRONMENT_FIELDS} }} }}
      {_PAGE_INFO}
    }}
  }}
}}
"""

PROJECT_SERVICES_QUERY = f"""
query ProjectServices($projectId: String!, $first: Int!, $after: String) {{
  project(id: $projectId) {{
    services(first: $first, after: $after) {{
      edges {{ node {{ {_SERVICE_FIELDS} }} }}
      {_PAGE_INFO}
    }}
  }}
}}
"""

PROJECT_VOLUMES_QUERY = f"""
query ProjectVolumes($projectId: String!, $first: Int!, $after: String) {{
  project(id: $projectId) {{
    volumes(first: $first, after: $after) {{
      edges {{ node {{ {_VOLUME_FIELDS} }} }}
      {_PAGE_INFO}
    }}
  }}
}}
"""

ENVIRONMENT_SERVICE_INSTANCES_QUERY = f"""
query EnvironmentServiceInstances($environmentId: String!, $first: Int!, $after: String) {{
  environment(id: $environmentId) {{
    serviceInstances(first: $first, after: $after) {{
      edges {{ node {{ {_SERVICE_INSTANCE_FIELDS} }} }}
      {_PAGE_INFO}
    }}
  }}
}}
"""

ENVIRONMENT_VOLUME_INSTANCES_QUERY = f"""
query EnvironmentVolumeInstances($environmentId: String!, $first: Int!, $after: String) {{
  environment(id: $environmentId) {{
    volumeInstances(first: $first, after: $after) {{
      edges {{ node {{ {_VOLUME_INSTANCE_FIELDS} }} }}
      {_PAGE_INFO}
    }}
  }}
}}
"""

ENVIRONMENT_VARIABLES_QUERY = f"""
query EnvironmentVariables($environmentId: String!, $first: Int!, $after: String) {{
  environment(id: $environmentId) {{
    variables(first: $first, after: $after) {{
      edges {{ node {{ {_VARIABLE_FIELDS} }} }}
      {_PAGE_INFO}
    }}
  }}
}}
"""

ENVIRONMENT_DEPLOYMENT_TRIGGERS_QUERY = f"""
query EnvironmentDeploymentTriggers($environmentId: String!, $first: Int!, $after: String) {{
  environment(id: $environmentId) {{
    deploymentTriggers(first: $first, after: $after) {{
      edges {{ node {{ {_DEPLOYMENT_TRIGGER_FIELDS} }} }}
      {_PAGE_INFO}
    }}
  }}
}}
"""

# Connection key on Environment -> the document that pages through it.
#
# `deployments` is deliberately absent. Every other connection describes current state and
# must be complete, or cleanup would delete whatever it could not see. Deployments are an
# append-only history that grows without bound, and Cartography only needs the recent
# window: it is capped at DEPLOYMENT_PAGE_SIZE per environment and never drained. The
# cleanup consequence is intended - deployments that age out of the window are removed from
# the graph rather than accumulating forever.
ENVIRONMENT_CHILD_QUERIES = {
    "serviceInstances": ENVIRONMENT_SERVICE_INSTANCES_QUERY,
    "volumeInstances": ENVIRONMENT_VOLUME_INSTANCES_QUERY,
    "variables": ENVIRONMENT_VARIABLES_QUERY,
    "deploymentTriggers": ENVIRONMENT_DEPLOYMENT_TRIGGERS_QUERY,
}

# How many of the most recent deployments to keep per environment.
DEPLOYMENT_PAGE_SIZE = 10

# Connection key on Project -> the document that pages through it.
PROJECT_CHILD_QUERIES = {
    "services": PROJECT_SERVICES_QUERY,
    "volumes": PROJECT_VOLUMES_QUERY,
}

PROJECT_TOKENS_QUERY = """
query ProjectTokens($projectId: String!, $first: Int!, $after: String) {
  projectTokens(projectId: $projectId, first: $first, after: $after) {
    edges {
      node {
        id
        name
        displayToken
        projectId
        environmentId
        createdAt
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
"""

API_TOKENS_QUERY = """
query ApiTokens($first: Int!, $after: String) {
  apiTokens(first: $first, after: $after) {
    edges {
      node {
        id
        name
        displayToken
        workspaceId
        expiresAt
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
"""
