# Data model

```text
multi.activity.plan ──┬── multi.activity.feature
                      └── multi.activity.subscription
                                    │
                          multi.activity.tenant
                                    │
                              res.company
                                    │
                    multi.activity.establishment
                           │         │
                    stock.warehouse  pos.config
                           │         │
                      stock.move   pos.order / pos.session
                                    │
                    multi.activity.expense
                    multi.activity.audit.log
                    salon.appointment
                    restaurant.table / restaurant.order
                    multi.activity.ticket
```

## Ownership rules

- Tenant operational data has `company_id` = tenant company.
- Establishment-specific rows have `establishment_id` when Odoo has no
  better dimension (warehouse / POS config).
- `pos.order.establishment_id` is stored from `config_id`.
- `stock.warehouse.establishment_id` links inventory.

## Do not invent

| Need | Authoritative model |
| --- | --- |
| Customer / vendor | `res.partner` |
| Product / service | `product.template` |
| Employee | `hr.employee` |
| POS sale | `pos.order` |
| Cash session | `pos.session` |
| Stock | `stock.move` / `stock.quant` |
| Purchase | `purchase.order` |

## Sequences

`ir.sequence` for expenses, appointments, audit, tickets, tenants.
No `MAX(id)+1`.
