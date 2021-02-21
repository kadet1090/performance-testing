#!/usr/bin/env python

from elasticsearch.client import Elasticsearch
from elasticsearch_dsl import Search, A, Q
from argparse import ArgumentParser, BooleanOptionalAction
from datetime import datetime
from pprint import PrettyPrinter
import humanize
import pandas as pd 

def add_statistics_aggregation(agg):
    agg \
    .metric('percentiles', 'percentiles', field="stats.response_times", percents=[ 50, 80, 95 ]) \
    .metric('requests_count', 'sum', field="stats.num_requests") \
    .metric('max_time', 'max', field="stats.max_response_time") \
    .metric('avg_time', 'avg', field="stats.response_times") \
    .metric('min_time', 'min', field="stats.min_response_time") \
    .metric('failures_count', 'sum', field="stats.num_failures") \
    .metric('content_length', 'avg', field="stats.total_content_length")

def time_query(start, end):
    return Q("range", **{'@timestamp': { 
        'gte': start.isoformat(),
        'lte': end.isoformat(),
    }})

def containers_query(containers):
    return Q("terms", **{"container.name": containers})


def get_memory_stats(elasticsearch, start, end, containers = [], additional_filter = None):
    query = time_query(start, end) & Q("exists", field="docker.memory")

    if len(containers) > 0:
        query = query & containers_query(containers)

    if additional_filter is not None:
        query = query & additional_filter

    search = Search(using=elasticsearch, index="metricbeat-*") \
        .extra(size=0) \
        .query(query)

    search.aggs \
        .bucket('containers', 'terms', field="container.name") \
        .metric('baseline', 'min', field="docker.memory.usage.total") \
        .metric('average', 'avg', field="docker.memory.usage.total") \
        .metric('percentiles', 'percentiles', field="docker.memory.usage.total", percents=[50, 80, 95]) \
        .metric('peak', 'max', field="docker.memory.usage.max") \
    
    response = search.execute()

    def generator():
        for bucket in response.aggregations.containers.buckets:
            yield [
                bucket.key,
                bucket.baseline.value,
                bucket.peak.value,
                bucket.average.value,
                bucket.percentiles.values['50.0'],
                bucket.percentiles.values['80.0'],
                bucket.percentiles.values['95.0'],
            ]
    
    data = generator()

    df = pd.DataFrame(data, columns=["container", "baseline", "peak", "average", "median", "80th percentile", "95th percentile"])
    df = df.set_index("container")

    return df

def get_cpu_stats(elasticsearch, start, end, containers = [], additional_filter = None):
    query = time_query(start, end) & Q("exists", field="docker.cpu")

    if len(containers) > 0:
        query = query & containers_query(containers)

    if additional_filter is not None:
        query = query & additional_filter

    search = Search(using=elasticsearch, index="metricbeat-*") \
        .extra(size=0) \
        .query(query)

    search.aggs \
        .bucket('containers', 'terms', field="container.name", size=1000) \
        .metric('baseline', 'min', field="docker.cpu.total.pct") \
        .metric('average', 'avg', field="docker.cpu.total.pct") \
        .metric('percentiles', 'percentiles', field="docker.cpu.total.pct", percents=[50, 80, 95]) \
        .metric('peak', 'max', field="docker.cpu.total.pct") \
    
    response = search.execute()

    def generator():
        for bucket in response.aggregations.containers.buckets:
            yield [
                bucket.key,
                bucket.baseline.value,
                bucket.peak.value,
                bucket.average.value,
                bucket.percentiles.values['50.0'],
                bucket.percentiles.values['80.0'],
                bucket.percentiles.values['95.0'],
            ]
    
    data = generator()

    df = pd.DataFrame(data, columns=["container", "baseline", "peak", "average", "median", "80th percentile", "95th percentile"])
    df = df.set_index("container")

    return df

def get_request_stats(elasticsearch, start, end, per_path = False, additional_filter = None):
    query = time_query(start, end)

    if additional_filter is not None:
        query = query & additional_filter

    search = Search(using=elasticsearch, index="locust*") \
        .extra(size=0) \
        .query(query)

    search.aggs \
        .bucket('containers', 'terms', field="container.name", size=1000) \
        .metric('baseline', 'min', field="docker.cpu.total.pct") \
        .metric('average', 'avg', field="docker.cpu.total.pct") \
        .metric('percentiles', 'percentiles', field="docker.cpu.total.pct", percents=[50, 80, 95]) \
        .metric('peak', 'max', field="docker.cpu.total.pct") \
    
    add_statistics_aggregation(search.aggs)
    if per_path:
        add_statistics_aggregation(search.aggs.bucket('per_path', 'terms', field="path.keyword", size=1000))

    response = search.execute()

    def get_observation_from_agg(results):
        return {
            "minimum": results.min_time.value,
            "average": results.avg_time.value,
            "maximum": results.max_time.value,
            "content length": results.content_length.value,
            "requests": int(results.requests_count.value),
            "failures": int(results.failures_count.value),
            "rps": results.requests_count.value / (end - start).total_seconds(),
            **{ f"{int(float(percentile))}th percentile": float(value) for percentile, value in results.percentiles.values.to_dict().items() }
        }

    def generator():
        yield { "path": "all", **get_observation_from_agg(response.aggregations) }
        if per_path:
            for bucket in response.aggregations.per_path.buckets:
                yield { "path": bucket.key, **get_observation_from_agg(bucket) }
    
    data = generator()

    df = pd.DataFrame(data)
    df = df.set_index("path")

    return df


if __name__ == "__main__":
    parser = ArgumentParser(description="Extract statistical data from Elasticsearch")

    parser.add_argument(
        '--elasticsearch', '-e', 
        dest='elasticsearch', default="http://localhost:9200", type=str, 
        help="Elasticsearch host")

    parser.add_argument(
        '--container', '-c',
        nargs='*',
        dest='containers', type=str, 
        help="Container name")

    parser.add_argument(
        '--per-path', '-p', 
        dest='per_path', action='store_true',
        help="Enable per path stats")

    parser.add_argument(
        '--cpu', '-C', 
        dest='cpu', action='store_true',
        help="Enable cpu stats")

    parser.add_argument(
        '--memory', '-M',
        dest='memory', action='store_true',
        help="Enable memory stats")

    parser.add_argument(
        'from',
        type=datetime.fromisoformat, 
        help="Date of the experiment start")

    parser.add_argument(
        'to', 
        type=datetime.fromisoformat, 
        help="Date of the experiment end")

    args = parser.parse_args()
    es   = Elasticsearch(hosts=[ args.elasticsearch ])

    start, end = getattr(args, 'from'), getattr(args, 'to')

    requests_df = get_request_stats(es, start, end, args.per_path)
    print(requests_df)

    if args.memory:
        memory_df = get_memory_stats(es, start, end, containers=args.containers)
        print(memory_df.to_string(formatters={ column: humanize.naturalsize for column in memory_df.columns }))

    if args.cpu:
        cpu_df = get_cpu_stats(es, start, end, containers=args.containers)
        print(cpu_df.to_string(formatters={ column: "{:.1%}".format for column in cpu_df.columns }))
