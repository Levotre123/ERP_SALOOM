# Architecture — Multi-Activity SaaS (Odoo 18)

## Product

A commercial multi-tenant platform for owners who run one or more establishments
(salon, barber, restaurant, bar, café, snack, future verticals).

```text
SAAS PLATFORM
    ├── Plans / Features / Subscriptions
    └── Tenants (res.company)
            └── Establishments
                    ├── POS / Cash / Stock / Expenses
                    ├── Customers / Employees
                    └── Verticals (Salon now; Restaurant/Bar next)
```

## Technical foundation

| Layer | Choice |
| --- | --- |
| ERP | Odoo 18 Community (`odoo:18.0`) |
| Database | PostgreSQL 16 (external on Render) |
| Filestore | `/var/lib/odoo` persistent disk |
| Custom code | `addons/` → `/mnt/extra-addons` |
| Core | Never patched |

## Addon map

| Module | Role |
| --- | --- |
| `multi_activity_core` | Establishment, business types, user scope, mixins |
| `multi_activity_saas` | Tenant, plan, feature, subscription, tickets, provisioning |
| `multi_activity_security` | Groups, record rules, entitlement checks |
| `multi_activity_operations` | Cash close extras, expenses, audit, POS/product hooks |
| `multi_activity_dashboard` | Owner dashboard and KPIs |
| `multi_activity_salon` | Appointments, commissions (first vertical) |
| `multi_activity_restaurant` | Tables, kitchen states, order workflow |
| `multi_activity_bar` | Drink UoM / dose / bottle conversion |
| `multi_activity` | Bundle to install the MVP set |

Odoo already owns: `res.partner`, `product.*`, `pos.order`, `pos.session`,
`stock.*`, `purchase.order`, `hr.employee`, `account.move`. Custom addons
**extend** those models; they do not replace them.

## Request path

```text
User
  → Odoo ACL (ir.model.access)
  → Groups (role)
  → Record rules (company + establishment)
  → Entitlement service (plan limits / features)
  → ORM
```

Menus are filtered for UX. They are **not** the security boundary.

## Estimated profit (dashboard)

```text
Estimated profit = POS revenue (paid orders, tax-included or configured)
                 − operational expenses in state posted
```

Cash collected (session payments) is shown separately from revenue.
These three figures are never treated as interchangeable.
