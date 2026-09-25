# Security

## Roles → groups

| Role | Group |
| --- | --- |
| Platform Administrator | `multi_activity_security.group_platform_admin` |
| Tenant Owner | `multi_activity_security.group_tenant_owner` |
| Company Administrator | `multi_activity_security.group_company_admin` |
| Manager | `multi_activity_security.group_manager` |
| Cashier | `multi_activity_security.group_cashier` |
| Waiter | `multi_activity_security.group_waiter` |
| Hairdresser / Barber | `multi_activity_security.group_hairdresser` |
| Storekeeper | `multi_activity_security.group_storekeeper` |

## Enforcement layers

1. `ir.model.access.csv` — model CRUD
2. Record rules — `company_id` and `establishment_id`
3. Entitlement service — plan max establishments / users / features
4. Audit log — cancellations, refunds, price changes, cash gaps, stock adjustments

## Isolation

A user of Tenant A cannot read Tenant B sales, partners, expenses,
appointments, or tickets via menu, search, URL, or RPC. Tests in
`multi_activity_security` assert `AccessError`.

Platform admins see tenants/plans/subscriptions/tickets. They do **not**
get POS/stock/expense ACL.

## Hard rules

- No casual `sudo()`
- No trusting establishment IDs from the client without rule checks
- Attachments inherit record rules via `res_id` + linked model
- No hard-delete of POS orders / payments / stock moves
- Tenant users never see SaaS admin menus
