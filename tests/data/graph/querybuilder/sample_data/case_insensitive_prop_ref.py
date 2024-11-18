FAKE_GITHUB_USER_DATA = [
    {
        'hasTwoFactorEnabled': None,
        'node': {
            'url': 'https://example.com/hjsimpson',
            'login': 'HjsimPson',  # Upper and lowercase
            'name': 'Homer Simpson',
            'isSiteAdmin': False,
            'email': 'hjsimpson@example.com',
            'company': 'Springfield Nuclear Power Plant',
        },
        'role': 'MEMBER',
    }, {
        'hasTwoFactorEnabled': None,
        'node': {
            'url': 'https://example.com/mbsimpson',
            'login': 'mbsimp-son',  # All lowercase
            'name': 'Marge Simpson',
            'isSiteAdmin': False,
            'email': 'mbsimpson@example.com',
            'company': 'Simpson Residence',
        },
        'role': 'ADMIN',
    },
]

FAKE_GITHUB_ORG_DATA = {
    'url': 'https://example.com/my_org',
    'login': 'my_org',
}

FAKE_EMPLOYEE_DATA = [
    {
        'id': 123,
        'email': 'hjsimpson@example.com',
        'first_name': 'Homer',
        'last_name': 'Simpson',
        'name': 'Homer Simpson',
        'github_username': 'hjsimpson',  # pure lowercase
    },
    {
        'id': 456,
        'email': 'mbsimpson@example.com',
        'first_name': 'Marge',
        'last_name': 'Simpson',
        'github_username': 'mbsimp-son',  # pure lowercase
    },
]

FAKE_EMPLOYEE2_DATA = [
    {
        'id': 123,
        'email': 'hjsimpson@example.com',
        'first_name': 'Homer',
        'last_name': 'Simpson',
        'name': 'Homer Simpson',
        'github_username': 'jsimpso',  # substring
    },
    {
        'id': 456,
        'email': 'mbsimpson@example.com',
        'first_name': 'Marge',
        'last_name': 'Simpson',
        'github_username': 'mbsimp',  # substring
    },
]
