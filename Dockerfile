# Production image for Render: official Odoo 18 + custom addons.
# PostgreSQL is external (Render managed). Do not install a database here.
FROM odoo:18.0

USER root

COPY requirements.txt /tmp/requirements.txt
RUN if grep -qE '^[[:space:]]*[^#[:space:]]' /tmp/requirements.txt; then \
        pip3 install --break-system-packages --no-cache-dir -r /tmp/requirements.txt; \
    fi \
    && rm -f /tmp/requirements.txt

COPY addons /mnt/extra-addons
COPY odoo.conf.template /opt/odoo/odoo.conf.template
COPY entrypoint.sh /entrypoint.sh

RUN chmod 755 /entrypoint.sh \
    && chmod 644 /opt/odoo/odoo.conf.template \
    && mkdir -p /mnt/extra-addons /var/lib/odoo \
    && chown -R odoo:odoo /mnt/extra-addons /var/lib/odoo /opt/odoo

# Listen address is set at runtime from $PORT (Render) or 8069 (local).
EXPOSE 8069

# Unauthenticated Odoo health endpoint. Render also checks /web/health.
HEALTHCHECK --interval=30s --timeout=10s --start-period=180s --retries=10 \
    CMD python3 -c "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:%s/web/health' % os.environ.get('PORT','8069'), timeout=5)"

# Entrypoint starts as root to write config and fix disk ownership, then setpriv to odoo.
ENTRYPOINT ["/entrypoint.sh"]
CMD ["odoo"]
