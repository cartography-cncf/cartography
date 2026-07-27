"""
GraphQL documents for the Railway public API.

Railway's rate limit is per hour (100 requests on the Free plan, 1000 on Hobby, 10000 on
Pro), so this module deliberately favours a few deeply nested documents over many flat ones.
See docs/root/modules/railway/config.md for the resulting request budget.
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

# Everything hanging off a single project, in one request.
#
# SECURITY: the `variables` selection deliberately requests only `name` and `isSealed`.
# Railway can return variable values, but Cartography must never ingest secret material.
# Do not add a `value` field here.
PROJECT_BUNDLE_QUERY = """
query ProjectBundle($projectId: String!, $first: Int!) {
  project(id: $projectId) {
    id
    environments(first: $first) {
      edges {
        node {
          id
          name
          projectId
          createdAt
          isEphemeral
          serviceInstances(first: $first) {
            edges {
              node {
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
              }
            }
            pageInfo {
              hasNextPage
              endCursor
            }
          }
          deployments(first: $first) {
            edges {
              node {
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
              }
            }
            pageInfo {
              hasNextPage
              endCursor
            }
          }
          volumeInstances(first: $first) {
            edges {
              node {
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
              }
            }
            pageInfo {
              hasNextPage
              endCursor
            }
          }
          variables(first: $first) {
            edges {
              node {
                id
                name
                isSealed
                serviceId
                environmentId
                createdAt
              }
            }
            pageInfo {
              hasNextPage
              endCursor
            }
          }
          deploymentTriggers(first: $first) {
            edges {
              node {
                id
                provider
                repository
                branch
                serviceId
                environmentId
              }
            }
            pageInfo {
              hasNextPage
              endCursor
            }
          }
        }
      }
      pageInfo {
        hasNextPage
        endCursor
      }
    }
    services(first: $first) {
      edges {
        node {
          id
          name
          icon
          projectId
          createdAt
          updatedAt
          templateId
          isRestricted
        }
      }
      pageInfo {
        hasNextPage
        endCursor
      }
    }
    volumes(first: $first) {
      edges {
        node {
          id
          name
          projectId
          createdAt
        }
      }
      pageInfo {
        hasNextPage
        endCursor
      }
    }
  }
}
"""

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
