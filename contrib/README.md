# Contrib: scripts to help you maintain Serenata de Amor

## `.env.sample`

Sample environment variables to run Serenata de Amor.

## `crontab/`

This is a reference of the `crontab` we keep in our servers and the scripts/executables we schedule for maintenance.

## `data/`

Sample data to run Jarbas, check Jarba's `README.md` to know how load it.

## `deploy.sh`

This is a script we use for deploy, running locally `ssh user@serever ./deploy.sh` to launch new versions of our applications.

## `update/`

This is a pair of Ansible Playbooks and environment settings to automatically run Rosie and update Jarbas.