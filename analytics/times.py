#!/usr/bin/env python
from elasticsearch_dsl import Search, A, Q
from argparse import ArgumentParser
import humanize
import pandas as pd 
import utils.args
from datetime import datetime

from utils.queries import memory_query, cpu_query, time_query
from utils.aggs import add_requests_aggs, add_memory_aggs, add_cpu_aggs, resource_generator, request_generator, time_bucket

def add_offset_variable(df: pd.DataFrame, index=[]):
    df["offset"] = (df["time"] - min(df["time"])).map(lambda x: x.total_seconds())
    df = df.set_index(["offset", *index])
    return df

def time_series_generator(aggregation, subgenerator):
    for time_segment in aggregation:
        segment_start = datetime.utcfromtimestamp(time_segment.key / 1000)
        for observation in subgenerator(time_segment):
            yield { "time": segment_start, **observation }

def get_memory_time_series(elasticsearch, start, end, containers = [], additional_filter = None, interval="5s"):
    query = memory_query(start, end, containers, additional_filter)

    search = Search(using=elasticsearch, index="metricbeat-*") \
        .extra(size=0) \
        .query(query)

    add_memory_aggs(time_bucket(search.aggs, start, end, interval=interval))
    
    response = search.execute()

    data = time_series_generator(response.aggregations.time, resource_generator)

    df = pd.DataFrame(data)
    df = add_offset_variable(df, ["container"])

    return df

def get_cpu_time_series(elasticsearch, start, end, containers = [], additional_filter = None, interval="5s"):
    query = cpu_query(start, end, containers, additional_filter)

    search = Search(using=elasticsearch, index="metricbeat-*") \
        .extra(size=0) \
        .query(query)

    add_cpu_aggs(time_bucket(search.aggs, start, end, interval=interval))
    
    response = search.execute()

    data = time_series_generator(response.aggregations.time, resource_generator)

    df = pd.DataFrame(data)
    df = add_offset_variable(df, ["container"])

    return df

def get_request_time_series(elasticsearch, start, end, per_path = False, additional_filter = None, interval="5s"):
    query = time_query(start, end)

    if additional_filter is not None:
        query = query & additional_filter

    search = Search(using=elasticsearch, index="locust*") \
        .extra(size=0) \
        .query(query)
    
    time_series = time_bucket(search.aggs, start, end, interval=interval)

    add_requests_aggs(time_series)
    if per_path:
        add_requests_aggs(time_series.bucket('per_path', 'terms', field="path.keyword", size=1000))

    response = search.execute()
    data = time_series_generator(response.aggs.time, lambda results: request_generator(results, start, end))

    df = pd.DataFrame(data)
    df = add_offset_variable(df, ["path"])
    return df

if __name__ == "__main__":
    parser = ArgumentParser(description="Extract time series data from Elasticsearch")

    utils.args.add_elastic_arg(parser)
    utils.args.add_containers_arg(parser)
    utils.args.add_date_range_args(parser)
    utils.args.add_per_path_arg(parser)
    utils.args.add_resources_args(parser)

    parser.add_argument("--interval", "-i", dest="interval", type=str, help="Interfal between next time steps", default="5s")
 
    args = parser.parse_args()
    es   = args.elasticsearch

    start, end = getattr(args, 'from'), getattr(args, 'to')

    requests_df = get_request_time_series(es, start, end, args.per_path, interval=args.interval)
    print(requests_df)

    if args.memory:
        memory_df = get_memory_time_series(es, start, end, containers=args.containers, interval=args.interval)
        print(memory_df.to_string(formatters={ column: humanize.naturalsize for column in memory_df.columns if column not in ["offset", "time"] }))

    if args.cpu:
        cpu_df = get_cpu_time_series(es, start, end, containers=args.containers, interval=args.interval)
        print(cpu_df.to_string(formatters={ column: "{:.1%}".format for column in cpu_df.columns if column not in ["offset", "time"] }))
