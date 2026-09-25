# Backup and restore

A complete Odoo backup is always:

```text
PostgreSQL dump  +  /var/lib/odoo/filestore/<db>
```

taken at the same moment.

## Backup

1. Render Postgres backup or `pg_dump`
2. Copy or snapshot the disk under `/var/lib/odoo`
3. Store both with the same timestamp and database name

## Restore

1. Restore the dump into the same `DB_NAME`
2. Restore `filestore/<db>` onto the disk
3. Start Odoo without `-i` / `-u all`
4. Open attachments, not only the login page

Tenant deletion must never be an automatic drop of this pair.
