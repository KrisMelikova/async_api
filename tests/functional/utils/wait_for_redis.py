import time
import logging

from redis import Redis
from redis.exceptions import ConnectionError

if __name__ == "__main__":
    redis_client = Redis(host="cache", port=6379)
    while True:
        logging.info("Pinging redis")
        try:
            if redis_client.ping():
                break
        except (ConnectionError, ConnectionRefusedError) as e:
            logging.error("Failed to connect to redis...")
        time.sleep(1)
