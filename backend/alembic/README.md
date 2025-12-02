# Database Migrations

This directory contains Alembic migrations for the AI Compliance Auditor database schema.

## Running Migrations

To apply all migrations to your database:

```bash
# From the backend directory
alembic upgrade head
```

To rollback the last migration:

```bash
alembic downgrade -1
```

To rollback all migrations:

```bash
alembic downgrade base
```

## Migration Files

The migrations are applied in the following order:

1. **001_initial_organizations_users.py** - Creates organizations and users tables
2. **002_policies_and_chunks.py** - Creates policies and policy_chunks tables
3. **003_compliance_rules.py** - Creates compliance_rules table
4. **004_audit_documents_violations.py** - Creates audit_documents and violations tables

## Database Schema

### Tables Created

- **organizations**: Multi-tenant organization data
- **users**: User authentication with organization association
- **policies**: Policy document metadata
- **policy_chunks**: Chunked policy text for embedding
- **compliance_rules**: Extracted compliance rules from policies
- **audit_documents**: Documents to be audited
- **violations**: Detected compliance violations

### Indexes

All foreign keys have indexes for efficient querying:
- `organization_id` on users, policies, compliance_rules, audit_documents
- `policy_id` on policy_chunks, compliance_rules
- `audit_document_id` on violations
- `severity` on violations
- `email` (unique) on users

## Environment Variables

Ensure the `DATABASE_URL` environment variable is set before running migrations:

```bash
export DATABASE_URL="postgresql://user:password@localhost:5432/compliance_db"
```

Or create a `.env` file in the backend directory with:

```
DATABASE_URL=postgresql://user:password@localhost:5432/compliance_db
```
