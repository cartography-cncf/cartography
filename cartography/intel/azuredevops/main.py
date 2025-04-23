import argparse
import os
import sys
import json
# from AzureDevOpsAuth import AzureDevOpsAuth
# from AzureDevOpsClient import AzureDevOpsClient
from AzureInventory import AzureInventory

def parse_arguments():
    """
    Parse command-line arguments

    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(description='Azure DevOps Inventory Tool')

    # Authentication group
    auth_group = parser.add_argument_group('Authentication')
    auth_type = auth_group.add_mutually_exclusive_group()
    auth_type.add_argument('--pat', '-t', help='Azure DevOps Personal Access Token')


    # Other arguments
    parser.add_argument('--organization', '-o', help='Azure DevOps Organization URL')
    parser.add_argument('--list-projects', '-p', action='store_true', help='List all projects')
    parser.add_argument('--list-repositories', '-r', action='store_true', help='List all repositories')
    parser.add_argument('--list-extensions', '-e', action='store_true', help='List all extensions')
    parser.add_argument('--list-service-hooks', '-s', help='List all service hooks for a consumer "Adler.cloudanix-code-webhook.consumer" ')
    parser.add_argument('--delete-service-hook', '-d', help='Delete a service hook')
    parser.add_argument('--create-service-hook', '-c',action='store_true', help='Create a Cloudanix service hooks for all project')
    parser.add_argument('--install-extension', '-i', help='Install an extensions')
    parser.add_argument('--uninstall-extension', '-u', help='Uninstall an extensions')

    return parser.parse_args()

def main():
    """
    Main function for the Azure DevOps Inventory Tool.

    This function parses command-line arguments, initializes the AzureInventory object,
    and performs the requested operation based on the provided arguments.

    Operations include:
    - Listing projects
    - Listing repositories
    - Listing extensions
    - Listing service hooks
    - Creating service hooks
    - Deleting service hooks
    - Installing extensions
    - Uninstalling extensions
    """
    args = parse_arguments()

    # Check if token is provided via argument or environment variable
    token = args.pat or os.environ.get('AZURE_DEVOPS_PAT')
    if not token:
        print("Error: Azure DevOps Personal Access Token is required for PAT authentication.")
        print("Provide it using --pat argument or set AZURE_DEVOPS_PAT environment variable.")
        sys.exit(1)

    if not args.organization:
        print("Error: Azure DevOps Organization URL is required.")
        sys.exit(1)

    # Get authentication credentials based on the chosen authentication type
    # credentials = AzureDevOpsAuth.get_pat_credentials(token)
    # client = AzureDevOpsClient(args.organization, credentials)
    #

    inventory = AzureInventory(token, args.organization)

    # Determine what to list based on command-line arguments
    if args.list_extensions:
        result = inventory.get_extensions()
        print("\nListing all extensions:")
    elif args.list_service_hooks:
        result = inventory.get_service_hooks(args.list_service_hooks)
        print("\nListing all service hooks:")
    elif args.delete_service_hook:
        result = inventory.delete_service_hook(args.delete_service_hook)
        print(f"\nDeleting service hook: {args.delete_service_hook}")
    elif args.create_service_hook:
        result = inventory.create_service_hook()
        print(f"\nCreating service hook: ")
    elif args.install_extension:
        result = inventory.install_extension(args.install_extension)
        print(f"\nInstalling extension: {args.install_extension}")
    elif args.uninstall_extension:
        result = inventory.uninstall_extension(args.uninstall_extension)
        print(f"\nUninstalling extension: {args.uninstall_extension}")
    elif args.list_repositories:
        result = inventory.get_all_project_repositories()
        print("\nListing all repositories:")
    elif args.list_projects:
        result = inventory.get_projects()
        print("\nListing all projects:")
    else:
        # Default to listing projects if no specific option is provided
        result = inventory.get_projects()
        print("\nListing all projects (default):")

    # Print the result as formatted JSON
    print(json.dumps(result, indent=4))


if __name__ == "__main__":
    main()