#!/usr/bin/env python
from elasticsearch_dsl import Search, A, Q
from argparse import ArgumentParser
import humanize
import pandas as pd 
import utils.args

from utils.queries import time_query, containers_query
from utils.aggs import add_requests_aggs, add_memory_aggs, add_cpu_aggs

def get_memory_stats(elasticsearch, start, end, containers = [], additional_filter = None):
    query = time_query(start, end) & Q("exists", field="docker.memory")

    if len(containers) > 0:
        query = query & containers_query(containers)

    if additional_filter is not None:
        query = query & additional_filter

    search = Search(using=elasticsearch, index="metricbeat-*") \
        .extra(size=0) \
        .query(query)

    add_memory_aggs(search.aggs)
    
    response = search.execute()

    def generator():
        for bucket in response.aggregations.containers.buckets:
            yield {
                "container": bucket.key,
                "baseline": bucket.baseline.value,
                "peak": bucket.peak.value,
                "average": bucket.average.value,
                **{ f"{int(float(percentile))}th percentile": float(value) for percentile, value in bucket.percentiles.values.to_dict().items() }
            }

    return pd.DataFrame(generator()).set_index("container")

def get_cpu_stats(elasticsearch, start, end, containers = [], additional_filter = None):
    query = time_query(start, end) & Q("exists", field="docker.cpu")

    if len(containers) > 0:
        query = query & containers_query(containers)

    if additional_filter is not None:
        query = query & additional_filter

    search = Search(using=elasticsearch, index="metricbeat-*") \
        .extra(size=0) \
        .query(query)

    add_cpu_aggs(search.aggs)
    
    response = search.execute()

    def generator():
        for bucket in response.aggregations.containers.buckets:
            yield {
                "container": bucket.key,
                "baseline": bucket.baseline.value,
                "peak": bucket.peak.value,
                "average": bucket.average.value,
                **{ f"{int(float(percentile))}th percentile": float(value) for percentile, value in bucket.percentiles.values.to_dict().items() }
            }

    return pd.DataFrame(generator()).set_index("container")

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

    utils.args.add_elastic_arg(parser)
    utils.args.add_containers_arg(parser)
    utils.args.add_date_range_args(parser)
    utils.args.add_per_path_arg(parser)

    parser.add_argument(
        '--cpu', '-C', 
        dest='cpu', action='store_true',
        help="Enable cpu stats")

    parser.add_argument(
        '--memory', '-M',
        dest='memory', action='store_true',
        help="Enable memory stats")

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
