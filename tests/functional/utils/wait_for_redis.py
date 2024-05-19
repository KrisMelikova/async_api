import time

from redis import Redis

if __name__ == '__main__':
    redis_client = Redis(hosts='http://cache-1', port=6379)
    while True:
        print("Pinging redis")
        if redis_client.ping():
            break
        time.sleep(1)
