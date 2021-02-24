from elasticsearch_dsl import Q
from functools import partial

def time_query(start, end):
    return Q("range", **{'@timestamp': { 
        'gte': start.isoformat(),
        'lte': end.isoformat(),
    }})

def containers_query(containers):
    return Q("terms", **{"container.name": containers})

def resource_query(start, end, resource, containers=[], additional_filter=None):
    query = time_query(start, end) & Q("exists", field=f"docker.{resource}")

    if len(containers) > 0:
        query = query & containers_query(containers)

    if additional_filter is not None:
        query = query & additional_filter

    return query

def memory_query(start, end, containers=[], additional_filter=None):
    return resource_query(start, end, "memory", containers, additional_filter)

def cpu_query(start, end, containers=[], additional_filter=None):
    return resource_query(start, end, "cpu", containers, additional_filter)