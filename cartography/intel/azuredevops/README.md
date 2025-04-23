# Azure DevOps API Client

A Python client library for interacting with the Azure DevOps REST API. This library provides a simple and intuitive interface for working with Azure DevOps resources such as projects, repositories, service hooks, and extensions.

## Features

- **Projects Management**: List and retrieve project information
- **Repositories Management**: List and retrieve repository information
- **Service Hooks Management**: Create, list, and delete service hook subscriptions
- **Extensions Management**: List and manage installed extensions
- **JSON Serialization**: Automatic conversion of Azure DevOps API objects to JSON-serializable dictionaries

## Installation

### Prerequisites

- Python 3.6 or higher
- Azure DevOps Personal Access Token (PAT) with appropriate permissions

### Required PAT Permissions

Your Personal Access Token needs the following permissions:

- **Code**: Read & Write
- **Extensions**: Read & Manage
- **Project and Team**: Read
- **Service Hooks**: Read, Write & Manage

### Dependencies

Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage Examples

### Authentication

```python
from AzureDevOpsAuth import AzureDevOpsAuth
from AzureDevOpsClient import AzureDevOpsClient
from AzureInventory import AzureInventory

# Using Personal Access Token (PAT)
token = "your-personal-access-token"
organization_url = "https://dev.azure.com/your-organization"

# Initialize the inventory manager (recommended approach)
inventory = AzureInventory(token, organization_url)

# Or initialize the client directly
credentials = AzureDevOpsAuth.get_pat_credentials(token)
client = AzureDevOpsClient(organization_url, credentials)
```

### Working with Projects

```python
# Get all projects
projects = inventory.get_projects()
print(json.dumps(projects, indent=4))

# Example output:
# [
#     {
#         "id": "project-id-1",
#         "name": "Project Name",
#         "description": "Project Description",
#         "url": "https://dev.azure.com/organization/project",
#         "state": "wellFormed"
#     },
#     ...
# ]
```

### Working with Repositories

```python
# Get all repositories for a specific project
repositories = inventory.get_repositories("ProjectName")
print(json.dumps(repositories, indent=4))

# Get all repositories across all projects
all_repos = inventory.get_all_project_repositories()
print(json.dumps(all_repos, indent=4))

# Example output:
# [
#     {
#         "id": "repo-id-1",
#         "name": "Repository Name",
#         "url": "https://dev.azure.com/organization/project/_git/repo",
#         "default_branch": "refs/heads/main",
#         "size": 12345,
#         "remote_url": "https://dev.azure.com/organization/project/_git/repo",
#         "ssh_url": "git@ssh.dev.azure.com:v3/organization/project/repo",
#         "web_url": "https://dev.azure.com/organization/project/_git/repo"
#     },
#     ...
# ]
```

### Working with Service Hooks

```python
# Get all service hooks
service_hooks = inventory.get_service_hooks()
print(json.dumps(service_hooks, indent=4))

# Get service hooks for a specific consumer
consumer_hooks = inventory.get_service_hooks(consumer_id="Adler.cloudanix-code-webhook.consumer")
print(json.dumps(consumer_hooks, indent=4))

# Create service hooks for all projects
# This will create pull request and git push hooks for all projects
success = inventory.create_service_hook()
print(f"Service hooks created: {success}")

# Note: The current implementation creates predefined hooks for all projects
# with the Cloudanix webhook consumer

# Delete a service hook
success = inventory.delete_service_hook("subscription-id")
print(f"Service hook deleted: {success}")
```

### Working with Extensions

```python
# Get all installed extensions
extensions = inventory.get_extensions()
print(json.dumps(extensions, indent=4))

# Install an extension
success = inventory.install_extension("Adler.cloudanix-image-scanner")
print(f"Extension installed: {success}")

# Uninstall an extension
success = inventory.uninstall_extension("Adler.cloudanix-image-scanner")
print(f"Extension uninstalled: {success}")

# Example output of get_extensions():
# [
#     {
#         "extensionId": "extension-id",
#         "extensionName": "Extension Name",
#         "publisherName": "Publisher Name",
#         "version": "1.0.0",
#         "flags": "none"
#     },
#     ...
# ]
```

## Using the AzureDevOpsClient Directly

If you need more control, you can use the AzureDevOpsClient class directly:

```python
from AzureDevOpsAuth import AzureDevOpsAuth
from AzureDevOpsClient import AzureDevOpsClient
import json

# Authentication
token = "your-personal-access-token"
organization_url = "https://dev.azure.com/your-organization"
credentials = AzureDevOpsAuth.get_pat_credentials(token)

# Initialize the client
client = AzureDevOpsClient(organization_url, credentials)

# Get projects
projects = client.get_projects()

# Get repositories for a project
repositories = client.get_repositories("ProjectName")

# Get service hooks (optionally filtered by consumer_id)
service_hooks = client.get_service_hooks(consumer_id="Adler.cloudanix-code-webhook.consumer")

# Get service hook publishers
publishers = client.get_service_hook_publishers()

# Get service hook consumers
consumers = client.get_service_hook_consumers()

# Get branches for a repository
branches = client.get_branches("ProjectName", "RepositoryName")

# Get installed extensions
extensions = client.get_installed_extensions()

# Create a service hook
hook_definition = {
    "consumerId": "webHooks",
    "consumerActionId": "httpRequest",
    "consumerInputs": {
        "url": "https://example.com/webhook"
    },
    "eventType": "git.push",
    "publisherId": "tfs",
    "publisherInputs": {
        "projectId": "ProjectId",
        "repository": "RepositoryName"
    }
}
created_hook = client.create_service_hook(hook_definition)

# Delete a service hook
success = client.delete_service_hook("subscription-id")
```

