## GCP Configuration

.. _gcp_config:

Follow these steps to analyze GCP projects with Cartography.

1. Prepare your GCP credential(s).

    1. Create an identity - either a User Account or a Service Account - for Cartography to run as
    1. Ensure that this identity has the following roles (https://cloud.google.com/iam/docs/understanding-roles) attached to it:
        - `roles/iam.securityReviewer`
        - `roles/resourcemanager.organizationViewer`: needed to list/get GCP Organizations
        - `roles/resourcemanager.folderViewer`: needed to list/get GCP Folders
    1. Ensure that the machine you are running Cartography on can authenticate to this identity.
        - **Method 1**: You can do this by setting your `GOOGLE_APPLICATION_CREDENTIALS` environment variable to point to a json file containing your credentials.  As per SecurityCommonSense™️, please ensure that only the user account that runs Cartography has read-access to this sensitive file.
        - **Method 2**: If you are running Cartography on a GCE instance or other GCP service, you can make use of the credential management provided by the default service accounts on these services.  See the [official docs](https://cloud.google.com/docs/authentication/production) on Application Default Credentials for more details.

### Multiple GCP Project Setup

In order for Cartography to be able to pull all assets from all GCP Projects within an Organization, the User/Service Account assigned to Cartography needs to be created at the **Organization** level.
This is because [IAM access control policies applied on the Organization resource apply throughout the hierarchy on all resources in the organization](https://cloud.google.com/resource-manager/docs/cloud-platform-resource-hierarchy#organizations).
