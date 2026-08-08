# Workday Configuration

## Prerequisites

- Access to a Workday RaaS (Report as a Service) API endpoint that returns
  employee directory data as JSON.

## Authentication

Use a Workday API username and password. Store the password in an environment
variable, not in a command-line argument.

## Required Permissions

The API credentials need read access to the employee data exposed by the RaaS
report. Request read-only access.

## Configure Cartography

Set the following options:

| Parameter | CLI argument | Description |
|-----------|--------------|-------------|
| Workday API URL | `--workday-api-url` | The Workday RaaS endpoint URL |
| Workday API login | `--workday-api-login` | Username for API authentication |
| Workday API password | `--workday-api-password-env-var` | Name of the environment variable containing the API password |

Use HTTPS for the Workday API URL.

## Run Cartography

```bash
export WORKDAY_PASSWORD="your-password-here"

cartography \
  --neo4j-uri bolt://localhost:7687 \
  --selected-modules workday \
  --workday-api-url "https://wd5-services.myworkday.com/ccx/service/customreport2/company/report/directory" \
  --workday-api-login "api_user@company" \
  --workday-api-password-env-var "WORKDAY_PASSWORD"
```

## Advanced Configuration

### RaaS response format

The Workday API endpoint must return JSON with the following structure:

```json
{
  "Report_Entry": [
    {
      "Employee_ID": "emp001",
      "Name": "Alice Johnson",
      "businessTitle": "Software Engineer",
      "Email_-_Work": "alice.johnson@example.com",
      "Supervisory_Organization": "Engineering Department",
      "Worker_s_Manager_group": [{"Manager_ID": "emp003"}]
    }
  ]
}
```

Required fields are:

| Field name | Description |
|------------|-------------|
| `Employee_ID` | Unique employee identifier |
| `Name` | Employee full name |
| `Email_-_Work` | Work email address |
| `Supervisory_Organization` | Organization/department name |
| `Worker_s_Manager_group` | Array of manager IDs for REPORTS_TO relationships |

Optional fields (businessTitle, Worker_Type, location, Cost_Center, etc.) are documented in [schema.md](schema.md).

## Troubleshooting

**HTTP 401 Unauthorized:**
- Verify credentials are correct and the password environment variable is set

**HTTP 404 Not Found:**
- Verify the Workday API URL is correct and the report endpoint exists

**Empty Response:**
- Check that the Workday report returns data and the format is JSON (not XML)

**Missing Fields:**
- Work with Workday admin to ensure the report includes required fields (see schema.md)
