# Tenant isolation

## Mapping

| Spec term | Implementation |
| --- | --- |
| Tenant | `multi.activity.tenant` + `res.company` |
| Establishment | `multi.activity.establishment` |
| Allowed sites | `res.users.establishment_ids` |
| Current site | `res.users.current_establishment_id` |

## Record rule pattern

Operational models:

```text
['|',
 ('company_id', '=', False),
 ('company_id', 'in', user.company_ids.ids)]
```

Establishment-restricted roles:

```text
[('establishment_id', 'in', user.establishment_ids.ids)]
```

Owner / company admin (same company, all sites):

```text
[('company_id', 'in', user.company_ids.ids)]
```

## Cross-tenant test

Create companies A and B, users UA and UB, a `pos.order` (or expense) on B.
`with_user(UA)` search/read of B’s record must raise `AccessError`.

## Residual risks (Option A)

- A future developer using `sudo()` can pierce isolation — forbidden in
  review.
- Server-wide reports must always run in the user environment.
- Path to Option B (DB per tenant) is the long-term hardening.
