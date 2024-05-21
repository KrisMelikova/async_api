import time
import logging
from elasticsearch import Elasticsearch

if __name__ == "__main__":
    while True:
        time.sleep(30)
        logging.info("Pinging Elastic")
        es_client = Elasticsearch(
            hosts="http://search:9200",
            verify_certs=False,
            request_timeout=1000,
            retry_on_timeout=False,
        )
        if es_client.ping(error_trace=False):
            logging.info("The connection is established")
            break
