### Alembic documentation
https://alembic.sqlalchemy.org/en/latest/

### Cookbook
https://alembic.sqlalchemy.org/en/latest/cookbook.html#rudimental-schema-level-multi-tenancy-for-postgresql-databases

Notes:
- we set `DB_URL` in `.env` file and rewrite it in `alembic/env.py` file (`alembic.ini` file is not used of security reasons)
