import pandas as pd 
from argparse import ArgumentParser
from yaml import load
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

from stats import get_request_stats, get_memory_stats, get_cpu_stats
import utils.args
import humanize

time_formatter = "{:.0f}ms".format
percent_formatter = "{:.1%}".format
memory_formatter = humanize.naturalsize

formatters = {
    "minimum": time_formatter,
    "average": time_formatter,
    "maximum": time_formatter,
    "rps": "{:.2f}".format,
    "50th percentile": time_formatter,
    "80th percentile": time_formatter,
    "95th percentile": time_formatter,
    "peak memory": memory_formatter,
    "95th memory percentile": memory_formatter,
    "average cpu": percent_formatter,
    "95th cpu percentile": percent_formatter,
}

if __name__ == "__main__":
    parser = ArgumentParser("Summarizes results")
    parser.add_argument("definitions", help="YAML file with test definitions")
    parser.set_defaults(format=lambda df: pd.DataFrame.to_string(df, formatters=formatters))

    output_format_group = parser.add_mutually_exclusive_group()
    output_format_group.add_argument(
        "--latex", "-l", 
        help="Output as LaTeX table", 
        const=lambda df: pd.DataFrame.to_latex(df, formatters=formatters), 
        action='store_const', 
        dest="format")
    output_format_group.add_argument(
        "--csv", "-c", 
        help="Output as CSV", 
        const=pd.DataFrame.to_csv, 
        action='store_const', 
        dest="format")

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

    stats_df = stats_df.set_index(["suite"])
    stats_df = stats_df.drop(columns=["content length", "requests"])

    print(args.format(stats_df))