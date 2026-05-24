# Operon — Django SaaS Starter

A modern Django SaaS application scaffold with multi-tenant support, subdomain-based tenant routing, and per-tenant admin dashboards.

## Prerequisites

- Python 3.10+
- PostgreSQL 14+
- pip or pipenv

## Environment Setup

### 1. Clone and Create Virtual Environment

```bash
git clone <repo-url>
cd operon
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements/dev.txt

pre-commit install
```

### 3. Configure Environment Variables

Create a `.env` file in the project root:

### 4. Initialize Database

Create the PostgreSQL database:

```bash
createdb operon_db
```

Run shared migrations (creates shared schema):

```bash
python manage.py migrate_schemas --shared
```

### 5. Creating Public Tenant

```bash
python manage.py shell
```

```python
from tenants.models import Tenant, Domain

# Create tenant
tenant = Tenant.objects.create(
    schema_name='public',
    name='Website',
    subdomain='',
    is_active=True
)

# Create domain mapping
Domain.objects.create(
    domain='localhost',
    tenant=tenant,
    is_primary=True
)
```

### 6. Start Development Server

```bash
python manage.py runserver
```

Access the application:

- **Public Portal**: http://localhost:8000

### Database Migrations

For shared schema:

```bash
python manage.py makemigrations
python manage.py migrate_schemas --shared
```

### Load Data

```bash
python manage.py all_tenants_command loaddata order_status.json
python manage.py all_tenants_command loaddata payment_methods.json
```
