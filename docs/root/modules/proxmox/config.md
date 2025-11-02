## Configuration

Follow these steps to sync your Proxmox Virtual Environment infrastructure with Cartography.

### Prerequisites

- **Proxmox VE 7.0+** (tested with 8.x)
- **API Token or User Credentials**
- **Permissions**: Read-only access is sufficient (the `PVEAuditor` role is recommended)

### Option 1: API Token Authentication (Recommended)

1. **Create an API token in Proxmox:**
   1. Navigate to **Datacenter → Permissions → API Tokens** in the Proxmox web interface
   2. Click **Add** to create a new token
   3. Set the user to `root@pam` (or another user with appropriate permissions)
   4. Set the token name to `cartography`
   5. Uncheck **Privilege Separation** (or grant the `PVEAuditor` role separately)
   6. Click **Add** and save the token value securely

2. **Set environment variables:**
   ```bash
   export PROXMOX_TOKEN_NAME="cartography"
   export PROXMOX_TOKEN_VALUE="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
   ```

3. **Run Cartography:**
   ```bash
   cartography --neo4j-uri bolt://localhost:7687 \
       --proxmox-host proxmox.example.com \
       --proxmox-user root@pam \
       --proxmox-token-name-env-var PROXMOX_TOKEN_NAME \
       --proxmox-token-value-env-var PROXMOX_TOKEN_VALUE
   ```

### Option 2: Password Authentication

1. **Set the password environment variable:**
   ```bash
   export PROXMOX_PASSWORD="your-password"
   ```

2. **Run Cartography:**
   ```bash
   cartography --neo4j-uri bolt://localhost:7687 \
       --proxmox-host proxmox.example.com \
       --proxmox-user root@pam \
       --proxmox-password-env-var PROXMOX_PASSWORD
   ```

### Required Permissions

The Proxmox user or API token needs the following permissions:

- **VM.Audit**: Read VM and container configurations
- **Datastore.Audit**: Read storage information
- **Sys.Audit**: Read system and node information

The built-in **PVEAuditor** role provides all necessary permissions for read-only access.

### SSL Configuration

By default, SSL certificates are verified. To disable SSL verification (not recommended for production):

```bash
cartography --proxmox-host proxmox.example.com \
    --proxmox-verify-ssl false \
    ...other options...
```

### Advanced Options

**Custom Port:**
```bash
cartography --proxmox-port 8007 \
    ...other options...
```

**Custom User:**
```bash
cartography --proxmox-user admin@pve \
    ...other options...
```

### Syncing Multiple Clusters

To sync multiple Proxmox clusters, run Cartography separately for each cluster:

```bash
# Cluster 1
cartography --proxmox-host proxmox-prod.example.com ...

# Cluster 2
cartography --proxmox-host proxmox-dev.example.com ...
```

Each cluster will be represented as a separate `ProxmoxCluster` node in the graph.

### Troubleshooting

**Connection Issues:**
- Verify the Proxmox host is reachable
- Check that port 8006 (default) is accessible
- Ensure firewall rules allow access
- Try with `--proxmox-verify-ssl false` to rule out SSL issues

**Authentication Errors:**
- Verify the API token or password is correct
- Check that the token hasn't expired
- Ensure the user has the required permissions
- Verify the user format is correct (e.g., `root@pam`, not just `root`)

**Permission Errors:**
- Ensure the user/token has the `PVEAuditor` role or equivalent
- Check ACL permissions on the `/` path
- Verify permissions using: `pveum user permissions <user>`
