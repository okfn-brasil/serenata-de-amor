#!/bin/bash

GIT_REPO=/opt/jarbas.git
PUBLIC_WWW=/opt/jarbas

echo "\n==> Deploying to application directory…\n"
cd $PUBLIC_WWW || exit
unset GIT_DIR
git pull $GIT_REPO master

echo "\n==> Activating virtualenv…\n"
. /opt/jarbas.venv/bin/activate

echo "\n==> Installing NodeJS packages…\n"
if [ -d node_modules/ ]; then
    rm -rf node_modules/
fi
if [ -d elm-stuff/ ]; then
    rm -rf elm-stuff/
fi
yarn install

echo "\n==> Installing Python packages…\n"
pip install -U pip
pip install -U -r requirements.txt

echo "\n==> Running migrations…\n"
python manage.py migrate

echo "\n==> Updating CEAP dataset page\n"
python manage.py ceapdatasets

echo "\n==> Building assets\n"
yarn assets

echo "\n==> Collecting static files\n"
python manage.py collectstatic --no-input

echo "\n==> Done!\n"
