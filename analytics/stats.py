#!/usr/bin/env python

from elasticsearch.client import Elasticsearch
from elasticsearch_dsl import Search, A, Q
from argparse import ArgumentParser, BooleanOptionalAction
from datetime import datetime
from pprint import PrettyPrinter
import humanize

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
    dest='per_path', action=BooleanOptionalAction,
    help="Enable per path stats")

parser.add_argument(
    'from',
    type=datetime.fromisoformat, 
    help="Date of the experiment start")

parser.add_argument(
    'to', 
    type=datetime.fromisoformat, 
    help="Date of the experiment end")

def add_statistics_aggregation(agg):
    agg \
    .metric('percentiles', 'percentiles', field="stats.response_times", percents=[ 50, 80, 95 ]) \
    .metric('request_count', 'sum', field="stats.num_requests") \
    .metric('max_time', 'max', field="stats.max_response_time") \
    .metric('avg_time', 'avg', field="stats.response_times") \
    .metric('min_time', 'min', field="stats.min_response_time") \
    .metric('failures_count', 'sum', field="stats.num_failures") \
    .metric('content_length', 'avg', field="stats.total_content_length")

def print_stats(results):
    rps = results.request_count.value / 300

    print(f"\tMin time: {results.min_time.value:.1f}")
    print(f"\tAverage time: {results.avg_time.value:.1f}")
    print(f"\tMax time: {results.max_time.value:.1f}")
    for percentile, value in results.percentiles.values.to_dict().items():
        print(f"\t{int(float(percentile)):d}th percentile: {value:.1f}")
    print(f"\t(Average) Content length: {results.content_length.value:.1f}")
    print(f"\tRequests: {int(results.request_count.value)}")
    print(f"\tFailures: {int(results.failures_count.value)}")
    print(f"\tAverage Req/s: {rps:.1f}")

if __name__ == "__main__":
    args    = parser.parse_args()
    es      = Elasticsearch(hosts=[ args.elasticsearch ])
    printer = PrettyPrinter()

    time_query = Q("range", **{'@timestamp': { 
        'gte': getattr(args, 'from').isoformat(),
        'lte': getattr(args, 'to').isoformat(),
    }})

    container_name = Q("terms", **{"container.name": args.containers})
    memory_query   = time_query & container_name & Q("exists", field="docker.memory")
    cpu_query      = time_query & container_name & Q("exists", field="docker.cpu")

    locust_search = Search(using=es, index="locust*").extra(size=0).query(time_query)
    memory_search = Search(using=es, index="metricbeat-*").extra(size=0).query(memory_query)
    cpu_search    = Search(using=es, index="metricbeat-*").extra(size=0).query(cpu_query)

    add_statistics_aggregation(locust_search.aggs)
    if args.per_path:
        add_statistics_aggregation(locust_search.aggs.bucket('per_path', 'terms', field="path.keyword"))

    memory_search.aggs \
        .metric('avg_mem', 'avg', field="docker.memory.usage.total") \
        .metric('min_mem', 'min', field="docker.memory.usage.total") \
        .metric('max_mem', 'max', field="docker.memory.usage.total")

    cpu_search.aggs \
        .metric('avg_pct', 'avg', field="docker.cpu.total.pct") \
        .metric('min_pct', 'min', field="docker.cpu.total.pct") \
        .metric('max_pct', 'max', field="docker.cpu.total.pct")

    locust_response = locust_search.execute()
    memory_response = memory_search.execute()
    cpu_response    = cpu_search.execute()

    print("Total stats:")  
    print_stats(locust_response.aggregations)
    if args.per_path:
        for aggregation in locust_response.aggregations.per_path.buckets:
            print(f"{aggregation.key}")
            print_stats(aggregation)

    print("Memory stats:")
    print(f"\tMinimum usage: {humanize.naturalsize(memory_response.aggregations.min_mem.value)}")
    print(f"\tAverage usage: {humanize.naturalsize(memory_response.aggregations.avg_mem.value)}")
    print(f"\tMaximum usage: {humanize.naturalsize(memory_response.aggregations.max_mem.value)}")
            
    print("CPU stats:")
    print(f"\tMinimum usage: {cpu_response.aggregations.min_pct.value * 100:.1f}%")
    print(f"\tAverage usage: {cpu_response.aggregations.avg_pct.value * 100:.1f}%")
    print(f"\tMaximum usage: {cpu_response.aggregations.max_pct.value * 100:.1f}%")