## Using the AzureDevOpsExtensions Class

For working specifically with extensions:

```python
from AzureDevOpsExtensions import AzureDevOpsExtensions
import json

# Initialize the extensions manager
token = "your-personal-access-token"
organization_url = "https://dev.azure.com/your-organization"
extensions_manager = AzureDevOpsExtensions(organization_url, token)

# List installed extensions with formatted output
installed_extensions = extensions_manager.list_installed_extensions(format_output=True)
print(json.dumps(installed_extensions, indent=4))

# Install an extension
success = extensions_manager.install_extension("Microsoft.Azure-Repos-Git")
print(f"Extension installed: {success}")

# Uninstall an extension
success = extensions_manager.uninstall_extension("Microsoft.Azure-Repos-Git")
print(f"Extension uninstalled: {success}")
```

## Error Handling

The library includes robust error handling to ensure that API errors don't crash your application:

```python
try:
    # Try to get projects
    projects = inventory.get_projects()

    # Process projects
    for project in projects:
        print(f"Project: {project['name']}")
except Exception as e:
    print(f"Error: {str(e)}")
```

## JSON Serialization

The library automatically handles JSON serialization of Azure DevOps API objects:

```python
import json
from AzureInventory import AzureInventory

inventory = AzureInventory(token, organization_url)

# Get service hooks
service_hooks = inventory.get_service_hooks()

# Serialize to JSON
json_str = json.dumps(service_hooks, indent=4)
print(json_str)

# Or use the built-in serialization method with the custom AzureDevOpsEncoder
# This is especially useful for complex Azure DevOps API objects that aren't directly serializable
json_str = inventory.to_json(service_hooks)
print(json_str)
```

## Command Line Usage

The tool can be used directly from the command line using the `main.py` script. Here are some examples:

### Basic Usage

```bash
# Set your PAT as an environment variable (recommended)
export AZURE_DEVOPS_PAT="your-personal-access-token"

# Or provide it directly in the command (less secure)
python main.py --pat "your-personal-access-token" --organization "https://dev.azure.com/your-organization"
```

### Listing Resources

```bash
# List all projects (default action)
python main.py -o "https://dev.azure.com/your-organization" -t "your-pat"

# List all projects explicitly
python main.py -o "https://dev.azure.com/your-organization" -t "your-pat" --list-projects

# List all repositories across all projects
python main.py -o "https://dev.azure.com/your-organization" -t "your-pat" --list-repositories

# List all extensions
python main.py -o "https://dev.azure.com/your-organization" -t "your-pat" --list-extensions

# List all service hooks for a specific consumer
python main.py -o "https://dev.azure.com/your-organization" -t "your-pat" --list-service-hooks "Adler.cloudanix-code-webhook.consumer"
```

### Managing Service Hooks

```bash
# Create a service hook (using the default configuration in AzureInventory.py)
python main.py -o "https://dev.azure.com/your-organization" -t "your-pat" --create-service-hook

# Delete a service hook by ID
python main.py -o "https://dev.azure.com/your-organization" -t "your-pat" --delete-service-hook "307a2a08-768b-40b3-b792-0ffbf97bb7a3"
```

### Managing Extensions

```bash
# Install an extension
python main.py -o "https://dev.azure.com/your-organization" -t "your-pat" --install-extension "Adler.cloudanix-image-scanner"

# Uninstall an extension
python main.py -o "https://dev.azure.com/your-organization" -t "your-pat" --uninstall-extension "Adler.cloudanix-image-scanner"
```

### Command Line Options

```
usage: main.py [-h] [--pat PAT] [--organization ORGANIZATION] [--list-projects]
               [--list-repositories] [--list-extensions]
               [--list-service-hooks LIST_SERVICE_HOOKS]
               [--delete-service-hook DELETE_SERVICE_HOOK] [--create-service-hook]
               [--install-extension INSTALL_EXTENSION]
               [--uninstall-extension UNINSTALL_EXTENSION]

Azure DevOps Inventory Tool

options:
  -h, --help            show this help message and exit
  --organization ORGANIZATION, -o ORGANIZATION
                        Azure DevOps Organization URL
  --list-projects, -p   List all projects
  --list-repositories, -r
                        List all repositories
  --list-extensions, -e
                        List all extensions
  --list-service-hooks LIST_SERVICE_HOOKS, -s LIST_SERVICE_HOOKS
                        List all service hooks for a specific consumer
  --delete-service-hook DELETE_SERVICE_HOOK, -d DELETE_SERVICE_HOOK
                        Delete a service hook
  --create-service-hook, -c
                        Create a service hook using the default configuration
  --install-extension INSTALL_EXTENSION, -i INSTALL_EXTENSION
                        Install an extension
  --uninstall-extension UNINSTALL_EXTENSION, -u UNINSTALL_EXTENSION
                        Uninstall an extension

Authentication:
  --pat PAT, -t PAT     Azure DevOps Personal Access Token
```

## Project Structure

The project is organized into several modules, each with a specific responsibility:

- **AzureDevOpsAuth.py**: Handles authentication with Azure DevOps using PAT or OAuth
- **AzureDevOpsClient.py**: Low-level client for interacting with the Azure DevOps API
- **AzureInventory.py**: High-level interface for working with Azure DevOps resources
- **main.py**: Command-line interface for the tool

### Class Hierarchy

```
AzureDevOpsAuth
└── Authentication methods (PAT, OAuth)

AzureDevOpsClient
├── Projects management
├── Repositories management
├── Service hooks management
├── Extensions management
└── Branches management

AzureInventory
├── Uses AzureDevOpsClient
└── Provides high-level methods with JSON serialization
```


