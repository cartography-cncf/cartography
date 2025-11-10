## Proxmox Configuration

Follow these steps to analyze Proxmox Virtual Environment infrastructure with Cartography.

1. **Prepare your Proxmox credentials**

    Proxmox VE 7.0+ is required (tested with 8.x). Read-only access is sufficient - the `PVEAuditor` role is recommended.

### Option 1: API Token Authentication (Recommended)

1. Create an API token in Proxmox:
    1. Navigate to **Datacenter → Permissions → API Tokens** in the Proxmox web interface.
    1. Click **Add** to create a new token.
    1. Set the user to `root@pam` (or another user with appropriate permissions).
    1. Set the token name to `cartography`.
    1. Uncheck **Privilege Separation** (or grant the `PVEAuditor` role separately).
    1. Click **Add** and save the token value securely.

1. Populate environment variables with the token name and value. You can pass the environment variable names via CLI with the `--proxmox-token-name-env-var` and `--proxmox-token-value-env-var` parameters.

    ```bash
    export PROXMOX_TOKEN_NAME="cartography"
    export PROXMOX_TOKEN_VALUE="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
    ```

### Option 2: Password Authentication

1. Populate an environment variable with the password. You can pass the environment variable name via CLI with the `--proxmox-password-env-var` parameter.

    ```bash
    export PROXMOX_PASSWORD="your-password"
    ```

1. The Proxmox user or API token needs the following permissions:

    - **VM.Audit**: Read VM and container configurations
    - **Datastore.Audit**: Read storage information
    - **Sys.Audit**: Read system and node information

    The built-in **PVEAuditor** role provides all necessary permissions for read-only access.

1. Provide the Proxmox host using the `--proxmox-host` parameter and user using the `--proxmox-user` parameter (e.g., `root@pam`).

1. [Optional] To use a custom port, use the `--proxmox-port` parameter (default is 8006).

1. [Optional] To disable SSL verification (not recommended for production), use the `--proxmox-verify-ssl false` parameter.

1. [Optional] To enable QEMU Guest Agent data collection (requires guest agent installed in VMs), use the `--proxmox-enable-guest-agent` flag.

1. [Optional] To sync multiple Proxmox clusters, run Cartography separately for each cluster. Each cluster will be represented as a separate `ProxmoxCluster` node in the graph.
