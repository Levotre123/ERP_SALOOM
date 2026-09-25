#!/bin/bash
# Render/production entrypoint for official odoo:18.0
# - Validates configuration
# - Generates /etc/odoo/odoo.conf (no shell interpolation of secrets)
# - Never prints passwords or master password
# - exec's Odoo so PID 1 receives SIGTERM
set -euo pipefail
set +x

umask 077

CONFIG_PATH="${ODOO_CONFIG_PATH:-/etc/odoo/odoo.conf}"
TEMPLATE_PATH="${ODOO_CONFIG_TEMPLATE:-/opt/odoo/odoo.conf.template}"
DATA_DIR="${ODOO_DATA_DIR:-/var/lib/odoo}"
PORT="${PORT:-8069}"

log() {
    printf '%s\n' "$*" >&2
}

fail() {
    log "ERROR: $*"
    exit 1
}

# ---------------------------------------------------------------------------
# Generate runtime configuration (Python: safe URL parse + INI escaping)
# ---------------------------------------------------------------------------
python3 - "$TEMPLATE_PATH" "$CONFIG_PATH" "$DATA_DIR" "$PORT" <<'PY'
import os
import re
import sys
from urllib.parse import unquote, urlparse

template_path, config_path, data_dir, port = sys.argv[1:5]

WEAK_ADMIN = {
    "admin",
    "admin123",
    "odoo",
    "123456",
    "password",
    "changeme",
    "secret",
    "admin_passwd",
}


