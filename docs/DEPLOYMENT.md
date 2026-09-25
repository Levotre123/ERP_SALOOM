# Deployment

Unchanged from `README-RENDER.md`:

```text
Git → Render Docker (odoo:18.0) → PostgreSQL 16
                                 → disk /var/lib/odoo
```

Custom addons are copied to `/mnt/extra-addons`.

After first deploy, install the bundle **once** (not on every start):

```text
ODOO_INIT=multi_activity
ODOO_DATABASE=<db>
```

Then unset `ODOO_INIT`. Do not use `ODOO_UPDATE=all`.

TLS: Render proxy, `proxy_mode=True`.
