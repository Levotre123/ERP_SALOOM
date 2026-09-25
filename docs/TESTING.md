# Testing

Run inside the Odoo container or with addons on `addons_path`:

```bash
odoo -d odoo --test-enable --stop-after-init \
  -i multi_activity \
  --test-tags /multi_activity_security,/multi_activity_operations,/multi_activity_salon
```

## Mandatory cases

| Case | Expected |
| --- | --- |
| Tenant A reads Tenant B expense | AccessError |
| Manager A reads Establishment B | AccessError |
| Owner sees both own establishments | Allowed |
| Basic plan, 2nd establishment | ValidationError |
| POS session close: expected 500, counted 480 | Difference −20, audit |
| Product price 10 → 12 | Audit old/new |
| Salon appointment completed | Commission snapshot stored |
| Low stock vs min_qty | Dashboard flag |

Restaurant table → kitchen → paid and bar 50 ml / 750 ml UoM conversion
are covered by automated tests when those modules are installed.

## Profit formula

Estimated profit = paid POS `amount_total` − confirmed `multi.activity.expense`
amounts in the selected period. Cash received is POS payments and is reported
separately.
