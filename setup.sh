#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$REPO_ROOT/.env"

cd "$REPO_ROOT"

# Ensure git commits use the requested identity
if command -v git >/dev/null 2>&1; then
    git -C "$REPO_ROOT" config user.name "zZedix"
    git -C "$REPO_ROOT" config user.email "zZedix@users.noreply.github.com"
fi

require_command() {
    local name="$1"
    local instructions="$2"
    if ! command -v "$name" >/dev/null 2>&1; then
        echo "Error: $name is required. $instructions" >&2
        exit 1
    fi
}

require_command docker "Please install Docker: https://docs.docker.com/get-docker/"
require_command python3 "Python 3 is required to generate configuration secrets."

if docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD=(docker compose)
elif command -v docker-compose >/dev/null 2>&1; then
    COMPOSE_CMD=(docker-compose)
else
    echo "Error: Docker Compose plugin or docker-compose binary not found." >&2
    exit 1
fi

if [ ! -f "$ENV_FILE" ]; then
    echo "Creating .env from template"
    cp "$REPO_ROOT/env.example" "$ENV_FILE"
fi

set_env_var() {
    local key="$1"
    local value="$2"
    if grep -q "^${key}=" "$ENV_FILE"; then
        if sed --version >/dev/null 2>&1; then
            sed -i "s#^${key}=.*#${key}=${value}#" "$ENV_FILE"
        else
            sed -i '' "s#^${key}=.*#${key}=${value}#" "$ENV_FILE"
        fi
    else
        printf '%s=%s\n' "$key" "$value" >> "$ENV_FILE"
    fi
}

get_env_var() {
    local key="$1"
    local default_value="${2-}"
    if grep -q "^${key}=" "$ENV_FILE"; then
        grep "^${key}=" "$ENV_FILE" | tail -n1 | cut -d'=' -f2-
    else
        printf '%s' "$default_value"
    fi
}

SECRET_KEY_VALUE="$(get_env_var SECRET_KEY)"
if [ -z "$SECRET_KEY_VALUE" ] || [ "$SECRET_KEY_VALUE" = "change_me_to_random_base64" ]; then
    NEW_SECRET_KEY="$(python3 -c 'import secrets, base64; print(base64.urlsafe_b64encode(secrets.token_bytes(32)).decode())')"
    set_env_var SECRET_KEY "$NEW_SECRET_KEY"
fi

read -r -p "Enter your domain (leave blank for HTTP only): " DOMAIN
DOMAIN="${DOMAIN// /}"

if [ -n "$DOMAIN" ]; then
    ENABLE_SSL=true
    read -r -p "Enter email for Let's Encrypt notifications [admin@${DOMAIN}]: " EMAIL_FOR_LETSENCRYPT
    if [ -z "$EMAIL_FOR_LETSENCRYPT" ]; then
        EMAIL_FOR_LETSENCRYPT="admin@${DOMAIN}"
    fi
else
    ENABLE_SSL=false
    EMAIL_FOR_LETSENCRYPT=""
fi

set_env_var DOMAIN "$DOMAIN"
set_env_var ENABLE_SSL "$ENABLE_SSL"
set_env_var EMAIL_FOR_LETSENCRYPT "$EMAIL_FOR_LETSENCRYPT"
set_env_var APP_HOST "$(get_env_var APP_HOST 0.0.0.0)"
set_env_var APP_PORT "$(get_env_var APP_PORT 8080)"
set_env_var APP_HTTP_PORT "$(get_env_var APP_HTTP_PORT 8080)"
set_env_var GUNICORN_WORKERS "$(get_env_var GUNICORN_WORKERS 2)"

if [ "$ENABLE_SSL" = true ]; then
    echo "Starting HTTPS deployment for $DOMAIN"
else
    echo "Starting HTTP-only deployment"
fi

# Always bring down existing stack before starting
"${COMPOSE_CMD[@]}" -f "$REPO_ROOT/docker-compose.yml" down --remove-orphans

if [ "$ENABLE_SSL" = true ]; then
    # Start application and nginx to serve ACME challenges over HTTP
    "${COMPOSE_CMD[@]}" -f "$REPO_ROOT/docker-compose.yml" up -d e4p
    "${COMPOSE_CMD[@]}" -f "$REPO_ROOT/docker-compose.yml" --profile https up -d nginx

    echo "Waiting for nginx to be ready..."
    sleep 5

    echo "Requesting Let's Encrypt certificate for $DOMAIN"
    "${COMPOSE_CMD[@]}" -f "$REPO_ROOT/docker-compose.yml" --profile https run --rm \
        --env CERTBOT_EMAIL="$EMAIL_FOR_LETSENCRYPT" \
        certbot certonly --webroot -w /var/www/certbot \
        --agree-tos --no-eff-email \
        --email "$EMAIL_FOR_LETSENCRYPT" \
        -d "$DOMAIN" --non-interactive

    echo "Reloading nginx with HTTPS configuration"
    "${COMPOSE_CMD[@]}" -f "$REPO_ROOT/docker-compose.yml" --profile https up -d nginx

    echo "Starting automatic certificate renewal service"
    "${COMPOSE_CMD[@]}" -f "$REPO_ROOT/docker-compose.yml" --profile https up -d certbot-renew

    cat <<MSG
✅ Deployment complete.
Your application should be available at: https://$DOMAIN
NGINX automatically reloads every 12 hours to pick up renewed certificates.
MSG
else
    "${COMPOSE_CMD[@]}" -f "$REPO_ROOT/docker-compose.yml" up -d e4p
    cat <<MSG
✅ Deployment complete.
Your application should be available at: http://localhost:8080
MSG
fi
