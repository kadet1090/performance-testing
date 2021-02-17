#!/usr/bin/env python

from elasticsearch.client import Elasticsearch
from elasticsearch_dsl import Search, A, Q
from argparse import ArgumentParser
from datetime import datetime

parser = ArgumentParser(description="Extract statistical data from Elasticsearch")
parser.add_argument(
    '--elasticsearch', '-e', 
    dest='elasticsearch', default="http://localhost:9200", type=str, 
    help="Elasticsearch host")


parser.add_argument(
    'from',
    type=datetime.fromisoformat, 
    help="Date of the experiment start")

parser.add_argument(
    'to', 
    type=datetime.fromisoformat, 
    help="Date of the experiment end")

if __name__ == "__main__":
    args = parser.parse_args()
    es   = Elasticsearch(hosts=[ args.elasticsearch ])

    time_query = Q("range", **{'@timestamp': { 
        'gt': getattr(args, 'from').isoformat(),
        'lt': getattr(args, 'to').isoformat(),
    }})

    locust_search = Search(using=es, index="locust*").extra(size=0).query(time_query)
    locust_search.aggs.metric('total_percentiles', 'percentiles', field="stats.response_times")
    locust_search.aggs \
        .bucket('per_path', 'terms', field="path.keyword") \
        .metric('percentiles', 'percentiles', field="stats.response_times") \
        .metric('request_count', 'sum', field="stats.num_requests") \
        .metric('failures_count', 'sum', field="stats.num_failures") \
        .metric('content_length', 'avg', field="stats.total_content_length")
    
    response = locust_search.execute()
    print("Percentiles: ")
    for percentile, value in response.aggregations.total_percentiles.values.to_dict().items():
        print(f"{percentile}%: {value:.1f}")
    