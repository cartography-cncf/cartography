## Workday Configuration

Follow these steps to configure Cartography to sync employee and organization data from Workday.

### Prerequisites

1. Access to a Workday API endpoint
2. Workday API credentials (username and password)
3. Appropriate permissions to access the Workday directory/employee API

### Workday API Access

The Workday module uses HTTP Basic Authentication to access a Workday API endpoint that returns employee directory data. Your Workday administrator will need to:

1. Configure a Workday RaaS (Report as a Service) report or custom API endpoint
2. Ensure the report includes the required fields (see below)
3. Provide API credentials with read access to employee data

### Required API Response Format

The Workday API endpoint should return JSON with the following structure:

```json
{
  "Report_Entry": [
    {
      "Employee_ID": "emp001",
      "Name": "Alice Johnson",
      "businessTitle": "Software Engineer",
      "Worker_Type": "Employee",
      "location": "San Francisco Office",
      "Location_Address_-_Country": "United States",
      "Email_-_Work": "alice.johnson@example.com",
      "Cost_Center": "Engineering",
      "GBL-Custom-Function": "Product Development",
      "Sub-Function": "Backend Engineering",
      "Team": "Core Platform",
      "Sub_Team": "API Team",
      "Company": "Example Corp",
      "Supervisory_Organization": "Engineering Department",
      "Worker_s_Manager_group": [
        {"Manager_ID": "emp003"}
      ]
    }
  ]
}
```

### Required Fields

The following fields must be present in the Workday API response:

| Field Name | Description | Used For |
|------------|-------------|----------|
| `Employee_ID` | Unique employee identifier | Node ID, relationships |
| `Name` | Employee full name | Display name |
| `Email_-_Work` | Work email address | Email property, potential cross-module relationships |
| `Supervisory_Organization` | Organization/department name | Organization nodes and MEMBER_OF_ORGANIZATION relationships |
| `Worker_s_Manager_group` | Array of manager IDs | REPORTS_TO relationships |

### Optional Fields

Additional fields enhance the data model but are not required:

- `businessTitle` - Job title
- `Worker_Type` - Employee, Contractor, etc.
- `location` - Office location
- `Location_Address_-_Country` - Country
- `Cost_Center` - Cost center code
- `GBL-Custom-Function` - Functional area
- `Sub-Function` - Sub-functional area
- `Team` - Team name
- `Sub_Team` - Sub-team name
- `Company` - Company/entity name

### Configuration

1. Set your Workday credentials in environment variables:
   ```bash
   export WORKDAY_PASSWORD="your-password-here"
   ```

2. Run Cartography with Workday module:
   ```bash
   cartography \
     --neo4j-uri bolt://localhost:7687 \
     --selected-modules workday \
     --workday-api-url "https://wd5-services.myworkday.com/ccx/service/customreport2/company/report/directory" \
     --workday-api-login "api_user@company" \
     --workday-api-password-env-var "WORKDAY_PASSWORD"
   ```

### Configuration Options

| Parameter | CLI Argument | Environment Variable | Required | Description |
|-----------|-------------|---------------------|----------|-------------|
| Workday API URL | `--workday-api-url` | N/A | Yes | The Workday API endpoint URL |
| Workday API Login | `--workday-api-login` | N/A | Yes | Username for API authentication |
| Workday API Password | `--workday-api-password-env-var` | Set by you | Yes | Name of the environment variable containing the API password |

### Security Considerations

- **Passwords**: Never pass passwords directly on the command line. Always use environment variables
- **HTTPS**: Ensure the Workday API URL uses HTTPS (not HTTP)
- **Least Privilege**: Request API credentials with read-only access to employee data
- **PII**: Employee data includes personally identifiable information (names, emails). Secure your Neo4j database appropriately

### Performance

- **API timeout**: Requests timeout after 60 seconds (connect) + 60 seconds (read)
- **Single request**: The module makes one API call to fetch all employee data
- **Expected sync time**: Typically completes in under 1 minute for most organizations

### Troubleshooting

**HTTP 401 Unauthorized:**
- Verify credentials are correct
- Check that the API user has permission to access the report
- Ensure the password environment variable is set correctly

**HTTP 404 Not Found:**
- Verify the Workday API URL is correct
- Check that the report endpoint exists and is published

**Empty Response:**
- Verify the Workday report returns data when accessed directly
- Check report filters (may be filtering out all employees)
- Ensure the report format is JSON (not XML)

**Missing Fields:**
- The module logs warnings for employees missing required fields
- Sync continues but affected employees may have incomplete data
- Work with Workday admin to ensure report includes all required fields

### Example Configuration

```bash
# Set password in environment
export WORKDAY_PASSWORD="mySecurePassword123"

# Run sync
cartography \
  --neo4j-uri bolt://localhost:7687 \
  --selected-modules workday \
  --workday-api-url "https://wd5-services.myworkday.com/ccx/service/customreport2/company/report/employee_directory" \
  --workday-api-login "integrations@company" \
  --workday-api-password-env-var "WORKDAY_PASSWORD"
```
