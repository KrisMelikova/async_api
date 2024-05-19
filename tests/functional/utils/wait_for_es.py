import time

from elasticsearch import Elasticsearch

if __name__ == '__main__':
    es_client = Elasticsearch(hosts='http://functional-search-1:9200', verify_certs=False)
    while True:
        if es_client.ping():
            break
        time.sleep(1)