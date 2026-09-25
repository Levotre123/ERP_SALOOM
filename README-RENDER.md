# Odoo 18 on Render

Production deployment guide for this repository. No secrets belong in Git.

## Architecture

```text
Git repository
      ↓
Render Web Service (Docker)
      ↓
odoo:18.0 + /mnt/extra-addons
      │
      ├────────────► Render PostgreSQL 16 (private)
      │
      └────────────► Persistent Disk
                        /var/lib/odoo
                           └── filestore/<database>/
```

Both PostgreSQL **and** the filestore are required for a complete Odoo instance.

Application code (core Odoo + `addons/`) comes from the Docker image. Persistent disk is only for runtime data. PostgreSQL is never installed in the Odoo container.

This repository was empty when the deployment files were added: there are **no custom addons yet**. Drop modules into `addons/` and rebuild.

## Prerequisites

- Render account (paid web + Postgres plans; Odoo will not stay healthy on 512 MB)
- Git remote Render can access
- Docker (optional, for local verification)
- For an existing production Odoo: a matching PostgreSQL dump **and** filestore backup taken at the same time

Recommended minimum:

| Resource | Suggested plan | Why |
| --- | --- | --- |
| Web service | Render `standard` (2 GB) | Odoo is memory-heavy |
| PostgreSQL | `basic-1gb`, major version **16** | Official Odoo 18 target |
| Disk | 10 GB at `/var/lib/odoo` | Attachments/documents |

Keep the web service and database in the **same region**. This Blueprint uses `frankfurt`.

## Render PostgreSQL creation

Blueprint (`render.yaml`) creates `odoo-postgres` automatically:

- PostgreSQL 16
- Database name `odoo`, user `odoo` (Render may add a suffix)
- `ipAllowList: []` — private network only

If you create the database in the dashboard instead:

1. New → PostgreSQL
2. Same region as the web service
3. PostgreSQL 16
4. Restrict the IP allow list to internal connections
5. Copy the **Internal** connection fields, not the public URL, into the web service

Do not use `localhost` as `DB_HOST` on Render.

## Environment variables

| Variable | Required | Secret | Purpose |
| --- | --- | --- | --- |
| `DATABASE_URL` | Yes on Render | Yes | Private `postgresql://` URL; parsed into host/port/name/user/password |
| `DB_HOST` | Yes if no URL | No | PostgreSQL private hostname |
| `DB_PORT` | If no URL | No | Default `5432` |
| `DB_NAME` | Yes if no URL | No | Odoo database name (also used for `dbfilter`) |
| `DB_USER` | Yes if no URL | No | PostgreSQL user |
| `DB_PASSWORD` | Yes if no URL | Yes | PostgreSQL password |
| `ODOO_ADMIN_PASSWD` | Yes | Yes | Database-manager **master** password, not the Admin user password |
| `PORT` | Render-provided | No | HTTP listen port (`0.0.0.0:$PORT`) |
| `ODOO_LIST_DB` | Recommended | No | `False` in production after the first database exists |
| `ODOO_PROXY_MODE` | Recommended | No | `True` on Render (HTTPS is terminated at the proxy) |
| `ODOO_WORKERS` | Optional | No | Default `0` (required for Discuss on a single Render port) |
| `ODOO_MAX_CRON_THREADS` | Optional | No | Default `1` |
| `ODOO_LIMIT_TIME_CPU` | Optional | No | Default `120` |
| `ODOO_LIMIT_TIME_REAL` | Optional | No | Default `240` |
| `ODOO_LIMIT_MEMORY_SOFT` | Optional | No | Default `805306368` (~768 MB) |
| `ODOO_LIMIT_MEMORY_HARD` | Optional | No | Default `1342177280` (~1.25 GB) |
| `ODOO_LOG_LEVEL` | Optional | No | Default `info` |
| `ODOO_DB_SSLMODE` | Optional | No | Default `prefer` |
| `ODOO_DBFILTER` | Optional | No | Default `^<DB_NAME>$` |
| `ODOO_UPDATE` | No | No | Explicit `-u module1,module2` (never `all`) |
| `ODOO_INIT` | No | No | Explicit `-i` for a controlled first install |
| `ODOO_DATABASE` | No | No | Passed as `-d` with init/update only |
| `ODOO_STOP_AFTER_INIT` | No | No | Set `1` for one-shot CLI init |
| `ODOO_AUTO_INIT_IF_EMPTY` | Recommended | No | `true`: install `base` only if the DB has no Odoo schema |

