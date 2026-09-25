# Platform administrator guide

## Who

Users in **SaaS / Platform Administrator**. They must not be cashiers
on tenant companies.

## Daily

1. **Tenants** — trial / active / past due / suspended
2. **Plans & features** — limits and entitlements (no hardcoded prices)
3. **Subscriptions** — renewals, grace
4. **Tickets** — support from tenant owners
5. **Provisioning logs** — retry failed onboarding

## Suspend a tenant

Set tenant status to `suspended`. Owner login is blocked; data is kept.

## Languages

English is always available. French (`fr_FR`) is activated with the suite.
Open **SaaS Admin → Languages** to install more Odoo language packs.
Set tenant **Language** before provisioning so the owner starts in that UI.

Do not hardcode one country language in custom code. Use Odoo translations.

## Do not

- Browse tenant POS or stock “to debug” from the platform company
- Share `ODOO_ADMIN_PASSWD` or DB passwords
- Destroy a tenant database to collect an unpaid invoice
