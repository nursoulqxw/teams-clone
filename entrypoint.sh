#!/bin/sh
set -e

python manage.py migrate --noinput

# Only the web process needs static files
case "$1" in
    daphne) python manage.py collectstatic --noinput ;;
esac

exec "$@"
