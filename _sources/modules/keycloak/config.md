# Keycloak Configuration

## Authentication

1. Log in to the Keycloak admin console.
2. In the `master` realm, create a client.
3. Under **General settings**, set the client type to `OpenID Connect`.
4. Under **Capability config**, enable only **Client authentication** and
   **Service account roles**.
5. Open the client's **Credentials** tab and copy the client secret.
6. Store the client secret in an environment variable:

   ```bash
   export KEYCLOAK_CLIENT_SECRET="<your-client-secret>"
   ```

## Configure Cartography

Provide the client ID with `--keycloak-client-id` and the Keycloak base URL
with `--keycloak-url`. If the authentication client is in a realm other than
`master`, identify that realm with `--keycloak-realm`.

By default, Cartography reads the client secret from
`KEYCLOAK_CLIENT_SECRET`. Use `--keycloak-client-secret-env-var` to select a
different environment variable.

## Run Cartography

```bash
cartography \
  --selected-modules keycloak \
  --keycloak-client-id "<your-client-id>" \
  --keycloak-url https://keycloak.example.com \
  --keycloak-realm master \
  --keycloak-client-secret-env-var KEYCLOAK_CLIENT_SECRET
```

## Advanced Configuration

The realm passed with `--keycloak-realm` is used for authentication. Cartography
syncs all realms that the client can access.
