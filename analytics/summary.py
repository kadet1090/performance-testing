import pandas as pd 
from argparse import ArgumentParser
from yaml import load
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

from stats import get_request_stats, get_memory_stats, get_cpu_stats
import utils.args

if __name__ == "__main__":
    parser = ArgumentParser("Summarizes results")
    parser.add_argument("definitions", help="YAML file with test definitions")
    utils.args.add_elastic_arg(parser)

    args = parser.parse_args()

    definitions = load(open(args.definitions), Loader=Loader)

    stats_df = pd.DataFrame()

    for suite in definitions['tests']:
        current_df = get_request_stats(args.elasticsearch, suite['from'], suite['to'])
        current_df["suite"] = suite["name"]

        memory_df = get_memory_stats(args.elasticsearch, suite['from'], suite['to'], containers=suite["containers"])
        current_df["peak memory"] = sum(memory_df["peak"])
        current_df["95th memory percentile"] = sum(memory_df["95th percentile"])

        cpu_df = get_cpu_stats(args.elasticsearch, suite['from'], suite['to'], containers=suite["containers"])
        current_df["average cpu"] = sum(cpu_df["average"])
        current_df["95th cpu percentile"] = sum(cpu_df["95th percentile"])

        stats_df = stats_df.append(current_df)

    stats_df = stats_df.set_index(["suite"], append=True)
    stats_df = stats_df.drop(columns=["content length", "requests", "failures", "rps"])
    print(stats_df)