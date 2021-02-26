#!/usr/bin/env python

from argparse import ArgumentParser
from elasticsearch.client import Elasticsearch, IndicesClient
import utils.args
import requests
import os

dirname = os.path.dirname(__file__)

if __name__ == "__main__":
    parser = ArgumentParser("Initialize elasticsearch indexes")
    utils.args.add_elastic_arg(parser)
    parser.add_argument("--kibana",
                        "-k",
                        dest="kibana",
                        help="Kibana URL",
                        default="http://localhost:5601")

    args = parser.parse_args()

    es = args.elasticsearch  # type:Elasticsearch
    indices = IndicesClient(es)

    print("Creating locust* index template")
    indices.put_index_template(
        "locust_template", {
            "index_patterns": ["locust*"],
            "template": {
                "settings": {
                    "number_of_replicas": 1,
                },
                "mappings": {
                    "properties": {
                        "@timestamp": {
                            "type": "date"
                        },
                        "client_id": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "host": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "method": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "path": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "stats": {
                            "properties": {
                                "max_response_time": {
                                    "type": "float"
                                },
                                "min_response_time": {
                                    "type": "float"
                                },
                                "num_failures": {
                                    "type": "long"
                                },
                                "num_none_requests": {
                                    "type": "long"
                                },
                                "num_requests": {
                                    "type": "long"
                                },
                                "response_times": {
                                    "type": "long"
                                },
                                "total_content_length": {
                                    "type": "long"
                                },
                                "total_response_time": {
                                    "type": "float"
                                }
                            }
                        }
                    },
                    "numeric_detection": True,
                }
            }
        })

    print("Creating locust* kibana index pattern")
    requests.post(f"{args.kibana}/api/saved_objects/_import",
                  files={
                      "file": ("export.ndjson",
                               open(os.path.join(dirname, "kibana/index-pattern.ndjson"), "rb"), 
                               'application/ndjson')
                  },
                  headers={"kbn-xsrf": "true"})
