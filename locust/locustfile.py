import time
import os
import sys
import gevent

from locust import HttpUser, task, tag, between, LoadTestShape, events
from random import randint, choice, seed
from queue import Queue
from elasticsearch import Elasticsearch, exceptions

class ElasticsearchLogger:
    def __init__(self, hosts, index="locust"):
        self.es = Elasticsearch(hosts)
        self.index = index
        self.queue = Queue()

    def log(self, stats):
        self.queue.put(stats)

    def run(self):
        while True:
            stats = self.queue.get()
            self.es.index(index=self.index, body=stats)

def select(dict, keys):
    return { key: dict[key] for key in keys }

def unwind(times):
    result = []
    for ms, count in times.items():
        result.extend([ ms ] * int(count))
    return result


# only on master node
if '--master' in sys.argv:
    ELASTICSEARCH_HOSTS = os.getenv("ELASTICSEARCH_HOST", "127.0.0.1:9200").split(sep=" ")
    logger = ElasticsearchLogger(ELASTICSEARCH_HOSTS)
    host = ""

    @events.worker_report.add_listener
    def save_to_elastic(client_id, data):
        global logger
        global host

        for stats in data['stats']:
            logger.log({
                "@timestamp": str(int(stats['start_time'] * 1000)),
                "client_id": client_id,
                "method": stats['method'],
                "path": stats['name'],
                "host": host,
                "stats": {
                    "num_requests": stats['num_requests'],
                    "num_failures": stats['num_failures'],
                    "num_none_requests": stats['num_none_requests'],
                    "total_response_time": stats['total_response_time'],
                    "total_content_length": stats['total_content_length'],
                    "max_response_time": stats['max_response_time'],
                    "min_response_time": stats['min_response_time'],
                    "response_times": unwind(stats['response_times']),
                }
            })

    @events.test_start.add_listener
    def save_host(environment):
        global host
        host = environment.host

    gevent.spawn(logger.run)

seed(3721)

MAX_USER_COUNT = int(os.getenv("MAX_USER_COUNT", "250"))
TIME_LIMIT     = int(os.getenv("TIME_LIMIT", "500"))

class CustomShapeLoad(LoadTestShape):
    time_limit = TIME_LIMIT
    user_count = MAX_USER_COUNT
    spawn_rate = 20

    def tick(self):
        run_time = self.get_run_time()

        if run_time < self.time_limit:
            return (self.user_count, self.spawn_rate)

        return None

def is_not_code_sample(post):
    return "Code Sample" not in post["title"]

class BlogUser(HttpUser):
    wait_time = between(1, 2.5)

    def on_start(self):
        self.max_pages = 3
        self.tags = [ tag['name'] for tag in self.client.get("/en/api/tags").json() if tag['name'] != 'sample' ]
        self.queries = ["Lorem ipsum", "vitae velit", "Ubi est", "dolor"]

    @tag("light")
    @task(5)
    def browse_tag(self):
        tag = choice(self.tags)
        self.client.get(f"/en/blog?tag={tag}")

        posts = self.client.get(f"/en/api/posts?tag={tag}").json()
        self.browse_posts(posts, 3, is_not_code_sample)

    @tag("heavy")
    @task(2)
    def browse_tag(self):
        tag = "sample"
        self.client.get(f"/en/blog?tag={tag}")

        posts = self.client.get(f"/en/api/posts?tag={tag}").json()
        self.browse_posts(posts, 3)

    @tag("light")
    @task(10)
    def browse_task(self):
        page = randint(1, self.max_pages)

        self.client.get(f"/en/blog/page/{page}")
        posts = self.client.get(f"/en/api/posts?page={page}").json()
        self.browse_posts(posts, 4, is_not_code_sample)

    @tag("light")
    @task(2)
    def search_task(self):
        query = choice(self.queries)
        posts = self.client.get(f"/en/api/search?q={query}").json()
        self.browse_posts(posts, 2, is_not_code_sample)

    def browse_posts(self, posts, count, check = lambda post: True):
        posts = [ post for post in posts if check(post) ]

        if len(posts) == 0:
            return

        for _ in range(count):
            post = choice(posts)
            self.client.get(post['url'])
