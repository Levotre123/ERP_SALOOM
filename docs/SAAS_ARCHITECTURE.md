# SaaS tenancy decision

## Options evaluated

| | Option A — one DB, company per tenant | Option B — DB per tenant + control plane |
| --- | --- | --- |
| Isolation | Strong if record rules are complete; residual risk (bugs, sudo, reports) | Strongest (separate catalogs, attachments, users) |
| Upgrades | One registry, one `-u` | N databases to migrate |
| Backups | One dump + one filestore | Per-tenant dump + filestore pairs |
| Provisioning | Create company, user, establishment | Create DB, install modules, filestore dir |
| Billing | Control-plane models in same DB | Same models in a platform DB |
| This Render stack | Fits one web service + one Postgres | Needs a provisioner service and many DBs |

## Decision (MVP and current production)

**Option A with an explicit control-plane data model.**

Each SaaS customer is a `multi.activity.tenant` bound to one `res.company`.
Establishments live under that company. Record rules enforce company and
establishment scope. Platform administrators manage tenants/plans and do
**not** receive operational ACL on POS/stock/expenses.

This is **not** “Odoo multi-company equals SaaS”. Isolation is a custom
security layer on top of `company_id`.

## Why not Option B yet

The live deployment is a single Odoo 18 container and one Render PostgreSQL.
Database-per-tenant cannot be provisioned safely there without a second
control-plane service, per-tenant databases, and per-tenant filestore
volumes. The models (`tenant`, `plan`, `subscription`, provisioning log)
are shaped so a later provisioner can create a real database and point
`tenant.database_name` at it.

## Lifecycle

```text
signup → trial → active → past_due → grace → suspended → cancelled
```

Expired payment **never** drops the database. Suspension blocks login /
operations; data stays until a documented retention job (not automatic
destroy).

## Provisioning (same DB)

```text
Create tenant
  → create res.company (currency, name)
  → create owner user (company scoped)
  → create first establishment (+ warehouse when stock is installed)
  → apply plan features
  → log result (retryable, idempotent)
```

Tenant users never receive PostgreSQL credentials.
