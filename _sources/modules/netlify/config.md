# Netlify Configuration

Cartography needs a Netlify personal access token and the slug of the team to sync.

## Authentication

1. Go to [User settings > Applications > Personal access tokens](https://app.netlify.com/user/applications#personal-access-tokens)
   and create a new token.
1. Store it in an environment variable.

```bash
export NETLIFY_TOKEN="<your-token>"
```

```{note}
A Netlify personal access token carries the full permissions of the user who created it, so
create it from an account whose role in the team is as low as the sync allows. Cartography only
issues `GET` requests, but the token itself is not read-only, so treat it as a privileged
credential. Netlify also invalidates every token created before a password reset, so a reset
breaks the sync until the token is recreated.
```

## Required Permissions

Cartography reads team-level and site-level resources, so the token's user needs to be a member
of the team you want to sync. Which resources come back depends on the role and on the team's
plan:

| Resource | Requirement |
|---|---|
| Team, members, sites, deploys, functions, forms, snippets, build hooks, notification hooks, deploy keys, DNS | Any team member role |
| Team-wide (shared) environment variables | A plan that includes shared environment variables. A Free team was observed to answer with an empty list rather than a 403. If the call is rejected, Cartography logs a warning, still syncs site-scoped variables, and skips the environment variable cleanup for that run so previously ingested shared variables are not deleted. |
| Dev servers, agent runners | A plan that includes them. Both are on the Free plan with a quota of one each. |
| Netlify DB branches and snapshots | Only fetched for sites whose payload reports `has_database`. |
| TLS certificates | Only present once a site has a custom domain with a provisioned certificate. |

## Configure Cartography

| Option | Required | Description |
|---|---|---|
| `--netlify-token-env-var` | Yes | Name of the environment variable holding the personal access token. |
| `--netlify-account-slug` | Yes | Slug of the team to sync. One run syncs one team. |
| `--netlify-base-url` | No | API endpoint, defaults to `https://api.netlify.com/api/v1`. |

The team slug is the segment in your team URL, `https://app.netlify.com/teams/<slug>/`, and
`netlify api listAccountsForUser --data '{}'` lists every slug a token can see. Cartography fails
with an explicit error listing the visible slugs if the one you pass is not among them.

## Run Cartography

```bash
cartography \
  --selected-modules netlify \
  --netlify-token-env-var NETLIFY_TOKEN \
  --netlify-account-slug your-team-slug
```

## References

- [Netlify OpenAPI reference](https://open-api.netlify.com/)
- [Netlify personal access tokens](https://docs.netlify.com/api/get-started/#authentication)