`ODOO_ADMIN_PASSWD` is **not** the normal `admin` user password. On Render it must be at least 16 characters and must not be a trivial value.

`DATABASE_URL` is parsed. It is never passed raw to Odoo.

## Persistent disk

| Setting | Value |
| --- | --- |
| Mount path | `/var/lib/odoo` |
| Odoo `data_dir` | `/var/lib/odoo` |
| Blueprint disk name | `odoo-filestore` |
| Default size | 10 GB |

If this disk is missing, attachments vanish on every deploy. That is not a production-ready state.

Do not store custom addons on the disk. They are copied into the image at `/mnt/extra-addons`.

## Deployment

### Blueprint (preferred)

1. Push this repository to GitHub/GitLab/Render Git
2. Render Dashboard → New → Blueprint
3. Select the repo (`render.yaml` at the root)
4. Confirm region, plans, and generated `ODOO_ADMIN_PASSWD`
5. Apply

### Manual dashboard

```text
Render Dashboard
      ↓
Create PostgreSQL 16 (private, same region)
      ↓
Create Web Service from Git
      ↓
Runtime: Docker
      ↓
Dockerfile path: ./Dockerfile
      ↓
Set environment variables (table above)
      ↓
Attach Persistent Disk
      ↓
Mount: /var/lib/odoo
      ↓
Health Check Path: /web/health
      ↓
Deploy
```

Health checks use `/web/health` (unauthenticated). Odoo can take 1–2 minutes to bind HTTP. A too-aggressive check causes restart loops.

## First startup

Normal container start **does not** run `-u all` and **does not** recreate PostgreSQL.

Render already provides an empty PostgreSQL database. Until that database contains Odoo tables, `/web/health` returns HTTP 500 (`ir.http` missing) and Render may restart the service.

This project therefore supports a **one-time empty-schema install**:

- `ODOO_AUTO_INIT_IF_EMPTY=true` (set in `render.yaml` and local Compose)
- If `ir_module_module` is **absent**, Odoo starts with `-i base -d $DB_NAME` **once**
- If the schema **exists** (normal restarts, restored dumps), startup is a plain connect — no `-i` / `-u`

First-time flow:

1. Deploy with the Blueprint defaults
2. Wait for `base` to install (often 1–3 minutes). Health checks need a long start window
3. Open the service URL and set the Admin **user** password
4. Keep `ODOO_LIST_DB=False` after you have exactly one database
5. Set Settings → System Parameters `web.base.url` to your HTTPS URL (`https://….onrender.com` or the custom domain)

To initialize **only** by hand, set `ODOO_AUTO_INIT_IF_EMPTY=false`, then either set `ODOO_LIST_DB=True` and use the database manager, or run a one-shot `ODOO_INIT=base`.

If you are restoring a dump, restore **before** the first start (or after, replacing the empty `base` install). Auto-init is skipped when Odoo tables already exist.

Do not hard-code `*.onrender.com` inside modules. Use Odoo’s base URL.

## Existing database migration

Do **not** create a fresh production database if you already have one.

```text
OLD SERVER
    ├── pg_dump (custom or plain)
    └── filestore/<db_name>/
             ↓
        Secure backup (same moment)
             ↓
         RENDER
       ┌─────┴─────┐
       ▼           ▼
 PostgreSQL     Disk /var/lib/odoo
 restore          filestore/<db_name>/
```

1. Put the source instance in maintenance / stop writers
2. Dump PostgreSQL and archive the matching `filestore/<database_name>`
3. Restore the dump into Render PostgreSQL (`DB_NAME` must match the old database name, or you must rename the filestore directory to match)
4. Copy the filestore onto the persistent disk at `/var/lib/odoo/filestore/<database_name>/`
5. Start Odoo **without** `-i` / `-u all`
6. Validate users, companies, contacts, attachments, documents, images, accounting, and custom data

A PostgreSQL-only restore is incomplete.

## Filestore migration

Typical source locations:

- `/var/lib/odoo/filestore/<db>`
- `~/.local/share/Odoo/filestore/<db>`
- A previous Docker volume mounted at `/var/lib/odoo`

