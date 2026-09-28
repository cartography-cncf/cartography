# GET /v1/projects/{ref}/advisors/security
SUPABASE_SECURITY_ADVISORS = {
    "lints": [
        {
            "name": "rls_disabled_in_public",
            "title": "RLS Disabled in Public",
            "level": "ERROR",
            "facing": "EXTERNAL",
            "categories": ["SECURITY"],
            "description": "Detects tables in the public schema with row level security disabled.",
            "detail": "Table `public.reactor_readings` is public, but RLS has not been enabled.",
            "remediation": "https://supabase.com/docs/guides/database/database-linter?lint=0013_rls_disabled_in_public",
            "metadata": {
                "schema": "public",
                "name": "reactor_readings",
                "entity": "public.reactor_readings",
                "type": "table",
            },
            "cache_key": "rls_disabled_in_public_public_reactor_readings",
        },
        {
            "name": "security_definer_view",
            "title": "Security Definer View",
            "level": "WARN",
            "facing": "EXTERNAL",
            "categories": ["SECURITY"],
            "description": "Detects views defined with the SECURITY DEFINER property.",
            "detail": "View `public.employee_summary` is defined with the SECURITY DEFINER property.",
            "remediation": "https://supabase.com/docs/guides/database/database-linter?lint=0010_security_definer_view",
            "metadata": {
                "schema": "public",
                "name": "employee_summary",
                "entity": "public.employee_summary",
                "type": "view",
            },
            "cache_key": "security_definer_view_public_employee_summary",
        },
    ],
}
