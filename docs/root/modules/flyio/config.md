## Fly.io Configuration

Follow these steps to analyze Fly.io objects with Cartography.

1. Create a read-only org-scoped Fly.io token.

    ```bash
    fly tokens create readonly -o <org-slug> --name "cartography" --expiry 720h
    ```

1. Populate an environment variable with the token.

    ```bash
    export FLY_API_TOKEN="<token>"
    ```

1. Run Cartography with the Fly.io module enabled.

    ```bash
    cartography --selected-modules flyio \
      --flyio-token-env-var FLY_API_TOKEN \
      --flyio-org-slug <org-slug>
    ```

1. Optionally override the Machines API base URL with `--flyio-base-url`.

    The default is `https://api.machines.dev`.
