#!/bin/sh
set -eu

TEMPLATES_DIR="${TEMPLATES_DIR:-/etc/nginx/templates}"
OUTPUT_PATH="${OUTPUT_PATH:-/etc/nginx/conf.d/default.conf}"
HTTP_TEMPLATE="${HTTP_TEMPLATE:-$TEMPLATES_DIR/app.http.conf.template}"
HTTPS_TEMPLATE="${HTTPS_TEMPLATE:-$TEMPLATES_DIR/app.https.conf.template}"
DOMAIN="${DOMAIN:-_}"
APP_UPSTREAM="${APP_UPSTREAM:-http://e4p:8080}"
ENABLE_SSL="${ENABLE_SSL:-false}"
CERT_PATH="/etc/letsencrypt/live/${DOMAIN}/fullchain.pem"
KEY_PATH="/etc/letsencrypt/live/${DOMAIN}/privkey.pem"
RELOAD_INTERVAL="${NGINX_RELOAD_INTERVAL:-43200}"

render_template() {
    local template="$1"
    if [ ! -f "$template" ]; then
        echo "Template $template not found" >&2
        exit 1
    fi
    mkdir -p "$(dirname "$OUTPUT_PATH")"
    envsubst '${DOMAIN} ${APP_UPSTREAM}' < "$template" > "$OUTPUT_PATH"
}

if [ "$ENABLE_SSL" = "true" ] && [ -f "$CERT_PATH" ] && [ -f "$KEY_PATH" ]; then
    echo "🔐 Detected certificate for $DOMAIN. Loading HTTPS configuration."
    render_template "$HTTPS_TEMPLATE"
else
    if [ "$ENABLE_SSL" = "true" ]; then
        echo "⚠️  SSL requested for $DOMAIN but certificate not found yet. Falling back to HTTP configuration." >&2
    else
        echo "🌐 Starting in HTTP mode."
    fi
    render_template "$HTTP_TEMPLATE"
fi

if [ "$ENABLE_SSL" = "true" ]; then
    (
        while true; do
            sleep "$RELOAD_INTERVAL"
            if [ -f "$CERT_PATH" ] && [ -f "$KEY_PATH" ]; then
                echo "🔄 Reloading nginx to pick up potential certificate updates."
                nginx -s reload || true
            fi
        done
    ) &
fi

exec nginx -g 'daemon off;'
