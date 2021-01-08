#!/usr/bin/env sh
set -eu

if [ ! -d "/etc/nginx/sites-enabled/" ]; then
    mkdir -p "/etc/nginx/sites-enabled/"
fi

envsubst '${DOMAIN}' < /etc/mystbin/sites-enabled/frontend.conf > /etc/nginx/sites-enabled/frontend.conf
envsubst '${API_DOMAIN}' < /etc/mystbin/sites-enabled/api.conf > /etc/nginx/sites-enabled/api.conf

. /etc/mystbin/ssl.sh

exec "$@"