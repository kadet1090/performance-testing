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
    .metric('baseline', 'min', field="docker.memory.usage.total") \
    .metric('average', 'avg', field="docker.memory.usage.total") \
    .metric('percentiles', 'percentiles', field="docker.memory.usage.total", percents=[50, 80, 95]) \
    .metric('peak', 'max', field="docker.memory.usage.max")

def add_cpu_aggs(agg: AggBase):
    return agg \
    .bucket('containers', 'terms', field="container.name", size=1000) \
    .metric('baseline', 'min', field="docker.cpu.total.pct") \
    .metric('average', 'avg', field="docker.cpu.total.pct") \
    .metric('percentiles', 'percentiles', field="docker.cpu.total.pct", percents=[50, 80, 95]) \
    .metric('peak', 'max', field="docker.cpu.total.pct") 