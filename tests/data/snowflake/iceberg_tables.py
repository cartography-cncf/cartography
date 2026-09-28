"""Raw Snowflake Iceberg table payloads.

Shaped as `GET /api/v2/databases/{db}/schemas/{schema}/iceberg-tables` returns them. The
payload does not repeat its database and schema, so `get()` groups each listing under
the parent it was fetched for; `SNOWFLAKE_ICEBERG_TABLE_LISTINGS` is that shape.
"""

from typing import Any

SNOWFLAKE_ICEBERG_TABLES: list[dict[str, Any]] = [
    # Snowflake-managed: it is its own catalog, so there is no catalog integration
    # to point at.
    {
        "name": "RADIATION_SAMPLES",
        "external_volume": "MONORAIL_VOLUME",
        "catalog": "SNOWFLAKE",
        "catalog_sync": "",
        "catalog_table_name": None,
        "catalog_namespace": None,
        "base_location": "springfield/nuclear_plant/radiation_samples/",
        "iceberg_table_type": "MANAGED",
        "storage_serialization_policy": "OPTIMIZED",
        "can_write_metadata": True,
        "owner": "PLANT_ENGINEER",
        "created_on": "2026-08-03T16:10:00.000+00:00",
    },
    # Read from a table an external catalog owns, so Snowflake only reads metadata.
    {
        "name": "INSPECTION_ARCHIVE",
        "external_volume": "MONORAIL_VOLUME",
        "catalog": "GLUE_CATALOG",
        "catalog_sync": "",
        "catalog_table_name": "inspection_archive",
        "catalog_namespace": "springfield",
        "base_location": "springfield/archive/",
        "iceberg_table_type": "UNMANAGED",
        "storage_serialization_policy": "COMPATIBLE",
        "can_write_metadata": False,
        "owner": "SAFETY_INSPECTOR",
        "created_on": "2026-08-03T16:11:00.000+00:00",
    },
]

SNOWFLAKE_ICEBERG_TABLE_LISTINGS: list[dict[str, Any]] = [
    {
        "database_name": "SPRINGFIELD",
        "schema_name": "NUCLEAR_PLANT",
        "iceberg_tables": SNOWFLAKE_ICEBERG_TABLES,
    },
]
