#!/bin/bash

GIT_REPO=/opt/jarbas.git
PUBLIC_WWW=/opt/jarbas

echo "==> Stopping the server"
kill -9 `cat /tmp/gunicorn.pid`

echo "==> Deploying to application directory…"
cd $PUBLIC_WWW || exit
unset GIT_DIR
git pull $GIT_REPO master

echo "==> Activating virtualenv…"
. /opt/jarbas.venv/bin/activate

echo "==> Installing NodeJS packages…"
if [ -d node_modules/ ]; then
    rm -rf node_modules/
fi
if [ -d elm-stuff/ ]; then
    rm -rf elm-stuff/
fi
npm install

echo "==> Installing Python packages…"
pip install -U pip
pip install -r requirements.txt

echo "==> Running migrations…"
python manage.py migrate

echo "==> Updating CEAP dataset page"
python manage.py ceapdatasets

echo "==> Building assets"
npm run assets

echo "==> Collecting static files"
python manage.py collectstatic --no-input

echo "==> Starting the server"
nohup gunicorn jarbas.wsgi:application --reload --bind 127.0.0.1:8001 --workers 1 --pid /tmp/gunicorn.pid &>/dev/null &

echo "==> Done!"
