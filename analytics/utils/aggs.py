from elasticsearch_dsl.aggs import AggBase

def add_requests_aggs(agg: AggBase):
    return agg \
    .metric('percentiles', 'percentiles', field="stats.response_times", percents=[ 50, 80, 95 ]) \
    .metric('requests_count', 'sum', field="stats.num_requests") \
    .metric('max_time', 'max', field="stats.max_response_time") \
    .metric('avg_time', 'avg', field="stats.response_times") \
    .metric('min_time', 'min', field="stats.min_response_time") \
    .metric('failures_count', 'sum', field="stats.num_failures") \
    .metric('content_length', 'avg', field="stats.total_content_length")

def add_memory_aggs(agg: AggBase):
    return agg \
    .bucket('containers', 'terms', field="container.name") \
    .metric('minimum', 'min', field="docker.memory.usage.total") \
    .metric('average', 'avg', field="docker.memory.usage.total") \
    .metric('percentiles', 'percentiles', field="docker.memory.usage.total", percents=[50, 80, 95]) \
    .metric('peak', 'max', field="docker.memory.usage.max")

def add_cpu_aggs(agg: AggBase):
    return agg \
    .bucket('containers', 'terms', field="container.name", size=1000) \
    .metric('minimum', 'min', field="docker.cpu.total.pct") \
    .metric('average', 'avg', field="docker.cpu.total.pct") \
    .metric('percentiles', 'percentiles', field="docker.cpu.total.pct", percents=[50, 80, 95]) \
    .metric('peak', 'max', field="docker.cpu.total.pct") 

def elastic_interval_to_seconds(interval: str):
    units = [
        (["miliseconds", "ms"], 1e-3),
        (["seconds", "s"], 1),
        (["minutes", "m"], 60),
    ]

    for suffixes, multiplier in units:
        if any([ interval.endswith(suffix) for suffix in suffixes ]):
            return int(int(''.join(filter(str.isdigit, interval))) * multiplier)

def time_bucket(agg: AggBase, start, end, interval="5s"):
    offset = int(start.timestamp() % elastic_interval_to_seconds(interval))
    return agg.bucket("time", 'date_histogram', field="@timestamp", time_zone="Europe/Warsaw", fixed_interval=interval, offset=f"+{offset}s")

def extract_percentiles(percentiles, format="{}th percentile".format):
    return { format(int(float(percentile))): float(value) for percentile, value in percentiles.values.to_dict().items() }

def get_request_observation(results, start, end):
    return {
        "minimum": results.min_time.value,
        "average": results.avg_time.value,
        "maximum": results.max_time.value,
        "content length": results.content_length.value,
        "requests": int(results.requests_count.value),
        "failures": int(results.failures_count.value),
        "rps": results.requests_count.value / (end - start).total_seconds(),
        **extract_percentiles(results.percentiles)
    }

def get_resource_observation(container):
    return {
        "container": container.key,
        "minimum": container.minimum.value,
        "peak": container.peak.value,
        "average": container.average.value,
        **extract_percentiles(container.percentiles)
    }

def resource_generator(aggregation):
    for bucket in aggregation.containers.buckets:
        yield get_resource_observation(bucket)

def request_generator(aggregation, start, end):
    yield { "path": "all", **get_request_observation(aggregation, start, end) }
    if "per_path" in aggregation:
        for bucket in aggregation.per_path.buckets:
            yield { "path": bucket.key, **get_request_observation(bucket, start, end) }