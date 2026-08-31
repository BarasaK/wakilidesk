# Milestone 0: Project Foundation

## Directory structure

```text
wakilidesk/
├── docker/
├── docs/
├── src/
│   ├── accounts/
│   ├── common/
│   ├── config/
│   └── firms/
├── tests/
├── docker-compose.yml
├── Dockerfile
├── manage.py
├── pyproject.toml
├── pytest.ini
├── .env.example
└── README.md
```

## Done

- Django project skeleton
- Docker development stack
- Custom User model
- Firm, FirmMembership, Role, Permission models
- Tenant membership service functions
- Current firm middleware foundation
- Health endpoint
- Seed command for two firms
- Initial tenant isolation test

## Review before Milestone 1

- Confirm whether role permissions should remain custom tables or map directly onto Django auth permissions.
- Confirm whether first onboarding should enforce email verification in Milestone 1 or allow a development bypass.
- Confirm production object storage target before document upload work starts.
