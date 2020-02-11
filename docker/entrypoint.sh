#!/usr/bin/env bash

cd /app/src

mkdir -p /app/src/var/static \
         /app/src/var/conf/extra_static \
         /app/src/var/media/upload \
         /app/src/var/data \
         /app/src/var/cache \
         /app/src/var/log \
         /app/src/var/conf/extra_templates \
         /app/src/var/conf/extra_locale \
         /app/src/var/tmp

# if not custom.py present, create it
if [ ! -f /app/src/var/conf/custom.py ]; then
    touch /app/src/var/conf/custom.py
fi

# if not parsers.py present, create it
if [ ! -f /app/src/var/conf/parsers.py ]; then
    touch /app/src/var/conf/parsers.py
fi

# When a volume is mounted to /app/src, bulkimport/parsers.py and venv are hidden
if [ "$ENV" = "dev" ]; then
    ln -sf /app/src/var/conf/parsers.py /app/src/bulkimport/parsers.py
    if [ ! -d env ]; then
        python3 -m venv env
        env/bin/pip install --no-cache-dir -r requirements.txt
    fi
fi

# Activate venv
. env/bin/activate

# Set POSTGRES_HOST to Docker host IP instead of localhost
echo -e "\nPOSTGRES_HOST=$POSTGRES_HOST"
if [ "$POSTGRES_HOST" = "localhost" ]; then
    export POSTGRES_HOST=`ip route | grep default | sed 's/.* \([0-9]\+\.[0-9]\+\.[0-9]\+\.[0-9]\+\) .*/\1/'`
fi
echo "POSTGRES_HOST=$POSTGRES_HOST"

# Defaults SECRET_KEY to a random value
SECRET_KEY_FILE=/app/src/var/conf/secret_key
if [ -z $SECRET_KEY ]; then
    if [ ! -f $SECRET_KEY_FILE ]; then
        echo "Generate a secret key"
        dd bs=48 count=1 if=/dev/urandom 2>/dev/null | base64 > $SECRET_KEY_FILE
        chmod go-r $SECRET_KEY_FILE
    fi
    export SECRET_KEY=`cat $SECRET_KEY_FILE`
fi

# wait for postgres
until PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -p "$POSTGRES_PORT" -d "$POSTGRES_DB" -c '\q'; do
    >&2 echo "Postgres is unavailable - sleeping"
    sleep 1
done

>&2 echo "Postgres is up - executing command"

# exec
exec "$@"
