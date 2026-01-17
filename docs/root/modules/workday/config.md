## Workday Configuration

### Prerequisites

- Access to a Workday RaaS (Report as a Service) API endpoint with employee directory data
- API credentials (username and password) with read access to employee data

### Required API Response Format

The Workday API endpoint should return JSON with the following structure:

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

### Required Fields

| Field Name | Description |
|------------|-------------|
| `Employee_ID` | Unique employee identifier |
| `Name` | Employee full name |
| `Email_-_Work` | Work email address |
| `Supervisory_Organization` | Organization/department name |
| `Worker_s_Manager_group` | Array of manager IDs for REPORTS_TO relationships |

Optional fields (businessTitle, Worker_Type, location, Cost_Center, etc.) are documented in [schema.md](schema.md).

### Configuration

1. Set your Workday password in an environment variable:
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

| Parameter | CLI Argument | Required | Description |
|-----------|-------------|----------|-------------|
| Workday API URL | `--workday-api-url` | Yes | The Workday API endpoint URL |
| Workday API Login | `--workday-api-login` | Yes | Username for API authentication |
| Workday API Password | `--workday-api-password-env-var` | Yes | Name of environment variable containing the API password |

### Security Considerations

- **Credentials**: Use environment variables only, never command-line arguments
- **HTTPS**: Ensure the Workday API URL uses HTTPS
- **PII**: Employee data contains personally identifiable information - secure your Neo4j database with authentication and encryption
- **Least Privilege**: Request read-only API access

### Troubleshooting

**HTTP 401 Unauthorized:**
- Verify credentials are correct and the password environment variable is set

**HTTP 404 Not Found:**
- Verify the Workday API URL is correct and the report endpoint exists

**Empty Response:**
- Check that the Workday report returns data and the format is JSON (not XML)

**Missing Fields:**
- Work with Workday admin to ensure the report includes required fields (see schema.md)
