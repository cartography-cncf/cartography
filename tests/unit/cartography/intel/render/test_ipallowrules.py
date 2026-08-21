from cartography.intel.render.ipallowrules import extract_rows


def test_extract_rows_flattens_ip_allow_list():
    raw = [
        {
            "id": "srv-1",
            "ipAllowList": [
                {"cidrBlock": "0.0.0.0/0", "description": "everywhere"},
                {"cidrBlock": "203.0.113.0/24", "description": "office"},
            ],
        },
    ]

    rows = extract_rows(raw, "service", "tea-1")

    assert {row["id"] for row in rows} == {"srv-1/0.0.0.0/0", "srv-1/203.0.113.0/24"}
    assert all(row["resourceId"] == "srv-1" for row in rows)
    assert all(row["resourceType"] == "RenderService" for row in rows)
    assert all(row["service_id"] == "srv-1" for row in rows)
    assert all(row["ownerId"] == "tea-1" for row in rows)


def test_extract_rows_skips_items_with_no_allow_list():
    raw = [{"id": "srv-1", "ipAllowList": None}, {"id": "srv-2"}]

    assert extract_rows(raw, "service", "tea-1") == []


def test_extract_rows_skips_entries_missing_a_cidr_block():
    raw = [{"id": "srv-1", "ipAllowList": [{"description": "no cidr here"}]}]

    assert extract_rows(raw, "service", "tea-1") == []


def test_extract_rows_skips_items_with_no_id():
    raw = [{"ipAllowList": [{"cidrBlock": "0.0.0.0/0", "description": "everywhere"}]}]

    assert extract_rows(raw, "service", "tea-1") == []
