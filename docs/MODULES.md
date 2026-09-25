# Modules and Odoo mapping

## Inspection of this project

- Image: official `odoo:18.0` Community (tested `18.0-20260908`)
- Custom addons before this work: none
- Enterprise addons: not present
- Deploy: Docker + Render Postgres + disk `/var/lib/odoo`

## Community vs Enterprise (relevant)

| App | Community 18 | Enterprise | Decision |
| --- | --- | --- | --- |
| base, mail, bus, contacts | Yes | Yes | Use |
| product, sale | Yes | Yes | Use |
| point_of_sale | Yes | Yes | Extend |
| stock, purchase, account | Yes | Yes | Use |
| hr, hr_attendance, calendar | Yes | Yes | Use |
| website, payment | Yes | Yes | Optional later |
| pos_restaurant, appointment, loyalty, helpdesk, hr_payroll | No / limited | Yes | Custom or Phase 2 |

## Requirement matrix (summary)

| Requirement | Standard Odoo | Custom |
| --- | --- | --- |
| Companies / users / ACL | `res.company`, `res.users`, groups | SaaS roles + establishment scope |
| Products / services | `product.template` (type + duration) | Duration, commission fields |
| POS / payments | `point_of_sale` | Establishment on config/order |
| Cash session | `pos.session` | Counted vs expected, alert, audit |
| Stock / WH | `stock` | One warehouse per establishment |
| Purchases / vendors | `purchase`, `res.partner` | Scoped by company |
| Customers | `res.partner` | History views |
| Employees | `hr.employee` | Establishment + performance |
| Expenses | Enterprise `hr_expense` | Custom `multi.activity.expense` |
| Appointments | Enterprise `appointment` | `salon.appointment` |
| Commissions | — | Stored snapshot on appointment |
| Restaurant floor/KDS | Enterprise `pos_restaurant` | Phase 2 module |
| Bar dose UoM | `uom` | Bar UoM data + helpers |
| SaaS plans / tenants | — | `multi_activity_saas` |
| Tickets | Enterprise Helpdesk | `multi.activity.ticket` |
| Audit | chatter / mail | Dedicated audit log |
| Dashboard | — | Owner KPI action |
| Reports | export + QWeb | Dashboard + domains |
| Notifications | mail / activity | Low stock, cash gap |

## What we refuse to rebuild

Independent stock engine, independent POS engine, `custom.customer`,
`custom.product`, `custom.stock`, hardcoded USD or tax rates.

## Install

Install the bundle on a database that already has `base`:

```bash
odoo -d odoo -i multi_activity --stop-after-init
```

Do not use `-u all` in production.
