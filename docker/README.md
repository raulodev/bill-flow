# docker-compose files

This folder contains examples of docker-compose files for running the application.

<!-- ## docker-compose.yml

This file is an example of a docker-compose file that uses the PostgreSQL database. -->

## docker-compose-sqlite.yml

This file is an example of a docker-compose file that uses the SQLite database.


## Usage

To start the application, run the following command:

```shell
docker compose -f docker/docker-compose-sqlite.yml up
```
Open your browser and navigate to `http://localhost:8080/docs` to access the Swagger UI.


