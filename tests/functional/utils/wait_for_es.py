import time
import logging
from elasticsearch import Elasticsearch
from elastic_transport import ConnectionError

if __name__ == '__main__':


    while True:
        logging.info("Pinging Elastic")
        try:
            es_client = Elasticsearch(hosts='http://search:9200', verify_certs=False)
            if es_client.ping():
                logging.info("The connection is established")
                break
        except:
            logging.warning("Failed to establish connection...")
        time.sleep(1)