Never commit the filestore. Copy it with `scp`, `rsync`, or a Render one-off shell onto the disk:

```text
/var/lib/odoo/filestore/<exact_database_name>/
```

Owner should be `odoo` (the entrypoint corrects top-level ownership).

## Custom module upgrade procedure

1. Put the module in `addons/<module_name>/` with a valid `__manifest__.py`
2. Add any extra Python packages to `requirements.txt`
3. Deploy the new image (normal start, no automatic update)
4. Set `ODOO_UPDATE=<module_name>` and `ODOO_DATABASE=<db>` **once**
5. After the upgrade finishes, **unset** `ODOO_UPDATE`
6. Confirm menus, models, views, and assets; watch logs for tracebacks

`ODOO_UPDATE=all` is rejected by the entrypoint.

## Backup procedure

Take PostgreSQL and filestore together.

1. Render PostgreSQL → backup / `pg_dump`
2. Archive `/var/lib/odoo/filestore` from the disk (Render disk snapshot or a one-off copy)
3. Store both with the same timestamp and database name
4. Test a restore on a non-production service periodically

## Restore procedure

1. Restore the PostgreSQL dump into an empty/compatible database
2. Restore `filestore/<db>` onto `/var/lib/odoo/filestore/<db>`
3. Start Odoo with the same `DB_NAME` / `dbfilter`
4. Open attachments and reports, not only the login screen

## Troubleshooting

### Database connection

Check `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` / `DATABASE_URL`.

- Host must be the **private** Render hostname
- Region mismatch causes timeouts
- Public-only DB with `ipAllowList: []` will fail from the internet (expected)
- The entrypoint logs host/db/user, never passwords

### Odoo returns 502

- Container still starting (wait; `/web/health` not up yet)
- Process not bound to `0.0.0.0:$PORT`
- OOM on a too-small plan (`ODOO_WORKERS` too high)
- Health check path wrong (must be `/web/health`)
- Read Render logs, not only the HTTP status

### Attachments disappear

- Disk not mounted at `/var/lib/odoo`
- `data_dir` is not `/var/lib/odoo`
- Filestore directory name ≠ database name
- Files written outside the disk (ephemeral container filesystem)

### Custom module missing

- Module is not under `addons/`
- Missing `__manifest__.py` / `__init__.py`
- `addons_path` does not include `/mnt/extra-addons`
- Apps → Update Apps List
- Unmet `depends` in the manifest

### Blank page / asset errors

- Module not compatible with Odoo 18
- Browser console 404/500 on `/web/assets`
- `proxy_mode` false behind Render HTTPS
- `web.base.url` still `http://localhost:8069`
- Do not override `gevent` / `greenlet` in `requirements.txt`

### Discuss / live notifications fail

Keep `ODOO_WORKERS=0` on Render. Multiprocessing needs `/websocket` on the gevent port; Render only forwards `$PORT`.

## Rollback procedure

**Code**

1. Revert to the previous Git commit
2. Render redeploys the previous image
3. Do **not** assume the database schema rolled back

**Database / filestore**

1. Restore the matching dump + filestore pair
2. Do not “downgrade” schema by starting older modules against a newer database without a tested plan

If a module upgrade ran, rolling back only the image can leave the registry/schema ahead of the code.

## Local development

```bash
docker compose up --build
```

- Odoo: http://localhost:8069
- Local Postgres user/password are **development only**
- `ODOO_LIST_DB=True`, `ODOO_PROXY_MODE=False`
- Volume `odoo-data` → `/var/lib/odoo`
- `./addons` is bind-mounted for live custom modules

Do not reuse the local volume or local passwords in production.

## Custom addons

Place each module in `addons/<technical_name>/`:

```text
addons/
  my_module/
    __init__.py
    __manifest__.py
    models/
    views/
    security/
```

The image copies that tree to `/mnt/extra-addons`. No custom modules were present when this guide was written.

## Security notes

- `list_db = False` after initialization
- `dbfilter` locked to `DB_NAME`
- Master password from `ODOO_ADMIN_PASSWD` (generated on Render)
- Database private-only
- `proxy_mode = True` so Odoo trusts `X-Forwarded-*` from Render
- Logs go to stdout for Render; secrets are not printed
- Do not commit `.env`, dumps, or filestore
