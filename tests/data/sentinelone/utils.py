# Test data for get_application_id function

# Standard test cases
APPLICATION_ID_TEST_CASES = [
    {
        "name": "Microsoft Office",
        "vendor": "Microsoft",
        "expected": "microsoft:microsoft_office",
    },
    {
        "name": "Google Chrome",
        "vendor": "Google Inc.",
        "expected": "google_inc:google_chrome",
    },
    {
        "name": "Adobe Photoshop",
        "vendor": "Adobe Systems",
        "expected": "adobe_systems:adobe_photoshop",
    },
    {
        "name": "VLC Media Player",
        "vendor": "VideoLAN",
        "expected": "videolan:vlc_media_player",
    },
]

# Edge cases
APPLICATION_ID_EDGE_CASES = [
    {
        "name": "App with Special Characters!@#$%",
        "vendor": "Vendor with Special Characters!@#$%",
        "expected": "vendor_with_special_characters:app_with_special_characters",
    },
    {
        "name": "  App with Leading/Trailing Spaces  ",
        "vendor": "  Vendor with Leading/Trailing Spaces  ",
        "expected": "vendor_with_leadingtrailing_spaces:app_with_leadingtrailing_spaces",
    },
    {
        "name": "Multiple   Spaces   Between   Words",
        "vendor": "Multiple   Spaces   Between   Words",
        "expected": "multiple___spaces___between___words:multiple___spaces___between___words",
    },
    {
        "name": "MiXeD CaSe AppLiCaTiOn",
        "vendor": "MiXeD CaSe VeNdOr",
        "expected": "mixed_case_vendor:mixed_case_application",
    },
    {
        "name": "123 Numeric App 456",
        "vendor": "789 Numeric Vendor 012",
        "expected": "789_numeric_vendor_012:123_numeric_app_456",
    },
    {
        "name": "",
        "vendor": "",
        "expected": ":",
    },
    {
        "name": "Single",
        "vendor": "Single",
        "expected": "single:single",
    },
]
