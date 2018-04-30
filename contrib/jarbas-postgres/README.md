# Jarbas's PostgreSQL

This is a simple repository with instructions to spin up the PostgreSQL used by
[Jarbas](https://jarbas.serenata.ai) in production. Requires
[Docker](https://docs.docker.com/install/), and
[Docker Machine](https://docs.docker.com/machine/install-machine/).

1. Copy `docker-compose.yml.example` as `docker-compose.yml`
2. Edit it adding the desired credentials (`POSTGRES_PASSWORD`, `POSTGRES_USER`
and `POSTGRES_DB`)
3. Spare a server to which you have SSH access
4. Add this server to Docker Machine:<br>
`docker-machine create --driver=generic --generic-ip-address=<server IP> jarbas-postgres`
5. Activate this Docker Machine:<br>
`eval $(docker-machine env jarbas-postgres)`
6. Spin up the database server:<br>`docker-compose up -d`

