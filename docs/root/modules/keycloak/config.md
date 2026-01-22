## Keycloak Configuration

Follow these steps to enable Keycloak integration with Cartography.

1. **Create your client in Keycloak**
   1. Log into the Keycloak admin console
   1. Inside the `master` realm, create a new client:
      * Under **General settings**, set the client type to `OpenID Connect`
      * In the **Capability config** section, enable only `Client authentication`, and check only `Service account roles`
   1. Go to the **Credentials** tab of your client and copy the client secret
   1. Store the client secret in an environment variable. You’ll need to pass the variable name to Cartography using the `--keycloak-client-secret-env-var` CLI flag
   1. Provide the client ID using the `--keycloak-client-id` parameter
1. Set the base URL of your Keycloak instance with the `--keycloak-url` parameter
1. If you created your client in a realm other than `master`, specify it using the `--keycloak-realm` parameter