def die(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    raise SystemExit(1)


def ini_escape(value: str) -> str:
    # Odoo uses ConfigParser interpolation: a raw "%" must be "%%".
    return value.replace("%", "%%")


def parse_database_url(url: str) -> dict:
    parsed = urlparse(url)
    if parsed.scheme not in ("postgres", "postgresql"):
        die("DATABASE_URL must use postgres:// or postgresql://")
    if not parsed.hostname:
        die("DATABASE_URL is missing a host")
    name = unquote(parsed.path.lstrip("/")) if parsed.path else ""
    if not name:
        die("DATABASE_URL is missing a database name")
    return {
        "host": parsed.hostname,
        "port": str(parsed.port or 5432),
        "user": unquote(parsed.username) if parsed.username else "",
        "password": unquote(parsed.password) if parsed.password else "",
        "name": name.split("?")[0],
    }


def first(*keys: str) -> str:
    for key in keys:
        value = os.environ.get(key)
        if value:
            return value
    return ""


db = {}
database_url = first("DATABASE_URL")
if database_url:
    db = parse_database_url(database_url)

host = first("DB_HOST") or db.get("host", "")
port_db = first("DB_PORT") or db.get("port", "5432")
user = first("DB_USER") or db.get("user", "")
password = first("DB_PASSWORD") or db.get("password", "")
name = first("DB_NAME") or db.get("name", "")
admin = first("ODOO_ADMIN_PASSWD")

missing = []
if not host:
    missing.append("DB_HOST (or DATABASE_URL)")
if not user:
    missing.append("DB_USER (or DATABASE_URL)")
if not password:
    missing.append("DB_PASSWORD (or DATABASE_URL)")
if not name:
    missing.append("DB_NAME (or DATABASE_URL)")
if not admin:
    missing.append("ODOO_ADMIN_PASSWD")
if missing:
    die("missing required configuration: " + ", ".join(missing))

on_render = bool(os.environ.get("RENDER"))
if on_render and host in {"localhost", "127.0.0.1", "::1"}:
    die("DB_HOST cannot be localhost on Render; use the private Render PostgreSQL host")

if admin.strip().lower() in WEAK_ADMIN:
    if on_render:
        die("ODOO_ADMIN_PASSWD is too weak for production; set a long random secret")
    print("WARNING: ODOO_ADMIN_PASSWD is weak; use a strong secret in production", file=sys.stderr)
elif on_render and len(admin) < 16:
    die("ODOO_ADMIN_PASSWD must be at least 16 characters in production")

if "\n" in password or "\n" in admin:
    die("passwords must not contain newlines")

dbfilter = first("ODOO_DBFILTER") or ("^" + re.escape(name) + "$")
addons_path = first("ODOO_ADDONS_PATH") or (
    "/usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons"
)
list_db = first("ODOO_LIST_DB") or "False"
proxy_mode = first("ODOO_PROXY_MODE") or ("True" if on_render else "False")
workers = first("ODOO_WORKERS") or "0"
max_cron = first("ODOO_MAX_CRON_THREADS") or "1"
limit_cpu = first("ODOO_LIMIT_TIME_CPU") or "120"
limit_real = first("ODOO_LIMIT_TIME_REAL") or "240"
limit_soft = first("ODOO_LIMIT_MEMORY_SOFT") or "805306368"
limit_hard = first("ODOO_LIMIT_MEMORY_HARD") or "1342177280"
limit_req = first("ODOO_LIMIT_REQUEST") or "8192"
log_level = first("ODOO_LOG_LEVEL") or "info"
sslmode = first("ODOO_DB_SSLMODE") or "prefer"
without_demo = first("ODOO_WITHOUT_DEMO") or "True"
http_interface = first("ODOO_HTTP_INTERFACE") or "0.0.0.0"

try:
    workers_int = int(workers)
except ValueError:
    die("ODOO_WORKERS must be an integer")
if on_render and workers_int > 0:
    print(
        "WARNING: ODOO_WORKERS>0 needs /websocket routed to the gevent port. "
        "Render forwards a single PORT, so Discuss/live features may break. "
        "Keep ODOO_WORKERS=0 unless you add a path-aware proxy.",
        file=sys.stderr,
    )

values = {
    "ADMIN_PASSWD": ini_escape(admin),
    "DB_HOST": ini_escape(host),
    "DB_PORT": ini_escape(str(port_db)),
    "DB_USER": ini_escape(user),
    "DB_PASSWORD": ini_escape(password),
    "DB_NAME": ini_escape(name),
    "DB_SSLMODE": ini_escape(sslmode),
    "DBFILTER": ini_escape(dbfilter),
    "LIST_DB": ini_escape(list_db),
    "PROXY_MODE": ini_escape(proxy_mode),
    "DATA_DIR": ini_escape(data_dir),
    "ADDONS_PATH": ini_escape(addons_path),
    "HTTP_INTERFACE": ini_escape(http_interface),
    "HTTP_PORT": ini_escape(str(port)),
    "WORKERS": ini_escape(str(workers)),
    "MAX_CRON_THREADS": ini_escape(str(max_cron)),
    "LIMIT_TIME_CPU": ini_escape(str(limit_cpu)),
    "LIMIT_TIME_REAL": ini_escape(str(limit_real)),
    "LIMIT_MEMORY_SOFT": ini_escape(str(limit_soft)),
    "LIMIT_MEMORY_HARD": ini_escape(str(limit_hard)),
    "LIMIT_REQUEST": ini_escape(str(limit_req)),
    "LOG_LEVEL": ini_escape(log_level),
    "WITHOUT_DEMO": ini_escape(without_demo),
}

try:
    template = open(template_path, encoding="utf-8").read()
except OSError as exc:
    die(f"cannot read config template: {exc}")

rendered = template
for key, value in values.items():
    rendered = rendered.replace("{{" + key + "}}", value)

if "{{" in rendered:
    leftover = sorted(set(re.findall(r"\{\{[A-Z0-9_]+\}\}", rendered)))
    die("unresolved config placeholders: " + ", ".join(leftover))

os.makedirs(os.path.dirname(config_path), exist_ok=True)
fd = os.open(config_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
with os.fdopen(fd, "w", encoding="utf-8") as handle:
    handle.write(rendered)

runtime_path = "/tmp/odoo-runtime.env"
with open(runtime_path, "w", encoding="utf-8") as handle:
    handle.write(f"DB_HOST={host}\n")
    handle.write(f"DB_PORT={port_db}\n")
    handle.write(f"DB_NAME={name}\n")
    handle.write(f"DB_USER={user}\n")

print(
    "Generated Odoo config: host={host} port={port} db={db} user={user} "
    "http=0.0.0.0:{http} workers={workers} proxy_mode={proxy} list_db={list_db} "
    "data_dir={data}".format(
        host=host,
        port=port_db,
        db=name,
        user=user,
        http=port,
        workers=workers,
        proxy=proxy_mode,
        list_db=list_db,
        data=data_dir,
    ),
    file=sys.stderr,
)
PY

# Non-secret connection facts for the wait loop (password is not written here).
# shellcheck disable=SC1091
. /tmp/odoo-runtime.env
export DB_HOST DB_PORT DB_NAME DB_USER

# ---------------------------------------------------------------------------
# Persistent filestore directory (Render disk mount: /var/lib/odoo)
# ---------------------------------------------------------------------------
mkdir -p "$DATA_DIR"
if ! chown odoo:odoo "$DATA_DIR"; then
    log "WARNING: could not chown $DATA_DIR; ensure the persistent disk is writable by uid odoo"
fi
chmod 750 "$DATA_DIR" || true

if [ -d /mnt/extra-addons ]; then
    chown -R odoo:odoo /mnt/extra-addons || true
fi

chown odoo:odoo "$CONFIG_PATH"
chmod 600 "$CONFIG_PATH"

# ---------------------------------------------------------------------------
# Wait for PostgreSQL (no credentials logged)
# ---------------------------------------------------------------------------
wait_for_postgres() {
    local attempt=1
    local max="${DB_CONNECT_TIMEOUT:-60}"
    log "Waiting for PostgreSQL TCP connectivity (timeout ${max}s)..."
    while [ "$attempt" -le "$max" ]; do
        if python3 -c 'import os, socket
host = os.environ["DB_HOST"]
port = int(os.environ.get("DB_PORT", "5432"))
socket.create_connection((host, port), 3).close()
'; then
            log "PostgreSQL is reachable."
            return 0
        fi
        sleep 1
        attempt=$((attempt + 1))
    done
    fail "PostgreSQL is not reachable at the configured host/port"
}

# ---------------------------------------------------------------------------
# Optional explicit module operations (never default to -u all)
# ---------------------------------------------------------------------------
extra_args=()
if [ -n "${ODOO_UPDATE:-}" ]; then
    if [ "${ODOO_UPDATE}" = "all" ]; then
        fail "Refusing ODOO_UPDATE=all; upgrade specific modules instead (e.g. ODOO_UPDATE=sale,my_module)"
    fi
    extra_args+=("-u" "$ODOO_UPDATE")
    log "Explicit module update requested."
fi
if [ -n "${ODOO_INIT:-}" ]; then
    extra_args+=("-i" "$ODOO_INIT")
    log "Explicit module init requested."
fi
if [ -n "${ODOO_DATABASE:-}" ]; then
    extra_args+=("-d" "$ODOO_DATABASE")
fi
if [ "${ODOO_STOP_AFTER_INIT:-}" = "1" ] || [ "${ODOO_STOP_AFTER_INIT:-}" = "true" ]; then
    extra_args+=("--stop-after-init")
fi

run_as_odoo() {
    if [ "$(id -u)" = "0" ]; then
        # Official odoo:18.0 has setpriv, not gosu.
        exec setpriv --reuid=odoo --regid=odoo --init-groups -- "$@"
    fi
    exec "$@"
}

odoo_schema_present() {
    python3 -c '
import os
import sys
from urllib.parse import unquote, urlparse

try:
    import psycopg2
except ImportError:
    raise SystemExit(2)

host = os.environ.get("DB_HOST")
port = os.environ.get("DB_PORT") or "5432"
user = os.environ.get("DB_USER")
password = os.environ.get("DB_PASSWORD")
name = os.environ.get("DB_NAME")
url = os.environ.get("DATABASE_URL") or ""
if url and (not host or not password or not user or not name):
    parsed = urlparse(url)
    host = host or parsed.hostname
    port = port or str(parsed.port or 5432)
    user = user or (unquote(parsed.username) if parsed.username else "")
    password = password or (unquote(parsed.password) if parsed.password else "")
    name = name or unquote(parsed.path.lstrip("/")).split("?")[0]
try:
    conn = psycopg2.connect(
        host=host, port=port, user=user, password=password, dbname=name, connect_timeout=5
    )
    cur = conn.cursor()
    cur.execute(
        "SELECT 1 FROM information_schema.tables "
        "WHERE table_schema = %s AND table_name = %s",
        ("public", "ir_module_module"),
    )
    present = cur.fetchone() is not None
    conn.close()
except Exception:
    raise SystemExit(3)
raise SystemExit(0 if present else 1)
'
}

maybe_init_empty_database() {
    local rc=0
    odoo_schema_present || rc=$?
    if [ "$rc" -eq 0 ]; then
        log "Existing Odoo schema detected; normal start (no automatic -i/-u)."
        return 0
    fi
    if [ "$rc" -eq 2 ]; then
        log "WARNING: psycopg2 not available; cannot detect Odoo schema."
        return 0
    fi
    if [ "$rc" -eq 3 ]; then
        log "WARNING: could not inspect PostgreSQL schema yet."
        return 0
    fi
    if [ -n "${ODOO_INIT:-}" ]; then
        if [ -z "${ODOO_DATABASE:-}" ]; then
            extra_args+=("-d" "$DB_NAME")
        fi
        log "PostgreSQL database has no Odoo schema; using explicit ODOO_INIT."
        return 0
    fi
    if [ "${ODOO_AUTO_INIT_IF_EMPTY:-}" = "true" ]; then
        extra_args+=("-d" "$DB_NAME" "-i" "base")
        log "PostgreSQL database is empty; installing base once (ODOO_AUTO_INIT_IF_EMPTY)."
        return 0
    fi
    log "WARNING: database '${DB_NAME}' has no Odoo schema. /web/health will fail until you initialize it (set ODOO_LIST_DB=True or ODOO_INIT=base, or ODOO_AUTO_INIT_IF_EMPTY=true)."
}

start_odoo() {
    wait_for_postgres
    maybe_init_empty_database
    log "Starting Odoo on 0.0.0.0:${PORT} (logs -> stdout)"
    run_as_odoo odoo \
        --config="$CONFIG_PATH" \
        --http-interface=0.0.0.0 \
        --http-port="$PORT" \
        "${extra_args[@]}" \
        "$@"
}

if [ "${1:-}" = "odoo" ] || [ "${1:-}" = "odoo-bin" ]; then
    shift
    start_odoo "$@"
elif [ $# -eq 0 ]; then
    start_odoo
else
    run_as_odoo "$@"
fi
