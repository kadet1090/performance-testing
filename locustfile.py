import time
from locust import HttpUser, task, between
from random import randint, choice, seed

seed(3721)

class BlogUser(HttpUser):
    wait_time = between(1, 2.5)

    def on_start(self):
        self.max_pages = 3
        self.tags = [ tag['name'] for tag in self.client.get("/en/api/tags").json() ]
        self.queries = ["Lorem ipsum", "vitae velit", "Ubi est", "dolor"]

    @task(5)
    def browse_tag(self):
        tag = choice(self.tags)
        self.client.get(f"/en/blog?tag={tag}")

        posts = self.client.get(f"/en/api/posts?tag={tag}").json()
        self.browse_posts(posts, 3)

    @task(10)
    def browse_task(self):
        page = randint(1, self.max_pages)

        self.client.get(f"/en/blog/page/{page}")
        posts = self.client.get(f"/en/api/posts?page={page}").json()
        self.browse_posts(posts, 4)

    @task(2)
    def search_task(self):
        query = choice(self.queries)
        posts = self.client.get(f"/en/api/search?q={query}").json()
        self.browse_posts(posts, 2)

    def browse_posts(self, posts, count):
        if len(posts) == 0:
            return

        for _ in range(count):
            post = choice(posts)
            self.client.get(post['url'])
