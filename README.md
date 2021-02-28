PHP Web/Application Servers benchmark
========================

This repository contains simple benchmark suite for testing performance of different hosting configurations for PHP
applications. System Under Test (SUT) is based on the official ["Symfony Demo Application"][1], which was slightly
modified to add more time demanding tasks in form of posts with code highlighted by [keylighter][2].

Load tests are performed using [locust][6] utility, [elasticsearch][7] is used as storage for all the metrics. Hardware
utilization metrics are collected by [metricbeat docker module][8].

Requirements
------------

* [docker][3] and [docker-compose][4] installed;
* Python 3.9 installed, [virtualenv][5] highly recommended - required for analytics;
* `make` installed for building all the docker images;
* At least 4GB of RAM available;
* Linux based OS - it may or may not work as intended on other OS. Be aware, that docker works natively only on linux so
  on MacOS and Windows it could have bigger performance impact.

Setup
-----
This project makes extensive use of containers. All required images can be built using provided `Makefile` with
simple `make` command. If for some reason you will ever need to rebuild images (for example after updating the project)
you may have to use `make -B all` command to force rebuild.

To use provided analytic tools in `analytics` directory it is highly recommended to setup [virtualenv][5] for python:

```bash
$ python -m venv venv
$ source ./venv/bin/activate
```

All requirements are specified in `requirements.txt`, to install them just use `pip -r requirements.txt`, remember to do
that in virtualenv!

To properly setup indexes and kibana views you have to run few more commands:
```bash
$ docker-compose up -d kibana elastic # this will run kibana and elasticsearch
$ docker-compose run metricbeat setup # this will add indexes and views for metricbeat (hardware utilization)
$ ./analytics/setup.py                # this will add indexes and views for performance metrics
$ docker-compose down                 # this will turn off kibana and elasticsearch
```

Those steps will have to be repeated after tearing down docker volumes (for example after doing `docker-compose down 
-v`).

Basic Usage
-----
All services are defined in the main `docker-compose.yml` file. You can start all of them with `docker-compose`:

```bash
$ docker-compose up
```

You can also start the services selectively by using their names - architecture and all the services are described in
more details in [separate document][00-architecture]. By default, services can be accessed on addresses listed below:

```
Stats and metrics
http://localhost:9200 - ElasticSearch (stats and metrics)
http://localhost:5601 - Kibana (visualization)

Load testing
http://localhost:8080 - Locust master

Various frontends
http://localhost:8081 - Roadrunner (standalone)
http://localhost:8082 - Builtin PHP Server (php -S)
http://localhost:8083 - nginx + fpm
http://localhost:8084 - Apache2 (mod_php)
http://localhost:8085 - Roadrunner + nginx for static content
http://localhost:8086 - PHP-PM + nginx for static content
```

Please consult [load testing document][01-load-testing] for details on how load tests are constructed and how to run
them.

Developing
----------
If for some reason you want to make changes to the SUT you can use much simpler `docker-compose.dev.yml` file:

```bash
$ docker-compose -f docker-compose.dev.yml up
```

This will start one `php` based on builtin PHP server that has source code mounted on and therefore it is easy to 
make changes. The created container also contains composer, so if you want to install some dependencies you should do it 
from this container (to assure compatibility):
```bash
$ docker-compose -f docker-compose.dev.yml exec -u $(id -u) phpcomposer ... 
```
Symfony console commands can be called in almost the same way:
```bash 
$ docker-compose -f docker-compose.dev.yml exec php console ... 
```

Remember that if you want to benchmark the changes you need to rebuild the containers using `make` command!

Further developing and contributing guidelines can be found [in the docs][d0-developing]

[1]: https://github.com/symfony/demo
[2]: https://github.com/kadet1090/keylighter
[3]: https://docs.docker.com/get-docker
[4]: https://docs.docker.com/compose/install/
[5]: https://docs.python.org/3/library/venv.html
[6]: https://locust.io/
[7]: https://www.elastic.co/elasticsearch/
[8]: https://www.elastic.co/guide/en/beats/metricbeat/current/metricbeat-module-docker.html
[00-architecture]: ./docs/00-architecture.md
[01-load-testing]: ./docs/01-load-testing.md
[d0-developing]: ./docs/d0-developing.md
