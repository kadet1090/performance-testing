#!/usr/bin/env python
from elasticsearch_dsl import Search, A, Q
from argparse import ArgumentParser
import humanize
import pandas as pd 
import utils.args

from utils.queries import time_query, memory_query, cpu_query
from utils.aggs import add_requests_aggs, add_memory_aggs, add_cpu_aggs, resource_generator, request_generator

def get_memory_stats(elasticsearch, start, end, containers = [], additional_filter = None):
    query = memory_query(start, end, containers, additional_filter)

    search = Search(using=elasticsearch, index="metricbeat-*") \
        .extra(size=0) \
        .query(query)

    add_memory_aggs(search.aggs)
    
    response = search.execute()
    return pd.DataFrame(resource_generator(response.aggregations)).set_index("container")

def get_cpu_stats(elasticsearch, start, end, containers = [], additional_filter = None):
    query = cpu_query(start, end, containers, additional_filter)

    search = Search(using=elasticsearch, index="metricbeat-*") \
        .extra(size=0) \
        .query(query)

    add_cpu_aggs(search.aggs)
    
    response = search.execute()
    return pd.DataFrame(resource_generator(response.aggregations)).set_index("container")

def get_request_stats(elasticsearch, start, end, per_path = False, additional_filter = None):
    query = time_query(start, end)

    if additional_filter is not None:
        query = query & additional_filter

    search = Search(using=elasticsearch, index="locust*") \
        .extra(size=0) \
        .query(query)
    
    add_requests_aggs(search.aggs)
    if per_path:
        add_requests_aggs(search.aggs.bucket('per_path', 'terms', field="path.keyword", size=1000))

    response = search.execute()
    
    data = request_generator(response.aggs, start, end)
    return pd.DataFrame(data).set_index("path")

if __name__ == "__main__":
    parser = ArgumentParser(description="Extract statistical data from Elasticsearch")

    utils.args.add_elastic_arg(parser)
    utils.args.add_containers_arg(parser)
    utils.args.add_date_range_args(parser)
    utils.args.add_per_path_arg(parser)
    utils.args.add_resources_args(parser)

    args = parser.parse_args()
    es   = args.elasticsearch

    start, end = getattr(args, 'from'), getattr(args, 'to')

    requests_df = get_request_stats(es, start, end, args.per_path)
    print(requests_df)

    if args.memory:
        memory_df = get_memory_stats(es, start, end, containers=args.containers)
        print(memory_df.to_string(formatters={ column: humanize.naturalsize for column in memory_df.columns }))

    if args.cpu:
        cpu_df = get_cpu_stats(es, start, end, containers=args.containers)
        print(cpu_df.to_string(formatters={ column: "{:.1%}".format for column in cpu_df.columns }))
