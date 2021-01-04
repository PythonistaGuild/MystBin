#!/usr/bin/env sh
set -eu

envsubst '${DOMAIN}' < /etc/nginx/sites-enabled/frontend.conf > /etc/nginx/sites-enabled/frontend.conf
envsubst '${API_DOMAIN}' < /etc/nginx/sites-enabled/api.conf > /etc/nginx/sites-enabled/api.conf

. /.ssl.sh

exec "$@"