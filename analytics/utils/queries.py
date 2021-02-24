from elasticsearch_dsl import Q

def time_query(start, end):
    return Q("range", **{'@timestamp': { 
        'gte': start.isoformat(),
        'lte': end.isoformat(),
    }})

def containers_query(containers):
    return Q("terms", **{"container.name": containers})