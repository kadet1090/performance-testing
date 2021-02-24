from argparse import ArgumentParser
from elasticsearch.client import Elasticsearch
from datetime import datetime

def add_elastic_arg(parser: ArgumentParser):
    parser.add_argument(
        '--elasticsearch', '-e',
        nargs='*', 
        dest='elasticsearch', 
        default="http://localhost:9200", 
        type=lambda hosts: Elasticsearch(hosts), 
        help="Elasticsearch host")

def add_containers_arg(parser: ArgumentParser):
    parser.add_argument(
        '--container', '-c',
        nargs='*',
        dest='containers', type=str, 
        help="container name")

def add_date_range_args(parser: ArgumentParser):
    parser.add_argument(
        'from',
        type=datetime.fromisoformat, 
        help="Date of the experiment start")

    parser.add_argument(
        'to', 
        type=datetime.fromisoformat, 
        help="Date of the experiment end")

def add_per_path_arg(parser: ArgumentParser):
    parser.add_argument(
        '--per-path', '-p', 
        dest='per_path', action='store_true',
        help="Enable per path stats")

def add_resources_args(parser: ArgumentParser):
    parser.add_argument(
        '--cpu', '-C', 
        dest='cpu', action='store_true',
        help="Enable cpu stats")

    parser.add_argument(
        '--memory', '-M',
        dest='memory', action='store_true',
        help="Enable memory stats") 