## Tenant Management

### Creating Tenants

```bash
python manage.py shell
```

```python
from tenants.models import Tenant, Domain

# Create tenant
tenant = Tenant.objects.create(
    schema_name='client1',
    name='Client One',
    subdomain='client1',
    is_active=True
)

# Create domain mapping
Domain.objects.create(
    domain='client1.localhost',
    tenant=tenant,
    is_primary=True
)
```

### Creating Tenant Users

```bash
python manage.py create_tenant_user <schema_name> <username> <password> [--is_staff] [--is_superuser]
```

Examples:

```bash
# Regular tenant user
python manage.py create_tenant_user client1 john password123

# Tenant admin
python manage.py create_tenant_user client1 admin admin123 --is_staff --is_superuser
```

### Accessing Tenant Admin

Once a tenant is created with a user, visit:

- **Tenant Admin**: http://client1.localhost:8000/admin
- **Tenant Dashboard**: http://client1.localhost:8000

### Schema doesn't exist

Run migrations for the specific tenant:

```bash
python manage.py migrate_schemas --schema=client1
```
