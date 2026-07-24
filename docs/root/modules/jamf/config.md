## Jamf Configuration

Follow these steps to analyze Jamf objects with Cartography.

1. Prepare a read-only Jamf username and password.
1. Pass the Jamf base URI (e.g. `https://hostname.jamfcloud.com`) to the `--jamf-base-uri` CLI arg.
1. Pass the Jamf username to the `--jamf-user` CLI arg.
1. Populate an environment variable with the password.
1. Pass that env var name to the `--jamf-password-env-var` CLI arg.
