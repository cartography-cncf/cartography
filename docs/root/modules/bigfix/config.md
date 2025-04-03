## BigFix Configuration

Follow these steps to analyze BigFix objects with Cartography.
1. Prepare a read-only BigFix username and password.
1. Polulate environ;ent variable as defined below.

### Cartography Configuration

| Name | Type     | Description |
|------|----------|-------------|
| CARTOGRAPHY_BIGFIX__USERNAME | `str` | The BigFix username for authentication. |
| CARTOGRAPHY_BIGFIX__PASSWORD | `str` | The name of environment variable containing the BigFix password for authentication. |
| CARTOGRAPHY_BIGFIX__ROOT_URL | `str` | The BigFix Root URL, a.k.a the BigFix API URL |