# Services architecture overview

![architecture overview](./images/architecture.png)
**Figure 1. Benchmark architecture overview.**

This document aims to describe architecture of the project in more detail. The functional overview of the architecture is 
presented on the figure 1. In general, services can be categorized into three groups with different tasks, described 
in later sections. 

All the services are properly containerized and whole stack is described by the main `docker-compose.yml` file. 
Communication between load generator and system under test is meant to be done solely via the docker network created by 
`docker-compose`, ports from frontend services are exposed only for the user convenience.

## Metric collection
Services from this category are responsible for properly handling metrics and exposing them to further analysis. It 
consists of three independent services:

### ElasticSearch
```yaml
elastic:
  image: docker.elastic.co/elasticsearch/elasticsearch:7.11.0
  environment:
    - "discovery.type=single-node"
    - "ES_JAVA_OPTS=-Xms256m -Xmx256m"
  ports:
    - 9200:9200
  volumes:
    - esdata:/usr/share/elasticsearch/data
```

ElasticSearch is responsible for collecting and aggregating metrics collected from other services. In this case it 
is run in the `single-node` mode, which is not recommended for production usage. In the case of this particular 
application it can be used, as loss of the data would not be catastrophic. All persistent data is stored in the 
persistent docker volume, so it won't be lost after container recreation. The elasticsearch API is exposed to host 
by the standard port `9200`.

### Kibana
```yaml
kibana:
  image: docker.elastic.co/kibana/kibana:7.11.0
  environment:
    ELASTICSEARCH_HOSTS: http://elastic:9200/
  ports:
    - 5601:5601
  depends_on: ["elastic"]
```

Kibana is used to visualize and browse collected metrics. It can also be used to do simple analysis of the data and 
to develop queries and aggregations that could be later used by some scripts. It is exposed to the host by the 
standard port `5601`.

### Metricbeat
```yaml
metricbeat:
  image: docker.elastic.co/beats/metricbeat:7.11.0
  restart: on-failure
  user: root
  depends_on:
    - kibana
    - elastic
  volumes:
    - /var/run/docker.sock:/var/run/docker.sock:ro
    - ./docker/metricbeat.yml:/usr/share/metricbeat/metricbeat.yml:ro
    - metricbeat:/usr/share/metricbeat/data
  environment:
    - ELASTICSEARCH_HOST=http://elastic:9200
    - KIBANA_HOST=http://kibana:5601
```

The job of the metricbeat service is to collect information about hardware utilization and to push it to the 
elasticsearch. As we are interested only in per service stats, metrics are only collected from the [docker module][1]. 
Docker API is accessible to metricbeat via volume mount of host's docker socket. Metricbeat depends on fully 
bootstrapped kibana to work properly, but there is no simple solution to run it after kibana is ready - therefore it 
must be configured to restart after failure.

Exact configuration for this service can be found in [`/docker/metricbeat.yml`](../docker/metricbeat.yml) file.

## Load generation

## System Under Test

[1]: https://www.elastic.co/guide/en/beats/metricbeat/current/metricbeat-module-docker.html
